from os import access, W_OK
from pathlib import Path
from dataclasses import dataclass, field

from gi.repository import GObject, GLib # type: ignore

from .config import *


@dataclass
class FilePool(GObject.Object):
    __gtype_name__ = 'FilePool'

    paths: list[Path]
    glob_pattern: str
    
    def __post_init__(self) -> None:
        super().__init__()

        self.paths = [p for p in self.paths if p.is_dir()]

    def files(self) -> list[Path]:
        files = []

        for d in self.paths:
            files += [p for p in d.rglob(self.glob_pattern) if p.is_file()]

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
    
    @property
    def __doc__(self): return None

    @__doc__.setter # Added to avoid clash when dataclass tries to set __doc__ of GObject.Object
    def __doc__(self, _): ...


class WritableFilePool(FilePool):
    default_dir: Path = field(init=False)

    def __post_init__(self):
        super().__post_init__()
        if not all(access(p, W_OK) for p in self.paths):
            raise Exception('At least one of paths must be writable')

        self.default_dir = self.paths[0]

    def new_file_path(self, name: str, suffix: str = '.desktop', separator = '-') -> Path:
        other_files = list(self.default_dir.glob(f'{name}*{suffix}'))
        other_files = [f.name.removeprefix(name).removeprefix(separator).removesuffix(suffix) for f in other_files]
        other_indexes = [int(i) if i else 0 for i in other_files if i.isdigit() or i == '']

        next_available_index = next((i for i in range(0, len(other_indexes)+1) if i not in other_indexes), None)
        if next_available_index is None:
            raise Exception('No available index found')

        return self.default_dir / f'{name}{separator + str(next_available_index) if next_available_index > 0 else ""}{suffix}'

    def remove_all(self, name: str) -> None:
        for dir in self.paths:
            for f in dir.glob(name):
                f.unlink()

    def rename_all(self, old_name: str, new_name: str) -> None:
        for dir in self.paths:
            for f in dir.glob(old_name):
                f.rename(f.with_name(new_name))

GObject.signal_new('files-loading', FilePool, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ())
GObject.signal_new('files-empty', FilePool, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ())
GObject.signal_new('files-error', FilePool, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (GObject.TYPE_PYOBJECT,))
GObject.signal_new('files-loaded', FilePool, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (GObject.TYPE_PYOBJECT,))


USER_POOL = WritableFilePool(
    paths = [
        USER_DATA / 'applications',
    ],
    glob_pattern = '*.desktop'
)

SYSTEM_POOL = FilePool(
    paths = [
        SYSTEM_DATA / 'applications',
        FLATPAK_USER / 'exports/share/applications',
        FLATPAK_SYSTEM / 'exports/share/applications',
        HOST_DATA / 'applications',
        Path('/var/lib/snapd/desktop/applications'),
    ],
    glob_pattern = '*.desktop'
)

SEARCH_POOL = FilePool(
    paths = USER_POOL.paths + SYSTEM_POOL.paths,
    glob_pattern = '*.desktop'
)
