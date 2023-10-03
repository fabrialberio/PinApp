from dataclasses import dataclass, field
from pathlib import Path
from typing import Type, TypeVar, Generic, Any, Callable

from gi.repository import GLib


type LocalizedFieldType = str | list[str]
type FieldType = bool | int | float | str | \
                 list[bool] | list[int] | list[float] | list[str] | \
                 Localized[str] | Localized[list[str]]

@dataclass
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

    def __post_init__(self):
        self.locales = [l for l in self.locale_value.keys() if l is not None]

    def __getitem__(self, locale: str|None) -> LocalizedFieldType:
        return self.locale_value[locale]

TYPE_GET_MAP: dict[type[FieldType], Callable[[GLib.KeyFile, str, str], Any]] = {
    bool: GLib.KeyFile.get_boolean,
    int: GLib.KeyFile.get_integer,
    float: GLib.KeyFile.get_double,
    str: GLib.KeyFile.get_string,
    list[bool]: GLib.KeyFile.get_boolean_list,
    list[int]: GLib.KeyFile.get_integer_list,
    list[float]: GLib.KeyFile.get_double_list,
    list[str]: GLib.KeyFile.get_string_list,
    Localized[str]: lambda f, n, k: Localized.get_from_key_file(f, n, k, str),
    Localized[list[str]]: lambda f, n, k: Localized.get_from_key_file(f, n, k, list[str]),
}

TYPE_SET_MAP: dict[type[FieldType], Callable[['_KeyFile', str, str, Any], None]] = {
    bool: lambda f, n, k, v: f._key_file.set_boolean(n, k, v),
    int: GLib.KeyFile.set_integer,
    float: GLib.KeyFile.set_double,
    str: GLib.KeyFile.set_string,
    list[bool]: GLib.KeyFile.set_boolean_list,
    list[int]: GLib.KeyFile.set_integer_list,
    list[float]: GLib.KeyFile.set_double_list,
    list[str]: GLib.KeyFile.set_string_list,
    Localized[str]: lambda f, n, k, v: Localized.set_to_key_file(f, n, k, v, str),
    Localized[list[str]]: lambda f, n, k, v: Localized.set_to_key_file(f, n, k, v, list[str]),
}

@dataclass
class _KeyFile(GLib.KeyFile):
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
            f.write(self._key_file.to_data())

    def save(self):
        self.save_as(self.path)

    def get[GetType: FieldType, DefaultType: FieldType|None](self,
            group_name: str,
            key: str,
            get_as: Type[GetType],
            default: DefaultType = None
        ) -> GetType|DefaultType:
        if group_name not in self._key_file.get_groups()[0]:
            raise KeyError(f'Group "{group_name}" does not exist.')
        try:
            if (r := TYPE_GET_MAP[get_as](self._key_file, group_name, key)) is not None:
                return r
            else:
                return default
        except Exception:
            raise
            return default

    def set[SetType: FieldType](self,
            group_name: str,
            key: str,
            value: SetType,
            set_as: Type[SetType]
        ):
        TYPE_SET_MAP[set_as](self._key_file, group_name, key, value)

    def tree[TreeValues: FieldType, DefaultType: FieldType|None](self,
            get_as: Type[TreeValues] = str,
            default: DefaultType = None
        ) -> dict[str, dict[str, TreeValues|DefaultType]]:
        return {n: {
            k: self.get(n, k, get_as, default) for k in self._key_file.get_keys(n)[0]
        } for n in self._key_file.get_groups()[0]}

    def __dict__(self) -> dict[str, list[str]]:
        return {n: [
            k for k in self._key_file.get_keys(n)[0]
        ] for n in self._key_file.get_groups()[0]}


@dataclass
class DesktopEntry:
    no_display: bool
    hidden: bool
    d_bus_activatable: bool
    terminal: bool
    startup_notify: bool
    prefers_non_default_gpu: bool
    single_main_window: bool
    type_: str
    exec_: str
    icon: str
    version: str
    try_exec: str
    path: str
    startup_wm_class: str
    url: str
    only_show_in: list[str]
    not_show_in: list[str]
    actions: list[str]
    mime_type: list[str]
    categories: list[str]
    implements: list[str]
    name: str
    generic_name: str
    comment: str
    keywords: list[str]
    x_flatpak: str
    x_snap_instance_name: str
    x_gnome_autostart: bool
    

class DesktopFile(_KeyFile):
    search_str: str
    _saved_hash: int

    def __post_init__(self):
        super().__post_init__()

        self.load()

    def edited(self) -> bool:
        return self._saved_hash != hash(self)
    
    def load(self):
        super().load()

        self._saved_hash = hash(self)
        self.search_str = self.__search_str__()

    def save_as(self, path=None):
        super().save_as(path)

        self._saved_hash = hash(self)

    def __search_str__(self) -> str:
        file_name = self.path.stem
        de_values = '\n'.join(v for v in self.desktop_entry.__dict__().values())
        de_true_keys = '\n'.join(k for k, v in self.desktop_entry.__dict__().items() if v == 'true')
        da_values = '\n'.join(v for a in self.desktop_actions for v in a.__dict__().values())

        return '\n'.join([file_name, de_values, de_true_keys, da_values]).lower()
    
    def __hash__(self) -> int:
        return hash(tuple(self.tree().items()))