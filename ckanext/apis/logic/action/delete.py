import ckan.plugins.toolkit as toolkit
from ckan.lib.navl.dictization_functions import validate
from ckanext.apis.logic.schema import apiset_package_association_delete_schema
from ckanext.apis.model import ApisetPackageAssociation


def apiset_delete(context, data_dict):
    return toolkit.get_action('package_delete')(context, data_dict)

def apiset_package_association_delete(context, data_dict):
    model = context['model']
    toolkit.check_access('apiset_package_association_delete', context, data_dict)
    validated_data_dict, errors = validate(data_dict, apiset_package_association_delete_schema(), context)

    if errors:
        raise toolkit.ValidationError(errors)

    package_id, apiset_id = toolkit.get_or_bust(validated_data_dict, ['package_id', 'apiset_id'])
    apiset_package_association = ApisetPackageAssociation.get(package_id=package_id, apiset_id=apiset_id)

    if apiset_package_association is None:
        raise toolkit.ObjectNotFound(
            "ApisetPackageAssociation with package_id '{0}' and apiset_id '{1}' doesn't exist.".format(package_id, apiset_id))

    apiset_package_association.delete()
    model.repo.commit()
