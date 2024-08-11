from enum import Enum
from typing import Callable
from gettext import gettext as _

from gi.repository import Gtk, Adw, Gio, GObject # type: ignore
from xml.sax.saxutils import escape as escape_xml

from .config import *
from .desktop_file import DesktopFile, DesktopEntry


class AppsViewState(Enum):
    LOADING = 'loading'
    EMPTY = 'placeholder'
    APPS = 'apps'


@Gtk.Template(resource_path='/io/github/fabrialberio/pinapp/app_row.ui')
class AppRow(Adw.ActionRow):
    __gtype_name__ = 'AppRow'

    file: DesktopFile

    icon: Gtk.Image = Gtk.Template.Child()
    pinned_chip: Gtk.Box = Gtk.Template.Child()
    terminal_chip: Gtk.Box = Gtk.Template.Child()
    flatpak_chip: Gtk.Box = Gtk.Template.Child()
    snap_chip: Gtk.Box = Gtk.Template.Child()

    def __init__(self, gfile: Gio.File):
        super().__init__()

        if not gfile.query_exists():
            self.set_title(gfile.get_path())
            self.set_subtitle('Does not exist')
            return

        self.file = DesktopFile.load_from_path(gfile.get_path())

        self.connect('activated', lambda _: self.emit('file-open', gfile))
        self.file.connect('field-set', lambda d, f, v: self.update())
        self.update()

    def update(self):
        self.set_title(escape_xml(self.file.get_str(self.file.localize_current(DesktopEntry.NAME))))
        self.set_subtitle(escape_xml(self.file.get_str(self.file.localize_current(DesktopEntry.COMMENT))))

        set_icon_from_name(self.icon, self.file.get_str(DesktopEntry.ICON))

        self.icon.set_opacity(.2 if self.file.get_bool(DesktopEntry.NO_DISPLAY) else 1)
        self.terminal_chip.set_visible(self.file.get_bool(DesktopEntry.TERMINAL))
        self.flatpak_chip.set_visible(self.file.get_bool(DesktopEntry.X_FLATPAK))
        self.snap_chip.set_visible(self.file.get_bool(DesktopEntry.X_SNAP_INSTANCE_NAME))

GObject.signal_new('file-open', AppRow, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (GObject.TYPE_OBJECT,))


@Gtk.Template(resource_path='/io/github/fabrialberio/pinapp/apps_view.ui')
class AppListView(Adw.Bin):
    __gtype_name__ = 'AppListView'

    state: AppsViewState
    show_pinned_chip = False

    listbox: Gtk.ListBox = Gtk.Template.Child()
    view_stack: Adw.ViewStack = Gtk.Template.Child()
    new_app_button: Gtk.Button = Gtk.Template.Child()
    status_placeholder: Adw.StatusPage = Gtk.Template.Child()

    def __init__(self) -> None:
        super().__init__()

        self.set_state(AppsViewState.EMPTY)

    def set_state(self, state: AppsViewState):
        self.view_stack.set_visible_child_name(state.value)

    def bind_dir_list(self, dir_list: Gtk.DirectoryList) -> None:
        def match_file(gfile_info: Gio.FileInfo):
            return gfile_info.get_content_type() == 'application/x-desktop'

        files_model = Gtk.FilterListModel.new(dir_list, Gtk.CustomFilter.new(match_file))

        def create_row(gfile_info: Gio.FileInfo):
            gfile = gfile_info.get_attribute_object('standard::file')
            row = AppRow(gfile)

            pinned = gfile.get_parent().get_path() == str(USER_APPS)
            row.pinned_chip.set_visible(self.show_pinned_chip and pinned)
            row.connect('file-open', lambda _, f: self.emit('file-open', f))
            return row

        self.bind_model(Gtk.MapListModel.new(files_model, create_row))

    def bind_model(self, model: Gio.ListModel) -> None: # TODO: Does not update when unpinning apps
        def sort_files(first: Gio.File, second: Gio.File, data: None):
            first_name = first.file.localize_current(DesktopEntry.NAME)
            second_name = second.file.localize_current(DesktopEntry.NAME)

            lt = first.file.get_str(first_name) < second.file.get_str(second_name)
            return -1 if lt else 1
        
        self.listbox.bind_model(Gtk.SortListModel.new(model, Gtk.CustomSorter.new(sort_files)), lambda r: r)

    def items_changed(self, dir_list: Gtk.DirectoryList, *args):
        if dir_list.is_loading():
            self.set_state(AppsViewState.LOADING)
        elif dir_list.get_n_items() == 0:
            self.set_state(AppsViewState.EMPTY)
        else:
            self.set_state(AppsViewState.APPS)

    def set_filter(self, predicate: Callable[[AppRow], bool]):
        raise NotImplemented
        self.listbox.set_filter_func(predicate)

    def connect_entry(self, search_entry: Gtk.SearchEntry):
        def search(entry: Gtk.SearchEntry):
            self.custom_filter.set_filter_func(
                lambda f: search_entry.get_text().lower() in f.search_str
            )

        search_entry.connect('search-changed', search)

GObject.signal_new('file-open', AppListView, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (GObject.TYPE_OBJECT,))
