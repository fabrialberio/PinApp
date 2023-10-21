from xml.sax.saxutils import escape as escape_xml
from typing import Callable
from enum import Enum

from gi.repository import Gtk, Adw

from .config import *
from .file_pool import FilePool, USER_POOL
from .desktop_file import DesktopFile


_ = lambda x: x

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
            tooltip_text='Flatpak',
            color=AppChip.Color.BLUE)

    @classmethod
    def Snap(cls, show_label=False):
        return cls(
            icon_name='snap-symbolic',
            tooltip_text='Snap',
            color=AppChip.Color.ORANGE)

    def __init__(self,
                 icon_name: str,
                 tooltip_text: str | None = None,
                 color: Color = Color.GRAY
                 ) -> None:
        super().__init__(
            orientation=Gtk.Orientation.HORIZONTAL,
            valign=Gtk.Align.CENTER,
            spacing=8,
            css_classes=['chip-box', color.value],
            tooltip_text=tooltip_text)

        self.append(Gtk.Image(
            pixel_size=16,
            icon_name=icon_name))


class AppIcon(Gtk.Image):
    __gtype_name__ = 'AppIcon'

    def __init__(self, icon_name: str | None = None) -> None:
        super().__init__(
            pixel_size=32,
            css_classes=['icon-dropshadow'])

        self.set_app_icon_name(icon_name)

    def set_app_icon_name(self, icon_name: str | None):
        self.set_from_icon_name('application-x-executable')

        theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
        if icon_name is not None:
            # Checking for -symbolic because sometimes icons only have a symbolic version
            if theme.has_icon(icon_name) or theme.has_icon(f'{icon_name}-symbolic'):
                self.set_from_icon_name(icon_name)
            elif Path(icon_name).is_file():
                self.set_from_file(icon_name)

    def set_faded(self, hidden: bool):
        if hidden:
            self.set_opacity(.2)
        else:
            self.set_opacity(1)


class AppRow(Adw.ActionRow):
    __gtype_name__ = 'AppRow'

    file: DesktopFile
    _chip_box: Gtk.Box

    def __init__(self,
                 file: DesktopFile,
                 add_pinned_chip=False,
                 ) -> None:
        self.file = file

        super().__init__(
            title=escape_xml(self.file.desktop_entry.Name.unlocalized_or('')),
            title_lines=1,
            subtitle=escape_xml(
                self.file.desktop_entry.Comment.unlocalized_or('')),
            subtitle_lines=1,
            activatable=True,)

        icon = AppIcon(self.file.desktop_entry.Icon)
        self.add_prefix(icon)

        self._chip_box = Gtk.Box(spacing=6)
        self.add_suffix(self._chip_box)

        self.add_suffix(Gtk.Image(
            icon_name='go-next-symbolic',
            opacity=.6))

        if self.file.desktop_entry.NoDisplay:
            icon.set_faded(True)
        if self.file.desktop_entry.X_Flatpak:
            self.add_chip(AppChip.Flatpak())
        if self.file.desktop_entry.X_SnapInstanceName:
            self.add_chip(AppChip.Snap())
        if self.file.desktop_entry.Terminal:
            self.add_chip(AppChip.Terminal())
        if self.file.path.parent in USER_POOL.paths and add_pinned_chip:
            self.add_chip(AppChip.Pinned())

        self.connect('activated', lambda _: self.emit('file-open', file))

    def add_chip(self, chip: AppChip):
        self._chip_box.append(chip)


class AppsView(Adw.Bin):
    __gtype_name__ = 'AppsView'

    def __init__(self) -> None:
        super().__init__()

    def update(self, files: list[DesktopFile]):
        ...


class AppListView(AppsView):
    __gtype_name__ = 'AppListView'

    show_pinned_chip: bool = False
    _listbox: Gtk.ListBox

    def __init__(self, show_pinned_chip=False) -> None:
        super().__init__()

        self.show_pinned_chip = show_pinned_chip

        self._listbox = Gtk.ListBox(
            selection_mode=Gtk.SelectionMode.NONE,
            css_classes=['boxed-list'])

        self._listbox.set_sort_func(lambda a, b:
                                    a.file.desktop_entry.Name.unlocalized_or('') > b.file.desktop_entry.Name.unlocalized_or(''))

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
            row = AppRow(f, add_pinned_chip=self.show_pinned_chip)
            row.connect('file-open', lambda _, f: self.emit('file-open', f))
            self._listbox.append(row)

    # More performant than update, used for search
    def set_filter(self, predicate: Callable[[AppRow], bool]):
        self._listbox.set_filter_func(lambda r: predicate(r))


class AppGridView(AppsView):
    __gtype_name__ = 'AppGridView'

    def __init__(self) -> None:
        super().__init__()

    def update(self, files: list[DesktopFile]):
        ...


class PoolState(Enum):
    LOADED = 'pool_page'
    EMPTY = 'empty_page'
    LOADING = 'loading_page'
    ERROR = 'error_page'


class PoolStateView(Gtk.Stack):
    __gtype_name__ = 'PoolStateView'

    pool: FilePool
    pool_page: AppsView
    state: PoolState | None = None

    def __init__(self, pool: FilePool = None, pool_page: AppsView = None) -> None:
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

    def connect_pool(self, pool: FilePool, pool_page: AppsView):
        def _on_files_loaded(_, files: list[Path]):
            self.pool_page.update([DesktopFile(f) for f in files])
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
        self.empty_status_page.set_description(
            _('Try searching for something else'))
        self.empty_status_page.set_icon_name('system-search-symbolic')

    def connect_pool(self, pool: FilePool, pool_page: AppListView):
        super().connect_pool(pool, pool_page)

        def _on_files_loaded(files):
            self._files = [DesktopFile(f) for f in files]
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

        results = [f for f in self._files if query.lower() in f.search_str]
        self.pool_page.set_filter(lambda r: r.file in results)

        if results:
            self.set_state(PoolState.LOADED)
        else:
            self.set_state(PoolState.EMPTY)
