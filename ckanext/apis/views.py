# -*- coding: utf-8 -*-

from ast import keyword
from flask import Blueprint
import ckan.lib.base as base
import ckan.views.dataset as dataset
from ckan.views.dataset import GroupView as CkanDatasetGroupView
import ckan.logic as logic
import ckantoolkit as tk
import ckan.lib.helpers as h
from ckan.common import _, g, request
from ckan.views.home import CACHE_PARAMETERS
import ckan.lib.navl.dictization_functions as dict_fns
from . import utils
from typing import Any, Iterable, Optional, Union, cast
import ckan.model as model
import json
import logging
from ckan.views.api import _finish_ok
from ckan.plugins.toolkit import abort, ObjectNotFound

_setup_template_variables = dataset._setup_template_variables
_get_pkg_template = dataset._get_pkg_template
check_access = logic.check_access
get_action = logic.get_action
tuplize_dict = logic.tuplize_dict
clean_dict = logic.clean_dict
parse_params = logic.parse_params
flatten_to_string_key = logic.flatten_to_string_key
NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized

apis = Blueprint('apis_blueprint', __name__)


class EditView(dataset.EditView):

    def post(self, id):
        context = self._prepare(id)
        utils.check_edit_view_auth(id)

        data_dict = dataset.clean_dict(dataset.dict_fns.unflatten(dataset.tuplize_dict(dataset.parse_params(
            tk.request.form))))
        data_dict.update(dataset.clean_dict(dataset.dict_fns.unflatten(dataset.tuplize_dict(dataset.parse_params(
            tk.request.files)))))

        languages = ['fi', 'en', 'sv']

        def translated_field(name):
            data_dict[f'{name}'] = {}
            for language in languages:
                translated_val = data_dict.get(f'{name}-{language}')
                data_dict[f'{name}'][language] = translated_val

        def translated_keyword_field():
            data_dict['keywords'] = {'fi': [], 'en': [], 'sv': []}
            for language in languages:
                keywords = data_dict.get(f'keywords-{language}')
                # split the keywords if applicable
                if keywords:
                    split_keywords = keywords.split(',')
                    for kw in split_keywords:
                        data_dict['keywords'][language].append(kw)
            
        # convert fields with translations to correct data structure
        translated_field('title_translated')
        translated_field('notes_translated')
        translated_field('access_rights')
        translated_keyword_field()

        # Get resource fields and append them to the data_dict
        old_data = get_action(u'package_show')(context, {u'id': id})

        data = old_data
        data_dict['id'] = id

        # empty the groups from the old data, validation will fill them from new data
        data['groups'] = []
        # The form omits the category field if no categories are selected
        if not 'category' in data_dict:
            data_dict['category'] = ""

        data.update(data_dict)

        try:
            pkg = tk.get_action('package_update')(context, data)
        except tk.ValidationError as e:
            errors = e.error_dict
            error_summary = e.error_summary
            return self.get(id, data, errors, error_summary)

        tk.g.pkg_dict = pkg

        url = h.url_for('apis_blueprint.read', id=pkg['name'])
        return h.redirect_to(url)


    def get(self, id, data=None, errors=None, error_summary=None):
        utils.check_new_view_auth()
        context = self._prepare(id, data)
        package_type = utils.DATASET_TYPE_NAME

        try:
            pkg_dict = get_action(u'package_show')(
                dict(context, for_view=True), {
                    u'id': id
                }
            )
            context[u'for_edit'] = True
            old_data = get_action(u'package_show')(context, {u'id': id})
            # old data is from the database and data is passed from the
            # user if there is a validation error. Use users data if there.
            if data:
                old_data.update(data)
            data = old_data
        except (NotFound, NotAuthorized):
            return base.abort(404, _(u'Apiset not found'))

        pkg = context.get(u"package")
        resources_json = h.json.dumps(data.get(u'resources', []))

        try:
            check_access(u'package_update', context)
        except NotAuthorized:
            return base.abort(
                403,
                _(u'User %r not authorized to edit %s') % (g.user, id)
            )
        # convert tags if not supplied in data
        if data and not data.get(u'tag_string'):
            data[u'tag_string'] = u', '.join(
                h.dict_list_reduce(pkg_dict.get(u'tags', {}), u'name')
            )
        errors = errors or {}
        form_vars = {
            u'data': data,
            u'errors': errors,
            u'error_summary': error_summary,
            u'action': u'edit',
            u'dataset_type': package_type,
            u'form_style': u'edit'
        }
        errors_json = h.json.dumps(errors)

        _setup_template_variables(
            context, {u'id': id}, package_type=package_type
        )

        # we have already completed stage 1
        form_vars[u'stage'] = [u'active']
        if data.get(u'state', u'').startswith(u'draft'):
            form_vars[u'stage'] = [u'active', u'complete']

        edit_template = 'apiset/edit.html'
        return base.render(
            edit_template,
            extra_vars={
                u'form_vars': form_vars,
                u'form_snippet': 'apiset/package_form.html',
                u'dataset_type': package_type,
                u'pkg_dict': pkg_dict,
                u'pkg': pkg,
                u'resources_json': resources_json,
                u'errors_json': errors_json,
                u'view_type': 'apiset_edit'
            }
        )

