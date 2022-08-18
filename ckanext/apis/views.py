# -*- coding: utf-8 -*-

from flask import Blueprint
import ckantoolkit as tk
import ckan.lib.helpers as h
import ckan.views.dataset as dataset
import ckanext.apis.utils as utils
import ckan.lib.base as base
import ckan.logic as logic
from ckan.common import _, g, request
from ckan.views.home import CACHE_PARAMETERS
import ckan.lib.navl.dictization_functions as dict_fns

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

class BaseCreateView(dataset.CreateView):
    def get(self, data=None, errors=None, error_summary=None):
        utils.check_new_view_auth()
        return super(CreateView, self).get(utils.DATASET_TYPE_NAME, data, errors, error_summary)

    def post(self):
        data_dict = dataset.clean_dict(dataset.dict_fns.unflatten(dataset.tuplize_dict(dataset.parse_params(
            tk.request.form))))
        data_dict.update(dataset.clean_dict(dataset.dict_fns.unflatten(dataset.tuplize_dict(dataset.parse_params(
            tk.request.files)))))
        context = self._prepare()
        data_dict['type'] = utils.DATASET_TYPE_NAME
        context['message'] = data_dict.get('log_message', '')

        try:
            pkg_dict = tk.get_action('package_create')(context, data_dict)

        except tk.ValidationError as e:
            errors = e.error_dict
            error_summary = e.error_summary
            data_dict['state'] = 'none'
            return self.get(data_dict, errors, error_summary)

        url = h.url_for('apis_blueprint.manage_datasets', id=pkg_dict['name'])
        return h.redirect_to(url)

class BaseEditView(dataset.EditView):
    def get(self, id, data=None, errors=None, error_summary=None):
        utils.check_new_view_auth()
        return super(EditView, self).get(utils.DATASET_TYPE_NAME, id, data, errors, error_summary)

    def post(self, id):
        context = self._prepare(id)
        utils.check_edit_view_auth(id)

        data_dict = dataset.clean_dict(dataset.dict_fns.unflatten(dataset.tuplize_dict(dataset.parse_params(
            tk.request.form))))
        data_dict.update(dataset.clean_dict(dataset.dict_fns.unflatten(dataset.tuplize_dict(dataset.parse_params(
            tk.request.files)))))

        data_dict['id'] = id
        try:
            pkg = tk.get_action('package_update')(context, data_dict)
        except tk.ValidationError as e:
            errors = e.error_dict
            error_summary = e.error_summary
            return self.get(id, data_dict, errors, error_summary)

        tk.c.pkg_dict = pkg

        url = h.url_for('apis_blueprint.read', id=pkg['name'])
        return h.redirect_to(url)

class CreateView(BaseCreateView):
    def get(self, data=None, errors=None, error_summary=None):
        package_type = utils.DATASET_TYPE_NAME
        utils.check_new_view_auth()
        context = self._prepare(data)
        data = data or clean_dict(dict_fns.unflatten(tuplize_dict(parse_params(request.args, ignore_keys=CACHE_PARAMETERS))))
        resources_json = h.json.dumps(data.get(u'resources', []))
        # convert tags if not supplied in data
        if data and not data.get(u'tag_string'):
            data[u'tag_string'] = u', '.join(h.dict_list_reduce(data.get(u'tags', {}), u'name'))

        errors = errors or {}
        error_summary = error_summary or {}
        # in the phased add dataset we need to know that
        # we have already completed stage 1
        stage = [u'active']
        if data.get(u'state', u'').startswith(u'draft'):
            stage = [u'active', u'complete']

        # if we are creating from a group then this allows the group to be
        # set automatically
        data[u'group_id'] = request.args.get(u'group') or request.args.get(u'groups__0__id')

        form_vars = {
            u'data': data,
            u'errors': errors,
            u'error_summary': error_summary,
            u'action': u'new',
            u'stage': stage,
            u'dataset_type': package_type,
            u'form_style': u'new'
        }
        errors_json = h.json.dumps(errors)

        # TODO: remove
        g.resources_json = resources_json
        g.errors_json = errors_json

        _setup_template_variables(context, {}, package_type=package_type)

        new_template = 'apiset/new.html'
        return base.render(
            new_template,
            extra_vars={
                u'form_vars': form_vars,
                u'form_snippet': 'apiset/package_form.html',
                u'dataset_type': package_type,
                u'resources_json': resources_json,
                u'errors_json': errors_json
            }
        )

    def post(self):
        data_dict = dataset.clean_dict(dataset.dict_fns.unflatten(dataset.tuplize_dict(dataset.parse_params(
            tk.request.form))))
        data_dict.update(dataset.clean_dict(dataset.dict_fns.unflatten(dataset.tuplize_dict(dataset.parse_params(
            tk.request.files)))))
        context = self._prepare()
        data_dict['type'] = utils.DATASET_TYPE_NAME
        context['message'] = data_dict.get('log_message', '')

        try:
            pkg_dict = tk.get_action('package_create')(context, data_dict)

        except tk.ValidationError as e:
            errors = e.error_dict
            error_summary = e.error_summary
            data_dict['state'] = 'none'
            return self.get(data_dict, errors, error_summary)

        url = h.url_for('apis_blueprint.manage_datasets', id=pkg_dict['name'])
        return h.redirect_to(url)

class EditView(BaseEditView):
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

        edit_template = 'apiset/edit_base.html'
        return base.render(
            edit_template,
            extra_vars={
                u'form_vars': form_vars,
                u'form_snippet': 'apiset/package_form.html',
                u'dataset_type': package_type,
                u'pkg_dict': pkg_dict,
                u'pkg': pkg,
                u'resources_json': resources_json,
                u'errors_json': errors_json
            }
        )

    def post(self, id):
        context = self._prepare(id)
        utils.check_edit_view_auth(id)

        data_dict = dataset.clean_dict(dataset.dict_fns.unflatten(dataset.tuplize_dict(dataset.parse_params(
            tk.request.form))))
        data_dict.update(dataset.clean_dict(dataset.dict_fns.unflatten(dataset.tuplize_dict(dataset.parse_params(
            tk.request.files)))))

        data_dict['id'] = id
        try:
            pkg = tk.get_action('package_update')(context, data_dict)
        except tk.ValidationError as e:
            errors = e.error_dict
            error_summary = e.error_summary
            return self.get(id, data_dict, errors, error_summary)

        tk.c.pkg_dict = pkg

        url = h.url_for('apis_blueprint.read', id=pkg['name'])
        return h.redirect_to(url)

def index():
    return dataset.search(utils.DATASET_TYPE_NAME)

def manage_datasets(id):
    return utils.manage_datasets_view(id)

def read(id):
    return utils.read_view(id)

def delete(id):
    return utils.delete_view(id)

apis.add_url_rule('/apiset', view_func=index)
apis.add_url_rule('/apiset/delete/<id>', view_func=delete, methods=[u'GET', u'POST'])
apis.add_url_rule('/apiset/<id>', view_func=read)
apis.add_url_rule('/apiset/new', view_func=CreateView.as_view('new'))
apis.add_url_rule('/apiset/edit/<id>', view_func=EditView.as_view('edit'), methods=[u'GET', u'POST'])
apis.add_url_rule('/apiset/manage_datasets/<id>', view_func=manage_datasets, methods=[u'GET', u'POST'])


def get_blueprint():
    return [apis]
