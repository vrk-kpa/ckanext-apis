import logging
from ckan.plugins import toolkit

log = logging.getLogger(__name__)


def get_auth_functions():
    return {
        'apiset_create': apiset_create,
        'apiset_package_association_create': apiset_association_create,
        'apiset_delete': apiset_delete,
        'apiset_package_association_delete': apiset_association_delete,
        'apiset_update': apiset_update,
        'apiset_admin_remove': remove_apiset_admin,
        'apiset_package_list': apiset_package_list,
        'package_apiset_list': package_apiset_list,
        'apiset_admin_list': apiset_admin_list,
        'apiset_format_autocomplete': apiset_format_autocomplete,
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

def apiset_update(context, data_dict):
    user = context.get('user')
    try:
        toolkit.check_access('package_update', context, data_dict)
        return {'success': True}
    except toolkit.NotAuthorized:
        return {'success': False,
                'msg': toolkit._('User {0} not authorized to edit apisets').format(user)}

def apiset_create(context, data_dict):
    user = context.get('user')
    try:
        toolkit.check_access('package_create', context, data_dict)
        return {'success': True}
    except toolkit.NotAuthorized:
        return {'success': False,
                'msg': toolkit._('User {0} not authorized to create apisets').format(user)}

def apiset_association_create(context, data_dict):
    user = context.get('user')
    try:
        toolkit.check_access('package_update', context, data_dict)
        return {'success': True}
    except toolkit.NotAuthorized:
        return {'success': False,
                'msg': toolkit._('User {0} not authorized to associate apisets').format(user)}


def apiset_delete(context, data_dict):
    user = context.get('user')
    try:
        toolkit.check_access('package_delete', context, data_dict)
        return {'success': True}
    except toolkit.NotAuthorized:
        return {'success': False,
                'msg': toolkit._('User {0} not authorized to delete apisets').format(user)}

def apiset_association_delete(context, data_dict):
    user = context.get('user')
    try:
        toolkit.check_access('package_delete', context, data_dict)
        return {'success': True}
    except toolkit.NotAuthorized:
        return {'success': False,
                'msg': toolkit._('User {0} not authorized to delete apiset associations').format(user)}

@toolkit.auth_allow_anonymous_access
def apiset_format_autocomplete(context, data_dict):
    return {'success': True}
