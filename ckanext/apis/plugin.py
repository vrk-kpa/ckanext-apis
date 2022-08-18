import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from . import views
from . import helpers
from .logic.action import get, create, update, delete


class ApisPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.ITemplateHelpers)

    # IBlueprint
    def get_blueprint(self):
        return views.get_blueprint()

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'apis')

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

    # ITemplateHelpers
    def get_helpers(self):
        return {
            'get_showcase_pkgs': helpers.get_apiset_pkgs
        }
