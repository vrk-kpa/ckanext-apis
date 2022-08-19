import ckan.model as model
from ckan.plugins import toolkit as tk

c = tk.c
get_action = tk.get_action

def get_apiset_pkgs(apiset_id):

    context = {'model': model, 'session': model.Session,
               'user': c.user or c.author, 'auth_user_obj': c.userobj}

    apiset_pkgs = get_action('apiset_package_list')(context, {'apiset_id': apiset_id})

    return apiset_pkgs

def get_wysiwyg_editor():
    return tk.config.get('ckanext.apis.editor', '')
