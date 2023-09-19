from dataclasses import dataclass
from pathlib import Path
from typing import Type, TypeVar, Generic, Any

from configparser import ConfigParser, SectionProxy


T = TypeVar('T', str, int, float, bool, list[str])
Unknown = object()

@dataclass
class Field(Generic[T]):
    key: str
    _parent_section: SectionProxy
    _type: Type[T]

    @classmethod
    def parse_type(cls, key: str, value: str, _parent_section: SectionProxy) -> 'Field[Any]':
        if value in ['true', 'false']:
            return Field[bool](key, _parent_section, bool)
        elif value.isdigit():
            return Field[int](key, _parent_section, int)
        elif value.replace('.', '', 1).isdigit():
            return Field[float](key, _parent_section, float)
        elif value.endswith(';'):
            return Field[list[str]](key, _parent_section, list[str])
        else:
            return Field[str](key, _parent_section, str)


    def get(self, default: T|Unknown = Unknown) -> T:
        value: str | None = self._parent_section.get(self.key, fallback = None)

        if value is None:
            if default is Unknown:
                raise KeyError(f'Key "{self.key}" does not exist in section "{self._parent_section.name}"')
            else:
                return default

        if (self._type == bool):
            return value.lower() == 'true'
        elif (self._type == int):
            return int(value)
        elif (self._type == float):
            return float(value)
        elif (self._type == list[str]):
            return value.split(';')[:-1]
        else:
            return value

    def set(self, value: T):
        if (self._type == bool):
            self._parent_section[self.key] = str(value).lower()
        elif (self._type == int):
            self._parent_section[self.key] = str(value)
        elif (self._type == float):
            self._parent_section[self.key] = str(value)
        elif (self._type == list[str]):
            self._parent_section[self.key] = ';'.join(value) + ';'
        else:
            self._parent_section[self.key] = str(value)

    def __str__(self) -> str: return str(self.get(default = ''))
    def __dict__(self) -> dict[str, T]: return {self.key: self.get()}
    def __repr__(self) -> str: return f'<Field "{self.key}" type={self._type.__name__}>'

@dataclass
class LocalizedField(Field[T]):
    @staticmethod
    def split_localized_key(key: str) -> tuple[str, str]|None:
        if '[' in key and key.endswith(']'):
            return (key.split('[')[0], key.split('[')[1].removesuffix(']'))
        else:
            return None

    def __post_init__(self):
        if LocalizedField.split_localized_key(self.key):
            raise ValueError(f'LocalizedField key "{self.key}" cannot contain "[]", use Field instead.')

    @property
    def localized_keys(self) -> list[str]:
        return [k for k in self._parent_section.keys() if k.startswith(self.key+'[')]

    @property
    def locales(self) -> list[str]:
        return [k.removeprefix(self.key+'[').removesuffix(']') for k in self.localized_keys]

    def as_locale(self, locale: str) -> Field[T]:
        return Field[T](f'{self.key}[{locale}]', self._parent_section, self._type)

    def get_localized(self, locale: str, default: T|Unknown = Unknown) -> T:
        return self.as_locale(locale).get(default = default)
    
    def set_localized(self, locale: str, value: T):
        self.as_locale(locale).set(value)

    def __dict__(self) -> dict[str, T]:
        return {k: Field[T](k, self._parent_section, self._type).get() for k in self.localized_keys}
    def __repr__(self) -> str: return f'<LocalizedField "{self.key}" type={self._type.__name__}>'

@dataclass
class Section:
    _section: SectionProxy

    def __post_init__(self):
        self.title = self._section.name

    def field(self, key: str, _type: Type[T]) -> Field[T]:
        return Field(key, self._section, _type)

    def localized_field(self, key: str, _type: Type[T]) -> LocalizedField[T]:
        return LocalizedField(key, self._section, _type)

    def __dict__(self) -> dict[str, str]:
        return {k: self._section.get(k) for k in self._section.keys()}

    def __hash__(self) -> int:
        return hash(tuple(self.__dict__().items()))

