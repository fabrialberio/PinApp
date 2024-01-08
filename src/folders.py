from pathlib import Path
from typing import Callable

from threading import Thread

from .config import *
from .desktop_entry import DesktopEntry, ConfigParserError


class DesktopEntryFolder():
    '''Folder containing a list of DesktopFiles and managing related settings'''
    def __init__(self, path: Path):
        self.path = Path(path)
        self.files = []

    def get_files(self, ignore_parsing_errors=False):
        '''Returns a list of DesktopFile objects representing the .desktop files'''
        pattern = '*.desktop'
        files = self.path.rglob(pattern)

        self.files = []
        for f in files:
            try:
                self.files.append(DesktopEntry(f))
            except ConfigParserError:
                if not ignore_parsing_errors:
                    raise

    @property
    def exists(self) -> bool:
        return self.path.is_dir()


class FolderGroup():
    '''A group of DesktopEntryFolders sharing common properties'''
    writable: bool
    files: list[DesktopEntry] = []
    folders: list[DesktopEntryFolder]

    def __init__(self, paths: list[Path | str]) -> None:
        self.folders = [DesktopEntryFolder(p) for p in paths]

    def get_files(self, remove_duplicates=True, ignore_parsing_errors=False):
        self.files = []
        for d in self.folders:
            if d.exists:
                d.get_files(ignore_parsing_errors=ignore_parsing_errors)
                self.files += d.files

        if remove_duplicates:
            paths = [f.path for f in self.files]
            paths = list(set(paths))
            self.files = [DesktopEntry(p) for p in paths]

    def get_files_async(self,
            callback: 'Callable | None' = None,
            remove_duplicates=True,
            ignore_parsing_errors=False) -> None:
        def target():
            self.get_files(remove_duplicates=remove_duplicates, ignore_parsing_errors=ignore_parsing_errors)
            if callback is not None:
                callback()

        t = Thread(target=target)
        t.start()
    
    @property
    def empty(self):
        return self.files == []

    @property
    def any_exists(self):
        return any([d.exists for d in self.folders])

    @property
    def all_exist(self):
        return all([d.exists for d in self.folders])


class UserFolders(FolderGroup):
    writable = True

    def __init__(self) -> None:
        super().__init__([USER_APPS])

class SystemFolders(FolderGroup):
    writable = False

    def __init__(self) -> None:
        super().__init__(APP_PATHS)