import ckan.plugins.toolkit as toolkit


def apiset_delete(context, data_dict):
    return toolkit.get_action('package_delete')(context, data_dict)
