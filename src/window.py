# window.py
#
# Copyright 2022 Fabri210
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

#from apps_view import AppsView

from gi.repository import Gtk, Adw, Gio

from .utils import USER_APPS

from .file_page import FilePage
from .apps_page import PinsView, InstalledView

from .folders import DesktopEntryFolder
from .desktop_entry import DesktopEntry
from pathlib import Path

@Gtk.Template(resource_path='/io/github/fabrialberio/pinapp/window.ui')
class PinAppWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'PinAppWindow'

    new_file_button = Gtk.Template.Child('new_file_button')
    
    leaflet = Gtk.Template.Child('main_leaflet')
    view_stack = Gtk.Template.Child('view_stack')
    
    pins_view = Gtk.Template.Child('pins_view')
    installed_view = Gtk.Template.Child('installed_view')
    apps_page = Gtk.Template.Child('apps_page')
    file_page = Gtk.Template.Child('file_page')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.new_file_button.connect('clicked', lambda _: self.new_file())

        self.pins_view.connect('file-open', lambda _, f: self.open_file(f))
        self.pins_view.connect('file-new', lambda _: self.new_file())
        self.installed_view.connect('file-open', lambda _, f: self.open_file(f))

        self.file_page.connect('file-back', lambda _: self.show_apps())
        self.file_page.connect('file-save', lambda _: self.show_and_reload_apps())
        self.file_page.connect('file-delete', lambda _: self.show_and_reload_apps())

        builder = Gtk.Builder.new_from_resource('/io/github/fabrialberio/pinapp/apps_page_dialogs.ui')
        help_overlay = builder.get_object('help_overlay')
        help_overlay.set_transient_for(self)

        self.set_help_overlay(help_overlay)
        self.show_and_reload_apps()

    def open_file(self, file):
        self.file_page.load_file(file)
        self.leaflet.set_visible_child(self.file_page)

    def new_file(self):
        if self.file_page.visible:
            return

        builder = Gtk.Builder.new_from_resource('/io/github/fabrialberio/pinapp/apps_page_dialogs.ui')
        dialog = builder.get_object('filename_dialog')
        name_entry = builder.get_object('name_entry')

        def path_is_valid() -> bool:
            path = name_entry.get_text()
            if '/' in path:
                return False
            else:
                return True

        name_entry.connect('changed', lambda _: dialog.set_response_enabled(
            'create',
            path_is_valid()))

        def callback(widget, resp):
            if resp == 'create':
                path = USER_APPS / Path(f'{Path(name_entry.get_text())}.desktop')
                file = DesktopEntry.new_with_defaults(path)

                self.file_page.load_file(file)
                self.leaflet.set_visible_child(self.file_page)

        dialog.connect('response', callback)
        dialog.set_transient_for(self.get_root())
        dialog.show()

    def show_apps(self):
        self.leaflet.set_visible_child(self.apps_page)

    def show_and_reload_apps(self):
        self.show_apps()
        self.pins_view.load_apps(loading_ok=False)
        self.installed_view.load_apps(loading_ok=False)

    def show_about_window(self):
        builder = Gtk.Builder.new_from_resource('/io/github/fabrialberio/pinapp/apps_page_dialogs.ui')
        about_window = builder.get_object('about_window')
        about_window.set_transient_for(self)
        about_window.present()