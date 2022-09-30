from pathlib import Path
from threading import Thread

from .desktop_entry import DesktopEntry


class DesktopEntryFolder():
    '''Folder containing a list of DesktopFiles and managing related settings'''

    USER = f'{Path.home()}/.local/share/applications'
    FLATPAK_USER = f'{Path.home()}/.local/share/flatpak/exports/share'
    SYSTEM = '/usr/share/applications'
    FLATPAK_SYSTEM = '/var/lib/flatpak/exports/share/applications'
    
    recognized_folders = [USER, SYSTEM, FLATPAK_SYSTEM]

    @staticmethod
    def list_from_recognized() -> list['DesktopEntryFolder']:
        return [
            DesktopEntryFolder(p) \
            for p in DesktopEntryFolder.recognized_folders \
            if Path(p).is_dir()]

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
    def __init__(self, paths: list[Path | str]) -> None:
        self.files = None
        self.folders = [DesktopEntryFolder(p) for p in paths]
        self.writable = None

    def get_files(self, sort=True):
        self.files = []
        for d in self.folders:
            d.get_files(sort=False)
            self.files += d.files
        
        if sort: self.files = sorted(self.files)

    def get_files_async(self, sort=True, callback: callable = None):
        def target():
            self.get_files(sort)
            callback()

        t = Thread(target=target)
        t.start()
    
    @property
    def empty(self):
        return self.files == []

    @property
    def exists(self):
        return all([d.exists for d in self.folders])


class UserFolders(FolderGroup):
    def __init__(self) -> None:
        super().__init__([
            DesktopEntryFolder.USER])

        self.writable = True

class SystemFolders(FolderGroup):
    def __init__(self) -> None:
        super().__init__([
            DesktopEntryFolder.SYSTEM,
            DesktopEntryFolder.FLATPAK_USER, # TODO: Make this work
            DesktopEntryFolder.FLATPAK_SYSTEM])

        self.writable = False