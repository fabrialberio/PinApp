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
from gi import require_version

require_version('GObject', '2.0')
require_version('Gio', '2.0')
require_version('Gtk', '4.0')
require_version('Adw', '1')

from gi.repository import Gtk, Gio, Adw
from .window import PinAppWindow


class PinAppApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self):
        super().__init__(application_id='com.github.fabrialberio.pinapp',
                         flags=Gio.ApplicationFlags.FLAGS_NONE)

        self.create_action('quit', lambda a, v: self.quit(), ['<primary>q'])
        self.create_action('about', self.show_about_window)
        
        self.create_action('refresh', self.on_refresh)
        self.create_action('new-file', self.on_new_file, ['<primary>n'])
        
        self.create_action('exit', self.on_back, ['Escape'])
        self.create_action('save', self.on_save, ['<primary>s'])

        self.set_accels_for_action('win.show-help-overlay', ['<primary>question'])
        self.window = None

    def do_activate(self):
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """
        self.window = self.props.active_window
        if not self.window:
            self.window = PinAppWindow(application=self)

        self.window.present()

    def on_refresh(self, action, *args):
        if not self.window.apps_view.is_loading:
            self.window.apps_view.update_all_apps()

    def on_save(self, action, *args):
        self.window.file_view.emit('file-save')

    def on_new_file(self, action, *args):
        self.window.apps_view.on_new_file()

    def on_back(self, action, *args):
        self.window.file_view.emit('file-back')

    def show_about_window(self, action, *args):
        """Callback for the app.about action."""
        # I'm not shure this is the best way, but it works perfectly fine for now
        self.window.show_about_window()

    def create_action(self, name, callback, shortcuts=None):
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)


def main(version):
    """The application's entry point."""
    app = PinAppApplication()
    return app.run(sys.argv)
