import json
from dataclasses import dataclass, field, fields, asdict
from enum import Enum
from typing import Callable, Dict, Type


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
                key_field = self.__dataclass_fields__.get(key)
                value_type = key_field.type if key_field else (lambda a: a)
                value = value_type(self.raw[key])
                setattr(self, key, value)

    def _assign_raw(self):
        pass

    def _assign_raw_optional(self, key, field_cls=None):
        field_cls = field_cls or self.__dataclass_fields__[key].type
        value = self.raw.get(key, None)
        if value:
            setattr(self, key, field_cls(value))

    def to_json(self):
        """Сериализация исходного словаря в JSON формат"""
        return json.dumps(self.raw, ensure_ascii=False)

    @classmethod
    def from_json(cls, data: str):
        """Десериализация из JSON формата"""
        data_dict = json.loads(data)
        return cls(data_dict)

    def asdict(self):
        return asdict(self, dict_factory=dict_factory)


class ObjectBuilder:
    """Билдер, возвращает инстанс объекта, тип которого находится в маппинге"""

    mapping: Dict[str, Type[RawDataclass]] = None
    key: str = '@type'
    default: Callable = RawDataclass

    def __call__(self, object_dict, *args, **kwargs):
        return self.mapping.get(object_dict[self.key], self.default)(
            object_dict, *args, **kwargs
        )


def build_variables(cls: Type[RawDataclass], base=None):
    """Пробегается по всему дереву вложенных объектов и
    возвращает список из возможных переменных для доступа к значению
    через f-strings

    например {message.chat.last_message.sender.id}
    """
    variables = []
    base = base or cls.__name__.lower()

    for cls_field in fields(cls):
        if not cls_field.repr:
            continue

        variable = f'{base}.{cls_field.name}'
        _variables = [variable]

        if isinstance(cls_field.type, ObjectBuilder):
            _variables = build_variables_for_object_builder(cls_field, variable)

        elif isinstance(cls_field.type, type) and issubclass(
            cls_field.type, RawDataclass
        ):
            _variables = build_variables(cls_field.type, variable)

        variables.extend(_variables)

    return variables


def build_variables_for_object_builder(cls_field, base):
    """Пробегается по ObjectBuilder.mapping и объединяет всевозможные поля"""
    return list(
        {
            var
            for child_cls in cls_field.type.mapping.values()
            for var in build_variables(child_cls, base)
        }
    )


def dict_factory(values: list):
    values = list(values)

    for i, value in enumerate(values):
        if isinstance(value[1], Enum):
            values[i] = [value[0], str(value[1])]

    return dict(values)
