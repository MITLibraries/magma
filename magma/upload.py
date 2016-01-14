# -*- coding: utf-8 -*-
from __future__ import absolute_import

import glob
import os
from functools import reduce
from zipfile import ZipFile

from lxml import etree
from osgeo import gdal, ogr

from magma import UnsupportedFormat


class Shapefile(object):
    def __init__(self, file):
        self.ds = ogr.Open(file)
        self.layer = self.ds.GetLayer(0)

    def close(self):
        self.ds = None

    @property
    def name(self):
        return self.layer.GetName()

    @property
    def attributes(self):
        defn = self.layer.GetLayerDefn()
        for i in range(defn.GetFieldCount()):
            yield defn.GetFieldDefn(i).GetName()

    @property
    def extent(self):
        return self.layer.GetExtent()

    @property
    def data_type(self):
        return ("Vector", ogr.GeometryTypeToName(self.layer.GetGeomType()))


class GeoTIFF(object):
    attributes = []

    def __init__(self, file):
        self.ds = gdal.Open(file)

    @property
    def name(self):
        return os.path.basename(self.ds.GetDescription())

    @property
    def extent(self):
        xform = self.ds.GetGeoTransform()
        upper_left = xform[0], xform[3]
        lower_right = transform_point(xform, self.ds.RasterXSize,
                                      self.ds.RasterYSize)
        return upper_left[0], lower_right[0], lower_right[1], upper_left[1]

    @property
    def data_type(self):
        return 'Raster', 'Pixel'

    def close(self):
        self.ds = None


parser = etree.XMLParser(remove_blank_text=True)


class FGDC(object):
    def __init__(self, file):
        self.doc = etree.parse(file, parser=parser)
        self.root = self.doc.getroot()

    def write(self):
        return etree.tostring(self.doc, pretty_print=True)

    def set_extent(self, extent):
        westbc = self._get_path('idinfo/spdom/bounding/westbc')
        eastbc = self._get_path('idinfo/spdom/bounding/eastbc')
        southbc = self._get_path('idinfo/spdom/bounding/southbc')
        northbc = self._get_path('idinfo/spdom/bounding/northbc')
        if not all([westbc.text, eastbc.text, southbc.text, northbc.text]):
            westbc.text = str(extent[0])
            eastbc.text = str(extent[1])
            southbc.text = str(extent[2])
            northbc.text = str(extent[3])
        return self

    def set_data_type(self, datatype):
        direct = self._get_path('spdoinfo/direct')
        sdtstype = self._get_path('spdoinfo/ptvctinf/sdtsterm/sdtstype')
        if not direct.text:
            direct.text = datatype[0]
        if not sdtstype.text:
            sdtstype.text = datatype[1]
        return self

    def set_attributes(self, attrs):
        detailed = self._get_path('eainfo/detailed')
        if detailed.find('attr') is None:
            for attr in attrs:
                el = etree.SubElement(detailed, 'attr')
                label = etree.SubElement(el, 'attrlabl')
                label.text = attr
        return self

    def set_name(self, name):
        ftname = self._get_path('idinfo/citation/citeinfo/ftname')
        if not ftname.text:
            ftname.text = name
        return self

    def set_distribution(self):
        distinfo = etree.XML(_distribution_info, parser=parser)
        distrib = etree.SubElement(distinfo, 'distrib')
        distrib.append(etree.XML(_contact_info, parser=parser))
        self.root.append(distinfo)
        return self

    def set_metadata_contact(self):
        metc = self._get_path('metainfo/metc')
        if metc.find('cntinfo') is None:
            metc.append(etree.XML(_contact_info, parser=parser))
        return self

    def ensure_elements(self):
        elements = (
            'idinfo/citation/citeinfo/origin',
            'idinfo/citation/citeinfo/pubdata',
            'idinfo/citation/citeinfo/title',
            'idinfo/citation/citeinfo/pubinfo/publish',
            'idinfo/citation/citeinfo/onlink',
            'idinfo/descript/abstract',
            'idinfo/descript/purpose',
            'idinfo/timeperd/timeinfo/sngdate/caldate',
            'idinfo/timeperd/current',
            'idinfo/status/progress',
            'idinfo/status/update',
            'idinfo/keywords/theme/themekey',
            'idinfo/keywords/place/placekey',
            'idinfo/keywords/temporal/tempkey',
            'eainfo/detailed/attr/attrdef',
            'eainfo/detailed/attr/attrdefs',
        )
        for el in elements:
            self._get_path(el)
        return self

    def set_restricted_access(self):
        accconst = self._get_path('idinfo/accconst')
        accconst.text = "Restricted Access Online: Access granted to Licensee only. Available only to MIT affiliates."
        return self

    def _get_path(self, path):
        return get_path(path, self.root)


def process(ds, fgdc):
    metadata = FGDC(fgdc)
    metadata.set_extent(ds.extent).\
        set_data_type(ds.data_type).\
        set_attributes(ds.attributes).\
        set_name(ds.name).\
        set_distribution().\
        set_metadata_contact().\
        ensure_elements()
    return metadata


def datasource(datafile):
    ext = os.path.splitext(datafile)[1]
    if ext == '.zip':
        extract_dir = os.path.abspath(os.path.dirname(datafile))
        archive = ZipFile(datafile, 'r')
        try:
            archive.extractall(extract_dir)
        finally:
            archive.close()
        shpfile = glob.glob("%s/*.shp" % extract_dir)[0]
        return Shapefile(shpfile)
    elif ext in ('.tif', '.tiff'):
        return GeoTIFF(datafile)
    raise UnsupportedFormat


def get_path(path, root):
    return reduce(get_or_set, path.split('/'), root)


def get_or_set(root, child):
    el = root.find(child)
    if el is None:
        el = etree.SubElement(root, child)
    return el


_distribution_info = """
  <distinfo>
    <distliab>Although this data is being distributed by MIT, no warranty expressed or implied is made by the Institute as to the accuracy of the data and related materials. The act of distribution shall not constitute any such warranty, and no responsibility is assumed by the Institute in the use of this data, or related materials.</distliab>
  </distinfo>"""

_contact_info = """
  <cntinfo>
    <cntorgp>
      <cntorg>GIS Lab, MIT Libraries</cntorg>
    </cntorgp>
    <cntpos>GIS Specialist</cntpos>
    <cntaddr>
      <addrtype>mailing and physical address</addrtype>
      <address>77 Massachusetts Avenue, Rotch Library, 7-238</address>
      <city>Cambridge</city>
      <state>MA</state>
      <postal>02139-4307</postal>
      <country>USA</country>
    </cntaddr>
    <cntvoice>617-258-5598</cntvoice>
    <cntemail>gishelp@mit.edu</cntemail>
  </cntinfo>"""


def transform_point(xform, x, y):
    geo_x = xform[0] + x * xform[1] + y * xform[2]
    geo_y = xform[3] + x * xform[4] + y * xform[5]
    return geo_x, geo_y
