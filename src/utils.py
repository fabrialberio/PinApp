from gi.repository import Gtk, Gdk
from pathlib import Path

from xml.sax.saxutils import escape

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


def escape_xml(string: str) -> str:
    return escape(string or '')

def set_icon_from_name(icon: Gtk.Image, icon_name: str) -> Gtk.Image:
    theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())

    icon.set_from_icon_name('application-x-executable')
    if icon_name != None:
        if Path(icon_name).is_file():
            icon.set_from_file(icon_name)
        elif theme.has_icon(icon_name) or theme.has_icon(f'{icon_name}-symbolic'): # Have to specify symbolic icons because they still show up
            icon.set_from_icon_name(icon_name)

    return icon