import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckan.lib.plugins as lib_plugins
import ckan.lib.helpers as h
import os
import sys
from ckan import model as ckan_model
from . import views
from . import helpers
from .logic.action import get, create, update, delete
from model import setup as model_setup
from logic import auth
from six import string_types
import json
import utils

try:
    from ckan.common import OrderedDict
except ImportError:
    from collections import OrderedDict

c = toolkit.c
_ = toolkit._


class ApisPlugin(plugins.SingletonPlugin, lib_plugins.DefaultDatasetForm):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IDatasetForm)
    plugins.implements(plugins.IFacets, inherit=True)
    plugins.implements(plugins.IPackageController, inherit=True)

    # IBlueprint
    def get_blueprint(self):
        return views.get_blueprint()

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'apis')
        toolkit.add_ckan_admin_tab(config_, 'apis_blueprint.admins', 'Apiset Config')

        if toolkit.check_ckan_version(min_version='2.9.0'):
            mappings = config_.get('ckan.legacy_route_mappings', {})
            if isinstance(mappings, string_types):
                mappings = json.loads(mappings)

            bp_routes = [
                'index', 'new', 'delete',
                'read', 'edit', 'manage_datasets',
                'apiset_package_list', 'admins', 'admin_remove'
            ]
            mappings.update({
                'apiset_' + route: 'apis_blueprint.' + route
                for route in bp_routes
            })
            # https://github.com/ckan/ckan/pull/4521
            config_['ckan.legacy_route_mappings'] = json.dumps(mappings)

    # IConfigurable
    def configure(self, config):
        model_setup()

    # IActions
    def get_actions(self):
        return {
            'apiset_show': get.apiset_show,
            'apiset_list': get.apiset_list,
            'apiset_package_list': get.apiset_package_list,
            'package_apiset_list': get.package_apiset_list,
            'apiset_admin_list': get.apiset_admin_list,
            'apiset_create': create.apiset_create,
            'apiset_package_association_create': create.apiset_package_association_create,
            'apiset_update': update.apiset_update,
            'apiset_patch': update.apiset_patch,
            'apiset_delete': delete.apiset_delete,
            'apiset_package_association_delete': delete.apiset_package_association_delete,
        }

    # IAuthFunctions
    def get_auth_functions(self):
        return auth.get_auth_functions()

    # IDatasetForm
    def package_types(self):
        return [utils.DATASET_TYPE_NAME]

    def is_fallback(self):
        return False

    def search_template(self):
        return 'apiset/search.html'

    def new_template(self):
        return 'apiset/new.html'

    def read_template(self):
        return 'apiset/read.html'

    def edit_template(self):
        return 'apiset/edit_base.html'

    def package_form(self):
        return 'apiset/new_package_form.html'

    # IFacets
    def dataset_facets(self, facets_dict, package_type):
        '''Only show tags for Apiset search list.'''
        if package_type != utils.DATASET_TYPE_NAME:
            return facets_dict
        return OrderedDict({'tags': _('Tags')})

    # IPackageController
    def _add_to_pkg_dict(self, context, pkg_dict):
        '''
        Add key/values to pkg_dict and return it.
        '''

        if pkg_dict['type'] != 'apiset':
            return pkg_dict

        image_url = pkg_dict.get('image_url')
        pkg_dict[u'image_display_url'] = image_url
        if image_url and not image_url.startswith('http'):
            pkg_dict[u'image_url'] = image_url
            pkg_dict[u'image_display_url'] = \
                h.url_for_static('uploads/{0}/{1}'
                                 .format(utils.DATASET_TYPE_NAME,
                                         pkg_dict.get('image_url')),
                                 qualified=True)

        # Add dataset count
        pkg_dict[u'num_datasets'] = len(
            toolkit.get_action('apiset_package_list')(
                context, {'apiset_id': pkg_dict['id']}))

        # Rendered notes
        if helpers.get_wysiwyg_editor() == 'ckeditor':
            pkg_dict[u'apiset_notes_formatted'] = pkg_dict['notes']
        else:
            pkg_dict[u'apiset_notes_formatted'] = \
                h.render_markdown(pkg_dict['notes'])

        return pkg_dict

    def after_show(self, context, pkg_dict):
        '''
        Modify package_show pkg_dict.
        '''
        pkg_dict = self._add_to_pkg_dict(context, pkg_dict)

    def before_view(self, pkg_dict):
        '''
        Modify pkg_dict that is sent to templates.
        '''

        context = {'model': ckan_model, 'session': ckan_model.Session,
                   'user': c.user or c.author}

        return self._add_to_pkg_dict(context, pkg_dict)

    def before_search(self, search_params):
        '''
        Unless the query is already being filtered by this dataset_type
        (either positively, or negatively), exclude datasets of type
        `apiset`.
        '''
        fq = search_params.get('fq', '')
        filter = 'dataset_type:{0}'.format(utils.DATASET_TYPE_NAME)
        if filter not in fq:
            search_params.update({'fq': fq + " -" + filter})
        return search_params

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

    # ITemplateHelpers
    def get_helpers(self):
        return {
            'get_apiset_pkgs': helpers.get_apiset_pkgs
        }
