from ckan.plugins import toolkit as tk

_ = tk._
Invalid = tk.Invalid


def convert_package_name_or_id_to_id_for_type_apiset(package_name_or_id, context):
    return convert_package_name_or_id_to_id_for_type(package_name_or_id, context, package_type='apiset')


def convert_package_name_or_id_to_id_for_type_dataset(package_name_or_id, context):
    return convert_package_name_or_id_to_id_for_type(package_name_or_id, context, package_type='dataset')


def convert_package_name_or_id_to_id_for_type(package_name_or_id, context, package_type='dataset'):
    session = context['session']
    model = context['model']
    result = session.query(model.Package) \
        .filter_by(id=package_name_or_id, type=package_type).first()
    if not result:
        result = session.query(model.Package) \
            .filter_by(name=package_name_or_id, type=package_type).first()
    if not result:
        raise Invalid('%s: %s' % (_('Not found'), _('Dataset')))
    return result.id
