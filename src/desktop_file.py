from dataclasses import dataclass
from gettext import gettext as _
from pathlib import Path
from typing import override, Self

from .key_file import Localized, KeyFile, Field, HintedGroup
from .file_pool import AUTOSTART_POOL, USER_POOL, AUTOSTART_DISABLED_SUFFIX


class _DesktopEntry(HintedGroup):
    GROUP_NAME = 'Desktop Entry'

    NODISPLAY = Field[bool](GROUP_NAME, 'NoDisplay', bool)
    HIDDEN = Field[bool](GROUP_NAME, 'Hidden', bool)
    DBUSACTIVATABLE = Field[bool](GROUP_NAME, 'DBusActivatable', bool)
    TERMINAL = Field[bool](GROUP_NAME, 'Terminal', bool)
    STARTUPNOTIFY = Field[bool](GROUP_NAME, 'StartupNotify', bool)
    PREFERSNONDEFAULTGPU = Field[bool](GROUP_NAME, 'PrefersNonDefaultGPU', bool)
    SINGLEMAINWINDOW = Field[bool](GROUP_NAME, 'SingleMainWindow', bool)
    TYPE = Field[str](GROUP_NAME, 'Type', str)
    EXEC = Field[str](GROUP_NAME, 'Exec', str)
    ICON = Field[str](GROUP_NAME, 'Icon', str)
    VERSION = Field[str](GROUP_NAME, 'Version', str)
    TRYEXEC = Field[str](GROUP_NAME, 'TryExec', str)
    PATH = Field[str](GROUP_NAME, 'Path', str)
    STARTUPWMCLASS = Field[str](GROUP_NAME, 'StartupWMClass', str)
    URL = Field[str](GROUP_NAME, 'URL', str)
    ONLYSHOWIN = Field[list[str]](GROUP_NAME, 'OnlyShowIn', list[str])
    NOTSHOWIN = Field[list[str]](GROUP_NAME, 'NotShowIn', list[str])
    ACTIONS = Field[list[str]](GROUP_NAME, 'Actions', list[str])
    MIMETYPE = Field[list[str]](GROUP_NAME, 'MimeType', list[str])
    CATEGORIES = Field[list[str]](GROUP_NAME, 'Categories', list[str])
    IMPLEMENTS = Field[list[str]](GROUP_NAME, 'Implements', list[str])
    NAME = Field[Localized[str]](GROUP_NAME, 'Name', Localized[str])
    GENERICNAME = Field[Localized[str]](GROUP_NAME, 'GenericName', Localized[str])
    COMMENT = Field[Localized[str]](GROUP_NAME, 'Comment', Localized[str])
    KEYWORDS = Field[Localized[list[str]]](GROUP_NAME, 'Keywords', Localized[list[str]])
    X_FLATPAK = Field[str](GROUP_NAME, 'X-Flatpak', str)
    X_SNAPINSTANCENAME = Field[str](GROUP_NAME, 'X-SnapInstanceName', str)
    X_GNOME_AUTOSTART = Field[bool](GROUP_NAME, 'X-GNOME-Autostart', bool)

    @classmethod
    def fields(cls) -> list[Field]:
        return [f for f in cls.__dict__.values() if isinstance(f, Field)]

DesktopEntry = _DesktopEntry(_DesktopEntry.GROUP_NAME)

class DesktopAction(HintedGroup):
    GROUP_PREFIX = 'Desktop Action '
    GROUP_NAME: str
    
    NAME: Field[Localized[str]]
    ICON: Field[str]
    EXEC: Field[str]

    def __init__(self, action_name: str) -> None:
        super().__init__(self.GROUP_PREFIX + action_name)

        self.NAME = Field[Localized[str]](self.GROUP_NAME, 'Name', Localized[str])
        self.ICON = Field[str](self.GROUP_NAME, 'Icon', str)
        self.EXEC = Field[str](self.GROUP_NAME, 'Exec', str)

    def fields(self) -> list[Field]:
        return [f for f in self.__dict__.values() if isinstance(f, Field)]

@dataclass(eq = False, init = False)
class DesktopFile(KeyFile):
    """
    Represents a desktop file.

    Based on the freedesktop.org desktop entry
    [specification](https://specifications.freedesktop.org/desktop-entry-spec/desktop-entry-spec-0.9.5.html).
    """
    SUFFIX = '.desktop'

    search_str: str
    _saved_hash: int
    _autostart_path: Path
    desktop_action_names: list[str]

    @classmethod
    def new_with_defaults(cls) -> Self:
        f = cls(USER_POOL.new_file_path(_('pinned-app'), DesktopFile.SUFFIX))

        f.set(DesktopEntry.TYPE, 'Application')
        f.set(DesktopEntry.NAME, Localized[str](_('New Application')))
        f.set(DesktopEntry.EXEC, '')
        f.set(DesktopEntry.ICON, '')

        return f

    def __post_init__(self):
        super().__post_init__()

        self.load()

    def edited(self) -> bool:
        return self._saved_hash != hash(self)

    def autostart(self) -> bool:
        '''Wether the file (or a copy with the same name) is configured for autostart.'''
        return self._autostart_path.exists()
        
    def set_autostart(self, value: bool) -> None:
        '''
        Configure the file for autostart.
        
        Creates a copy of the file in the autostart pool.
        '''
        if self.autostart() == value:
            return

        if value:
            autostart_disabled_path = self._autostart_path.with_suffix(f'{DesktopFile.SUFFIX}{AUTOSTART_DISABLED_SUFFIX}')

            if autostart_disabled_path.exists():
                AUTOSTART_POOL.rename_all(autostart_disabled_path.name, self.path.name)
            else:
                self.save_as(self._autostart_path)

            self.set(DesktopEntry.X_GNOME_AUTOSTART, True)
        else:
            AUTOSTART_POOL.rename_all(self.path.name, f'{self.path.name}{AUTOSTART_DISABLED_SUFFIX}')
            self.set(DesktopEntry.X_GNOME_AUTOSTART, False)

    def user_pool(self) -> bool:
        '''Wether the file is in the user pool.'''
        return self.path.parent in USER_POOL.paths
    
    def as_user_pool(self) -> Self:
        '''Returns the file in the user pool.'''
        if self.user_pool():
            return self

        user_path = USER_POOL.new_file_path(self.path.name, DesktopFile.SUFFIX)
        self.save_as(user_path)
        return DesktopFile(user_path)

    @override
    def load(self):
        super().load()

        self.desktop_action_names = [
            n for n in self._key_file.get_groups()[0] if n.startswith(DesktopAction.GROUP_PREFIX)
        ]

        self._saved_hash = hash(self)
        self._autostart_path = AUTOSTART_POOL.default_dir / self.path.name
        self.search_str = self._search_str()

    @override
    def save_as(self, path=None):
        super().save_as(path)

        if self.autostart():
            super().save_as(self._autostart_path)

        self._saved_hash = hash(self)

    def _search_str(self) -> str:
        tree = self.tree(str, '')
        desktop_entry = tree[DesktopEntry.GROUP_NAME]
        desktop_actions = [tree[n] for n in self.desktop_action_names]

        de_values = '\n'.join(desktop_entry.values())
        de_true_keys = '\n'.join(k for k, v in desktop_entry.items() if v == 'true')
        da_values = '\n'.join(v for a in desktop_actions for v in a.values())

        return '\n'.join([self.path.stem, de_values, de_true_keys, da_values]).lower()

    def __hash__(self) -> int:
        return hash(tuple((k, tuple(v.items())) for k, v in self.tree().items()))
