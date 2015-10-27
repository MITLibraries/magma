# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os

import pytest
from webtest import TestApp

from magma.app import create_app


@pytest.yield_fixture
def app():
    app = create_app()
    ctx = app.test_request_context()
    ctx.push()
    yield app
    ctx.pop()


@pytest.fixture
def testapp(app):
    return TestApp(app)


@pytest.fixture
def shapefile():
    return _fixtures('SDE_DATA_BD_A8GNS_2003/SDE_DATA_BD_A8GNS_2003.shp')


@pytest.fixture
def geotiff():
    return _fixtures('grayscale.tif')


def _fixtures(path):
    current_dir = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(current_dir, 'fixtures', path)
