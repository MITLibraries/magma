# -*- coding: utf-8 -*-
from __future__ import absolute_import

from contextlib import closing

import pytest

from magma.upload import FGDC, GeoTIFF, Shapefile, process

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


@pytest.yield_fixture
def shp(shapefile):
    with closing(Shapefile(shapefile)) as datasource:
        yield datasource


@pytest.yield_fixture
def tif(geotiff):
    with closing(GeoTIFF(geotiff)) as datasource:
        yield datasource


def test_shapefile_has_name(shp):
    assert shp.name == 'SDE_DATA_BD_A8GNS_2003'


def test_shapefile_has_attributes(shp):
    attrs = list(shp.attributes)
    assert 'RC' in attrs


def test_shapefile_has_extent(shp):
    assert shp.extent == (-64.9080556, -64.6166667, 32.2333333, 32.4166667)


def test_shapefile_has_data_type(shp):
    assert shp.data_type == ('Vector', 'Point')


def test_raster_has_name(tif):
    assert tif.name == 'grayscale.tif'


def test_raster_has_empty_attributes(tif):
    assert tif.attributes == []


def test_raster_has_extent(tif):
    assert tif.extent == (-80.0, -60.0, 35.0, 45.0)


def test_raster_has_data_type(tif):
    assert tif.data_type == ('Raster', 'Pixel')


def test_sets_extent():
    doc = StringIO('<metadata></metadata>')
    r = FGDC(doc)
    r.set_extent((1, 2, 3, 4))
    assert r.doc.find('idinfo/spdom/bounding/westbc').text == '1'
    assert r.doc.find('idinfo/spdom/bounding/eastbc').text == '2'
    assert r.doc.find('idinfo/spdom/bounding/southbc').text == '3'
    assert r.doc.find('idinfo/spdom/bounding/northbc').text == '4'


def test_does_not_overwrite_extent():
    doc = StringIO("""
        <metadata>
          <idinfo>
            <spdom>
              <bounding>
                <westbc>5</westbc>
                <eastbc>6</eastbc>
                <southbc>7</southbc>
                <northbc>8</northbc>
              </bounding>
            </spdom>
          </idinfo>
        </metadata>""")
    r = FGDC(doc)
    r.set_extent((1, 2, 3, 4))
    assert r.doc.find('idinfo/spdom/bounding/westbc').text == '5'
    assert r.doc.find('idinfo/spdom/bounding/eastbc').text == '6'
    assert r.doc.find('idinfo/spdom/bounding/southbc').text == '7'
    assert r.doc.find('idinfo/spdom/bounding/northbc').text == '8'


def test_sets_attributes():
    doc = StringIO("<metadata/>")
    r = FGDC(doc)
    r.set_attributes(['foo', 'bar'])
    atrb = [e.text for e in r.root.iterfind('eainfo/detailed/attr/attrlabl')]
    assert atrb == ['foo', 'bar']


def test_does_not_overwrite_attributes():
    doc = StringIO("""
        <metadata>
            <eainfo>
                <detailed>
                    <attr>
                        <attrlabl>FOO</attrlabl>
                    </attr>
                    <attr>
                        <attrlabl>BAR</attrlabl>
                    </attr>
                </detailed>
            </eainfo>
        </metadata>""")
    r = FGDC(doc)
    r.set_attributes(['baz', 'gaz'])
    atrb = [e.text for e in r.root.iterfind('eainfo/detailed/attr/attrlabl')]
    assert atrb == ['FOO', 'BAR']


def test_sets_name():
    doc = StringIO("<metadata/>")
    r = FGDC(doc)
    r.set_name('foobar')
    assert r.doc.find('idinfo/citation/citeinfo/ftname').text == 'foobar'


def test_does_not_overwrite_name():
    doc = StringIO("""
        <metadata>
            <idinfo>
                <citation>
                    <citeinfo>
                        <ftname>foobaz</ftname>
                    </citeinfo>
                </citation>
            </idinfo>
        </metadata>""")
    r = FGDC(doc)
    r.set_name('foobar')
    assert r.doc.find('idinfo/citation/citeinfo/ftname').text == 'foobaz'


def test_sets_distribution():
    r = FGDC(StringIO('<metadata/>'))
    r.set_distribution()
    assert r.doc.find('distinfo/distliab').text.startswith("Although this")


def test_does_not_overwrite_distribution():
    r = FGDC(StringIO("""
        <metadata>
          <distinfo>
            <distliab>Something</distliab>
          </distinfo>
        </metadata>"""))
    r.set_distribution()
    distliabs = [e.text[:8] for e in r.doc.findall('distinfo/distliab')]
    assert all([t in distliabs for t in ['Although', 'Somethin']])


def test_sets_metadata_contact():
    r = FGDC(StringIO('<metadata/>'))
    r.set_metadata_contact()
    assert r.doc.find('metainfo/metc/cntinfo/cntorgp/cntorg').text == \
        "GIS Lab, MIT Libraries"


def test_does_not_overwrite_metadata_contact():
    r = FGDC(StringIO("""
        <metadata>
          <metainfo>
            <metc>
              <cntinfo>
                <cntorgp>
                  <cntorg>Foobar</cntorg>
                </cntorgp>
              </cntinfo>
            </metc>
          </metainfo>
        </metadata>"""))
    r.set_metadata_contact()
    assert r.doc.find('metainfo/metc/cntinfo/cntorgp/cntorg').text == \
        "Foobar"


def test_ensures_elements_exist():
    r = FGDC(StringIO('<metadata/>'))
    r.ensure_elements()
    assert r.doc.find('idinfo/citation/citeinfo/origin') is not None


def test_sets_restricted_access():
    r = FGDC(StringIO("""
        <metadata>
          <idinfo>
            <accconst>Foobar</accconst>
          </idinfo>
         </metadata>"""))
    r.set_restricted_access()
    assert r.doc.find('idinfo/accconst').text == "Restricted Access Online: Access granted to Licensee only. Available only to MIT affiliates."


def test_adds_keyword_thesauri():
    r = FGDC(StringIO("""
        <metadata>
          <idinfo>
            <keywords>
              <theme>
                <themekey>Foo</themekey>
              </theme>
              <place>
                <placekey>Bar</placekey>
              </place>
            </keywords>
          </idinfo>
        </metadata>"""))
    r.add_keywords()
    assert len(r.doc.findall('idinfo/keywords/theme/themekt')) == 1
    assert len(r.doc.findall('idinfo/keywords/place/placekt')) == 1


def test_process_ensures_elements_exist(shp):
    r = process(StringIO("<metadata/>"), shp)
    assert r.doc.find('idinfo/descript/purpose') is not None
