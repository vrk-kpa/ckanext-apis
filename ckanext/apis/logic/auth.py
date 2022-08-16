import logging
import ckan.model as model
from ckan.plugins import toolkit
from ckanext.apis.model import ApisetAdmin

log = logging.getLogger(__name__)


def _is_apiset_admin(context):
    user = context.get('user', '')
    userobj = model.User.get(user)
    return ApisetAdmin.is_user_apiset_admin(userobj)


def get_auth_functions():
    return {
        'apiset_package_association_create': apiset_association_create,
        'apiset_package_association_delete': apiset_association_delete,
        'apiset_admin_remove': remove_apiset_admin,
        'apiset_package_list': apiset_package_list,
        'package_apiset_list': package_apiset_list,
        'apiset_admin_list': apiset_admin_list,
    }



@toolkit.auth_allow_anonymous_access
def apiset_package_list(context, data_dict):
    return {'success': True}


@toolkit.auth_allow_anonymous_access
def package_apiset_list(context, data_dict):
    return {'success': True}


def apiset_admin_list(context, data_dict):
    return {'success': False}


def remove_apiset_admin(context, data_dict):
    return {'success': False}


def apiset_association_create(context, data_dict):
    return {'success': _is_apiset_admin(context)}


def apiset_association_delete(context, data_dict):
    return {'success': _is_apiset_admin(context)}
