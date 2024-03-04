from enum import Enum
from typing import Callable
from gettext import gettext as _

from gi.repository import Gtk, Adw, Pango, GObject # type: ignore
from xml.sax.saxutils import escape

from .config import *
from .file_pool import FilePool, USER_POOL, SYSTEM_POOL
from .desktop_file import DesktopFile, DesktopEntry


def escape_xml(string: str) -> str:
    return escape(string or '')


class AppChip(Gtk.Box):
    __gtype_name__ = 'AppChip'

    class Color(Enum):
        GRAY = 'chip-gray'
        BLUE = 'chip-blue'
        YELLOW = 'chip-yellow'
        ORANGE = 'chip-orange'

    @classmethod
    def Pinned(cls):
        return cls(
            icon_name='view-pin-symbolic',
            color=AppChip.Color.YELLOW)

    @classmethod
    def Terminal(cls):
        return cls(icon_name='utilities-terminal-symbolic')

    @classmethod
    def Flatpak(cls, show_label=False):
        return cls(
            icon_name='flatpak-symbolic',
            label='Flatpak',
            color=AppChip.Color.BLUE,
            show_label=show_label)
    
    @classmethod
    def Snap(cls, show_label=False):
        return cls(
            icon_name='snap-symbolic',
            label='Snap',
            color=AppChip.Color.ORANGE,
            show_label=show_label)

    def __init__(self,
            icon_name: str,
            label: str = None,
            show_label: bool = True,
            color: Color = Color.GRAY
        ) -> None:
        super().__init__(
            orientation=Gtk.Orientation.HORIZONTAL,
            valign=Gtk.Align.CENTER,
            spacing=8,
            css_classes=['chip-box', color.value],
            tooltip_text = label)

        self.append(Gtk.Image(
            pixel_size=16,
            icon_name=icon_name))

        if label != None and show_label:
            label_attrs = Pango.AttrList()
            font_desc = Pango.FontDescription()
            font_desc.set_weight(Pango.Weight.BOLD)
            font_desc.set_variant(Pango.Variant.ALL_SMALL_CAPS)
            label_attrs.insert(Pango.AttrFontDesc.new(font_desc))

            self.append(Gtk.Label(
                label=label,
                attributes=label_attrs))

class AppRow(Adw.ActionRow):
    __gtype_name__ = 'AppRow'

    def __init__(self,
            file: DesktopFile,
            chips: list[AppChip] = []):
        self.file = file

        super().__init__(
            title = escape_xml(self.file.get(DesktopEntry.NAME, '')),
            title_lines = 1,
            subtitle = escape_xml(self.file.get(DesktopEntry.COMMENT, '')),
            subtitle_lines = 1,
            activatable = True,)

        icon = Gtk.Image(
            pixel_size=32,
            margin_top=6,
            margin_bottom=6,
            css_classes=['icon-dropshadow'])
        set_icon_from_name(icon, file.get(DesktopEntry.ICON, ''))

        self.add_prefix(icon)

        self.chip_box = Gtk.Box(spacing=6)
        self.add_suffix(self.chip_box)

        self.add_suffix(Gtk.Image(
            icon_name='go-next-symbolic',
            opacity=.6))


        if self.file.get(DesktopEntry.NO_DISPLAY, False):
            icon.set_opacity(.2)
        if self.file.get(DesktopEntry.X_FLATPAK, False):
            self.add_chip(AppChip.Flatpak())
        if self.file.get(DesktopEntry.X_SNAP_INSTANCE_NAME, False):
            self.add_chip(AppChip.Snap())
        if self.file.get(DesktopEntry.TERMINAL, False):
            self.add_chip(AppChip.Terminal())

        for c in chips:
            self.add_chip(c)

        self.connect('activated', lambda _: self.emit('file-open', file))

    def add_chip(self, chip: AppChip):
        self.chip_box.append(chip)


    # Used for sorting apps by name in SearchView
    def __lt__(self, other) -> bool:
        if isinstance(other, AppRow):
            return self.file.get(DesktopEntry.NAME, '').lower() < other.get(DesktopEntry.NAME, '').lower()
        else:
            raise TypeError(f"'<' not supported between instances of {type(self)} and {type(other)}")

