import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from .logic.action import get, create, update, delete


class ApisPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IPackageController, inherit=True)

    # IConfigurer

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
                'apiset_delete': delete.apiset_delete
                }

    def before_search(self, search_params):
        '''Prevents the apisets being shown in dataset search results.'''

        fq = search_params.get('fq', '')
        if 'dataset_type:apiset' not in fq:
            fq = u"{0} -dataset_type:apiset".format(search_params.get('fq', ''))
            search_params.update({'fq': fq})

        return search_params