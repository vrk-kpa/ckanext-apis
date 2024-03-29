import logging
import ckan.views.dataset as dataset
import ckantoolkit as toolkit
import ckan.plugins as plugins
import ckan.logic as logic
import ckan.lib.helpers as h
from collections import OrderedDict
from urllib.parse import urlencode
from ckan import model
from ckan.plugins.toolkit import _
from .model import ApisetPackageAssociation


DATASET_TYPE_NAME = 'apiset'
NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
ValidationError = logic.ValidationError
check_access = logic.check_access
get_action = logic.get_action
tuplize_dict = logic.tuplize_dict
clean_dict = logic.clean_dict
parse_params = logic.parse_params
flatten_to_string_key = logic.flatten_to_string_key
_encode_params = dataset._encode_params
g = toolkit.g
log = logging.getLogger(__name__)

def check_edit_view_auth(id):
    context = {
        'model': model,
        'session': model.Session,
        'user': g.user or g.author,
        'auth_user_obj': g.userobj,
        'save': 'save' in toolkit.request.params,
        'moderated': toolkit.config.get('moderated'),
        'pending': True
    }
    data_dict = {'id': id}

    try:
        toolkit.check_access('package_update', context, data_dict)
    except toolkit.NotAuthorized:
        return toolkit.abort(
            401,
            _('User not authorized to edit {id}').format(id=id))

def check_new_view_auth():
    context = {
        'model': model,
        'session': model.Session,
        'user': toolkit.g.user or toolkit.g.author,
        'auth_user_obj': toolkit.g.userobj,
        'save': 'save' in toolkit.request.params
    }

    try:
        toolkit.check_access('package_create', context)
    except toolkit.NotAuthorized:
        return toolkit.abort(401, _('Unauthorized to create a package'))

def _add_dataset_search(apiset_id, apiset_name):
    from ckan.lib.search import SearchError
    g = toolkit.g

    package_type = DATASET_TYPE_NAME
    # unicode format (decoded from utf8)
    q = g.q = toolkit.request.params.get('q', u'')
    g.query_error = False
    page = h.get_page_number(toolkit.request.params)

    limit = int(toolkit.config.get('ckan.datasets_per_page', 20))

    # most search operations should reset the page counter:
    params_nopage = [(k, v) for k, v in toolkit.request.params.items()
                     if k != 'page']

    def drill_down_url(alternative_url=None, **by):
        return h.add_url_param(alternative_url=alternative_url,
                               controller=package_type
                               if toolkit.check_ckan_version('2.9') else 'package',
                               action='search',
                               new_params=by)

    g.drill_down_url = drill_down_url

    def remove_field(key, value=None, replace=None):
        return h.remove_url_param(key,
                                  value=value,
                                  replace=replace,
                                  controller=package_type,
                                  action='search')

    g.remove_field = remove_field

    sort_by = toolkit.request.params.get('sort', None)
    params_nosort = [(k, v) for k, v in params_nopage if k != 'sort']

    def _search_url(params, name):
        url = h.url_for('apis_blueprint.manage_datasets', id=name)
        return url_with_params(url, params)

    def url_with_params(url, params):
        params = _encode_params(params)
        return url + u'?' + urlencode(params)

    def _sort_by(fields):
        """
        Sort by the given list of fields.
        Each entry in the list is a 2-tuple: (fieldname, sort_order)
        eg - [('metadata_modified', 'desc'), ('name', 'asc')]
        If fields is empty, then the default ordering is used.
        """
        params = params_nosort[:]

        if fields:
            sort_string = ', '.join('%s %s' % f for f in fields)
            params.append(('sort', sort_string))
        return _search_url(params, apiset_name)

    g.sort_by = _sort_by
    if sort_by is None:
        g.sort_by_fields = []
    else:
        g.sort_by_fields = [field.split()[0] for field in sort_by.split(',')]

    def pager_url(q=None, page=None):
        params = list(params_nopage)
        params.append(('page', page))
        return _search_url(params, apiset_name)

    g.search_url_params = urlencode(_encode_params(params_nopage))

    try:
        g.fields = []
        # g.fields_grouped will contain a dict of params containing
        # a list of values eg {'tags':['tag1', 'tag2']}
        g.fields_grouped = {}
        search_extras = {}
        fq = ''
        for (param, value) in toolkit.request.params.items():
            if param not in ['q', 'page', 'sort'] \
                    and len(value) and not param.startswith('_'):
                if not param.startswith('ext_'):
                    g.fields.append((param, value))
                    fq += ' %s:"%s"' % (param, value)
                    if param not in g.fields_grouped:
                        g.fields_grouped[param] = [value]
                    else:
                        g.fields_grouped[param].append(value)
                else:
                    search_extras[param] = value

        context = {
            'model': model,
            'session': model.Session,
            'user': g.user or g.author,
            'for_view': True,
            'auth_user_obj': g.userobj
        }

        # For now only look for datasets
        fq = '+dataset_type:dataset'

        # Only search for datasets not already associated with the apiset
        associated_package_ids = ApisetPackageAssociation.get_package_ids_for_apiset(apiset_id)
        # flatten resulting list to space separated string
        if associated_package_ids:
            associated_package_ids_str = \
                ' OR '.join([id[0] for id in associated_package_ids])
            fq += ' !id:({0})'.format(associated_package_ids_str)


        facets = OrderedDict()

        default_facet_titles = {
            'organization': _('Organizations'),
            'groups': _('Groups'),
            'tags': _('Tags'),
            'res_format': _('Formats'),
            'license_id': _('Licenses'),
        }

        # for CKAN-Versions that do not provide the facets-method from
        # helper-context, import facets from ckan.common
        if hasattr(h, 'facets'):
            current_facets = h.facets()
        else:
            from ckan.common import g
            current_facets = g.facets

        for facet in current_facets:
            if facet in default_facet_titles:
                facets[facet] = default_facet_titles[facet]
            else:
                facets[facet] = facet

        # Facet titles
        for plugin in plugins.PluginImplementations(plugins.IFacets):
            facets = plugin.dataset_facets(facets, package_type)

        g.facet_titles = facets

        data_dict = {
            'q': q,
            'fq': fq.strip(),
            'facet.field': list(facets.keys()),
            'rows': limit,
            'start': (page - 1) * limit,
            'sort': sort_by,
            'extras': search_extras
        }

        query = toolkit.get_action('package_search')(context, data_dict)
        g.sort_by_selected = query['sort']

        g.page = h.Page(collection=query['results'],
                        page=page,
                        url=pager_url,
                        item_count=query['count'],
                        items_per_page=limit)
        g.facets = query['facets']
        g.search_facets = query['search_facets']
        g.page.items = query['results']
    except SearchError as se:
        log.error('Dataset search error: %r', se.args)
        g.query_error = True
        g.facets = {}
        g.search_facets = {}
        g.page = h.Page(collection=[])
    g.search_facets_limits = {}
    for facet in g.search_facets.keys():
        try:
            limit = int(
                toolkit.request.params.get(
                    '_%s_limit' % facet,
                    int(toolkit.config.get('search.facets.default', 10))))
        except toolkit.ValueError:
            toolkit.abort(
                400,
                _("Parameter '{parameter_name}' is not an integer").format(
                    parameter_name='_%s_limit' % facet))
        g.search_facets_limits[facet] = limit

