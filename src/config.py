from pathlib import Path

from gi.repository import Gtk, Gdk, GLib # type: ignore


LOCALE_DIR = Path('/app/share/locale')

APP_DATA = GLib.get_user_data_dir()
GLib.mkdir_with_parents(APP_DATA + '/icons', 777)

LOCAL_DATA = Path(GLib.get_home_dir()) / '.local/share'
HOST_DATA = Path('/run/host/usr/share')
SYSTEM_DATA = Path('/usr/share')
FLATPAK_USER = LOCAL_DATA / 'flatpak'
FLATPAK_SYSTEM = Path('/var/lib/flatpak')

USER_APPS = LOCAL_DATA / 'applications'

ICON_PATHS = [
    LOCAL_DATA / 'icons',
    HOST_DATA / 'icons',
    SYSTEM_DATA / 'icons',
    FLATPAK_USER / 'exports/share/icons',
    FLATPAK_SYSTEM / 'exports/share/icons',
]

APP_PATHS = [Path(p) for p in GLib.get_system_data_dirs()] + [
    HOST_DATA / 'applications',
    FLATPAK_USER / 'exports/share/applications',
    FLATPAK_SYSTEM / 'exports/share/applications',
    Path('/var/lib/snapd/desktop/applications'),
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
