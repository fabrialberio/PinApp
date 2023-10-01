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
from enum import Enum

from gi.repository import Gtk, Adw

from .desktop_file import DesktopFile
from .file_pools import USER_POOL, SYSTEM_POOL, SEARCH_POOL
from .apps_page import SearchView, PoolStateView, AppListView

class WindowPage(Enum):
    APPS_PAGE = 'apps-page'
    FILE_PAGE = 'file-page'

@Gtk.Template(resource_path='/io/github/fabrialberio/pinapp/window.ui')
class PinAppWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'PinAppWindow'

    new_file_button = Gtk.Template.Child('new_file_button')

    navigation_view = Gtk.Template.Child('navigation_view')
    file_page = Gtk.Template.Child('file_page')

    view_stack = Gtk.Template.Child('view_stack')
    pins_view: PoolStateView = Gtk.Template.Child('pins_view')
    installed_view: PoolStateView = Gtk.Template.Child('installed_view')
    search_view: SearchView = Gtk.Template.Child('search_view')

    search_bar = Gtk.Template.Child('search_bar')
    search_entry = Gtk.Template.Child('search_entry')
    search_button = Gtk.Template.Child('search_button')

    last_view: WindowPage = WindowPage.APPS_PAGE

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.pins_view.connect_pool(USER_POOL, AppListView())
        self.installed_view.connect_pool(SYSTEM_POOL, AppListView())
        self.search_view.connect_pool(SEARCH_POOL, AppListView())

        button = Gtk.Button(
            halign=Gtk.Align.CENTER,
            css_classes=['suggested-action', 'pill'],
            child=Adw.ButtonContent(
                label=_('Add new app'),
                icon_name='list-add-symbolic'))
        button.connect('clicked', lambda _: self.new_file())

        self.pins_view.empty_status_page.set_child(button)

        self.new_file_button.connect('clicked', lambda _: self.new_file())

        self.pins_view.pool_page.connect('file-open', lambda _, f: self.open_file(f))
        self.installed_view.pool_page.connect('file-open', lambda _, f: self.open_file(f))
        self.search_view.pool_page.connect('file-open', lambda _, f: self.open_file(f))

        self.file_page.connect('file-leave', lambda _: self.set_page(WindowPage.APPS_PAGE))
        self.file_page.connect('file-changed', lambda _: self.reload_pins())

        self.connect('close-request', lambda _: self.do_close_request())

        builder = Gtk.Builder.new_from_resource('/io/github/fabrialberio/pinapp/apps_page_dialogs.ui')
        help_overlay = builder.get_object('help_overlay')
        help_overlay.set_transient_for(self)
        self.set_help_overlay(help_overlay)

        self._init_search()
        self.reload_apps()
        self.set_view(self.pins_view)

    def _init_search(self):
        self.search_bar.set_key_capture_widget(self)
        self.search_bar.connect_entry(self.search_entry)
        self.search_view.connect_entry(self.search_entry)

        def view_changed_cb(*args):
            '''Disables search mode when the view is changed to something else'''
            if self.search_bar.get_search_mode() == True and self.get_view() != self.search_view:
                self.search_bar.set_search_mode(False)

        self.search_entry.connect('search-changed', lambda e: self.set_search_mode(True))
        self.search_button.connect('toggled', lambda b: self.set_search_mode(b.get_active()))
        self.view_stack.connect('notify', view_changed_cb)

    def set_page(self, new_page: WindowPage):
        if new_page == WindowPage.APPS_PAGE:
            self.navigation_view.pop_to_tag(WindowPage.APPS_PAGE.value)
        elif new_page == WindowPage.FILE_PAGE:
            self.navigation_view.push_by_tag(WindowPage.FILE_PAGE.value)

    def get_page(self) -> WindowPage:
        return WindowPage(self.navigation_view.get_visible_page().get_tag())

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
            self.set_page(WindowPage.APPS_PAGE)
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
        self.set_page(WindowPage.FILE_PAGE)

    def new_file(self):
        # TODO crashes with new DesktopFile
        if self.get_page() != WindowPage.APPS_PAGE:
            return

        path = USER_POOL.new_file_name('pinned-app')
        file = DesktopFile.new_with_defaults(path)

        self.file_page.load_file(file)
        self.set_page(WindowPage.FILE_PAGE)

    def load_path(self, path: Path):
        if path is None:
            return

        self.file_page.load_path(path)
        self.set_page(WindowPage.FILE_PAGE)

    def reload_pins(self):
        self.set_view(self.pins_view)
        USER_POOL.files_async()

    def reload_apps(self):
        USER_POOL.files_async()
        SYSTEM_POOL.files_async()
        SEARCH_POOL.files_async()

    def do_close_request(self, *args):
        '''Return `False` if the window can close, otherwise `True`'''
        def quit():
            self.close()
            self.destroy()

        if self.get_page() == WindowPage.FILE_PAGE:
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