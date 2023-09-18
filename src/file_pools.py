from os import access, W_OK
from typing import Callable
from pathlib import Path
from threading import Thread
from dataclasses import dataclass

from .utils import *
from .desktop_file import DesktopFile


@dataclass
class DesktopFilePool:
    paths: list[Path]
    _pattern = '*.desktop'

    def __post_init__(self):
        self._dirs = [p for p in self.paths if p.is_dir()]

    def files(self) -> list[DesktopFile]:
        files = []

        for d in self._dirs:
            files += [p for p in d.rglob(self._pattern) if p.is_file()]

        files = list(set(files)) # Remove duplicate paths
        return [DesktopFile(p) for p in files]

    def files_async(self, callback: Callable[[list[DesktopFile]], None]) -> None:
        def target():
            files = self.files()
            callback(files)

        t = Thread(target=target)
        t.start()

class WritableDesktopFilePool(DesktopFilePool):
    def __post_init__(self):
        super().__post_init__()
        self._dirs = [p for p in self._dirs if access(p, W_OK)]

        if not self._dirs:
            raise Exception('At least one of paths must be writable')

    def new_file_name(self, name: str, separator = '-', suffix = '.desktop') -> Path:
        parent = self._dirs[0]

        other_files = list(parent.glob(f'{name}*{suffix}'))
        other_files = [f.name.removeprefix(name).removeprefix(separator).removesuffix(suffix) for f in other_files]
        other_indexes = [int(i) if i else 0 for i in other_files if i.isdigit() or i == '']

        next_available_index = next((i for i in range(0, len(other_indexes)+1) if i not in other_indexes), None)
        if next_available_index == None:
            raise Exception('No available index found')

        return parent / f'{name}{separator + str(next_available_index) if next_available_index > 0 else ""}{suffix}'


USER_POOL = WritableDesktopFilePool(
    paths = [
        USER_DATA / 'applications',
    ]
)

SYSTEM_POOL = DesktopFilePool(
    paths = [
        SYSTEM_DATA / 'applications',
        HOST_DATA / 'applications',
        Path('/var/lib/snapd/desktop/applications'),
    ]
)

EMPTY_POOL = WritableDesktopFilePool(
    paths = []
)