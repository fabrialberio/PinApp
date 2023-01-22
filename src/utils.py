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