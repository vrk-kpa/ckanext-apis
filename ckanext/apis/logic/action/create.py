import ckan.plugins.toolkit as toolkit
from ckan.lib.navl.dictization_functions import validate
from ckanext.apis.logic.schema import apiset_package_association_create_schema
from ckanext.apis.model import ApisetPackageAssociation
from ckanext.apis.logic.converters import (convert_package_name_or_id_to_title_or_name)
import logging

def apiset_create(context, data_dict):
    data_dict['type'] = 'apiset'
    return toolkit.get_action('package_create')(context, data_dict)

def apiset_package_association_create(context, data_dict):

    toolkit.check_access('apiset_package_association_create', context, data_dict)
    validated_data_dict, errors = validate(data_dict, apiset_package_association_create_schema(), context)

    if errors:
        raise toolkit.ValidationError(errors)

    package_id, apiset_id = toolkit.get_or_bust(validated_data_dict, ['package_id', 'apiset_id'])

    if ApisetPackageAssociation.exists(package_id=package_id, apiset_id=apiset_id):
        raise toolkit.ValidationError(
            "ApisetPackageAssociation with package_id '{0}' and apiset_id '{1}' already exists.".format(package_id,
                                                                                                        apiset_id),
            error_summary=u"The dataset, {0}, is already in the apiset".format(
                convert_package_name_or_id_to_title_or_name(package_id, context)))

    return ApisetPackageAssociation.create(package_id=package_id, apiset_id=apiset_id)