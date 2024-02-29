from dataclasses import dataclass, field
from pathlib import Path
from typing import Generic, Optional, Type, TypeVar, get_origin, get_args

from gi.repository import GObject, GLib # type: ignore


def split_key_locale(key: str) -> tuple[str, Optional[str]]:
    if '[' in key and key.endswith(']'):
        key, locale = key[:-1].rsplit('[', 1)
        return key, locale
    return key, None

def join_key_locale(key: str, locale: Optional[str]) -> str:
    if locale is not None:
        return f"{key}[{locale}]"
    return key


FT = TypeVar('FT', bool, str, list[str])
LT = TypeVar("LT", str, list[str])
DT = TypeVar('DT')

@dataclass(frozen=True, eq=False)
class Field(Generic[FT]):
    group: str
    key: str
    _type: Type[FT]

    def __eq__(self, other: 'Field | LocaleField'):
        return self.group == other.group and self.key == other.key

class LocaleField(Field[LT]):
    def localize(self, locale: Optional[str]) -> 'Field[LT]':
        return Field[LT](self.group, join_key_locale(self.key, locale), self._type)

class DesktopEntry:
    '''https://specifications.freedesktop.org/desktop-entry-spec/latest/ar01s06.html'''

    group = 'Desktop Entry'
    
    HIDDEN =                    Field[bool](group, 'Hidden', bool)
    TERMINAL =                  Field[bool](group, 'Terminal', bool)
    NO_DISPLAY =                Field[bool](group, 'NoDisplay', bool)
    STARTUP_NOTIFY =            Field[bool](group, 'StartupNotify', bool)
    D_BUS_ACTIVATABLE =         Field[bool](group, 'DBusActivatable', bool)
    SINGLE_MAIN_WINDOW =        Field[bool](group, 'SingleMainWindow', bool)
    PREFERS_NON_DEFAULT_GPU =   Field[bool](group, 'PrefersNonDefaultGPU', bool)
    URL =               Field[str](group, 'URL', str)
    TYPE =              Field[str](group, 'Type', str)
    EXEC =              Field[str](group, 'Exec', str)
    ICON =              Field[str](group, 'Icon', str)
    PATH =              Field[str](group, 'Path', str)
    VERSION =           Field[str](group, 'Version', str)
    TRY_EXEC =          Field[str](group, 'TryExec', str)
    STARTUP_WM_CLASS =  Field[str](group, 'StartupWMClass', str)
    ACTIONS =       Field[list[str]](group, 'Actions', list[str])
    MIME_TYPE =     Field[list[str]](group, 'MimeType', list[str])
    CATEGORIES =    Field[list[str]](group, 'Categories', list[str])
    IMPLEMENTS =    Field[list[str]](group, 'Implements', list[str])
    NOT_SHOW_IN =   Field[list[str]](group, 'NotShowIn', list[str])
    ONLY_SHOW_IN =  Field[list[str]](group, 'OnlyShowIn', list[str])
    NAME =          LocaleField[str](group, 'Name', str)
    COMMENT =       LocaleField[str](group, 'Comment', str)
    KEYWORDS =      LocaleField[list[str]](group, 'Keywords', list[str])
    GENERIC_NAME =  LocaleField[str](group, 'GenericName', str)
    X_FLATPAK =             Field[str](group, 'X-Flatpak', str)
    X_SNAP_INSTANCE_NAME =  Field[str](group, 'X-SnapInstanceName', str)
    XGNOME_AUTOSTART =              Field[bool](group, 'X-GNOME-Autostart', bool)
    X_GNOME_USES_NOTIFICATIONS =    Field[bool](group, 'X-GNOME-UsesNotifications', bool)

    fields: list[Field | LocaleField] = [
        HIDDEN, TERMINAL, NO_DISPLAY, STARTUP_NOTIFY, D_BUS_ACTIVATABLE,
        SINGLE_MAIN_WINDOW, PREFERS_NON_DEFAULT_GPU, URL, TYPE, EXEC, ICON, PATH,
        VERSION, TRY_EXEC, STARTUP_WM_CLASS, ACTIONS, MIME_TYPE, CATEGORIES,
        IMPLEMENTS, NOT_SHOW_IN, ONLY_SHOW_IN, NAME, COMMENT, KEYWORDS, GENERIC_NAME,
        X_FLATPAK, XGNOME_AUTOSTART, X_SNAP_INSTANCE_NAME, X_GNOME_USES_NOTIFICATIONS
    ]
    

