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
from gettext import gettext as _

from gi.repository import Gtk, Adw, GLib # type: ignore

from .desktop_file import DesktopFile, DesktopEntry
from .file_page import FilePage # Required to initialize GObject
from .file_pool import USER_POOL, SYSTEM_POOL, SEARCH_POOL
from .apps_page import AppListView, SearchView


class WindowTab(Enum):
    LOADING = 'loading_tab'
    PINS = 'pins_tab'
    INSTALLED = 'installed_tab'
    SEARCH = 'search_tab'


class WindowPage(Enum):
    APPS_PAGE = 'apps-page'
    FILE_PAGE = 'file-page'


@Gtk.Template(resource_path='/io/github/fabrialberio/pinapp/window.ui')
class PinAppWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'PinAppWindow'

    header_bar: Adw.HeaderBar = Gtk.Template.Child()
    new_file_button: Gtk.Button = Gtk.Template.Child()
    navigation_view: Adw.NavigationView = Gtk.Template.Child()
    file_page: FilePage = Gtk.Template.Child()
    view_stack: Adw.ViewStack = Gtk.Template.Child()
    pins_tab: AppListView = Gtk.Template.Child()
    installed_tab: AppListView = Gtk.Template.Child()
    search_tab: SearchView = Gtk.Template.Child()
    search_bar: Gtk.SearchBar = Gtk.Template.Child()
    search_entry: Gtk.SearchEntry = Gtk.Template.Child()
    search_button: Gtk.Button = Gtk.Template.Child()

    last_tab = WindowTab.PINS

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.pins_tab.bind_string_list(USER_POOL.files)
        self.installed_tab.bind_string_list(SYSTEM_POOL.files)
        self.search_tab.bind_string_list(SEARCH_POOL.files)

        button = Gtk.Button(
            halign=Gtk.Align.CENTER,
            css_classes=['suggested-action', 'pill'],
            child=Adw.ButtonContent(
                label=_('Add new app'),
                icon_name='list-add-symbolic'
            )
        )
        self.pins_tab.placeholder.set_child(button)
        
        def new_file(widget: Gtk.Widget):
            self.new_file()

        button.connect('clicked', new_file)
        self.new_file_button.connect('clicked', new_file)

        def open_file(widget: Gtk.Widget, file: DesktopFile):
            self.file_page.load_file(file)
            self.set_page(WindowPage.FILE_PAGE)

        self.pins_tab.connect('file-open', open_file)
        self.installed_tab.connect('file-open', open_file)
        self.search_tab.connect('file-open', open_file)

        self.file_page.connect('file-leave', lambda _: self.set_page(WindowPage.APPS_PAGE))
        self.file_page.connect('file-changed', lambda _: self.reload_pins())

        self.connect('close-request', lambda _: self.do_close_request())

        builder = Gtk.Builder.new_from_resource('/io/github/fabrialberio/pinapp/apps_page_dialogs.ui')
        help_overlay = builder.get_object('help_overlay')
        help_overlay.set_transient_for(self)
        self.set_help_overlay(help_overlay)

        def on_pins_loaded(pool):
            if self.current_tab() == WindowTab.LOADING:
                self.set_tab(self.last_tab)
                self.header_bar.set_sensitive(True)

        USER_POOL.connect('loaded', on_pins_loaded)

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

        self.search_entry.connect(
            'search-changed', lambda e: self.set_search_mode(True))
        self.search_button.connect(
            'toggled', lambda b: self.set_search_mode(b.get_active()))
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

    def new_file(self):
        if self.current_page() != WindowPage.APPS_PAGE:
            return

        tmp_path = Path(GLib.get_tmp_dir()) / 'pinned-app'
        tmp_path.touch()

        file = DesktopFile(tmp_path)
        file.set(DesktopEntry.NAME, _('New application'))
        file.set(DesktopEntry.TYPE, 'Application')
        file.set(DesktopEntry.EXEC, DesktopEntry.EXEC.default_value())
        file.set(DesktopEntry.ICON, DesktopEntry.ICON.default_value())

        self.file_page.load_file(file)
        self.set_page(WindowPage.FILE_PAGE)

    def reload_pins(self):
        self.set_tab(WindowTab.PINS)
        USER_POOL.load()

    def reload_apps(self):
        USER_POOL.load()
        SYSTEM_POOL.load()
        SEARCH_POOL.load()

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
