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


class WindowTab(Enum):
    PINS = 'pins_tab'
    INSTALLED = 'installed_tab'
    SEARCH = 'search_tab'
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
    pins_tab: PoolStateView = Gtk.Template.Child('pins_tab')
    installed_tab: PoolStateView = Gtk.Template.Child('installed_tab')
    search_tab: SearchView = Gtk.Template.Child('search_tab')

    search_bar = Gtk.Template.Child('search_bar')
    search_entry = Gtk.Template.Child('search_entry')
    search_button = Gtk.Template.Child('search_button')

    last_tab: WindowTab = WindowTab.PINS

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.pins_tab.connect_pool(USER_POOL, AppListView())
        self.installed_tab.connect_pool(SYSTEM_POOL, AppListView())
        self.search_tab.connect_pool(SEARCH_POOL, AppListView(show_pinned_chip = True))

        button = Gtk.Button(
            halign=Gtk.Align.CENTER,
            css_classes=['suggested-action', 'pill'],
            child=Adw.ButtonContent(
                label=_('Add new app'),
                icon_name='list-add-symbolic'))
        button.connect('clicked', lambda _: self.new_file())

        self.pins_tab.empty_status_page.set_child(button)

        self.new_file_button.connect('clicked', lambda _: self.new_file())

        self.pins_tab.pool_page.connect('file-open', lambda _, f: self.open_file(f))
        self.installed_tab.pool_page.connect('file-open', lambda _, f: self.open_file(f))
        self.search_tab.pool_page.connect('file-open', lambda _, f: self.open_file(f))

        self.file_page.connect('file-leave', lambda _: self.set_page(WindowPage.APPS_PAGE))
        self.file_page.connect('file-changed', lambda _: self.reload_pins())

        self.connect('close-request', lambda _: self.do_close_request())

        builder = Gtk.Builder.new_from_resource('/io/github/fabrialberio/pinapp/apps_page_dialogs.ui')
        help_overlay = builder.get_object('help_overlay')
        help_overlay.set_transient_for(self)
        self.set_help_overlay(help_overlay)

        self._init_search()
        self.reload_apps()

    def _init_search(self):
        self.search_bar.set_key_capture_widget(self)
        self.search_bar.connect_entry(self.search_entry)
        self.search_tab.connect_entry(self.search_entry)

        def tab_changed_cb(*args):
            '''Disables search mode when the view is changed to something else'''
            if self.search_bar.get_search_mode() is True and self.current_tab() != WindowTab.SEARCH:
                self.search_bar.set_search_mode(False)

        self.search_entry.connect('search-changed', lambda e: self.set_search_mode(True))
        self.search_button.connect('toggled', lambda b: self.set_search_mode(b.get_active()))
        self.view_stack.connect('notify', tab_changed_cb)

    def set_page(self, new_page: WindowPage):
        if new_page == WindowPage.APPS_PAGE:
            self.navigation_view.pop_to_tag(WindowPage.APPS_PAGE.value)
        elif new_page == WindowPage.FILE_PAGE:
            self.navigation_view.push_by_tag(WindowPage.FILE_PAGE.value)

    def current_page(self) -> WindowPage:
        return WindowPage(self.navigation_view.get_visible_page().get_tag())

    def set_tab(self, new_tab: WindowTab):
        if new_tab != self.current_tab():
            self.last_tab = self.current_tab()
            self.view_stack.set_visible_child_name(new_tab.value)

    def current_tab(self) -> WindowTab:
        return WindowTab(self.view_stack.get_visible_child_name())

    def set_search_mode(self, state: bool, clear_entry=False):
        '''Shows or hides search view and search bar'''
        if state:
            self.set_page(WindowPage.APPS_PAGE)
            self.set_tab(WindowTab.SEARCH)

            self.search_bar.set_search_mode(True)
            self.search_entry.grab_focus()

            if clear_entry:
                self.search_entry.set_text('')
        else:
            if self.current_tab() == WindowTab.SEARCH:
                self.set_tab(self.last_tab)
            self.search_bar.set_search_mode(False)

    def open_file(self, file):
        self.file_page.load_file(file)
        self.set_page(WindowPage.FILE_PAGE)

    def new_file(self):
        # TODO crashes with new DesktopFile
        if self.current_page() != WindowPage.APPS_PAGE:
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
        self.set_tab(WindowTab.PINS)
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

        if self.current_page() == WindowPage.FILE_PAGE:
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

        quit()

    def show_about_window(self):
        builder = Gtk.Builder.new_from_resource('/io/github/fabrialberio/pinapp/apps_page_dialogs.ui')
        about_window = builder.get_object('about_window')
        about_window.set_transient_for(self)
        about_window.present()
