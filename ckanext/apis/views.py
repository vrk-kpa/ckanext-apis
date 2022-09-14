# -*- coding: utf-8 -*-

from flask import Blueprint
import ckan.lib.base as base
import ckan.views.dataset as dataset
import ckan.logic as logic
import ckantoolkit as tk
import ckan.lib.helpers as h
from ckan.common import _, g, request
from ckan.views.home import CACHE_PARAMETERS
import ckan.lib.navl.dictization_functions as dict_fns
# from ckanext.showcase import views, utils as showcase_utils
from . import utils
# additions
from typing import Any, Iterable, Optional, Union, cast
import ckan.model as model
import json


import logging

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
        # TODO Check this
        # utils.check_edit_view_auth(id)


        data_dict = dataset.clean_dict(dataset.dict_fns.unflatten(dataset.tuplize_dict(dataset.parse_params(
            tk.request.form))))
        data_dict.update(dataset.clean_dict(dataset.dict_fns.unflatten(dataset.tuplize_dict(dataset.parse_params(
            tk.request.files)))))


        test = tk.request.form
        logging.error(json.dumps(test))

        # Get resource fields and append them to the data_dict
        old_data = get_action(u'package_show')(context, {u'id': id})

        '''
        The cleaned data comes in the form of:
        "title_translated-en": "testi enkku",
	    "title_translated-fi": "Mun kokoelma testi",
	    "title_translated-sv": "",
        
        while what needs to be saved is
        "title_translated": {
            "en": "",
            "fi": "Mun kokoelma testi",
            "sv": ""
        },
        '''


        data = old_data
        data_dict['id'] = id
        data['title_translated']['en'] = "enkku testi"

        # logging.error("___old___")
        # logging.error(json.dumps(data))
        # logging.error("__new____")
        # logging.error(json.dumps(data_dict))
        # logging.error("______")
        

        data.update(data_dict)

        # logging.error("____update___")
        # logging.error(json.dumps(data))
        # logging.error("____________")

        
        try:
            pkg = tk.get_action('package_update')(context, data)
            #pkg = tk.get_action('package_patch')(context, data_dict)
        except tk.ValidationError as e:
            errors = e.error_dict
            error_summary = e.error_summary
            #return self.get(id, data_dict, errors, error_summary)
            return self.get(id, data, errors, error_summary)

        tk.c.pkg_dict = pkg

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
        # are we doing a multiphase add?
        if data.get(u'state', u'').startswith(u'draft'):
            g.form_action = h.url_for(u'{}.new'.format(package_type))
            g.form_style = u'new'

            return CreateView().get(
                package_type,
                data=data,
                errors=errors,
                error_summary=error_summary
            )

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

def resources(id, package_type='dataset'):
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

def read(id):
    # use the default read function
    return dataset.read('apiset', id)

def manage_datasets(id):
    return utils.manage_datasets_view(id)

apis.add_url_rule('/apiset/manage_datasets/<id>', view_func=manage_datasets, methods=[u'GET', u'POST'])
apis.add_url_rule('/apiset/edit/<id>', view_func=EditView.as_view('edit'), methods=[u'GET', u'POST'])
apis.add_url_rule('/apiset/resources/<id>', view_func=resources)
apis.add_url_rule('/apiset/<id>', view_func=read)


def get_blueprint():
    return [apis]