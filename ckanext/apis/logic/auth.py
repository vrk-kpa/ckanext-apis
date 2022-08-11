import logging
import ckan.model as model
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
    }


def apiset_association_create(context, data_dict):
    return {'success': _is_apiset_admin(context)}


def apiset_association_delete(context, data_dict):
    return {'success': _is_apiset_admin(context)}
