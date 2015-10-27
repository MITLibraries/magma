# -*- coding: utf-8 -*-
from __future__ import absolute_import
import tempfile
import shutil
import os
from zipfile import ZipFile
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from flask import Blueprint, request, render_template, make_response
from werkzeug import secure_filename

from magma.upload import process


home_page = Blueprint('home_page', __name__)


@home_page.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        shp = request.files['data']
        fgdc = request.files['metadata']
        if not fgdc.filename:
            fgdc = StringIO('<metadata/>')
        tmp = tempfile.mkdtemp()
        filename = os.path.join(tmp, secure_filename(shp.filename))
        shp.save(filename)
        archive = ZipFile(filename, 'r')
        try:
            archive.extractall(tmp)
        finally:
            archive.close()
        try:
            metadata = process(tmp, fgdc)
        finally:
            shutil.rmtree(tmp)
        if request.form['access'] == 'restricted':
            metadata.set_restricted_access()
        response = make_response(metadata.write())
        response.headers['Content-type'] = 'text/xml'
        response.headers['Content-Disposition'] = 'attachment; filename=fgdc.xml'
        return response
    return render_template('index.html')
