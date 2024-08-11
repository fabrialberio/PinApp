from typing import Callable
from gettext import gettext as _

from gi.repository import Gtk, Adw, Gio, GObject # type: ignore
from xml.sax.saxutils import escape as escape_xml

from .config import *
from .desktop_file import DesktopFile, DesktopEntry


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

class AppListView(Adw.Bin):
    __gtype_name__ = 'AppListView'

    listbox: Gtk.ListBox
    placeholder: Adw.StatusPage
    scrolled_window: Gtk.ScrolledWindow
    show_pinned_chip = False

    def __init__(self) -> None:
        super().__init__()

        self.listbox = Gtk.ListBox(
            selection_mode=Gtk.SelectionMode.NONE,
            css_classes=['boxed-list']
        )

        self.placeholder = Adw.StatusPage(
            title=_('No apps found'),
            icon_name='folder-open-symbolic',
        )

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.append(self.listbox)

        self.scrolled_window = Gtk.ScrolledWindow(
            vexpand=True,
            child=Adw.Clamp(
                margin_top=12,
                margin_bottom=12,
                margin_start=12,
                margin_end=12,
                child=box
            )
        )

        self.set_child(self.scrolled_window)

    def bind_gfile_list(self, gfile_list: Gio.ListStore) -> None:   
        def create_row(gfile: Gio.File):
            row = AppRow(gfile)

            pinned = gfile.get_parent().get_path() == str(USER_APPS)
            row.pinned_chip.set_visible(self.show_pinned_chip and pinned)
            row.connect('file-open', lambda _, f: self.emit('file-open', f))
            return row

        self.bind_model(Gtk.MapListModel.new(gfile_list, create_row))

    def bind_model(self, model: Gio.ListModel) -> None: # TODO: Does not update when unpinning apps
        def sort_files(first: Gio.File, second: Gio.File, data: None):
            first_name = first.file.localize_current(DesktopEntry.NAME)
            second_name = second.file.localize_current(DesktopEntry.NAME)

            lt = first.file.get_str(first_name) < second.file.get_str(second_name)
            return -1 if lt else 1
        
        self.listbox.bind_model(Gtk.SortListModel.new(model, Gtk.CustomSorter.new(sort_files)), lambda r: r)

        def update_show_placeholder(model: Gtk.StringList, *args):
            new_child = self.placeholder if model.get_n_items() == 0 else self.scrolled_window

            if self.get_child() != new_child:
                self.set_child(new_child)

        model.connect('items-changed', update_show_placeholder)
        update_show_placeholder(model)        

    def set_filter(self, predicate: Callable[[AppRow], bool]):
        self.listbox.set_filter_func(predicate)

GObject.signal_new('file-open', AppListView, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (GObject.TYPE_OBJECT,))

class SearchView(AppListView):
    __gtype_name__ = 'SearchView'

    custom_filter: Gtk.CustomFilter
    show_pinned_chip = True

    def __init__(self) -> None:
        super().__init__()

        self.placeholder = Adw.StatusPage(
            title=_('No results found'),
            icon_name='system-search-symbolic',
            description=_('Try searching for something else')
        )

    def bind_row_model(self, row_model: Gio.ListModel) -> None:
        self.custom_filter = Gtk.CustomFilter.new(lambda f: True)
        return super().bind_model(Gtk.FilterListModel.new(row_model, self.custom_filter))

    def connect_entry(self, search_entry: Gtk.SearchEntry):
        def search(entry: Gtk.SearchEntry):
            self.custom_filter.set_filter_func(
                lambda f: search_entry.get_text().lower() in f.search_str
            )

        search_entry.connect('search-changed', search)
