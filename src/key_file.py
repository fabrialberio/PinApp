from dataclasses import dataclass, field
from pathlib import Path
from typing import Type, Callable, overload

from gi.repository import GLib


type Locale = str

type LocalizedType = str | list[str]
type FieldType = bool | int | float | str | \
    list[bool] | list[int] | list[float] | list[str] | \
    Localized[str] | Localized[list[str]]


@dataclass(frozen=True)
class Field[T: FieldType]:
    group_name: str
    key: str
    type_: type[T] = type(str)


@dataclass(init=False)
class Localized[T: LocalizedType]:
    locale_value: dict[Locale | None, T]
    locales: list[Locale] = field(init=False)

    @staticmethod
    def split_key_locale(key: str) -> tuple[str, Locale | None]:
        if '[' in key and key.endswith(']'):
            return (key.split('[')[0], key.split('[')[1].removesuffix(']'))
        else:
            return (key, None)

    @staticmethod
    def join_key_locale(key: str, locale: Locale | None) -> str:
        if locale is None:
            return key
        else:
            return f'{key}[{locale}]'

    @classmethod
    def get_from_key_file(cls,
                          key_file: 'KeyFile',
                          group_name: str,
                          key: str,
                          get_as: Type[T]
                          ) -> 'Localized[T]':
        key = Localized.split_key_locale(key)[0]
        key_value = {
            k: v for k, v in key_file.tree(get_as)[group_name].items()
            if Localized.split_key_locale(k)[0] == key
        }

        return Localized[get_as]({
            Localized.split_key_locale(k)[1]: v for k, v in key_value.items()
            if v is not None
        })

    @classmethod
    def set_to_key_file(cls,
                        key_file: 'KeyFile',
                        group_name: str,
                        key: str,
                        value: 'Localized[T]',
                        set_as: Type[T]
                        ):
        for locale, v in value.locale_value.items():
            key_file.set(Field(
                group_name,
                Localized.join_key_locale(key, locale),
                set_as
            ), v)

    @overload
    def __init__(self, value: T): ...
    @overload
    def __init__(self, value: T, locale: Locale): ...
    @overload
    def __init__(self, value: dict[Locale | None, T]): ...

    def __init__(self, value: T | dict[Locale | None, T], locale: Locale | None = None):
        if isinstance(value, dict):
            self.locale_value = value
        else:
            self.locale_value = {locale: value}

        self.locales = [l for l in self.locale_value.keys() if l is not None]

    def __getitem__(self, locale: Locale | None) -> T:
        return self.locale_value[locale]

    def unlocalized_or[D](self, default: D = None) -> T | D:
        if None in self.locale_value:
            return self.locale_value[None]
        else:
            return default


TYPE_GET_MAP: dict[type[FieldType], Callable[['_KeyFile', str, str], FieldType]] = {
    bool:                 lambda f, n, k: f._key_file.get_boolean(n, k),
    int:                  lambda f, n, k: f._key_file.get_integer(n, k),
    float:                lambda f, n, k: f._key_file.get_double(n, k),
    str:                  lambda f, n, k: f._key_file.get_string(n, k),
    list[bool]:           lambda f, n, k: f._key_file.get_boolean_list(n, k),
    list[int]:            lambda f, n, k: f._key_file.get_integer_list(n, k),
    list[float]:          lambda f, n, k: f._key_file.get_double_list(n, k),
    list[str]:            lambda f, n, k: f._key_file.get_string_list(n, k),
    Localized[str]:       lambda f, n, k: Localized.get_from_key_file(f, n, k, str),
    Localized[list[str]]: lambda f, n, k: Localized.get_from_key_file(f, n, k, list[str]),
}

TYPE_SET_MAP: dict[type[FieldType], Callable[['_KeyFile', str, str, FieldType], None]] = {
    bool:                 lambda f, n, k, v: f._key_file.set_boolean(n, k, v),
    int:                  lambda f, n, k, v: f._key_file.set_integer(n, k, v),
    float:                lambda f, n, k, v: f._key_file.set_double(n, k, v),
    str:                  lambda f, n, k, v: f._key_file.set_string(n, k, v),
    list[bool]:           lambda f, n, k, v: f._key_file.set_boolean_list(n, k, v),
    list[int]:            lambda f, n, k, v: f._key_file.set_integer_list(n, k, v),
    list[float]:          lambda f, n, k, v: f._key_file.set_double_list(n, k, v),
    list[str]:            lambda f, n, k, v: f._key_file.set_string_list(n, k, v),
    Localized[str]:       lambda f, n, k, v: Localized.set_to_key_file(f, n, k, v, str),
    Localized[list[str]]: lambda f, n, k, v: Localized.set_to_key_file(f, n, k, v, list[str]),
}


@dataclass
class KeyFile:
    path: Path
    _key_file: GLib.KeyFile = field(init=False)

    def __post_init__(self):
        self._key_file = GLib.KeyFile.new()

    def load(self):
        if not self.path.exists():
            raise FileExistsError(f'File "{self.path}" does not exist.')

        self._key_file.load_from_file(
            str(self.path),
            GLib.KeyFileFlags.KEEP_COMMENTS | GLib.KeyFileFlags.KEEP_TRANSLATIONS
        )

    def save_as(self, path: Path):
        with open(path, 'w+') as f:
            f.write(self._key_file.to_data()[0])

    def save(self):
        self.save_as(self.path)

    def get[T: FieldType, D: FieldType | None](self, field: Field[T], default: D = None) -> T | D:
        if field.group_name not in self._key_file.get_groups()[0]:
            raise KeyError(f'Group "{field.group_name}" does not exist.')
        try:
            if (r := TYPE_GET_MAP[field.type_](self, field.group_name, field.key)) is not None:
                return r

            return default
        except Exception:
            return default

    def set[T: FieldType](self, field: Field[T], value: T):
        TYPE_SET_MAP[field.type_](self, field.group_name, field.key, value)

    def tree[T: FieldType, D: FieldType | None](self,
                                                get_as: Type[T] = str,
                                                default: D = None
                                                ) -> dict[str, dict[str, T | D]]:
        return {n: {
            k: self.get(Field(n, k, get_as), default) for k in self._key_file.get_keys(n)[0]
        } for n in self._key_file.get_groups()[0]}


@dataclass(eq=False, init=False)
class HintedGroup:
    GROUP_NAME: str

    def __init__(self, group_name: str) -> None:
        self.GROUP_NAME = group_name

    def fields(self) -> list[Field]:
        ...

    def keys(self) -> list[str]:
        return [f.key for f in self.fields()]

    def __getitem__(self, key: str) -> Field:
        return next(f for f in self.fields() if f.key == key)

    def items(self) -> list[tuple[str, Field]]:
        return [(k, self[k]) for k in self.keys()]
