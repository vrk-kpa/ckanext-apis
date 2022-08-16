import ckan.plugins.toolkit as toolkit
import ckan.lib.dictization.model_dictize as model_dictize
from ckan.lib.navl.dictization_functions import validate
from ckanext.apis.logic.schema import apiset_package_list_schema, package_apiset_list_schema
from ckanext.apis.model import ApisetPackageAssociation, ApisetAdmin

@toolkit.side_effect_free
def apiset_show(context, data_dict):
    return toolkit.get_action('package_show')(context, data_dict)


@toolkit.side_effect_free
def apiset_list(context, data_dict):
    model = context["model"]

    q = (model.Session.query(model.Package)
         .filter(model.Package.type == 'apiset')
         .filter(model.Package.private == False) # noqa
         .filter(model.Package.state == 'active'))

    limit = data_dict.get('limit')
    if limit:
        q = q.limit(limit)

    offset = data_dict.get('offset')
    if offset:
        q = q.offset(offset)

    return [model_dictize.package_dictize(pkg, context) for pkg in q.all()]


@toolkit.side_effect_free
def apiset_package_list(context, data_dict):
    toolkit.check_access('apiset_package_list', context.copy(), data_dict)
    validated_data_dict, errors = validate(data_dict, apiset_package_list_schema(), context.copy())

    if errors:
        raise toolkit.ValidationError(errors)

    pkg_id_list = ApisetPackageAssociation.get_package_ids_for_apiset(validated_data_dict['apiset_id'])

    pkg_list = []
    if pkg_id_list:
        # for each package id, get the package dict and append to list if
        # active
        id_list = []
        for pkg_id in pkg_id_list:
            id_list.append(pkg_id[0])
        q = ' OR '.join(['id:{0}'.format(x) for x in id_list])
        _pkg_list = toolkit.get_action('package_search')(
            context,
            {'q': q, 'rows': 100})
        pkg_list = _pkg_list['results']
    return pkg_list


@toolkit.side_effect_free
def package_apiset_list(context, data_dict):
    toolkit.check_access('package_apiset_list', context, data_dict)
    validated_data_dict, errors = validate(data_dict, package_apiset_list_schema(), context)

    if errors:
        raise toolkit.ValidationError(errors)

    apiset_id_list = ApisetPackageAssociation.get_apiset_ids_for_package(validated_data_dict['package_id'])
    package_list = []

    q = ''
    fq = ''
    if apiset_id_list:
        id_list = []
        for apiset_id in apiset_id_list:
            id_list.append(apiset_id[0])
        fq = 'dataset_type:showcase'
        q = ' OR '.join(['id:{0}'.format(x) for x in id_list])
        _package_list = toolkit.get_action('package_search')(
            context,
            {'q': q, 'fq': fq, 'rows': 100})
        package_list = _package_list['results']

    return package_list


@toolkit.side_effect_free
def apiset_admin_list(context, data_dict):
    toolkit.check_access('apiset_admin_list', context, data_dict)
    model = context["model"]
    user_ids = ApisetAdmin.get_apiset_admin_ids()

    if user_ids:
        q = model.Session.query(model.User) \
            .filter(model.User.state == 'active') \
            .filter(model.User.id.in_(user_ids))

        showcase_admin_list = []
        for user in q.all():
            showcase_admin_list.append({'name': user.name, 'id': user.id})
        return showcase_admin_list

    return []
