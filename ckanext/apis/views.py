# -*- coding: utf-8 -*-

from flask import Blueprint
import ckantoolkit as tk
import ckan.lib.helpers as h
import ckan.views.dataset as dataset
import utils

apis = Blueprint('apis_blueprint', __name__)

class CreateView(dataset.CreateView):
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


def index():
    return dataset.search(utils.DATASET_TYPE_NAME)

def manage_datasets(id):
    return utils.manage_datasets_view(id)

def read(id):
    return utils.read_view(id)

def delete(id):
    return utils.delete_view(id)

class EditView(dataset.EditView):
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


apis.add_url_rule('/apiset', view_func=index)
apis.add_url_rule('/apiset/delete/<id>', view_func=delete, methods=[u'GET', u'POST'])
apis.add_url_rule('/apiset/<id>', view_func=read)
apis.add_url_rule('/apiset/new', view_func=CreateView.as_view('new'))
apis.add_url_rule('/apiset/edit/<id>', view_func=EditView.as_view('edit'), methods=[u'GET', u'POST'])
apis.add_url_rule('/apiset/manage_datasets/<id>', view_func=manage_datasets, methods=[u'GET', u'POST'])


def get_blueprints():
    return [apis]
