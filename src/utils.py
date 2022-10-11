from gi.repository import Gtk, Gio, Adw, GObject
from pathlib import Path

from xml.sax.saxutils import escape


def escape_xml(string: str) -> str:
    return escape(string or '')

def update_icon(icon: Gtk.Image, icon_name: str) -> Gtk.Image:
    if icon_name == None:
        icon.set_from_icon_name('application-x-executable')
    elif Path(icon_name).exists():
        icon.set_from_file(icon_name)
    else:
        icon.set_from_icon_name(icon_name)

    return icon