@dataclass(init=False, unsafe_hash=False)
class DesktopFile(GObject.Object):
    path: Path
    search_str: str
    _saved_hash: int
    _key_file: GLib.KeyFile = field(init=False)

    def __init__(self, path: Path):
        super().__init__()

        self.path = path
        self._key_file = GLib.KeyFile.new()
        self._key_file.load_from_file(
            str(self.path),
            GLib.KeyFileFlags.KEEP_COMMENTS | GLib.KeyFileFlags.KEEP_TRANSLATIONS
        )

        self._saved_hash = hash(self)
        self.search_str = self._key_file.to_data()[0].lower()

    @classmethod
    def default(cls, path: Path) -> 'DesktopFile':
        file = cls(path)

        file.set(DesktopEntry.TYPE, 'Application')
        file.set(DesktopEntry.NAME, 'New Application')
        file.set(DesktopEntry.EXEC, '')
        file.set(DesktopEntry.ICON, '')

        return file

    def edited(self) -> bool:
        return self._saved_hash != hash(self)

    def save_as(self, path: Path):
        with path.open('w') as f:
            f.write(self._key_file.to_data()[0])
        
        self._saved_hash = hash(self)

    def save(self):
        self.save_as(self.path)

    def __getitem__(self, field: Field[FT]) -> FT:
        ukey = split_key_locale(field.key)[0]

        if field._type == bool:
            return self._key_file.get_boolean(field.group, field.key)
        if field._type == str:
            return self._key_file.get_string(field.group, field.key)
        if field._type == list[str]:
            return self._key_file.get_string_list(field.group, field.key)
        
        raise ValueError(f'Unsupported field type: "{field._type}"')

    def get(self, field: Field[FT], default: DT = None) -> FT | DT:
        try:
            return self[field]
        except GLib.GError:
            return default

    def set(self, field: Field[FT], value: FT) -> None:
        if field._type == bool:
            self._key_file.set_boolean(field.group, field.key, value)
        elif field._type == str:
            self._key_file.set_string(field.group, field.key, value)
        elif field._type == list[str]:
            self._key_file.set_string_list(field.group, field.key, value)
        else:
            raise ValueError(f'Unsupported field type: "{field._type}"')

        self.emit('field-set', field, value)

    def remove(self, field: Field) -> None:
        self._key_file.remove_key(field.group, field.key)
        self.emit('field-removed', field)

    def locales(self, field: LocaleField[LT]) -> list[str]:
        return [
            l\
            for k, l in map(split_key_locale, self._key_file.get_keys(field.group)[0])\
            if k == field.key and l is not None
        ]

    def fields(self, group: str) -> list[Field[str] | LocaleField[str]]:
        '''Returns a list of all fields in the specified group, cast to str.'''

        key_field: dict[str, Field[str]] = {}

        for key in self._key_file.get_keys(group)[0]:
            ukey, locale = split_key_locale(key)
            
            if locale is None:
                key_field[ukey] = Field[str](group, key, str)
            else:
                key_field[ukey] = LocaleField[str](group, ukey, str)

        return list(key_field.values())

    def __hash__(self) -> int:
        return hash(self._key_file.to_data()[0])
    
    def __repr__(self) -> str:
        return f'DesktopFile({self.path})'

    @property
    def __doc__(self): return None

    @__doc__.setter # Added to avoid clash when dataclass tries to set __doc__ of GObject.Object
    def __doc__(self, _): ...

GObject.signal_new('field-set', DesktopFile, GObject.SignalFlags.RUN_FIRST, None, (GObject.TYPE_PYOBJECT, GObject.TYPE_PYOBJECT,))
GObject.signal_new('field-removed', DesktopFile, GObject.SignalFlags.RUN_FIRST, None, (GObject.TYPE_PYOBJECT,))
