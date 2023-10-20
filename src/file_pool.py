from os import access, W_OK
from pathlib import Path
from dataclasses import dataclass, field

from gi.repository import GObject, GLib

from .config import *


@dataclass(init=False)
class FilePool(GObject.Object):
    __gtype_name__ = 'DesktopFilePool'

    paths: list[Path]
    _pattern: str
    _dirs: list[Path] = field(init=False)

    def __init__(self, paths: list[Path], _pattern = '*.desktop') -> None:
        self.paths = paths
        self._pattern = _pattern

        super().__init__()

        self._dirs = [p for p in self.paths if p.is_dir()]

    def files(self) -> list[Path]:
        files = []

        for d in self._dirs:
            files += [p for p in d.rglob(self._pattern) if p.is_file()]

        files = list(set(files)) # Remove duplicate paths
        return files

    def files_async(self) -> None:
        '''Emit files-loaded, files-empty or files-error signals asynchronously'''

        self.emit('files-loading')

        def target():
            try:
                files = self.files()

                if files:
                    self.emit('files-loaded', files)
                else:
                    self.emit('files-empty')
            except Exception as e:
                self.emit('files-error', e)
                raise

        GLib.Thread.new('load_files', target)

    def __iter__(self):
        return iter(self.files())

class WritableFilePool(FilePool):
    def __post_init__(self):
        super().__post_init__()
        self._dirs = [p for p in self._dirs if access(p, W_OK)]

        if not self._dirs:
            raise Exception('At least one of paths must be writable')

        self.default_dir = self._dirs[0]

    def new_file_path(self, name: str, suffix = '.desktop', separator = '-') -> Path:
        other_files = list(self.default_dir.glob(f'{name}*{suffix}'))
        other_files = [f.name.removeprefix(name).removeprefix(separator).removesuffix(suffix) for f in other_files]
        other_indexes = [int(i) if i else 0 for i in other_files if i.isdigit() or i == '']

        next_available_index = next((i for i in range(0, len(other_indexes)+1) if i not in other_indexes), None)
        if next_available_index is None:
            raise Exception('No available index found')

        return self.default_dir / f'{name}{separator + str(next_available_index) if next_available_index > 0 else ""}{suffix}'

    def remove_all(self, name: str) -> None:
        for dir in self._dirs:
            for f in dir.glob(name):
                f.unlink()

    def rename_all(self, old_name: str, new_name: str) -> None:
        for dir in self._dirs:
            for f in dir.glob(old_name):
                f.rename(f.with_name(new_name))

USER_POOL = WritableFilePool(
    paths = [
        USER_DATA / 'applications',
    ]
)

SYSTEM_POOL = FilePool(
    paths = [
        SYSTEM_DATA / 'applications',
        FLATPAK_USER / 'exports/share/applications',
        FLATPAK_SYSTEM / 'exports/share/applications',
        HOST_DATA / 'applications',
        Path('/var/lib/snapd/desktop/applications'),
    ]
)

SEARCH_POOL = FilePool(
    USER_POOL.paths + SYSTEM_POOL.paths
)

AUTOSTART_POOL = WritableFilePool(
    paths = [
        Path.home() / '.config/autostart',
    ]
)