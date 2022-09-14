# encoding: utf-8
from __future__ import annotations

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from .logic.action import get, create, update, delete
from . import views
from ckanext.apis.model import setup as model_setup
from . import helpers
from ckanext.apis.logic import auth
import json
import logging


class ApisPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IAuthFunctions)

    # IBlueprint
    def get_blueprint(self):
        return views.get_blueprint()

    # IConfigurable
    def configure(self, config):
        model_setup()

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'apis')
        

    def get_actions(self):
        return {
                'apiset_show': get.apiset_show,
                'apiset_list': get.apiset_list,
                'apiset_create': create.apiset_create,
                'apiset_update': update.apiset_update,
                'apiset_patch': update.apiset_patch,
                'apiset_delete': delete.apiset_delete,
                'apiset_package_list': get.apiset_package_list,
                'package_apiset_list': get.package_apiset_list,
                'apiset_package_association_create': create.apiset_package_association_create,
                'apiset_package_association_delete': delete.apiset_package_association_delete,
                }

    def before_search(self, search_params):
        '''Prevents the apisets being shown in dataset search results.'''

        fq = search_params.get('fq', '')
        if 'dataset_type:apiset' not in fq:
            fq = u"{0} -dataset_type:apiset".format(fq)
            search_params['fq'] = fq

        return search_params

    def package_form(self):
        return 'apiset/new_package_form.html'

    def search_template(self):
        return 'apiset/search.html'
        
    def edit_template(self):
        return 'apiset/edit_base.html'

    # IAuthFunctions
    def get_auth_functions(self):
        return auth.get_auth_functions()

    # ITemplateHelpers
    def get_helpers(self):
        return {
            'get_apiset_pkgs': helpers.get_apiset_pkgs
        }
