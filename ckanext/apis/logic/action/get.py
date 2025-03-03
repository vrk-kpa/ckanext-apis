import ckan.plugins.toolkit as toolkit
import ckan.lib.dictization.model_dictize as model_dictize
import sqlalchemy
from ckan.lib.navl.dictization_functions import validate
from ckanext.apis.logic.schema import apiset_package_list_schema, package_apiset_list_schema
from ckanext.apis.model import ApisetPackageAssociation
from collections import Counter

import logging
log = logging.getLogger(__name__)

_and_ = sqlalchemy.and_
_func = sqlalchemy.func

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

    all_fields = toolkit.asbool(data_dict.get('all_fields', True))

    limit = data_dict.get('limit')
    if limit:
        q = q.limit(limit)
    offset = data_dict.get('offset')
    if offset:
        q = q.offset(offset)

    if all_fields:
        return [model_dictize.package_dictize(pkg, context) for pkg in q.all()]

    return [pkg.name for pkg in q.all()]

@toolkit.side_effect_free
def apiset_package_list(context, data_dict):
    toolkit.check_access('apiset_package_list', context.copy(), data_dict)
    validated_data_dict, errors = validate(data_dict, apiset_package_list_schema(), context.copy())

    if errors:
        raise toolkit.ValidationError(errors)

    pkg_id_list = ApisetPackageAssociation.get_package_ids_for_apiset(validated_data_dict['apiset_id'])

    pkg_list = []
    if pkg_id_list:
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
def apiset_format_autocomplete(context, data_dict):
    '''Return a list of apiset resource formats whose names contain a string.
    :param q: the string to search for
    :type q: string
    :param limit: the maximum number of resource formats to return (optional,
        default: ``5``)
    :type limit: int
    :rtype: list of strings
    '''
    model = context['model']
    session = context['session']

    toolkit.check_access('apiset_format_autocomplete', context, data_dict)

    q = data_dict['q']
    limit = data_dict.get('limit', 5)

    like_q = u'%"formats": "%' + q + u'%"%'

    query = (session.query(model.Resource.extras, model.Package.id)
        .join(model.Package)
        .filter(_and_(
            model.Resource.state == 'active',
            model.Package.type == 'apiset',
            model.Resource.extras.ilike(like_q)
        )))

    formats = []
    for resource in query:
        extras = resource.extras
        formats_string = extras.get('formats', None)
        if formats_string:
            resource_formats = formats_string.lower().split(',')
            for resource_format in resource_formats:
                if resource_format.find(q) != -1:
                    formats.append(resource_format)

    formats_counter = Counter(formats)

    return [value[0] for value in formats_counter.most_common(limit)]