def resources(id, package_type='apiset'):
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user,
        u'for_view': True,
        u'auth_user_obj': g.userobj
    }
    data_dict = {u'id': id, u'include_tracking': True}

    try:
        check_access(u'package_update', context, data_dict)
    except NotFound:
        return base.abort(404, _(u'Dataset not found'))
    except NotAuthorized:
        return base.abort(
            403,
            _(u'User %r not authorized to edit %s') % (g.user, id)
        )
    # check if package exists
    try:
        pkg_dict = get_action(u'package_show')(context, data_dict)
        pkg = context[u'package']
    except (NotFound, NotAuthorized):
        return base.abort(404, _(u'Dataset not found'))

    package_type = pkg_dict[u'type'] or u'dataset'
    _setup_template_variables(context, {u'id': id}, package_type=package_type)

    # TODO: remove
    g.pkg_dict = pkg_dict
    g.pkg = pkg

    return base.render(
            u'scheming/package/resources.html', {
            u'dataset_type': package_type,
            u'pkg_dict': pkg_dict,
            u'pkg': pkg
        })


class GroupView(CkanDatasetGroupView):
    def _prepare(self, id):
        context = {
            u'model': model,
            u'session': model.Session,
            u'user': g.user,
            u'for_view': True,
            u'auth_user_obj': g.userobj,
            u'use_cache': False
        }

        try:
            pkg_dict = get_action(u'package_show')(context, {u'id': id})
        except (NotFound, NotAuthorized):
            return base.abort(404, _(u'Apiset not found'))
        return context, pkg_dict

    def post(self, package_type, id):
        context, pkg_dict = self._prepare(id)

        category_list = request.form.getlist('categories')
        group_list = [{'name': c} for c in category_list]
        try:
            get_action('apiset_patch')(context, {"id": id, "groups": group_list, "category": category_list})
            return h.redirect_to('apiset_groups', id=id)
        except (ObjectNotFound, NotAuthorized):
            return abort(404, _('Apiset not found'))

    def get(self, package_type, id):
        context, pkg_dict = self._prepare(id)
        dataset_type = pkg_dict[u'type'] or package_type
        context[u'is_member'] = True
        users_groups = get_action(u'group_list_authz')(context, {u'id': id})

        pkg_group_ids = set(
            group[u'id'] for group in pkg_dict.get(u'groups', [])
        )

        user_group_ids = set(group[u'id'] for group in users_groups)

        group_dropdown = [[group[u'id'], group[u'display_name']]
                          for group in users_groups
                          if group[u'id'] not in pkg_group_ids]

        for group in pkg_dict.get(u'groups', []):
            group[u'user_member'] = (group[u'id'] in user_group_ids)

        # TODO: remove
        g.pkg_dict = pkg_dict
        g.group_dropdown = group_dropdown

        return base.render(
            u'package/group_list.html', {
                u'dataset_type': dataset_type,
                u'pkg_dict': pkg_dict,
                u'group_dropdown': group_dropdown
            }
        )


def read(id):
    # use the default read function
    return dataset.read('apiset', id)

def new():
    myview = dataset.CreateView()
    return myview.get('apiset')


def manage_datasets(id):
    return utils.manage_datasets_view(id)


def apiset_format_autocomplete():
    q = request.args.get(u'incomplete', u'')
    limit = request.args.get(u'limit', 5)
    formats = []
    if q:
        context = {u'model': model, u'session': model.Session,
                   u'user': g.user, u'auth_user_obj': g.userobj}
        data_dict = {u'q': q, u'limit': limit}
        formats = get_action(u'apiset_format_autocomplete')(context, data_dict)

    resultSet = {
        u'ResultSet': {
            u'Result': [{u'Format': format} for format in formats]
        }
    }
    return _finish_ok(resultSet)


def activity(id):
    """Render this package's public activity stream page.
    """
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user,
        u'for_view': True,
        u'auth_user_obj': g.userobj
    }

    data_dict = {u'id': id}
    try:
        pkg_dict = get_action(u'package_show')(context, data_dict)
        pkg = context[u'package']
        package_activity_stream = get_action(
            u'package_activity_list')(
            context, {u'id': pkg_dict[u'id']})
        dataset_type = pkg_dict[u'type'] or u'apiset'

    except NotFound:
        return base.abort(404, _(u'Apiset not found'))
    except NotAuthorized:
        return base.abort(403, _(u'Unauthorized to read apiset %s') % id)

    blueprint, endpoint = tk.get_endpoint()
    logging.warning(blueprint)
    logging.warning(endpoint)

    # TODO: remove
    g.pkg_dict = pkg_dict
    g.pkg = pkg

    return base.render(
        u'package/activity.html', {
            u'dataset_type': dataset_type,
            u'pkg_dict': pkg_dict,
            u'pkg': pkg,
            u'activity_stream': package_activity_stream,
            u'id': id,  # i.e. package's current name,
        })
        
    
def search():
    return dataset.search('apiset')


apis.add_url_rule('/apiset/manage_datasets/<id>', view_func=manage_datasets, methods=[u'GET', u'POST'])
apis.add_url_rule('/apiset/edit/<id>', view_func=EditView.as_view('edit'), methods=[u'GET', u'POST'])
apis.add_url_rule('/apiset/resources/<id>', view_func=resources)
apis.add_url_rule('/apiset/new', view_func=new)
apis.add_url_rule('/apiset/groups/<id>', view_func=GroupView.as_view(str(u'groups')), defaults={'package_type': 'apiset'})
apis.add_url_rule('/apiset/<id>', view_func=read)
apis.add_url_rule('/api/util/apiset/format_autocomplete', view_func=apiset_format_autocomplete)
apis.add_url_rule('/apiset/activity/<id>', view_func=activity)
apis.add_url_rule('/apiset', view_func=search)

def get_blueprint():
    return [apis]