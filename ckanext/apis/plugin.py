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

# from ckan.types import Schema
# import ckan.plugins as p
# import ckan.plugins.toolkit as tk


class ApisPlugin(plugins.SingletonPlugin):
    # plugins.implements(plugins.IDatasetForm)
    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IAuthFunctions)
    # plugins.implements(plugins.IDatasetForm)
    # plugins.implements(plugins.IFacets, inherit=True)


    # IBlueprint
    def get_blueprint(self):
        return views.get_blueprint()

    # # IConfigurer
    # def update_config(self, config_):
    #     toolkit.add_template_directory(config_, 'templates')
    #     toolkit.add_public_directory(config_, 'public')
    #     toolkit.add_resource('fanstatic', 'apis')
    #     toolkit.add_ckan_admin_tab(config_, 'apis_blueprint.admins', 'Apiset Config')

    #     if toolkit.check_ckan_version(min_version='2.9.0'):
    #         mappings = config_.get('ckan.legacy_route_mappings', {})
    #         if isinstance(mappings, string_types):
    #             mappings = json.loads(mappings)

    #         bp_routes = [
    #             'index', 'new', 'delete',
    #             'read', 'edit', 'manage_datasets',
    #             'apiset_package_list', 'admins', 'admin_remove'
    #         ]
    #         mappings.update({
    #             'apiset_' + route: 'apis_blueprint.' + route
    #             for route in bp_routes
    #         })
    #         # https://github.com/ckan/ckan/pull/4521
    #         config_['ckan.legacy_route_mappings'] = json.dumps(mappings)

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
                }

    def before_search(self, search_params):
        '''Prevents the apisets being shown in dataset search results.'''

        fq = search_params.get('fq', '')
        if 'dataset_type:apiset' not in fq:
            fq = u"{0} -dataset_type:apiset".format(fq)
            search_params['fq'] = fq

        return search_params

    def search_template(self):
        return 'apiset/search.html'

    # IAuthFunctions
    def get_auth_functions(self):
        return auth.get_auth_functions()


    # ITemplateHelpers
    def get_helpers(self):
        return {
            'get_apiset_pkgs': helpers.get_apiset_pkgs
        }

    # def is_fallback(self):
    #     # Return True to register this plugin as the default handler for
    #     # package types not handled by any other IDatasetForm plugin.
    #     return True

    # def package_types(self) -> list[str]:
    #     # This plugin doesn't handle any special package types, it just
    #     # registers itself as the default (above).
    #     return []