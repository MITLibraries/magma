# -*- coding: utf-8 -*-
from __future__ import absolute_import
import tempfile
import shutil
import os
from zipfile import BadZipfile
from contextlib import closing
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from flask import (Blueprint, flash, request, render_template, make_response,
                   session,)
from werkzeug import secure_filename

from magma.upload import process, datasource
from magma import UnsupportedFormat


home_page = Blueprint('home_page', __name__)


@home_page.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'data' in request.files and request.files['data']:
            datafile = request.files['data']
        else:
            flash('A datafile is required to proceed.', 'danger')
            return render_template('index.html')
        fgdc = request.files.get('metadata') or StringIO('<metadata/>')

        tmp = tempfile.mkdtemp()
        filename = os.path.join(tmp, secure_filename(datafile.filename))
        datafile.save(filename)

        try:
            with closing(datasource(filename)) as ds:
                metadata = process(ds, fgdc)
            if request.form['access'] == 'restricted':
                metadata.set_restricted_access()
            response = make_response(metadata.write())
            response.headers['Content-type'] = 'text/xml'
            response.headers['Content-Disposition'] = \
                'attachment; filename=fgdc.xml'
            return response
        except BadZipfile:
            flash('Could not open zipfile.', 'danger')
        except UnsupportedFormat:
            flash('Uploaded datafile should be either a zipped shapefile or a GeoTIFF.', 'danger')
        finally:
            shutil.rmtree(tmp)
    return render_template('index.html')
