from dataclasses import dataclass
from typing import Any, Callable, Dict


@dataclass
class RawDataclass:
    """
    Датакласс с аттрибутом raw

    У дочернего класса задаются нужные атрибуты.
    Все значения из raw будут перенесены этим атрибутам.
    Если атрибута нет, или он уже установлен, то значение остается в raw.

    Метод ._assign_raw используется в дочернем классе, чтобы
    вручную определить атрибуты по более сложной логике перед
    автоматическим определением
    """

    raw: dict

    def __post_init__(self):
        self._assign_raw()

        keys = self.raw.keys()
        keys = list(keys)
        for key in keys:
            if hasattr(self, key) and getattr(self, key, None) is None:
                value = self.raw.pop(key)
                setattr(self, key, value)

    def _assign_raw(self):
        pass


class ObjectBuilder:
    """Билдер, возвращает инстанс объекта, тип которого находится в маппинге"""

    mapping: Dict[str, Callable[[dict, Any, Any], Any]] = None
    key: str = '@type'
    default: Callable = RawDataclass

    def __call__(self, object_dict, *args, **kwargs):
        return self.mapping.get(object_dict[self.key], self.default)(
            object_dict, *args, **kwargs
        )
