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

from .apps_view import AppsView
from .file_view import FileView

from .desktop_entry import DesktopEntry
from pathlib import Path

@Gtk.Template(resource_path='/com/github/fabrialberio/pinapp/window.ui')
class PinAppWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'PinAppWindow'

    leaflet = Gtk.Template.Child('main_leaflet')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.apps_view = AppsView()
        self.apps_view.connect('file-open', lambda _, f: self.open_file(f))
        self.leaflet.append(self.apps_view)

        self.file_view = FileView()
        self.file_view.connect('file-back', lambda _: self.show_apps())
        self.file_view.connect('file-save', lambda _: self.show_and_update_apps())
        self.file_view.connect('file-delete', lambda _: self.show_and_update_apps())
        self.leaflet.append(self.file_view)

        builder = Gtk.Builder.new_from_resource('/com/github/fabrialberio/pinapp/apps_view_dialogs.ui')
        help_overlay = builder.get_object('help_overlay')
        help_overlay.set_transient_for(self)

        self.set_help_overlay(help_overlay)

    def open_file(self, file):
        self.file_view.load_file(file)
        self.leaflet.set_visible_child(self.file_view)

    def show_apps(self):
        self.leaflet.set_visible_child(self.apps_view)

    def show_and_update_apps(self):
        self.show_apps()
        self.apps_view.update_user_apps()

    def show_about_window(self):
        builder = Gtk.Builder.new_from_resource('/com/github/fabrialberio/pinapp/apps_view_dialogs.ui')
        about_window = builder.get_object('about_window')
        about_window.set_transient_for(self)
        about_window.present()