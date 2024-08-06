from pathlib import Path
from typing import Optional

from gi.repository import GObject, GLib, Gio # type: ignore
from gi._gi import pygobject_new_full

from .file_pool import USER_POOL


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

    group = 'Desktop Entry'
    
    NAME =      Field(group, 'Name')
    COMMENT =   Field(group, 'Comment')
    TYPE =      Field(group, 'Type')
    EXEC =      Field(group, 'Exec')
    ICON =      Field(group, 'Icon')
    TERMINAL =  Field(group, 'Terminal')
    NO_DISPLAY =    Field(group, 'NoDisplay')
    ACTIONS =   Field(group, 'Actions')
    X_FLATPAK = Field(group, 'X-Flatpak')
    X_GNOME_AUTOSTART =     Field(group, 'X-GNOME-Autostart')
    X_SNAP_INSTANCE_NAME =  Field(group, 'X-SnapInstanceName')


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
                field = Field(group, key)
                self._add_to_model(field)

    def edited(self) -> bool:
        return self._saved_hash != hash(self)

    def pinned(self) -> bool:
        return self.path.parent in USER_POOL.dirs

    def save_as(self, path: Path):
        with path.open('w') as f:
            f.write(self._key_file.to_data()[0])
        
        self._saved_hash = hash(self)

    def save(self):
        self.save_as(self.path)

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
        self.emit('field-set', field, value)
        self._add_to_model(field)

    def set_str(self, field: Field, value: str) -> None:
        self._key_file.set_string(field.group, field.key, value)
        self.emit('field-set', field, value)
        self._add_to_model(field)

    def remove(self, field: Field) -> None:
        self._key_file.remove_key(field.group, field.key)
        self.emit('field-removed', field)
        self._remove_from_model(field)

    def localize_current(self, field: Field) -> Field:
        return field.localize(self._key_file.get_locale_for_key(field.group, field.key))

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
        if not found:
            self.fields.append(field)

    def _remove_from_model(self, field: Field) -> None:
        found, index = self._find_in_model(field)
        if found:
            self.fields.remove(index)

    def __hash__(self) -> int:
        return hash(self._key_file.to_data()[0])

GObject.signal_new('field-set', DesktopFile, GObject.SignalFlags.RUN_FIRST, None, (GObject.TYPE_PYOBJECT, GObject.TYPE_PYOBJECT,))
GObject.signal_new('field-removed', DesktopFile, GObject.SignalFlags.RUN_FIRST, None, (GObject.TYPE_PYOBJECT,))
