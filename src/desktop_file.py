from dataclasses import dataclass, field
from pathlib import Path
from typing import Type, Callable, overload

from gi.repository import GLib


type LocalizedFieldType = str | list[str]
type FieldType = bool | int | float | str | \
                 list[bool] | list[int] | list[float] | list[str] | \
                 Localized[str] | Localized[list[str]]


@dataclass(init = False)
class Localized[T: LocalizedFieldType]:
    locale_value: dict[str|None, T]
    locales: list[str] = field(init = False)

    @staticmethod
    def split_key_locale(key: str) -> tuple[str, str|None]:
        if '[' in key and key.endswith(']'):
            return (key.split('[')[0], key.split('[')[1].removesuffix(']'))
        else:
            return (key, None)
        
    @staticmethod
    def join_key_locale(key: str, locale: str|None) -> str:
        if locale is None:
            return key
        else:
            return f'{key}[{locale}]'

    @classmethod
    def get_from_key_file(cls,
            key_file: '_KeyFile',
            group_name: str,
            key: str,
            get_as: Type[T]
        ) -> 'Localized[T]':
        key = Localized.split_key_locale(key)[0]
        key_value = {k: v for k, v in key_file.tree(get_as)[group_name].items() \
                     if Localized.split_key_locale(k)[0] == key}

        return Localized[get_as]({Localized.split_key_locale(k)[1]: v for k, v in key_value.items() \
                                  if v is not None})
    
    @classmethod
    def set_to_key_file(cls,
            key_file: '_KeyFile',
            group_name: str,
            key: str,
            value: 'Localized[T]',
            set_as: Type[T]
        ):
        for locale, v in value.locale_value.items():
            key_file.set(group_name, Localized.join_key_locale(key, locale), v, set_as)

    @overload
    def __init__(self, value: T): ...
    @overload
    def __init__(self, value: T, locale: str): ...
    @overload
    def __init__(self, value: dict[str|None, T]): ...

    def __init__(self, value: T|dict[str|None, T], locale: str|None = None):
        if isinstance(value, dict):
            self.locale_value = value
        else:
            self.locale_value = {locale: value}

        self.locales = [l for l in self.locale_value.keys() if l is not None]

    def __getitem__(self, locale: str|None) -> LocalizedFieldType:
        return self.locale_value[locale]

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
class _KeyFile:
    path: Path
    _key_file: GLib.KeyFile = field(init = False)

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

    def get[T: FieldType, D: FieldType|None](self,
            group_name: str,
            key: str,
            get_as: Type[T],
            default: D = None
        ) -> T|D:
        if group_name not in self._key_file.get_groups()[0]:
            raise KeyError(f'Group "{group_name}" does not exist.')
        try:
            if (r := TYPE_GET_MAP[get_as](self, group_name, key)) is not None:
                return r
            else:
                return default
        except Exception:
            return default

    def set[T: FieldType](self,
            group_name: str,
            key: str,
            value: T,
            set_as: Type[T]
        ):
        TYPE_SET_MAP[set_as](self, group_name, key, value)

    def tree[T: FieldType, D: FieldType|None](self,
            get_as: Type[T] = str,
            default: D = None
        ) -> dict[str, dict[str, T|D]]:
        return {n: {
            k: self.get(n, k, get_as, default) for k in self._key_file.get_keys(n)[0]
        } for n in self._key_file.get_groups()[0]}

    def __dict__(self) -> dict[str, list[str]]:
        return {n: [
            k for k in self._key_file.get_keys(n)[0]
        ] for n in self._key_file.get_groups()[0]}


DESKTOP_ENTRY_GROUP_NAME = 'Desktop Entry'
DESKTOP_ACTION_GROUP_PREFIX = 'Desktop Action '

@dataclass
class MagicGroup:
    _key_file: _KeyFile
    _group_name: str

    def __getattr__(self, name: str) -> FieldType|None:
        if name in self.__annotations__:
            get_as = self.__annotations__[name]
            return self._key_file.get(self._group_name, name.replace('_', '-'), get_as)
        else:
            raise AttributeError(f'Attribute "{name}" does not exist.')
    
    def __setattr__(self, name: str, value: FieldType):
        if name in self.__annotations__:
            set_as = self.__annotations__[name]
            self._key_file.set(self._group_name, name.replace('_', '-'), value, set_as)
        else:
            super().__setattr__(name, value)

    def __dict__(self) -> dict[str, FieldType]:
        return {name: getattr(self, name) for name in self.__annotations__}

class DesktopEntry(MagicGroup):
    NoDisplay: bool
    Hidden: bool
    DBusActivatable: bool
    Terminal: bool
    StartupNotify: bool
    PrefersNonDefaultGPU: bool
    SingleMainWindow: bool
    Type: str
    Exec: str
    Icon: str
    Version: str
    TryExec: str
    Path: str
    StartupWMClass: str
    URL: str
    OnlyShowIn: list[str]
    NotShowIn: list[str]
    Actions: list[str]
    MimeType: list[str]
    Categories: list[str]
    Implements: list[str]
    Name: Localized[str]
    GenericName: Localized[str]
    Comment: Localized[str]
    Keywords: Localized[list[str]]
    X_Flatpak: str
    X_SnapInstanceName: str
    X_GNOME_Autostart: bool

class DesktopAction(MagicGroup):
    Name: Localized[str]
    Icon: str
    Exec: str

@dataclass(eq = False, init = False)
class DesktopFile(_KeyFile):
    search_str: str
    _saved_hash: int
    desktop_entry: DesktopEntry
    desktop_actions: list[DesktopAction]

    @classmethod
    def new_with_defaults(cls, path: Path) -> 'DesktopFile':
        f = cls(path)

        f.desktop_entry.Type = 'Application'
        f.desktop_entry.Name = Localized[str]('New Application')
        f.desktop_entry.Exec = 'echo "Hello World"'
        f.desktop_entry.Icon = ''

        return f

    def __post_init__(self):
        super().__post_init__()

        self.load()

    def edited(self) -> bool:
        return self._saved_hash != hash(self)
    
    def load(self):
        super().load()

        self.desktop_entry = DesktopEntry(self, DESKTOP_ENTRY_GROUP_NAME)
        self.desktop_actions = [
            DesktopAction(self, n) for n in self._key_file.get_groups()[0] \
            if n.startswith(DESKTOP_ACTION_GROUP_PREFIX)
        ]

        self._saved_hash = hash(self)
        self.search_str = self.__search_str__()

    def save_as(self, path=None):
        super().save_as(path)

        self._saved_hash = hash(self)

    def __search_str__(self) -> str:
        file_name = self.path.stem
        de_values = '\n'.join(self.get(self.desktop_entry._group_name, k, str, '') for k in self.desktop_entry.__dict__().keys())
        de_true_keys = '\n'.join(k for k, v in self.desktop_entry.__dict__().items() if v)
        da_values = '\n'.join(self.get(a._group_name, k, str, '') for a in self.desktop_actions for k in a.__dict__().keys())

        return '\n'.join([file_name, de_values, de_true_keys, da_values]).lower()
    
    def __hash__(self) -> int:
        return hash(tuple((k, tuple(v.items())) for k, v in self.tree().items()))