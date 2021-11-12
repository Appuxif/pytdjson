def build_from_mapping(mapping, object_dict):
    return mapping[object_dict['@type']](object_dict)
