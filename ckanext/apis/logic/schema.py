# -*- coding: utf-8 -*-

import six
from ckan.lib.navl.validators import (not_empty)
from .validators import (convert_package_name_or_id_to_id_for_type_apiset)
from .validators import (convert_package_name_or_id_to_id_for_type_dataset)


def apiset_package_association_create_schema():
    schema = {
        'package_id': [not_empty, six.text_type, convert_package_name_or_id_to_id_for_type_dataset],
        'apiset_id': [not_empty, six.text_type, convert_package_name_or_id_to_id_for_type_apiset]
    }
    return schema


def apiset_package_association_delete_schema():
    return apiset_package_association_create_schema()


def apiset_package_list_schema():
    return {'apiset_id': [not_empty, six.text_type, convert_package_name_or_id_to_id_for_type_apiset]}


def package_apiset_list_schema():
    return {'package_id': [not_empty, six.text_type, convert_package_name_or_id_to_id_for_type_dataset]}
