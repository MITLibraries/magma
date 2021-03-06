# -*- coding: utf-8 -*-
from __future__ import absolute_import

from webtest import Upload


def test_can_load_index(testapp):
    r = testapp.get('/')
    assert r.status_code == 200
    assert 'form' in r


def test_submit_valid_form(testapp):
    form = testapp.get('/').form
    form['data'] = Upload('tests/fixtures/SDE_DATA_BD_A8GNS_2003.zip')
    form['metadata'] = Upload('tests/fixtures/fgdc.xml')
    res = form.submit()
    assert res.content_type == 'text/xml'


def test_submit_with_shapefile_without_metadata(testapp):
    form = testapp.get('/').form
    form['data'] = Upload('tests/fixtures/SDE_DATA_BD_A8GNS_2003.zip')
    res = form.submit()
    assert res.content_type == 'text/xml'


def test_submit_metadata_without_shapefile(testapp, fgdc):
    form = testapp.get('/').form
    form['metadata'] = Upload(fgdc)
    res = form.submit()
    assert res.content_type == 'text/xml'


def test_submit_with_invalid_shapefile(testapp):
    form = testapp.get('/').form
    form['data'] = Upload('tests/fixtures/fgdc.xml')
    res = form.submit()
    assert 'Uploaded datafile should be either a zipped shapefile or a GeoTIFF.' in res


def test_submits_geotiff_with_metadata(testapp, geotiff, fgdc):
    form = testapp.get('/').form
    form['data'] = Upload(geotiff)
    form['metadata'] = Upload(fgdc)
    res = form.submit()
    assert res.content_type == 'text/xml'


def test_submits_geotiff_without_metadata(testapp, geotiff):
    form = testapp.get('/').form
    form['data'] = Upload(geotiff)
    res = form.submit()
    assert res.content_type == 'text/xml'


def test_submit_requires_datafile_or_metadata(testapp):
    form = testapp.get('/').form
    res = form.submit()
    assert 'A datafile or FGDC file is required' in res


def test_submit_sets_restricted_access(testapp, fgdc):
    form = testapp.get('/').form
    form['metadata'] = Upload(fgdc)
    form['access'] = 'restricted'
    res = form.submit()
    assert 'Restricted Access Online' in res.lxml.find('idinfo/accconst').text
