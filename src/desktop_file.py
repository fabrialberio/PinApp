from pathlib import Path
from typing import Optional
from enum import Enum, auto

from gi.repository import GObject, GLib, Gio # type: ignore
from gi._gi import pygobject_new_full


def split_key_locale(key: str) -> tuple[str, Optional[str]]:
    if '[' in key and key.endswith(']'):
        key, locale = key[:-1].rsplit('[', 1)
        return key, locale
    return key, None

def localize_key(key: str, locale: Optional[str]) -> str:
    ukey, _ = split_key_locale(key)

    if locale is not None:
        return f"{ukey}[{locale}]"
    return ukey


FT = bool | str | list[str]
LT = str | list[str]

class FieldType(Enum):
    BOOL = auto()
    STRING = auto()
    STRING_LIST = auto()
    LOCALIZED_STRING = auto()
    LOCALIZED_STRING_LIST = auto()

class Field(GObject.Object):
    group: str
    key: str
    field_type: FieldType

    def __init__(self, group: str, key: str, field_type: FieldType) -> None:
        super().__init__()

        self.group = group
        self.key = key
        self.field_type = field_type

    def default_value(self) -> FT:
        match self.field_type:
            case FieldType.BOOL:
                return False
            case FieldType.STRING | FieldType.LOCALIZED_STRING:
                return ''
            case FieldType.STRING_LIST | FieldType.LOCALIZED_STRING_LIST:
                return []

    def locale(self) -> Optional[str]:
        return split_key_locale(self.key)[1]

    def localize(self, locale: Optional[str]) -> 'Field':
        '''Appends a locale to the field's key.'''
        return Field(self.group, localize_key(self.key, locale), self.field_type)

    def __eq__(self, other: 'Field'):
        return self.group == other.group and self.key == other.key

    def __hash__(self):
        return hash((self.group, self.key))

class DesktopEntry:
    '''https://specifications.freedesktop.org/desktop-entry-spec/latest/ar01s06.html'''

    group = 'Desktop Entry'
    
    HIDDEN =                    Field(group, 'Hidden', FieldType.BOOL)
    TERMINAL =                  Field(group, 'Terminal', FieldType.BOOL)
    NO_DISPLAY =                Field(group, 'NoDisplay', FieldType.BOOL)
    STARTUP_NOTIFY =            Field(group, 'StartupNotify', FieldType.BOOL)
    D_BUS_ACTIVATABLE =         Field(group, 'DBusActivatable', FieldType.BOOL)
    SINGLE_MAIN_WINDOW =        Field(group, 'SingleMainWindow', FieldType.BOOL)
    PREFERS_NON_DEFAULT_GPU =   Field(group, 'PrefersNonDefaultGPU', FieldType.BOOL)
    URL =               Field(group, 'URL', FieldType.STRING)
    TYPE =              Field(group, 'Type', FieldType.STRING)
    EXEC =              Field(group, 'Exec', FieldType.STRING)
    ICON =              Field(group, 'Icon', FieldType.STRING)
    PATH =              Field(group, 'Path', FieldType.STRING)
    VERSION =           Field(group, 'Version', FieldType.STRING)
    TRY_EXEC =          Field(group, 'TryExec', FieldType.STRING)
    STARTUP_WM_CLASS =  Field(group, 'StartupWMClass', FieldType.STRING)
    ACTIONS =       Field(group, 'Actions', FieldType.STRING_LIST)
    MIME_TYPE =     Field(group, 'MimeType', FieldType.STRING_LIST)
    CATEGORIES =    Field(group, 'Categories', FieldType.STRING_LIST)
    IMPLEMENTS =    Field(group, 'Implements', FieldType.STRING_LIST)
    NOT_SHOW_IN =   Field(group, 'NotShowIn', FieldType.STRING_LIST)
    ONLY_SHOW_IN =  Field(group, 'OnlyShowIn', FieldType.STRING_LIST)
    NAME =          Field(group, 'Name', FieldType.LOCALIZED_STRING)
    COMMENT =       Field(group, 'Comment', FieldType.LOCALIZED_STRING)
    KEYWORDS =      Field(group, 'Keywords', FieldType.LOCALIZED_STRING_LIST)
    GENERIC_NAME =  Field(group, 'GenericName', FieldType.LOCALIZED_STRING)
    X_FLATPAK =             Field(group, 'X-Flatpak', FieldType.STRING)
    X_SNAP_INSTANCE_NAME =  Field(group, 'X-SnapInstanceName', FieldType.STRING)
    XGNOME_AUTOSTART =              Field(group, 'X-GNOME-Autostart', FieldType.BOOL)
    X_GNOME_USES_NOTIFICATIONS =    Field(group, 'X-GNOME-UsesNotifications', FieldType.BOOL)

    fields: list[Field] = [
        HIDDEN, TERMINAL, NO_DISPLAY, STARTUP_NOTIFY, D_BUS_ACTIVATABLE,
        SINGLE_MAIN_WINDOW, PREFERS_NON_DEFAULT_GPU, URL, TYPE, EXEC, ICON, PATH,
        VERSION, TRY_EXEC, STARTUP_WM_CLASS, ACTIONS, MIME_TYPE, CATEGORIES,
        IMPLEMENTS, NOT_SHOW_IN, ONLY_SHOW_IN, NAME, COMMENT, KEYWORDS, GENERIC_NAME,
        X_FLATPAK, XGNOME_AUTOSTART, X_SNAP_INSTANCE_NAME, X_GNOME_USES_NOTIFICATIONS
    ]
    

