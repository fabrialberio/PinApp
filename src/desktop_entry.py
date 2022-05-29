from pathlib import Path
from configparser import ConfigParser


class DesktopFileFolder():
    '''Folder containing a list of DesktopFiles and managing related settings'''
    
    def __init__(self, path: Path):
        self.path = path if path is Path else Path(path)
        self.path = self.path.expanduser()
        if not self.path.is_dir():
            raise ValueError(f'Path "{self.path} is not a directory"')

        self.files = []

    '''
    @classmethod
    def new(cls, path: Path):
        """Returns a new DesktopFileFolder object"""
        settings = Settings.new()
        paths = list(settings.get_value(Settings.APP_FOLDERS_KEY))

        if path not in paths:
            paths.append(path)

        settings.set(Settings.APP_FOLDERS_KEY, paths)

        return cls(path)

    @classmethod
    def get_folders(cls):
        """Returns a list of DesktopFileFolder objects corresponding to the folders in the settings"""
        settings = Settings.new()
        paths = list(settings.get_value(Settings.APP_FOLDERS_KEY))

        return [cls(p) for p in paths]


    def remove(self):
        settings = Settings.new()
        paths = list(settings.get_value(Settings.APP_FOLDERS_KEY))

        if self.path in paths:
            paths.remove(self.path)

        settings.set(Settings.APP_FOLDERS_KEY, paths)
    '''

    def get_files(self, recursive=False):
        '''Returns a list of DesktopFile objects rapresenting the .desktop files'''
        self.files = [
            DesktopFile(p) for p in (
                self.path.rglob('*.desktop') if recursive else self.path.glob('*.desktop') 
            )
        ]

        return self.files

class DesktopFile(ConfigParser):
    '''Representation of a .desktop file, implementing both dictionary-like and specific methods and properties'''
    APP_GROUPNAME = 'Desktop Entry'

    # Common keys
    CATEGORIES_KEY = 'Categories'
    APP_NAME_KEY = 'Name'
    COMMENT_KEY = 'Comment'
    EXEC_KEY = 'Exec'
    ICON_KEY = 'Icon'
    TYPE_KEY = 'Type'

    # Booleans
    IS_TERMINAL_KEY = 'Terminal'
    NO_DISPLAY_KEY = 'NoDisplay'
    TRUE_VALUE = 'true'
    FALSE_VALUE = 'false'


    def __init__(self, path) -> None:
        self.path = Path(path)
        if not (self.path.is_file() or self.path.suffix == 'desktop'):
            raise ValueError(f'Path {self.path} is not a .desktop file')

        super().__init__()
        self.load()
        if self.APP_GROUPNAME not in self.sections():
            self.add_section(self.APP_GROUPNAME)

    # File properties
    @property
    def filename(self) -> str: return self.path.name
    @property
    def parent(self) -> str: return self.path.parent
    @property
    def basename(self) -> str: return self.path.stem
    @property
    def extension(self) -> str: return self.path.suffix

    # Desktop file specific properties
    @property
    def app_dict(self) -> dict: return self[self.APP_GROUPNAME]

    def get_categories(self) -> list: 
        if self.CATEGORIES_KEY in self.app_dict:
            return [c for c in self.app_dict[self.CATEGORIES_KEY].split(';') if c]
        else:
            return []
    
    def set_categories(self, new_categories: list):
        '''Sets the categories of the desktop file'''
        self.set(self.APP_GROUPNAME, self.CATEGORIES_KEY, ';'.join(new_categories))

    def load(self):
        return self.read(self.path)

    def save(self) -> None:
        '''Saves the file'''
        with open(self.path, 'w') as f:
            self.write(f)