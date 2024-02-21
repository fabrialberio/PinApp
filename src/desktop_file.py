from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Generic, Optional, Type, TypeVar

from gi.repository import GLib


def split_key_locale(key: str) -> tuple[str, Optional[str]]:
    if '[' in key and key.endswith(']'):
        key, locale = key[:-1].rsplit('[', 1)
        return key, locale
    return key, None

def join_key_locale(key: str, locale: Optional[str]) -> str:
    if locale is not None:
        return f"{key}[{locale}]"
    return key

LT = TypeVar("LT", str, list[str])

@dataclass(frozen=True)
class Localized(Generic[LT]):
    locale_value: dict[Optional[str], LT]

    @classmethod
    def wrap(cls, value: LT) -> 'Localized[LT]':
        return cls({None: value})

    def __getitem__(self, locale: Optional[str]) -> LT:
        return self.locale_value[locale]

FT = TypeVar('FT',
    bool, int, float, str,
    list[bool], list[int], list[float], list[str],
    Localized[str], Localized[list[str]]
)
DT = TypeVar('DT')

@dataclass(frozen=True)
class Field(Generic[FT]):
    group: str
    key: str
    _type: Type[FT]

class DesktopEntry:
    _GROUP = 'Desktop Entry'
    
    HIDDEN =                    Field[bool](_GROUP, 'Hidden', bool)
    TERMINAL =                  Field[bool](_GROUP, 'Terminal', bool)
    NO_DISPLAY =                Field[bool](_GROUP, 'NoDisplay', bool)
    STARTUP_NOTIFY =            Field[bool](_GROUP, 'StartupNotify', bool)
    D_BUS_ACTIVATABLE =         Field[bool](_GROUP, 'DBusActivatable', bool)
    SINGLE_MAIN_WINDOW =        Field[bool](_GROUP, 'SingleMainWindow', bool)
    PREFERS_NON_DEFAULT_GPU =   Field[bool](_GROUP, 'PrefersNonDefaultGPU', bool)
    URL =               Field[str](_GROUP, 'URL', str)
    TYPE =              Field[str](_GROUP, 'Type', str)
    EXEC =              Field[str](_GROUP, 'Exec', str)
    ICON =              Field[str](_GROUP, 'Icon', str)
    PATH =              Field[str](_GROUP, 'Path', str)
    VERSION =           Field[str](_GROUP, 'Version', str)
    TRY_EXEC =          Field[str](_GROUP, 'TryExec', str)
    STARTUP_WM_CLASS =  Field[str](_GROUP, 'StartupWMClass', str)
    ACTIONS =       Field[list[str]](_GROUP, 'Actions', list[str])
    MIME_TYPE =     Field[list[str]](_GROUP, 'MimeType', list[str])
    CATEGORIES =    Field[list[str]](_GROUP, 'Categories', list[str])
    IMPLEMENTS =    Field[list[str]](_GROUP, 'Implements', list[str])
    NOT_SHOW_IN =   Field[list[str]](_GROUP, 'NotShowIn', list[str])
    ONLY_SHOW_IN =  Field[list[str]](_GROUP, 'OnlyShowIn', list[str])
    NAME =          Field[Localized[str]](_GROUP, 'Name', Localized[str])
    COMMENT =       Field[Localized[str]](_GROUP, 'Comment', Localized[str])
    KEYWORDS =      Field[Localized[list[str]]](_GROUP, 'Keywords', Localized[list[str]])
    GENERIC_NAME =  Field[Localized[str]](_GROUP, 'GenericName', Localized[str])
    X_FLATPAK =             Field[str](_GROUP, 'X-Flatpak', str)
    XGNOME_AUTOSTART =      Field[bool](_GROUP, 'X-GNOME-Autostart', bool)
    X_SNAP_INSTANCE_NAME =  Field[str](_GROUP, 'X-SnapInstanceName', str)

    @staticmethod
    def fields(): return [
        DesktopEntry.HIDDEN, DesktopEntry.TERMINAL, DesktopEntry.NO_DISPLAY, DesktopEntry.STARTUP_NOTIFY,
        DesktopEntry.D_BUS_ACTIVATABLE, DesktopEntry.SINGLE_MAIN_WINDOW, DesktopEntry.PREFERS_NON_DEFAULT_GPU,
        DesktopEntry.URL, DesktopEntry.TYPE, DesktopEntry.EXEC, DesktopEntry.ICON, DesktopEntry.PATH,
        DesktopEntry.VERSION, DesktopEntry.TRY_EXEC, DesktopEntry.STARTUP_WM_CLASS, DesktopEntry.ACTIONS,
        DesktopEntry.MIME_TYPE, DesktopEntry.CATEGORIES, DesktopEntry.IMPLEMENTS, DesktopEntry.NOT_SHOW_IN,
        DesktopEntry.ONLY_SHOW_IN, DesktopEntry.NAME, DesktopEntry.COMMENT, DesktopEntry.KEYWORDS,
        DesktopEntry.GENERIC_NAME, DesktopEntry.X_FLATPAK, DesktopEntry.XGNOME_AUTOSTART, DesktopEntry.X_SNAP_INSTANCE_NAME
    ]
    