class AppListView(Adw.Bin):
    __gtype_name__ = 'AppListView'

    show_pinned_chip: bool = False
    _listbox: Gtk.ListBox

    def __init__(self, show_pinned_chip: bool = False) -> None:
        super().__init__()

        self.show_pinned_chip = show_pinned_chip

        self._listbox = Gtk.ListBox(
            selection_mode=Gtk.SelectionMode.NONE,
            css_classes=['boxed-list'])

        self._listbox.set_sort_func(lambda a, b: a.file.get(DesktopEntry.NAME, '') > b.file.get(DesktopEntry.NAME, ''))

        # Wrap listbox in box to allow it to shrink to fit its contents
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.append(self._listbox)

        self.set_child(
            Gtk.ScrolledWindow(
                vexpand=True,
                child=Adw.Clamp(
                    margin_top=12,
                    margin_bottom=12,
                    margin_start=12,
                    margin_end=12,
                    child=box)))

    def update(self, files: list[DesktopFile]):
        # TODO Warning: Accessing a sequence while it is being sorted or searched is not allowed
        self._listbox.remove_all()

        for f in files:
            row = AppRow(f, chips=[AppChip.Pinned()] if self.show_pinned_chip else [])
            row.connect('file-open', lambda _, f: self.emit('file-open', f))
            self._listbox.append(row)

    # More performant than update, used for search
    def set_filter(self, predicate: Callable[[AppRow], bool]):
        self._listbox.set_filter_func(predicate)

class PoolState(Enum):
    LOADED = 'pool_page'
    EMPTY = 'empty_page'
    LOADING = 'loading_page'
    ERROR = 'error_page'


class PoolStateView(Gtk.Stack):
    __gtype_name__ = 'PoolStateView'

    pool: FilePool
    pool_page: AppListView
    state: PoolState | None = None

    def __init__(self, pool: FilePool = None, pool_page: AppListView = None) -> None:
        super().__init__()

        if pool and pool_page:
            self.connect_pool(pool, pool_page)

        self.empty_status_page = Adw.StatusPage(
            title=_('No apps found'),
            icon_name='folder-open-symbolic')
        self.add_named(self.empty_status_page, PoolState.EMPTY.value)

        self.loading_status_page = Adw.StatusPage(
            title=_('Loading apps'))
        self.add_named(self.loading_status_page, PoolState.LOADING.value)

        self.error_status_page = Adw.StatusPage(
            title=_('Error loading apps'),
            icon_name='dialog-error-symbolic')
        self.add_named(self.error_status_page, PoolState.ERROR.value)

        box = (self.loading_status_page
               .get_first_child()  # GtkScrolledWindow
               .get_first_child()  # GtkWiewport
               .get_first_child()  # GtkBox
               .get_first_child()  # AdwClamp
               .get_first_child())  # GtkBox
        box.remove(box.get_first_child())  # Removes the GtkImage with the icon
        box.prepend(Gtk.Spinner(
            width_request=32,
            height_request=32,
            opacity=.8,
            spinning=True))  # Replaces it with a spinner

        self.set_state(PoolState.EMPTY)

    def connect_pool(self, pool: FilePool, pool_page: AppListView):
        def _on_files_loaded(_, paths: list[Path]):
            files = []

            for p in paths:
                file = DesktopFile()
                file.load(p)
                files.append(file)

            self.pool_page.update(files)
            self.set_state(PoolState.LOADED)

        pool.connect('files-loading',
                     lambda _: self.set_state(PoolState.LOADING))
        pool.connect('files-loaded', _on_files_loaded)
        pool.connect('files-empty', lambda _: self.set_state(PoolState.EMPTY))
        pool.connect('files-error', lambda _,
                     e: self.set_state(PoolState.ERROR))

        self.pool_page = pool_page
        self.add_named(pool_page, PoolState.LOADED.value)

    def set_state(self, state: PoolState):
        if state.value == self.get_visible_child_name():
            return

        self.state = state
        self.set_visible_child_name(state.value)
        self.emit('state-changed')


class SearchView(PoolStateView):
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
        super().connect_pool(pool, pool_page)

        def _on_files_loaded(files):
            self._files = []

            for p in files:
                file = DesktopFile()
                file.load(p)
                self._files.append(file)

            self.pool_page.set_filter(lambda r: True)

        pool.connect('files-loaded', lambda _, files: _on_files_loaded(files))

    def connect_entry(self, search_entry: Gtk.SearchEntry):
        self.search_entry = search_entry
        self.search_entry.connect(
            'search-changed', lambda e: self.search(e.get_text()))

    def search(self, query: str):
        if self.state == PoolState.LOADING:
            return

        self.set_state(PoolState.LOADING)

        self.pool_page.set_filter(lambda r: query.lower() in r.file.search_str)

        self.set_state(PoolState.LOADED)

GObject.signal_new('file-open', AppRow, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (GObject.TYPE_PYOBJECT,))
GObject.signal_new('file-open', AppListView, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (GObject.TYPE_PYOBJECT,))
GObject.signal_new('state-changed', PoolStateView, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ())
