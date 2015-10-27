# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os

from flask import Flask

from magma.home import home_page


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.update(SECRET_KEY=os.environ.get('SECRET_KEY', 'changeme'))
    register_blueprints(app)
    return app


def register_blueprints(app):
    app.register_blueprint(home_page)
