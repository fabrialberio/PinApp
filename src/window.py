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

from pathlib import Path
from typing import Callable
from enum import Enum

from gi.repository import Gtk, Adw, Gio

from .utils import USER_APPS, new_file_name
from .desktop_entry import DesktopEntry


class Page(Enum):
    APPS_PAGE = 'apps-page'
    FILE_PAGE = 'file-page'

@Gtk.Template(resource_path='/io/github/fabrialberio/pinapp/window.ui')
class PinAppWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'PinAppWindow'

    new_file_button = Gtk.Template.Child('new_file_button')

    navigation_view = Gtk.Template.Child('navigation_view')
    file_page = Gtk.Template.Child('file_page')

    view_stack = Gtk.Template.Child('view_stack')
    pins_view = Gtk.Template.Child('pins_view')
    installed_view = Gtk.Template.Child('installed_view')
    search_view = Gtk.Template.Child('search_view')

    search_bar = Gtk.Template.Child('search_bar')
    search_entry = Gtk.Template.Child('search_entry')
    search_button = Gtk.Template.Child('search_button')

    last_view = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.new_file_button.connect('clicked', lambda _: self.new_file())

        self.pins_view.connect('file-open', lambda _, f: self.open_file(f))
        self.pins_view.connect('file-new', lambda _: self.new_file())
        self.installed_view.connect('file-open', lambda _, f: self.open_file(f))
        self.search_view.connect('file-open', lambda _, f: self.open_file(f))

        self.file_page.connect('file-leave', lambda _: self.set_page(Page.APPS_PAGE))
        self.file_page.connect('file-changed', lambda _: self.reload_apps(show_pins=True, show_apps=False, only_pins=True))

        self.connect('close-request', lambda _: self.do_close_request())

        builder = Gtk.Builder.new_from_resource('/io/github/fabrialberio/pinapp/apps_page_dialogs.ui')
        help_overlay = builder.get_object('help_overlay')
        help_overlay.set_transient_for(self)
        self.set_help_overlay(help_overlay)

        self._init_search()
        self.reload_apps(show_pins=True)

    def _init_search(self):
        self.search_bar.set_key_capture_widget(self)
        self.search_bar.connect_entry(self.search_entry)
        self.search_view.connect_entry(self.search_entry)

        self.search_view.set_source_views([self.pins_view, self.installed_view])

        def view_changed_cb(*args):
            '''Disables search mode when the view is changed to something else'''
            if self.search_bar.get_search_mode() == True and self.get_view() != self.search_view:
                self.search_bar.set_search_mode(False)

        self.search_entry.connect('search-changed', lambda e: self.set_search_mode(True))
        self.search_button.connect('toggled', lambda b: self.set_search_mode(b.get_active()))
        self.view_stack.connect('notify', view_changed_cb)

    def set_page(self, new_page: Page):
        if new_page == Page.APPS_PAGE:
            self.navigation_view.pop_to_tag(Page.APPS_PAGE.value)
        elif new_page == Page.FILE_PAGE:
            self.navigation_view.push_by_tag(Page.FILE_PAGE.value)

    def get_page(self) -> Page:
        return Page(self.navigation_view.get_visible_page().get_tag())

    def set_view(self, new_view: Gtk.Widget):
        if new_view in [
                self.pins_view,
                self.installed_view,
                self.search_view]:
            if new_view != (current_view := self.get_view()):
                self.last_view = current_view
                self.view_stack.set_visible_child(new_view)
        else:
            raise ValueError

    def get_view(self) -> Gtk.Widget:
        return self.view_stack.get_visible_child()

    def set_search_mode(self, state: bool, clear_entry=False):
        '''Shows or hides search view and search bar'''
        if state:
            self.set_page(Page.APPS_PAGE)
            self.set_view(self.search_view)

            self.search_bar.set_search_mode(True)
            self.search_entry.grab_focus()

            if clear_entry:
                self.search_entry.set_text('')
        else:
            if self.get_view() == self.search_view:
                self.set_view(self.last_view)
            self.search_bar.set_search_mode(False)

    def open_file(self, file):
        self.file_page.load_file(file)
        self.set_page(Page.FILE_PAGE)

    def new_file(self):
        if self.get_page() != Page.APPS_PAGE:
            return

        path = new_file_name(USER_APPS)
        file = DesktopEntry.new_with_defaults(path)

        self.file_page.load_file(file)
        self.set_page(Page.FILE_PAGE)


    def choose_file(self, callback: Callable[[Path], None]) -> None:
        def on_resp(dialog, resp: Gtk.ResponseType):
            if resp == Gtk.ResponseType.ACCEPT:
                callback(Path(dialog.get_file().get_path()))
            else:
                return

        desktop_file_filter = Gtk.FileFilter()
        desktop_file_filter.set_name(_('Desktop files'))
        desktop_file_filter.add_mime_type('application/x-desktop')

        dialog = Gtk.FileChooserNative()
        dialog.add_filter(desktop_file_filter)
        dialog.set_filter(desktop_file_filter)

        dialog.connect('response', on_resp)
        dialog.set_transient_for(self)
        dialog.show()

    def load_path(self, path: Path):
        if path is None:
            return

        self.file_page.load_path(path)
        self.set_page(Page.FILE_PAGE)

    def reload_apps(self, show_pins=False, show_apps=True, only_pins=False):
        if show_apps:
            self.set_page(Page.APPS_PAGE)

        if show_pins:
            self.set_view(self.pins_view)

        self.pins_view.load_apps(loading_ok=False)

        if not only_pins:
            self.installed_view.load_apps(loading_ok=False)

    def do_close_request(self, *args):
        '''Return `False` if the window can close, otherwise `True`'''
        def quit():
            self.close()
            self.destroy()

        if self.get_page() == Page.FILE_PAGE:
            if self.file_page.allow_leave:
                self.close()
                quit()
                return False
            else:
                def callback(_):
                    global block_close
                    block_close = False
                    quit()

                self.file_page.on_leave(callback=callback)

                return True
        else:
            quit()

    def show_about_window(self):
        builder = Gtk.Builder.new_from_resource('/io/github/fabrialberio/pinapp/apps_page_dialogs.ui')
        about_window = builder.get_object('about_window')
        about_window.set_transient_for(self)
        about_window.present()