@dataclass(eq=False, init=False)
class DesktopFile:
    path: Path
    search_str: str
    _saved_hash: int
    _key_file: GLib.KeyFile = field(init=False)

    def __init__(self, path: Path):
        self.path = path
        self._key_file = GLib.KeyFile.new()
        self._key_file.load_from_file(
            str(self.path),
            GLib.KeyFileFlags.KEEP_COMMENTS | GLib.KeyFileFlags.KEEP_TRANSLATIONS
        )

        self._saved_hash = hash(self._key_file.to_data()[0])
        self.search_str = self._key_file.to_data()[0]

    @classmethod
    def default(cls, path: Path) -> 'DesktopFile':
        file = cls(path)

        file.set(DesktopEntry.TYPE, 'Application')
        file.set(DesktopEntry.NAME, Localized[str].wrap('New Application'))
        file.set(DesktopEntry.EXEC, '')
        file.set(DesktopEntry.ICON, '')

        return file

    def edited(self) -> bool:
        return self._saved_hash != hash(self._key_file.to_data()[0])

    def save_as(self, path: Path):
        with path.open('w') as f:
            f.write(self._key_file.to_data()[0])

    def save(self):
        self.save_as(self.path)

    def __getitem__(self, field: Field[FT]) -> FT:
        ukey = split_key_locale(field.key)[0]

        if field._type == bool:
            return self._key_file.get_boolean(field.group, field.key)
        if field._type == int:
            return self._key_file.get_integer(field.group, field.key)
        if field._type == float:
            return self._key_file.get_double(field.group, field.key)
        if field._type == str:
            return self._key_file.get_string(field.group, field.key)
        if field._type == list[bool]:
            return self._key_file.get_boolean_list(field.group, field.key)
        if field._type == list[int]:
            return self._key_file.get_integer_list(field.group, field.key)
        if field._type == list[float]:
            return self._key_file.get_double_list(field.group, field.key)
        if field._type == list[str]:
            return self._key_file.get_string_list(field.group, field.key)
        if field._type == Localized[str]:
            return Localized[str](dict(map(
                lambda t: (t[1], self._key_file.get_locale_string(field.group, ukey, t[1])),
                filter(
                    lambda t: t[0] == ukey,
                    map(split_key_locale, self._key_file.get_keys(field.group)[0])
                )
            ))) # type: ignore
        if field._type == Localized[list[str]]:
            return Localized[list[str]](dict(map(
                lambda t: (t[1], self._key_file.get_locale_string_list(field.group, ukey, t[1])),
                filter(
                    lambda t: t[0] == ukey,
                    map(split_key_locale, self._key_file.get_keys(field.group)[0])
                )
            ))) # type: ignore
        
        raise ValueError(f'Unsupported field type: "{field._type}"')

    def get(self, field: Field[FT], default: DT = None) -> FT | DT:
        try:
            return self[field]
        except GLib.GError:
            return default
        
    def get_unlocalized(self, field: Field[Localized[LT]], default: DT = None) -> LT | DT: # type: ignore
        return self.get(field, Localized.wrap(default)).locale_value.get(None, default) # type: ignore

    def set(self, field: Field[FT], value: FT) -> None:
        ukey = split_key_locale(field.key)[0]

        if field._type == bool:
            self._key_file.set_boolean(field.group, field.key, value)
        elif field._type == int:
            self._key_file.set_integer(field.group, field.key, value)
        elif field._type == float:
            self._key_file.set_double(field.group, field.key, value)
        elif field._type == str:
            self._key_file.set_string(field.group, field.key, value)
        elif field._type == list[bool]:
            self._key_file.set_boolean_list(field.group, field.key, value)
        elif field._type == list[int]:
            self._key_file.set_integer_list(field.group, field.key, value)
        elif field._type == list[float]:
            self._key_file.set_double_list(field.group, field.key, value)
        elif field._type == list[str]:
            self._key_file.set_string_list(field.group, field.key, value)
        elif field._type == Localized[str]:
            assert isinstance(value, Localized)
            for l, v in value.locale_value.items():
                self._key_file.set_locale_string(field.group, ukey, l, v)
        elif field._type == Localized[list[str]]:
            assert isinstance(value, Localized)
            for l, v in value.locale_value.items():
                self._key_file.set_locale_string_list(field.group, ukey, l, v)

        raise ValueError(f'Unsupported field type: "{field._type}"')
