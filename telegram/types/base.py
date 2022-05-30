import json
from dataclasses import Field, asdict, dataclass, field, fields
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Type


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

    def __post_init__(self) -> None:

        if self.raw is None:
            return

        self._assign_raw()

        for key in self.raw.keys():
            if hasattr(self, key) and getattr(self, key, None) is None:
                key_field: Optional[
                    Field[RawDataclass]
                ] = self.__dataclass_fields__.get(key)

                if key_field is None:
                    value = self.raw[key]
                else:
                    value = key_field.type(self.raw[key])

                setattr(self, key, value)

    def _assign_raw(self) -> None:
        pass

    def _assign_raw_optional(
        self, key: str, field_cls: Optional[Type[Any]] = None
    ) -> None:
        field_cls = field_cls or self.__dataclass_fields__[key].type
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


class ObjectBuilder:
    """Билдер, возвращает инстанс объекта, тип которого находится в маппинге"""

    mapping: Dict[str, Type[RawDataclass]] = {}
    key: str = '@type'
    default: Type[RawDataclass] = RawDataclass

    def __call__(
        self, object_dict: Dict[Any, Any], *args: Any, **kwargs: Any
    ) -> RawDataclass:
        return self.mapping.get(object_dict[self.key], self.default)(
            object_dict, *args, **kwargs
        )


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
