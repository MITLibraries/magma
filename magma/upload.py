# -*- coding: utf-8 -*-
from __future__ import absolute_import
from contextlib import closing
from functools import reduce
import glob

from osgeo import ogr
from lxml import etree


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


class FGDC(object):
    def __init__(self, file):
        self.doc = etree.parse(file)
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

    def _get_path(self, path):
        return get_path(path, self.root)


def process(data, fgdc):
    files = glob.glob("%s/*.shp" % data)
    metadata = FGDC(fgdc)
    with closing(Shapefile(files[0])) as ds:
        metadata.set_extent(ds.extent).set_data_type(ds.data_type)\
            .set_attributes(ds.attributes).set_name(ds.name)
    return metadata


def get_path(path, root):
    return reduce(get_or_set, path.split('/'), root)


def get_or_set(root, child):
    el = root.find(child)
    if el is None:
        el = etree.SubElement(root, child)
    return el
