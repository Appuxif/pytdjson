from __future__ import annotations

import json
from dataclasses import Field, asdict, dataclass, field, fields
from enum import Enum
from operator import attrgetter, itemgetter
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
)


@dataclass()
class RawDataclass:
    """
    Датакласс с аттрибутом raw

    У дочернего класса задаются нужные атрибуты.
    Все значения из raw будут перенесены этим атрибутам.
    Если атрибута нет, или он уже установлен, то значение остается в raw.

    Метод ._assign_raw используется в дочернем классе, чтобы
    вручную определить атрибуты по более сложной логике перед
    автоматическим определением.

    Метод .as_json возвращает текстовое представление объекта в формате JSON.
    """

    raw: dict = field(repr=False)  # type: ignore

    _no_assign_raw = False

    def __post_init__(self) -> None:

        if self.raw is None:
            return

        if self._no_assign_raw:
            return

        self._assign_raw()

        for key in self.raw.keys():
            if hasattr(self, key) and getattr(self, key, None) is None:

                key_field: Optional[Field[RawDataclass]]
                key_field = self.__dataclass_fields__.get(key)  # noqa

                if key_field is None:
                    value = self.raw[key]
                else:
                    value = key_field.type(self.raw[key])  # noqa

                setattr(self, key, value)

    def _assign_raw(self) -> None:
        pass

    def _assign_raw_optional(
        self, key: str, field_cls: Optional[Type[Any]] = None
    ) -> None:
        field_cls = field_cls or self.__dataclass_fields__[key].type  # noqa
        value = self.raw.get(key, None)
        if value:
            setattr(self, key, field_cls(value))

    def to_json(self) -> str:
        """Сериализация исходного словаря в JSON формат"""
        return json.dumps(self.raw, ensure_ascii=False)

    @classmethod
    def from_json(cls, data: str) -> 'RawDataclass':
        """Десериализация из JSON формата"""
        data_dict = json.loads(data)
        return cls(data_dict)

    def asdict(self) -> Dict[Any, Any]:
        return asdict(self, dict_factory=dict_factory)


T = TypeVar('T')


@dataclass
class RawDataclassField(Generic[T]):
    """Дескриптор поля для RawDataclass"""

    field_kwargs: Dict[str, Any] = field(default_factory=dict)

    value_getter: Tuple[str, ...] = ()
    raw_key: str = ''

    key_name: str = ''
    _name = None

    def __get__(
        self, instance: RawDataclass, owner: Type[RawDataclass]
    ) -> None | Field[T] | T:

        if instance is None:
            return field(repr=True, init=False, default=self)

        if instance.raw is None:
            return None

        value_getter = self.value_getter or (self.key_name or self._name,)
        raw_value: Any = instance.raw
        value: T
        for key in value_getter:
            if isinstance(raw_value, dict):
                raw_value = raw_value.get(key, None)
            else:
                break

        if raw_value is None:
            return None

        dataclass_fields: Dict[Any, Any] = instance.__dataclass_fields__  # noqa
        key_field: Field[Any] | None = dataclass_fields.get(self._name)

        value = raw_value
        if key_field is not None:
            value = key_field.type(value)  # noqa

        return value

    def __set__(self, instance: RawDataclass, value: Any) -> None:
        value_getter = self.value_getter or (self.key_name or self._name,)
        raw_value = instance.raw
        for key in value_getter[:-1]:
            raw_value = raw_value[key]
        raw_value[value_getter[-1]] = value

    def __set_name__(self, owner: Type[RawDataclass], name: str) -> None:
        self._name = name


class ObjectBuilder:
    """Билдер, возвращает инстанс объекта, тип которого находится в маппинге"""

    mapping: Dict[str, Type[RawDataclass]] = {}
    key: str = '@type'
    default: Type[RawDataclass] = RawDataclass

    def __call__(self, object_dict: Dict[Any, Any]) -> RawDataclass:
        object_dataclass = self.mapping.get(object_dict[self.key])
        if object_dataclass is None:
            object_dataclass = self.default
        return object_dataclass(object_dict)


def build_variables(cls: Type[RawDataclass], base: Optional[str] = None) -> List[str]:
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


def build_variables_for_object_builder(
    cls_field: Field,  # type: ignore
    base: str,
) -> List[Any]:
    """Пробегается по ObjectBuilder.mapping и объединяет всевозможные поля"""
    return list(
        {
            var
            for child_cls in cls_field.type.mapping.values()
            for var in build_variables(child_cls, base)
        }
    )


def dict_factory(values: List[Tuple[str, Any]]) -> Dict[str, Any]:
    values = list(values)

    for i, value in enumerate(values):
        if isinstance(value[1], Enum):
            values[i] = [value[0], str(value[1])]  # type: ignore[call-overload]

    return dict(values)
