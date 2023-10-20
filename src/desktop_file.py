from dataclasses import dataclass, field
from pathlib import Path
from typing import Type, Callable, overload
from gi.repository import GLib

from .key_file import Localized, _KeyFile, MagicGroup


DESKTOP_ENTRY_GROUP_NAME = 'Desktop Entry'
DESKTOP_ACTION_GROUP_PREFIX = 'Desktop Action '

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
    """
    Represents a desktop file.

    Based on the freedesktop.org desktop entry
    [specification](https://specifications.freedesktop.org/desktop-entry-spec/desktop-entry-spec-0.9.5.html).
    """

    search_str: str
    _saved_hash: int
    desktop_entry: DesktopEntry
    desktop_actions: list[DesktopAction]

    @classmethod
    def new_with_defaults(cls, path: Path) -> 'DesktopFile':
        f = cls(path)

        f.desktop_entry.Type = 'Application'
        f.desktop_entry.Name = Localized[str]('New Application')
        f.desktop_entry.Exec = ''
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