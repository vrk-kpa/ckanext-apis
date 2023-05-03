import six
from ckan.lib.navl.validators import (not_empty)
from ckan.logic.validators import user_id_or_name_exists
from .validators import (convert_package_name_or_id_to_id_for_type_apiset)
from .validators import (convert_package_name_or_id_to_id_for_type_dataset)

from ckantoolkit import unicode_safe

def apiset_package_association_create_schema():
    schema = {
        'package_id': [not_empty, unicode_safe, convert_package_name_or_id_to_id_for_type_dataset],
        'apiset_id': [not_empty, unicode_safe, convert_package_name_or_id_to_id_for_type_apiset]
    }
    return schema


def apiset_package_association_delete_schema():
    return apiset_package_association_create_schema()


def apiset_package_list_schema():
    return {'apiset_id': [not_empty, unicode_safe, convert_package_name_or_id_to_id_for_type_apiset]}


def package_apiset_list_schema():
    return {'package_id': [not_empty, unicode_safe, convert_package_name_or_id_to_id_for_type_dataset]}


def apiset_admin_add_schema():
    return {'username': [not_empty, user_id_or_name_exists, unicode_safe]}


def apiset_admin_remove_schema():
    return apiset_admin_add_schema()