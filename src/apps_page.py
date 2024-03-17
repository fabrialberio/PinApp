from typing import Callable
from gettext import gettext as _

from gi.repository import Gtk, Adw, GObject # type: ignore
from xml.sax.saxutils import escape as escape_xml

from .config import *
from .desktop_file import DesktopFile, DesktopEntry


@Gtk.Template(resource_path='/io/github/fabrialberio/pinapp/app_row.ui')
class AppRow(Adw.ActionRow):
    __gtype_name__ = 'AppRow'

    icon: Gtk.Image = Gtk.Template.Child()
    pinned_chip: Gtk.Box = Gtk.Template.Child()
    terminal_chip: Gtk.Box = Gtk.Template.Child()
    flatpak_chip: Gtk.Box = Gtk.Template.Child()
    snap_chip: Gtk.Box = Gtk.Template.Child()

    def __init__(self, file: DesktopFile):
        super().__init__()

        self.file = file

        self.connect('activated', lambda _: self.emit('file-open', self.file))
        self.file.connect('field-set', lambda d, f, v: self.update())
        self.update()

    def update(self):
        self.set_title(escape_xml(self.file.get(
            self.file.localize_current(DesktopEntry.NAME), ''))) # type: ignore
        self.set_subtitle(escape_xml(self.file.get(
            self.file.localize_current(DesktopEntry.COMMENT), ''))) # type: ignore

        set_icon_from_name(self.icon, self.file.get(DesktopEntry.ICON, '')) # type: ignore

        self.icon.set_opacity(.2 if self.file.get(DesktopEntry.NO_DISPLAY, False) else 1)
        self.terminal_chip.set_visible(self.file.get(DesktopEntry.TERMINAL, False))
        self.flatpak_chip.set_visible(self.file.get(DesktopEntry.X_FLATPAK, False))
        self.snap_chip.set_visible(self.file.get(DesktopEntry.X_SNAP_INSTANCE_NAME, False))

GObject.signal_new('file-open', AppRow, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (GObject.TYPE_PYOBJECT,))

def get_files_model(string_list: Gtk.StringList):
    def create_file(item: Gtk.StringObject):
        return DesktopFile(Path(item.get_string()))
    
    def sort_files(first: DesktopFile, second: DesktopFile, data: None):
        lt = first.get(first.localize_current(DesktopEntry.NAME), '') < \
            second.get(second.localize_current(DesktopEntry.NAME), '') # type: ignore
        return -1 if lt else 1

    return Gtk.SortListModel.new(
        Gtk.MapListModel.new(string_list, create_file),
        Gtk.CustomSorter.new(sort_files)
    )

class AppListView(Adw.Bin):
    __gtype_name__ = 'AppListView'

    listbox: Gtk.ListBox
    scrolled_window: Gtk.ScrolledWindow
    placeholder: Adw.StatusPage

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

    def bind_model(self, string_list: Gtk.StringList, show_pinned_chip=False) -> None:
        model = get_files_model(string_list)
        
        def create_row(file: DesktopFile):
            row = AppRow(file)
            row.pinned_chip.set_visible(show_pinned_chip)
            row.connect('file-open', lambda _, f: self.emit('file-open', f))
            return row

        self.listbox.bind_model(model, create_row)

        def update_show_placeholder(model: Gtk.StringList, *args):
            new_child = self.placeholder if model.get_n_items() == 0 else self.scrolled_window

            if self.get_child() != new_child:
                self.set_child(new_child)

        model.connect('items-changed', update_show_placeholder)
        update_show_placeholder(model)        

    def set_filter(self, predicate: Callable[[AppRow], bool]):
        self.listbox.set_filter_func(predicate)

GObject.signal_new('file-open', AppListView, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (GObject.TYPE_PYOBJECT,))

"""
class SearchView(AppListView):
    '''Adds all apps from both PinsView and InstalledView, adds chips to them and filters them on search'''
    __gtype_name__ = 'SearchView'

    search_entry: Gtk.SearchEntry
    pool_page: AppListView
    _files: list[DesktopFile]

    def __init__(self) -> None:
        super().__init__()

        # Override empty page with a more appropriate one
        self.empty_status_page.set_title(_('No results found'))
        self.empty_status_page.set_icon_name('system-search-symbolic')
        self.empty_status_page.set_description(_('Try searching for something else'))

    def connect_pool(self, pool: FilePool, pool_page: AppListView):
        super().bind_pool(pool, pool_page)

        def _on_files_loaded(paths):
            self._files = [DesktopFile(p) for p in paths]
            self.pool_page.set_filter(lambda r: True)

        pool.connect('files-loaded', lambda _, files: _on_files_loaded(files))

    def connect_entry(self, search_entry: Gtk.SearchEntry):
        self.search_entry = search_entry
        self.search_entry.connect(
            'search-changed', lambda e: self.search(e.get_text()))

    def search(self, query: str):
        self.pool_page.set_filter(lambda r: query.lower() in r.file.search_str)
"""