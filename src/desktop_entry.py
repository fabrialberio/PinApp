from pathlib import Path
from configparser import ConfigParser, NoOptionError


class DesktopFileFolder():
    '''Folder containing a list of DesktopFiles and managing related settings'''
    
    def __init__(self, path: Path):
        self.path = Path(path)
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
    APP_SECTION = 'Desktop Entry'

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
        if not (self.path.is_file() or self.path.suffix == '.desktop'):
            raise ValueError(f'Path {self.path} is not a .desktop file')

        super().__init__(interpolation=None,)
        self.load()
        if self.APP_SECTION not in self.sections():
            self.add_section(self.APP_SECTION)

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
    def app_dict(self) -> dict: return self[self.APP_SECTION]
    @property
    def bool_items(self) -> dict: return dict(filter(lambda i: self.is_bool(i[0]), self.app_dict.items()))
    @property
    def float_items(self) -> dict: return dict(filter(lambda i: self.is_int(i[0]), self.app_dict.items()))
    @property
    def string_items(self) -> dict:
        '''All the values except numbers (float or int), booleans and categories'''
        return dict(filter(
            lambda i: not (
                self.is_int(i[0]) or 
                self.is_bool(i[0]) or 
                self.is_float(i[0]) or 
                self.is_categories(i[0])),
            self.app_dict.items()))
    
    def is_bool(self, key: str):
        try:
            self.getboolean(self.APP_SECTION, key)
        except (ValueError, NoOptionError):
            return False
        else:
            return True
    def is_int(self, key: str):
        try:
            self.getint(self.APP_SECTION, key)
        except (ValueError, NoOptionError):
            return False
        else:
            return True
    def is_float(self, key: str):
        try:
            self.getfloat(self.APP_SECTION, key)
        except (ValueError, NoOptionError):
            return False
        else:
            return True
    def is_categories(self, key: str):
        return key.title() == self.CATEGORIES_KEY

    @property
    def app_name(self) -> str: return self.app_dict.get(self.APP_NAME_KEY)
    @property
    def comment(self) -> str: return self.app_dict.get(self.COMMENT_KEY)
    @property
    def icon_name(self) -> str: return self.app_dict.get(self.ICON_KEY)
    @property
    def executable_path(self) -> str: return self.app_dict.get(self.EXEC_KEY)
    @property
    def app_type(self) -> str: return self.app_dict.get(self.TYPE_KEY)
    @property
    def is_terminal(self) -> str: return self.app_dict.get(self.IS_TERMINAL_KEY)
    @property
    def is_no_display(self) -> str: return self.app_dict.get(self.NO_DISPLAY_KEY)

    def get_categories(self) -> list: 
        if self.CATEGORIES_KEY in self.app_dict:
            return [c for c in self.app_dict[self.CATEGORIES_KEY].split(';') if c]
        else:
            return []
    
    def set_categories(self, new_categories: list):
        '''Sets the categories of the desktop file'''
        self.set(self.APP_SECTION, self.CATEGORIES_KEY, ';'.join(new_categories))

    def load(self):
        return self.read(self.path)

    def save(self) -> None:
        '''Saves the file'''
        with open(self.path, 'w') as f:
            self.write(f)