import ckan.model as model
import ckan.lib.navl.dictization_functions as df
from ckan.common import _


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