class DesktopFile(GObject.Object):
    path: Path
    fields: Gio.ListStore
    search_str: str
    _key_file: GLib.KeyFile
    _saved_hash: int

    def __init__(self, path: Path):
        super().__init__()

        self.path = path
        self.fields = Gio.ListStore.new(GObject.TYPE_OBJECT)

        self._key_file = GLib.KeyFile.new()
        self._key_file.load_from_file(
            str(path),
            GLib.KeyFileFlags.KEEP_COMMENTS | GLib.KeyFileFlags.KEEP_TRANSLATIONS
        )
        self._saved_hash = hash(self)
        self.search_str = self._key_file.to_data()[0].lower()

        for group in self._key_file.get_groups()[0]:
            for key in self._key_file.get_keys(group)[0]:
                field = Field(group, key, FieldType.STRING)
                self._add_to_model(field)

    def edited(self) -> bool:
        return self._saved_hash != hash(self)

    def save_as(self, path: Path):
        with path.open('w') as f:
            f.write(self._key_file.to_data()[0])
        
        self._saved_hash = hash(self)

    def save(self):
        self.save_as(self.path)

    def __getitem__(self, field: Field) -> FT:
        match field.field_type:
            case FieldType.BOOL:
                return self._key_file.get_boolean(field.group, field.key)
            case FieldType.STRING | FieldType.LOCALIZED_STRING:
                return self._key_file.get_string(field.group, field.key)
            case FieldType.STRING_LIST | FieldType.LOCALIZED_STRING_LIST:
                return self._key_file.get_string_list(field.group, field.key)

    def get(self, field: Field, default: Optional[FT] = None) -> Optional[FT]:
        try:
            return self[field]
        except GLib.GError:
            return default

    def localize_current(self, field: Field) -> Field:
        return field.localize(self._key_file.get_locale_for_key(field.group, field.key))

    def set(self, field: Field, value: FT) -> None:
        match field.field_type:
            case FieldType.BOOL:
                self._key_file.set_boolean(field.group, field.key, value)
            case FieldType.STRING | FieldType.LOCALIZED_STRING:
                self._key_file.set_string(field.group, field.key, value)
            case FieldType.STRING_LIST | FieldType.LOCALIZED_STRING_LIST:
                self._key_file.set_string_list(field.group, field.key, value)

        self.emit('field-set', field, value)
        self._add_to_model(field)

    def remove(self, field: Field) -> None:
        self._key_file.remove_key(field.group, field.key)
        self.emit('field-removed', field)
        self._remove_from_model(field)

    def locales(self, field: Field) -> list[str]:
        return [
            l\
            for k, l in (split_key_locale(f.key) for f in self.fields)
            if k == field.localize(None).key and l is not None
        ]

    def _find_in_model(self, field: Field) -> tuple[bool, int]:
        return self.fields.find_with_equal_func_full(
            field,
            lambda a, b: pygobject_new_full(a, False) == pygobject_new_full(b, False)
        )

    def _add_to_model(self, field: Field):
        found, index = self._find_in_model(field)
        if found:
            if field.field_type != self.fields.get_item(index).field_type:
                self.fields.remove(index)
                self.fields.insert(index, field)
        else:
            self.fields.append(field)

    def _remove_from_model(self, field: Field) -> None:
        found, index = self._find_in_model(field)
        if found:
            self.fields.remove(index)

    def __hash__(self) -> int:
        return hash(self._key_file.to_data()[0])

GObject.signal_new('field-set', DesktopFile, GObject.SignalFlags.RUN_FIRST, None, (GObject.TYPE_PYOBJECT, GObject.TYPE_PYOBJECT,))
GObject.signal_new('field-removed', DesktopFile, GObject.SignalFlags.RUN_FIRST, None, (GObject.TYPE_PYOBJECT,))
