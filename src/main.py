# main.py
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

import sys
from typing import Callable
from locale import bindtextdomain, textdomain

from gi import require_version

require_version('GObject', '2.0')
require_version('Gio', '2.0')
require_version('Gtk', '4.0')
require_version('Gdk', '4.0')
require_version('Adw', '1')
require_version('Pango', '1.0')

from gi.repository import Gtk, Gio, Adw, Gdk, GLib # type: ignore

from .config import LOCALE_DIR, ICON_PATHS
from .window import PinAppWindow, WindowPage, WindowTab
from .desktop_file import DesktopFile


class PinApp(Adw.Application):  
    def __init__(self):
        super().__init__(
            application_id='io.github.fabrialberio.pinapp',
            flags=Gio.ApplicationFlags.HANDLES_OPEN
        )

        def activate(app: PinApp):
            self.get_window().present()

        def open(app: PinApp, gfiles: list[Gio.File], n_files: int, hint: str):
            gfile = gfiles[0]
            
            if not gfile.query_exists():
                return

            window = self.get_window()
            window.file_page.set_file(gfile, DesktopFile.load_from_path(gfile.get_path()))
            window.set_page(WindowPage.FILE_PAGE)
            window.present()

        def on_escape(action: Gio.SimpleAction, param: GLib.Variant):
            window = self.get_window()

            match window.current_page():
                case WindowPage.FILE_PAGE:
                    window.set_page(WindowPage.APPS_PAGE)
                case WindowPage.APPS_PAGE:
                    match window.current_tab():
                        case WindowTab.INSTALLED:
                            window.set_tab(WindowTab.PINS)
                        case WindowTab.SEARCH:
                            window.set_search_mode(False)

        def on_quit(action: Gio.SimpleAction, param: GLib.Variant):
            self.get_window().do_close_request()

        def on_about(action: Gio.SimpleAction, param: GLib.Variant):
            self.get_window().show_about_window()

        def on_search(action: Gio.SimpleAction, parameter: GLib.Variant):
            self.get_window().set_search_mode(True)

        def on_new_file(action: Gio.SimpleAction, param: GLib.Variant):
            self.get_window().new_file()

        self.connect('activate', activate)
        self.connect('open', open)
        self.create_action('exit', on_escape, ['Escape'])
        self.create_action('quit', on_quit, ['<primary>q'])
        self.create_action('about', on_about)
        self.create_action('search', on_search, ['<primary>f'])
        self.create_action('new-file', on_new_file, ['<primary>n'])
        self.set_accels_for_action('win.show-help-overlay', ['<primary>question'])

    def get_window(self) -> PinAppWindow:
        return self.props.active_window or PinAppWindow(application=self)

    def create_action(self, name: str, callback: Callable, accels: list[str]=[]):
        action = Gio.SimpleAction.new(name, None)
        action.connect('activate', callback)
        self.add_action(action)
        self.set_accels_for_action(f'app.{name}', accels)

def main(version):
    bindtextdomain('pinapp', LOCALE_DIR)
    textdomain('pinapp')

    theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
    theme.set_search_path(theme.get_search_path() + [str(p) for p in ICON_PATHS])

    app = PinApp()
    return app.run(sys.argv)
