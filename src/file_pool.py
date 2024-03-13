from os import access, W_OK
from pathlib import Path

from gi.repository import GObject, GLib, Gio # type: ignore

from .config import *


class FilePool(GObject.Object):
    __gtype_name__ = 'FilePool'

    dirs: list[Path]
    files: Gio.ListStore
    glob_pattern: str

    def __init__(self, dirs: list[Path], glob_pattern: str) -> None:
        super().__init__()

        self.dirs = [p for p in dirs if p.is_dir()]
        self.glob_pattern = glob_pattern
        self.files = Gtk.StringList()

    def load(self) -> None:
        def target():
            loaded = [str(p) for dir in self.dirs for p in dir.rglob(self.glob_pattern)]
            stored = [self.files.get_string(i) for i in range(self.files.get_n_items())]

            for p in set(stored) - set(loaded):
                for i in range(self.files.get_n_items()):
                    if self.files.get_string(i) == p:
                        print(f'Removing {p}, at index {i}')
                        
                        self.files.remove(i)
                        break

            for p in set(loaded) - set(stored):
                self.files.append(p)

            self.emit('loaded')

        GLib.Thread.new('load_files', target)

GObject.signal_new('loaded', FilePool, GObject.SignalFlags.RUN_FIRST, None, ())


class WritableFilePool(FilePool):
    default_dir: Path

    def __init__(self, dirs: list[Path], glob_pattern: str):
        super().__init__(dirs, glob_pattern)
        if not all(access(p, W_OK) for p in self.dirs):
            raise Exception('At least one of paths must be writable.')

        self.default_dir = self.dirs[0]

    def new_file_path(self, name: str, suffix: str = '.desktop', separator = '-') -> Path:
        other_files = list(self.default_dir.glob(f'{name}*{suffix}'))
        other_files = [f.name.removeprefix(name).removeprefix(separator).removesuffix(suffix) for f in other_files]
        other_indexes = [int(i) if i else 0 for i in other_files if i.isdigit() or i == '']

        next_available_index = next((i for i in range(0, len(other_indexes)+1) if i not in other_indexes), None)
        if next_available_index is None:
            raise Exception('No available index found.')

        return self.default_dir / f'{name}{separator + str(next_available_index) if next_available_index > 0 else ""}{suffix}'

    def remove_all(self, name: str) -> None:
        for dir in self.dirs:
            for f in dir.glob(name):
                f.unlink()

    def rename_all(self, old_name: str, new_name: str) -> None:
        for dir in self.dirs:
            for f in dir.glob(old_name):
                f.rename(f.with_name(new_name))

USER_POOL = WritableFilePool(
    dirs = [
        USER_DATA / 'applications',
    ],
    glob_pattern = '*.desktop'
)

SYSTEM_POOL = FilePool(
    dirs = [
        SYSTEM_DATA / 'applications',
        FLATPAK_USER / 'exports/share/applications',
        FLATPAK_SYSTEM / 'exports/share/applications',
        HOST_DATA / 'applications',
        Path('/var/lib/snapd/desktop/applications'),
    ],
    glob_pattern = '*.desktop'
)

SEARCH_POOL = FilePool(
    dirs = USER_POOL.dirs + SYSTEM_POOL.dirs,
    glob_pattern = '*.desktop'
)
