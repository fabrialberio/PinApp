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

from enum import Enum
from typing import Optional
from gettext import gettext as _

from gi.repository import Gtk, Adw, Gio, GLib # type: ignore

from .desktop_file import DesktopFile, DesktopEntry
from .file_page import FilePage # Required to initialize GObject
from .config import USER_APPS, APP_PATHS
from .file_pool import create_gfile_checked
from .apps_view import AppListView


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

    header_bar: Adw.HeaderBar = Gtk.Template.Child()
    new_file_button: Gtk.Button = Gtk.Template.Child()
    navigation_view: Adw.NavigationView = Gtk.Template.Child()
    file_page: FilePage = Gtk.Template.Child()
    view_stack: Adw.ViewStack = Gtk.Template.Child()
    pins_tab: AppListView = Gtk.Template.Child()
    installed_tab: AppListView = Gtk.Template.Child()
    search_tab: AppListView = Gtk.Template.Child()
    search_bar: Gtk.SearchBar = Gtk.Template.Child()
    search_entry: Gtk.SearchEntry = Gtk.Template.Child()
    search_button: Gtk.Button = Gtk.Template.Child()

    last_tab = WindowTab.PINS

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.pins_tab.new_app_button.set_visible(True)
        self.pins_tab.new_app_button.connect('clicked', self.new_file)
        self.new_file_button.connect('clicked', self.new_file)

        def open_file(_tab: AppListView, gfile: Gio.File, desktop_file: DesktopFile):
            self.file_page.set_file(gfile, desktop_file)
            self.set_page(WindowPage.FILE_PAGE)

        self.pins_tab.connect('file-open', open_file)
        self.installed_tab.connect('file-open', open_file)
        self.search_tab.connect('file-open', open_file)
        
        # TODO: Is 'popped' the right signal?
        self.navigation_view.connect('popped', lambda v, p: self.file_page.on_leave())
        self.file_page.connect('pop-request', lambda w: self.set_page(WindowPage.APPS_PAGE))
        self.connect('close-request', lambda _: self.do_close_request())

        builder = Gtk.Builder.new_from_resource('/io/github/fabrialberio/pinapp/apps_page_dialogs.ui')
        help_overlay = builder.get_object('help_overlay')
        help_overlay.set_transient_for(self)
        self.set_help_overlay(help_overlay)

        self._init_app_views()
        self._init_search()
        self.set_tab(WindowTab.PINS)

    def _init_app_views(self):
        # TODO: Make everything async again?

        file_attrs = ','.join((
            Gio.FILE_ATTRIBUTE_STANDARD_CONTENT_TYPE,
            Gio.FILE_ATTRIBUTE_STANDARD_DISPLAY_NAME,
            Gio.FILE_ATTRIBUTE_STANDARD_EDIT_NAME,
        ))

        user_apps_gfile = Gio.File.new_for_path(str(USER_APPS))
        user_dir_list = Gtk.DirectoryList.new(file_attrs, user_apps_gfile)
        user_dir_list.connect('notify::loading', self.pins_tab.items_changed)

        system_apps_gfiles = map(Gio.File.new_for_path, map(str, APP_PATHS))
        system_list_store = Gio.ListStore.new(Gtk.DirectoryList)
        search_list_store = Gio.ListStore.new(Gtk.DirectoryList)
        for gfile in system_apps_gfiles:
            dir_list = Gtk.DirectoryList.new(file_attrs, gfile)
            system_list_store.append(dir_list)
            search_list_store.append(dir_list)

            dir_list.connect('notify::loading', self.installed_tab.items_changed)
            dir_list.connect('notify::loading', self.search_tab.items_changed)

        system_dir_list = Gtk.FlattenListModel.new(system_list_store)      

        search_list_store.append(user_dir_list)
        search_dir_list = Gtk.FlattenListModel.new(search_list_store)

        self.pins_tab.bind_dir_list(user_dir_list)
        self.installed_tab.bind_dir_list(system_dir_list)
        self.search_tab.bind_dir_list(search_dir_list)


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
        match new_page:
            case WindowPage.APPS_PAGE:
                if self.navigation_view.find_page(WindowPage.FILE_PAGE.value).get_can_pop():
                    self.navigation_view.pop_to_tag(WindowPage.APPS_PAGE.value)
            case WindowPage.FILE_PAGE:
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

    def new_file(self, _button: Optional[Gtk.Button] = None):
        if self.current_page() != WindowPage.APPS_PAGE:
            return

        gfile = create_gfile_checked('pinned-app.desktop', GLib.get_tmp_dir())

        desktop_file = DesktopFile.new()
        desktop_file.set_str(DesktopEntry.NAME, _('New application'))
        desktop_file.set_str(DesktopEntry.TYPE, GLib.KEY_FILE_DESKTOP_TYPE_APPLICATION)
        desktop_file.set_str(DesktopEntry.EXEC, '')
        desktop_file.set_str(DesktopEntry.ICON, '')

        self.file_page.set_file(gfile, desktop_file, is_new = True)
        self.set_page(WindowPage.FILE_PAGE)

    def do_close_request(self, *args):
        '''Return `False` if the window can close, otherwise `True`'''
        def quit():
            self.close()
            self.destroy()

        if self.current_page() == WindowPage.FILE_PAGE:
            # TODO: Fix this
            if self.file_page.allow_leave:
                self.close()
                quit()
                return False
            else:
                def callback(_):
                    quit()

                self.file_page.on_leave(callback=callback)

                return True

        quit()

    def show_about_window(self):
        builder = Gtk.Builder.new_from_resource('/io/github/fabrialberio/pinapp/apps_page_dialogs.ui')
        about_window = builder.get_object('about_window')
        about_window.set_transient_for(self)
        about_window.present()
