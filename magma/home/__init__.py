# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os
import shutil
import tempfile
from contextlib import closing
from zipfile import BadZipfile

from flask import (Blueprint, flash, make_response, render_template, request,)
from werkzeug import secure_filename

from magma import UnsupportedFormat
from magma.upload import datasource, process

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


home_page = Blueprint('home_page', __name__)


@home_page.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        datafile = request.files.get('data')
        metadata = request.files.get('metadata')
        if not (datafile or metadata):
            flash('A datafile or FGDC file is required to proceed.', 'danger')
            return render_template('index.html')
        fgdc = metadata or StringIO('<metadata/>')

        if datafile:
            tmp = tempfile.mkdtemp()
            filename = os.path.join(tmp, secure_filename(datafile.filename))
            datafile.save(filename)
            try:
                with closing(datasource(filename)) as ds:
                    metadata = process(fgdc, ds)
            except BadZipfile:
                flash('Could not open zipfile.', 'danger')
                return render_template('index.html')
            except UnsupportedFormat:
                flash('Uploaded datafile should be either a zipped shapefile or a GeoTIFF.', 'danger')
                return render_template('index.html')
            finally:
                shutil.rmtree(tmp)
        else:
            metadata = process(fgdc)
        if request.form['access'] == 'restricted':
            metadata.set_restricted_access()
        response = make_response(metadata.write())
        response.headers['Content-type'] = 'text/xml'
        response.headers['Content-Disposition'] = \
            'attachment; filename=fgdc.xml'
        return response

    return render_template('index.html')
