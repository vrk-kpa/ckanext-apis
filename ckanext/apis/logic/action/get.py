import ckan.plugins.toolkit as toolkit
import ckan.lib.dictization.model_dictize as model_dictize


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
