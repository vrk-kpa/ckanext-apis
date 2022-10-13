import ckan.model as model
import ckan.lib.navl.dictization_functions as df
from ckan.common import _
from ckan.lib.navl.dictization_functions import  missing, flatten_list, StopOnError
import json
import logging


def convert_package_name_or_id_to_title_or_name(package_name_or_id, context):
    session = context['session']
    result = session.query(model.Package).filter_by(
            id=package_name_or_id).first()
    if not result:
        result = session.query(model.Package).filter_by(
                name=package_name_or_id).first()
    if not result:
        raise df.Invalid('%s: %s' % (_('Not found'), _('Dataset')))
    return result.title or result.name


def save_to_groups(key, data, errors, context):
    # https://docs.ckan.org/en/ckan-2.7.3/api/#ckan.logic.action.create.package_create
    # Add selected items as groups to dataset
    value = data[key]

    if value and value is not missing:

        if isinstance(value, str):
            group_patch = flatten_list([{"name": value}])
            group_key = ('groups',) + list(group_patch.keys())[0]
            group_value = list(group_patch.values())[0]
            data[group_key] = group_value
        elif isinstance(value, list):
            data[key] = json.dumps(value)
            groups_with_details = []
            for identifier in value:
                groups_with_details.append({"name": identifier})
            group_patch = flatten_list(groups_with_details)

            for k, v in list(group_patch.items()):
                group_key = ('groups',) + k
                data[group_key] = v

    else:

        # Delete categories key if it is missing
        # TODO: Should delete existing groups from dataset
        data.pop(key, None)
        raise StopOnError

    return data[key]