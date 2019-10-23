import ckan.plugins.toolkit as toolkit


def apiset_create(context, data_dict):
    data_dict['type'] = 'apiset'
    return toolkit.get_action('package_create')(context, data_dict)
