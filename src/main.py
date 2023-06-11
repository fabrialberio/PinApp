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
from locale import bindtextdomain, textdomain
from pathlib import Path

from gi.repository import Gtk, Gio, Adw

from .utils import LOCALE_DIR
from .window import PinAppWindow

bindtextdomain('pinapp', LOCALE_DIR)
textdomain('pinapp')

class PinAppApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self):
        super().__init__(
            application_id='io.github.fabrialberio.pinapp',
            flags=Gio.ApplicationFlags.HANDLES_OPEN)

        self.create_action('quit', lambda a, _: self.window.do_close_request(), ['<primary>q'])
        self.create_action('about', lambda a, _: self.window.show_about_window())
        self.create_action('search', lambda a, _: self.window.set_search_mode(True), ['<primary>f'])
        
        self.create_action('reload', lambda a, _: self.window.reload_apps())
        self.create_action('new-file', lambda a, _: self.window.new_file(), ['<primary>n'])
        
        self.create_action('exit', self.on_escape, ['Escape'])

        self.set_accels_for_action('win.show-help-overlay', ['<primary>question'])
        self.window = None

    def do_activate(self):
        """Called when the application is activated"""
        self._create_window()
        self.window.present()

    def do_open(self, files, n_files, hint):
        print(f'Do open called!\n{files=}\t{n_files=}\t{hint=}')
        
        path = Path(files[0].get_path())
        print(f'{path=}')

        self._create_window()
        print(f'{self.window=}')
        self.window.load_path(path)
        self.window.present()

    def on_escape(self, *args):
        if self.window.get_page() == self.window.file_page:
            self.window.file_page.on_leave()
        elif self.window.get_page() == self.window.apps_page and self.window.get_view() == self.window.search_view:
            self.window.set_search_mode(False)

    def create_action(self, name, callback, shortcuts=None):
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)

    def _create_window(self):
        self.window = self.props.active_window
        if not self.window:
            self.window = PinAppWindow(application=self)

def main(version):
    """The application's entry point."""
    app = PinAppApplication()
    return app.run(sys.argv)
