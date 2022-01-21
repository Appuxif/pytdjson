import json
from dataclasses import dataclass, field
from typing import Any, Callable, Dict


@dataclass()
class RawDataclass:
    """
    Датакласс с аттрибутом raw

    У дочернего класса задаются нужные атрибуты.
    Все значения из raw будут перенесены этим атрибутам.
    Если атрибута нет, или он уже установлен, то значение остается в raw.

    Метод ._assign_raw используется в дочернем классе, чтобы
    вручную определить атрибуты по более сложной логике перед
    автоматическим определением

    Метод .as_json возвращает текстовое представление объекта в формате JSON
    """

    raw: dict = field(repr=False)

    def __post_init__(self):

        if self.raw is None:
            return

        self._assign_raw()

        keys = self.raw.keys()
        keys = list(keys)
        for key in keys:
            if hasattr(self, key) and getattr(self, key, None) is None:
                value = self.raw[key]
                setattr(self, key, value)

    def _assign_raw(self):
        pass

    def to_json(self):
        """Сериализация исходного словаря в JSON формат"""
        return json.dumps(self.raw, ensure_ascii=False)

    @classmethod
    def from_json(cls, data: str):
        """Десериализация из JSON формата"""
        data_dict = json.loads(data)
        return cls(data_dict)


class ObjectBuilder:
    """Билдер, возвращает инстанс объекта, тип которого находится в маппинге"""

    mapping: Dict[str, Callable[[dict, Any, Any], Any]] = None
    key: str = '@type'
    default: Callable = RawDataclass

    def __call__(self, object_dict, *args, **kwargs):
        return self.mapping.get(object_dict[self.key], self.default)(
            object_dict, *args, **kwargs
        )