def read_view(id):
    context = {
        'model': model,
        'session': model.Session,
        'user': g.user or g.author,
        'for_view': True,
        'auth_user_obj': g.userobj
    }
    data_dict = {'id': id}

    # check if apiset exists
    try:
        g.pkg_dict = toolkit.get_action('package_show')(context, data_dict)
    except toolkit.ObjectNotFound:
        return toolkit.abort(404, _('Apiset not found'))
    except toolkit.NotAuthorized:
        return toolkit.abort(401, _('Unauthorized to read apiset'))

    # get apiset packages
    g.showcase_pkgs = toolkit.get_action('apiset_package_list')(
        context, {
            'apiset_id': g.pkg_dict['id']
        })

    package_type = DATASET_TYPE_NAME
    return toolkit.render('apiset/read.html',
                     extra_vars={'dataset_type': package_type})

def manage_datasets_view(id):
    context = {
        'model': model,
        'session': model.Session,
        'user': toolkit.g.user or toolkit.g.author
    }
    data_dict = {'id': id}

    try:
        toolkit.check_access('package_update', context, data_dict)
    except toolkit.NotAuthorized:
        return toolkit.abort(401, _('User not authorized to edit {apiset_id}').format(apiset_id=id))

    try:
        toolkit.g.pkg_dict = toolkit.get_action('package_show')(context, data_dict)
    except toolkit.ObjectNotFound:
        return toolkit.abort(404, _('Apiset not found'))
    except toolkit.NotAuthorized:
        return toolkit.abort(401, _('Unauthorized to read apiset'))

    form_data = toolkit.request.form

    manage_route = 'apis_blueprint.manage_datasets'

    if toolkit.request.method == 'POST' and 'bulk_action.dataset_remove' in form_data:
        # Find the datasets to perform the action on, they are prefixed by dataset_ in the form data
        package_ids = []
        for param in form_data:
            if param.startswith('dataset_'):
                package_ids.append(param[8:])
        if package_ids:
            for package_id in package_ids:
                toolkit.get_action('apiset_package_association_delete')(
                    context, {
                        'apiset_id': toolkit.g.pkg_dict['id'],
                        'package_id': package_id
                    })
            h.flash_success(
                toolkit.ungettext(
                    "The dataset has been removed from the apiset.",
                    "The datasets have been removed from the apiset.",
                    len(package_ids)))
            url = h.url_for(manage_route, id=id)
            return h.redirect_to(url)

    elif toolkit.request.method == 'POST' and 'bulk_action.dataset_add' in form_data:
        # Find the datasets to perform the action on, they are prefixed by dataset_ in the form data
        package_ids = []
        for param in form_data:
            if param.startswith('dataset_'):
                package_ids.append(param[8:])
        if package_ids:
            successful_adds = []
            for package_id in package_ids:
                try:
                    toolkit.get_action('apiset_package_association_create')(
                            context, {
                                'apiset_id': toolkit.g.pkg_dict['id'],
                                'package_id': package_id
                            })
                except toolkit.ValidationError as e:
                    h.flash_notice(e.error_summary)
                else:
                    successful_adds.append(package_id)
            if successful_adds:
                h.flash_success(
                    toolkit.ungettext(
                        "The dataset has been added to the apiset.",
                        "The datasets have been added to the apiset.",
                        len(successful_adds)))
            url = h.url_for(manage_route, id=id)
            return h.redirect_to(url)

    _add_dataset_search(toolkit.g.pkg_dict['id'], toolkit.g.pkg_dict['name'])

    toolkit.g.apiset_pkgs = toolkit.get_action('apiset_package_list')(
        context, {
            'apiset_id': toolkit.g.pkg_dict['id']
        })

    return toolkit.render('apiset/manage_datasets.html', extra_vars={'view_type': 'manage_datasets'})


