# -*- coding: utf-8 -*-
from __future__ import absolute_import
from contextlib import closing
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

import pytest

from magma.upload import Shapefile, FGDC


@pytest.yield_fixture
def shp(shapefile):
    with closing(Shapefile(shapefile)) as datasource:
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