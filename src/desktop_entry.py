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
        self.files = [
            DesktopFile(p) for p in (
                self.path.rglob('*.desktop') if recursive else self.path.glob('*.desktop') 
            )
        ]


class DesktopFile():
    '''Representation of a .desktop file, implementing both dictionary-like and specific methods and properties'''
    DEFAULT_GROUPNAME = 'Desktop Entry'

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

        self._lines = []

    # File properties
    @property
    def filename(self) -> str: return self.path.name
    @property
    def parent(self) -> str: return self.path.parent
    @property
    def basename(self) -> str: return self.path.stem
    @property
    def extension(self) -> str: return self.path.suffix

    # Dictionary properties
    @property
    def items(self) -> list:
        self.load()
        return [tuple(l.split('=', maxsplit=1) ) for l in self._lines if '=' in l]
    @property
    def keys(self) -> list: return [i[0] for i in self.items]
    @property
    def values(self) -> list: return [i[1] for i in self.items]

    # Desktop file specific properties
    @property
    def categories(self) -> list: return [c for c in self.get(self.CATEGORIES_KEY).split(';') if c]
    @categories.setter
    def categories(self, new_categories):
        if type(new_categories) == list:
            self.update(self.CATEGORIES_KEY, ';'.join(new_categories) )
        elif new_categories:
            self.update(self.CATEGORIES_KEY, str(new_categories) )
        else:
            self.update(self.CATEGORIES_KEY, '')

    # Dictionary-like methods
    def get(self, key: str) -> str:
        '''Returns the value of a key'''
        self.load()
        for k, v in self.items:
            if k == key: 
                return v.removesuffix('\n')
        
        return None

    def update(self, key: str, new_value: str, groupname = DEFAULT_GROUPNAME):
        '''Updates the value of a key'''
        self.load()
        for i, l in enumerate(self._lines):
            if l.startswith(f'{key}='):
                self._lines[i] = f'{key}={new_value}\n'
                return self.save()

        # Otherwise, if the key does not exist
        for i, l in enumerate(self._lines):
            if l.startswith(f'[{groupname}]'):
                self._lines.insert(i+1, f'{key}={new_value}\n')
                return self.save()

    def is_bool(self, key: str) -> bool:
        '''If the key is boolean (true/false), returns True, otherwise returns False'''
        return self.get(key) in [self.TRUE_VALUE, self.FALSE_VALUE]

    def get_bool(self, key: str) -> bool:
        '''If the key is boolean (true/false), gets its value as a bool'''
        value = self.get(key)
        if self.is_bool(key):
            return value == 'true'
        else:
            raise ValueError(f'"{key}" must refer to a boolean')

    def update_bool(self, key: str, value: bool):
        '''If the key is boolean (true/false), updates the value'''
        if self.is_bool(key):
            self.update(key, self.TRUE_VALUE if value else self.FALSE_VALUE)
        else:
            raise ValueError(f'"{key}" must refer to a boolean')

    # File loading/saving
    def load(self, force=False) -> None:
        '''Loads the file if it has not been loaded yet or if force is True'''
        if (not self._lines) or force:
            with open(self.path, 'r') as f:
                self._lines = f.readlines()

    def save(self) -> None:
        '''Saves the file'''
        self.load()
        with open(self.path, 'w') as f:
            f.writelines([l.removesuffix('\n')+'\n' for l in self._lines])


if __name__ == '__main__':
    from desktop_entry import DesktopFile
    d = DesktopFile('/home/fabri/Documenti/Progetti/Gnome/PinApp/pinapp.desktop')
    
    d.categories = None

    print(d.get('Categories'))