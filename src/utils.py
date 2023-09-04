from enum import Enum
from sys import prefix
from pathlib import Path

from gi.repository import Gtk, Gdk


class RunningAs(Enum):
    DEFAULT = 'default'
    FLATPAK = 'flatpak'

if Path('/.flatpak-info').exists():
    RUNNING_AS = RunningAs.FLATPAK
else:
    RUNNING_AS = RunningAs.DEFAULT


USER_DATA = Path.home() / '.local/share'
USER_APPS = USER_DATA / 'applications'
USER_ICONS = USER_DATA / 'icons'

SYSTEM_DATA = Path('/usr/share')
SYSTEM_APPS = SYSTEM_DATA / 'applications'
SYSTEM_ICONS = SYSTEM_DATA / 'icons'

FLATPAK_USER = Path.home() / '.local/share/flatpak'
FLATPAK_USER_APPS = FLATPAK_USER / 'exports/share/applications'
FLATPAK_USER_ICONS = FLATPAK_USER / 'exports/share/icons'

FLATPAK_SYSTEM = Path('/var/lib/flatpak')
FLATPAK_SYSTEM_APPS = FLATPAK_SYSTEM / 'exports/share/applications'
FLATPAK_SYSTEM_ICONS = FLATPAK_SYSTEM / 'exports/share/icons'


if RUNNING_AS == RunningAs.FLATPAK:
    LOCALE_DIR = Path('/app/share/locale')

    HOST_DATA = Path('/run/host/usr/share')
    HOST_APPS = HOST_DATA / 'applications'
    HOST_ICONS = HOST_DATA / 'icons'
else:
    LOCALE_DIR = Path(prefix) / 'share' / 'locale'

    HOST_DATA = SYSTEM_DATA
    HOST_APPS = SYSTEM_APPS
    HOST_ICONS = SYSTEM_ICONS


def set_icon_from_name(icon: Gtk.Image, icon_name: str) -> Gtk.Image:
    theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())

    icon.set_from_icon_name('application-x-executable')
    if icon_name != None:
        # Checking for -symbolic because sometimes icons only have a symbolic version
        if theme.has_icon(icon_name) or theme.has_icon(f'{icon_name}-symbolic'):
            icon.set_from_icon_name(icon_name)
        elif Path(icon_name).is_file():
            icon.set_from_file(icon_name)


def new_file_name(parent: Path, suggestion: str = 'pinned-app', index_separator: str = '-', extension: str = '.desktop') -> Path:
    split_suggestion = suggestion.split(index_separator)
    if len(split_suggestion) > 1 and split_suggestion[-1].isdigit():
        suggestion = index_separator.join(split_suggestion[:-1]) # Remove trailing index from suggestion

    other_files = list(parent.glob(f'{suggestion}*{extension}'))
    other_files = [f.name.removeprefix(suggestion).removeprefix(index_separator).removesuffix(extension) for f in other_files]
    other_indexes = [int(i) if i else 0 for i in other_files if i.isdigit() or i == '']

    first_available_index = next((i for i in range(0, len(other_indexes)+1) if i not in other_indexes), None)
    if first_available_index == None:
        raise Exception('No available index found')

    def get_path_with_index(i: int):
        if i == 0:
            return parent / f'{suggestion}{extension}'
        else:
            return parent / f'{suggestion}{index_separator}{i}{extension}'

    return get_path_with_index(first_available_index)