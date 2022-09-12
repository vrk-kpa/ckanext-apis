# -*- coding: utf-8 -*-

from flask import Blueprint
import ckan.lib.base as base
import ckan.views.dataset as dataset
import ckan.logic as logic
import ckantoolkit as tk
import ckan.lib.helpers as h
from ckan.common import _, g, request
from ckan.views.home import CACHE_PARAMETERS
import ckan.lib.navl.dictization_functions as dict_fns
# from ckanext.showcase import views, utils as showcase_utils
from . import utils
import logging

_setup_template_variables = dataset._setup_template_variables
_get_pkg_template = dataset._get_pkg_template
check_access = logic.check_access
get_action = logic.get_action
tuplize_dict = logic.tuplize_dict
clean_dict = logic.clean_dict
parse_params = logic.parse_params
flatten_to_string_key = logic.flatten_to_string_key
NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized

apis = Blueprint('apis_blueprint', __name__)


def manage_datasets(id):
    return utils.manage_datasets_view(id)


apis.add_url_rule('/apiset/manage_datasets/<id>', view_func=manage_datasets, methods=[u'GET', u'POST'])

def get_blueprint():
    return [apis]