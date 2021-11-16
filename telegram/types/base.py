class ObjectBuilder:
    """Билдер, возвращает инстанс объекта, тип которого находится в маппинге"""

    mapping: dict = None
    key = '@type'

    def __call__(self, object_dict, *args, **kwargs):
        return self.mapping[object_dict[self.key]](object_dict, *args, **kwargs)
