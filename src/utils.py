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

APP_DIR = Path.home() / '.var/app/io.github.fabrialberio.pinapp'
APP_DATA = APP_DIR / 'data'

(APP_DATA / 'icons').mkdir(parents=True, exist_ok=True) # Create icons dir if it doesn't exist

USER_DATA = Path.home() / '.local/share'
SYSTEM_DATA = Path('/usr/share')
FLATPAK_USER = Path.home() / '.local/share/flatpak'
FLATPAK_SYSTEM = Path('/var/lib/flatpak')

if RUNNING_AS == RunningAs.FLATPAK:
    LOCALE_DIR = Path('/app/share/locale')
    HOST_DATA = Path('/run/host/usr/share')
else:
    LOCALE_DIR = Path(prefix) / 'share' / 'locale'
    HOST_DATA = SYSTEM_DATA

ICON_PATHS = [
    USER_DATA / 'icons',
    SYSTEM_DATA / 'icons',
    FLATPAK_USER / 'exports/share/icons',
    FLATPAK_SYSTEM / 'exports/share/icons',
    HOST_DATA / 'icons',
]

def set_icon_from_name(icon: Gtk.Image, icon_name: str) -> Gtk.Image:
    theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())

    icon.set_from_icon_name('application-x-executable')
    if icon_name != None:
        # Checking for -symbolic because sometimes icons only have a symbolic version
        if theme.has_icon(icon_name) or theme.has_icon(f'{icon_name}-symbolic'):
            icon.set_from_icon_name(icon_name)
        elif Path(icon_name).is_file():
            icon.set_from_file(icon_name)

