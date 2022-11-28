from pathlib import Path
from threading import Thread

from .desktop_entry import DesktopEntry

from .utils import *

class DesktopEntryFolder():
    '''Folder containing a list of DesktopFiles and managing related settings'''
    def __init__(self, path: Path):
        self.path = Path(path)
        self.files = []

    def get_files(self, sort=True):
        '''Returns a list of DesktopFile objects representing the .desktop files'''
        pattern = '*.desktop'
        
        self.files = [DesktopEntry(p) for p in (self.path.rglob(pattern))]
        if sort: self.files = sorted(self.files)

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

    def get_files(self, remove_duplicates=True, sort=True) -> list[DesktopEntry]:
        self.files = []
        for d in self.folders:
            if d.exists:
                d.get_files(sort=False)
                self.files += d.files

        if remove_duplicates:
            paths = [f.path for f in self.files]
            paths = list(set(paths))
            self.files = [DesktopEntry(p) for p in paths]

        if sort: self.files = sorted(self.files)

    def get_files_async(self, sort=True, callback: callable = None) -> None:
        def target():
            self.get_files(sort)
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
        super().__init__([
            USER_APPS])

class SystemFolders(FolderGroup):
    writable = False

    def __init__(self) -> None:
        super().__init__([
            HOST_APPS,
            SYSTEM_APPS,
            FLATPAK_USER_APPS,
            FLATPAK_SYSTEM_APPS])