from typing import Optional

from gi.repository import GObject, GLib, Gio # type: ignore
from gi._gi import pygobject_new_full

from .config import USER_APPS


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


class Field(GObject.Object):
    group: str
    key: str

    def __init__(self, group: str, key: str) -> None:
        super().__init__()

        self.group = group
        self.key = key

    def locale(self) -> Optional[str]:
        return split_key_locale(self.key)[1]

    def localize(self, locale: Optional[str]) -> 'Field':
        '''Appends a locale to the field's key.'''
        return Field(self.group, localize_key(self.key, locale))

    def __eq__(self, other: 'Field'):
        return self.group == other.group and self.key == other.key

    def __hash__(self):
        return hash((self.group, self.key))


class DesktopEntry:
    '''https://specifications.freedesktop.org/desktop-entry-spec/latest/recognized-keys.html'''

    group = GLib.KEY_FILE_DESKTOP_GROUP
    
    NAME =      Field(group, GLib.KEY_FILE_DESKTOP_KEY_NAME)
    COMMENT =   Field(group, GLib.KEY_FILE_DESKTOP_KEY_COMMENT)
    TYPE =      Field(group, GLib.KEY_FILE_DESKTOP_KEY_TYPE)
    EXEC =      Field(group, GLib.KEY_FILE_DESKTOP_KEY_EXEC)
    ICON =      Field(group, GLib.KEY_FILE_DESKTOP_KEY_ICON)
    TERMINAL =  Field(group, GLib.KEY_FILE_DESKTOP_KEY_TERMINAL)
    NO_DISPLAY =    Field(group, GLib.KEY_FILE_DESKTOP_KEY_NO_DISPLAY)
    ACTIONS =   Field(group, GLib.KEY_FILE_DESKTOP_KEY_ACTIONS)
    X_FLATPAK = Field(group, 'X-Flatpak')
    X_GNOME_AUTOSTART =     Field(group, 'X-GNOME-Autostart')
    X_SNAP_INSTANCE_NAME =  Field(group, 'X-SnapInstanceName')


class DesktopFile(GObject.Object):
    fields: Gio.ListStore
    search_str: str
    _key_file: GLib.KeyFile
    _init_hash: int

    @classmethod
    def new(cls) -> 'DesktopFile':
        return cls(GLib.KeyFile.new())

    @classmethod
    def load_from_path(cls, path: str) -> 'DesktopFile':
        key_file = GLib.KeyFile.new()
        key_file.load_from_file(
            path,
            GLib.KeyFileFlags.KEEP_COMMENTS | GLib.KeyFileFlags.KEEP_TRANSLATIONS
        )
        return cls(key_file)

    def __init__(self, key_file: GLib.KeyFile):
        super().__init__()

        self.fields = Gio.ListStore.new(GObject.TYPE_OBJECT)
        self._key_file = key_file
        self.search_str = self.to_data()
        self._init_hash = hash(self.search_str)

        for group in self._key_file.get_groups()[0]:
            for key in self._key_file.get_keys(group)[0]:
                field = Field(group, key)
                self._add_to_model(field)

    def write_to_path(self, path: str):
        with open(path, 'w') as f:
            f.write(self.to_data())
        
        self._init_hash = hash(self)

    def to_data(self) -> str:
        return self._key_file.to_data()[0]

    def edited(self) -> bool:
        return self._init_hash != hash(self.to_data())

    def has_field(self, field: Field) -> bool:
        found, index = self._find_in_model(field)
        return found

    def get_bool[D](self, field: Field, default: D = False) -> bool | D:
        try:
            return self._key_file.get_boolean(field.group, field.key)
        except GLib.GError:
            return default

    def get_str[D](self, field: Field, default: D = '') -> str | D:
        try:
            return self._key_file.get_string(field.group, field.key)
        except GLib.GError:
            return default

    def set_bool(self, field: Field, value: bool) -> None:
        self._key_file.set_boolean(field.group, field.key, value)
        self._add_to_model(field)
        self.emit('field-set', field, value)

    def set_str(self, field: Field, value: str) -> None:
        self._key_file.set_string(field.group, field.key, value)
        self._add_to_model(field)
        self.emit('field-set', field, value)

    def remove(self, field: Field) -> None:
        self._key_file.remove_key(field.group, field.key)
        self._remove_from_model(field)
        self.emit('field-removed', field)

    def localize_current(self, field: Field) -> Field:
        return field.localize(self._key_file.get_locale_for_key(field.group, field.key))

    def locales(self, field: Field) -> list[str]:
        return [
            l for k, l in (split_key_locale(f.key) for f in self.fields)
            if k == field.localize(None).key and l is not None
        ]

    def _find_in_model(self, field: Field) -> tuple[bool, int]:
        return self.fields.find_with_equal_func_full(
            field,
            lambda a, b: pygobject_new_full(a, False) == pygobject_new_full(b, False)
        )

    def _add_to_model(self, field: Field):
        found, index = self._find_in_model(field)
        if not found:
            self.fields.append(field)

    def _remove_from_model(self, field: Field) -> None:
        found, index = self._find_in_model(field)
        if found:
            self.fields.remove(index)

GObject.signal_new('field-set', DesktopFile, GObject.SignalFlags.RUN_FIRST, None, (GObject.TYPE_PYOBJECT, GObject.TYPE_PYOBJECT,))
GObject.signal_new('field-removed', DesktopFile, GObject.SignalFlags.RUN_FIRST, None, (GObject.TYPE_PYOBJECT,))
