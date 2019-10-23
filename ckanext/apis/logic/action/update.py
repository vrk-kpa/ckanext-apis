import ckan.plugins.toolkit as toolkit


def apiset_update(context, data_dict):
    return toolkit.get_action('package_update')(context, data_dict)


def apiset_patch(context, data_dict):
    return toolkit.get_action('package_patch')(context, data_dict)