@dataclass(eq = False)
class IniFile:
    path: Path

    def __post_init__(self):
        self._parser = ConfigParser(interpolation=None, strict=False)
        self._parser.optionxform = str


    def load(self):
        if not self.path.exists():
            raise FileExistsError(f'File "{self.path}" does not exist.')

        self._parser.clear()
        self._parser.read(self.path)

    def save_as(self, path: Path):
        with open(path, 'w+') as f:
            self._parser.write(f)

    def save(self):
        self.save_as(self.path)

    def __dict__(self) -> dict[str, Section]:
        return {t: Section(self._parser[t]) for t in self._parser.sections()}


class DesktopEntry(Section):
    NoDisplay: Field[bool]
    Hidden: Field[bool]
    DBusActivatable: Field[bool]
    Terminal: Field[bool]
    StartupNotify: Field[bool]
    PrefersNonDefaultGPU: Field[bool]
    SingleMainWindow: Field[bool]
    Type: Field[str]
    Exec: Field[str]
    Icon: Field[str]
    Version: Field[str]
    TryExec: Field[str]
    Path: Field[str]
    StartupWMClass: Field[str]
    URL: Field[str]
    OnlyShowIn: Field[list[str]]
    NotShowIn: Field[list[str]]
    Actions: Field[list[str]]
    MimeType: Field[list[str]]
    Categories: Field[list[str]]
    Implements: Field[list[str]]
    Name: LocalizedField[str]
    GenericName: LocalizedField[str]
    Comment: LocalizedField[str]
    Keywords: LocalizedField[list[str]]
    X_Flatpak: Field[bool]
    X_SnapInstanceName: Field[str]
    X_GNOME_Autostart: Field[bool]

    def __init__(self, _section: SectionProxy) -> None:
        for name, t in self.__annotations__.items():
            setattr(self, name, t(name.replace('_', '-'), _section, t.__args__[0]))

        super().__init__(_section)

class DesktopAction(Section):
    Name: LocalizedField[str]
    Icon: Field[str]
    Exec: Field[str]

    def __init__(self, _section: SectionProxy) -> None:
        for name, t in self.__annotations__.items():
            setattr(self, name, t(name.replace('_', '-'), _section, t.__args__[0]))

        super().__init__(_section)

@dataclass(eq = False)
class DesktopFile(IniFile):
    @classmethod
    def new_with_defaults(cls, path: Path) -> 'DesktopFile':
        file = cls(path)

        file.desktop_entry.Type.set('Application')
        file.desktop_entry.Name.set('')
        file.desktop_entry.Exec.set('notify-send "Hello World"')
        file.desktop_entry.Icon.set('')

        return file

    def __post_init__(self) -> None:
        super().__post_init__()

        self._saved_hash = None
        self.search_str = ''

        self.load()

    def edited(self) -> bool:
        return self._saved_hash != hash(self)

    def load(self):
        super().load()

        self._saved_hash = hash(self)
        self.search_str = self.__search_str__()

    def save_as(self, path=None):
        super().save_as(path)

        self._saved_hash = hash(self)

    @property
    def desktop_entry(self) -> DesktopEntry:
        return DesktopEntry(self._parser['Desktop Entry'])

    @property
    def desktop_actions(self) -> list[DesktopAction]:
        return [DesktopAction(self._parser[t]) for t in self._parser.sections() if t.startswith('Desktop Action')]

    def __search_str__(self) -> str:
        file_name = self.path.stem
        de_values = '\n'.join(v for v in self.desktop_entry.__dict__().values())
        de_true_keys = '\n'.join(k for k, v in self.desktop_entry.__dict__().items() if v == 'true')
        da_values = '\n'.join(v for a in self.desktop_actions for v in a.__dict__().values())

        return '\n'.join([file_name, de_values, de_true_keys, da_values]).lower()

    def __hash__(self) -> int:
        return hash(tuple(self.__dict__().items()))