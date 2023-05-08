# encoding: utf-8
from __future__ import annotations

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from .logic.action import get, create, update, delete
from . import views
from ckanext.apis.model import setup as model_setup
from . import helpers
from ckanext.apis.logic import auth
import os
import sys
from ckanext.apis.logic.converters import save_to_groups


class ApisPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.ITranslation)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IValidators)


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
                'apiset_format_autocomplete': get.apiset_format_autocomplete,
                }

    # IValidators
    def get_validators(self):
        return {
            # NOTE: this is a converter. (https://github.com/vrk-kpa/ckanext-scheming/#validators)
            'save_to_groups': save_to_groups,
        }   

    def before_search(self, search_params):
        '''CKAN <2.10 compatibility method'''
        return self.before_dataset_search(search_params)

    def before_dataset_search(self, search_params):
        '''Prevents the apisets being shown in dataset search results.'''

        fq = search_params.get('fq', '')
        if 'dataset_type:apiset' not in fq:
            fq = u"{0} -dataset_type:apiset".format(fq)
            search_params['fq'] = fq

        return search_params

    def before_index(self, pkg_dict):
        '''CKAN <2.10 compatibility method'''
        return self.before_dataset_index(pkg_dict)

    def before_dataset_index(self, pkg_dict):
        if pkg_dict.get('type', None) == 'apiset':
            org_pkg = toolkit.get_action('package_show')({'ignore_auth': True}, {'id': pkg_dict.get('id')})
            apiset_res_formats = []

            for resource in org_pkg.get('resources', []):
                for format in resource.get('formats', '').lower().split(','):
                    if format not in apiset_res_formats:
                        apiset_res_formats.append(format)

            if len(apiset_res_formats) > 0:
                pkg_dict['res_format'] = apiset_res_formats

        return pkg_dict

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

    # ITranslation

    # The following methods copied from ckan.lib.plugins.DefaultTranslation so
    # we don't have to mix it into the class. This means we can use Apiset
    # even if ITranslation isn't available (less than 2.5).

    def i18n_directory(self):
            '''Change the directory of the *.mo translation files
            The default implementation assumes the plugin is
            ckanext/myplugin/plugin.py and the translations are stored in
            i18n/
            '''
            # assume plugin is called ckanext.<myplugin>.<...>.PluginClass
            extension_module_name = '.'.join(self.__module__.split('.')[0:2])
            module = sys.modules[extension_module_name]
            return os.path.join(os.path.dirname(module.__file__), 'i18n')

    def i18n_locales(self):
        '''Change the list of locales that this plugin handles
        By default the will assume any directory in subdirectory in the
        directory defined by self.directory() is a locale handled by this
        plugin
        '''
        directory = self.i18n_directory()
        return [d for
                d in os.listdir(directory)
                if os.path.isdir(os.path.join(directory, d))]

    def i18n_domain(self):
        '''Change the gettext domain handled by this plugin
        This implementation assumes the gettext domain is
        ckanext-{extension name}, hence your pot, po and mo files should be
        named ckanext-{extension name}.mo'''
        return 'ckanext-{name}'.format(name=self.name)