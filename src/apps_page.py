from enum import Enum

from gi.repository import Gtk, Adw, Pango
from xml.sax.saxutils import escape as escape_xml

from .utils import *
from .file_pools import USER_POOL
from .desktop_file import DesktopFile


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
            label: str = '',
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
            add_pinned_chip = False,
            add_hidden_chip = True,
            add_flatpak_chip = True,
            add_snap_chip = True,
            add_terminal_chip = True,
        ) -> None:
        self.file = file

        super().__init__(
            title = escape_xml(self.file.desktop_entry.Name.get(default='')),
            title_lines = 1,
            subtitle = escape_xml(self.file.desktop_entry.Comment.get(default='')),
            subtitle_lines = 1,
            activatable = True,)

        icon = Gtk.Image(
            pixel_size=32,
            margin_top=6,
            margin_bottom=6,
            css_classes=['icon-dropshadow'])
        set_icon_from_name(icon, file.desktop_entry.Icon.get(default=''))

        self.add_prefix(icon)

        self.chip_box = Gtk.Box(spacing=6)
        self.add_suffix(self.chip_box)

        self.add_suffix(Gtk.Image(
            icon_name='go-next-symbolic',
            opacity=.6))

        if self.file.desktop_entry.NoDisplay.get(default=False) and add_hidden_chip:
            icon.set_opacity(.2)
        if self.file.desktop_entry.X_Flatpak.get(default = False) and add_flatpak_chip:
            self.add_chip(AppChip.Flatpak())
        if self.file.desktop_entry.X_SnapInstanceName.get(default = False) and add_snap_chip:
            self.add_chip(AppChip.Snap())
        if self.file.desktop_entry.Terminal.get(default=False) and add_terminal_chip:
            self.add_chip(AppChip.Terminal())
        if self.file.path.parent in USER_POOL.paths and add_pinned_chip:
            self.add_chip(AppChip.Pinned())

        self.connect('activated', lambda _: self.emit('file-open', file))

    def add_chip(self, chip: AppChip):
        self.chip_box.append(chip)


    # Used for sorting apps by name in SearchView
    def __lt__(self, other) -> bool:
        if isinstance(other, AppRow):
            return self.file.desktop_entry.Name.get(default='') < other.file.desktop_entry.Name.get(default='')
        else:
            raise TypeError(f"'<' not supported between instances of {type(self)} and {type(other)}")

class AppsView(Adw.Bin):
    __gtype_name__ = 'AppsView'

    def __init__(self) -> None:
        super().__init__()

    def update(self, files: list[DesktopFile]):
        ...
class AppListView(AppsView):
    __gtype_name__ = 'AppListView'

    def __init__(self) -> None:
        super().__init__()

    def update(self, files: list[DesktopFile], add_pinned_chip: bool = False):
        listbox = Gtk.ListBox(
            selection_mode=Gtk.SelectionMode.NONE,
            css_classes=['boxed-list'])

        rows = sorted([AppRow(f, add_pinned_chip = add_pinned_chip) for f in files])
        for row in rows:
            row.connect('file-open', lambda _, f: self.emit('file-open', f))
            listbox.append(row)

        self.set_child(
            Gtk.ScrolledWindow(
                vexpand = True,
                child = Adw.Clamp(
                    margin_top = 12,
                    margin_bottom = 12,
                    margin_start = 12,
                    margin_end = 12,
                    child = listbox)))

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

    pool_page: AppsView
    state: PoolState

    def __init__(self, pool_page: AppsView) -> None:
        super().__init__()

        self.pool_page = pool_page
        self.add_named(pool_page, PoolState.LOADED.value)
        
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
            .get_first_child() # GtkScrolledWindow
            .get_first_child() # GtkWiewport
            .get_first_child() # GtkBox
            .get_first_child() # AdwClamp
            .get_first_child()) # GtkBox
        box.remove(box.get_first_child()) # Removes the GtkImage with the icon
        box.prepend(Gtk.Spinner(
            width_request=32,
            height_request=32,
            opacity=.8,
            spinning=True)) # Replaces it with a spinner
        
        self.set_state(PoolState.EMPTY)

    def set_state(self, state: PoolState):
        if state.value == self.get_visible_child_name():
            return

        self.state = state
        self.set_visible_child_name(state.value)
        self.emit('state-changed')


class PinsView(PoolStateView):
    __gtype_name__ = 'PinsView'

    def __init__(self) -> None:
        super().__init__(pool_page = AppListView())

class InstalledView(PoolStateView):
    __gtype_name__ = 'InstalledView'

    def __init__(self) -> None:
        super().__init__(pool_page = AppListView())

class SearchView(PoolStateView):
    '''Adds all apps from both PinsView and InstalledView, adds chips to them and filters them on search'''
    __gtype_name__ = 'SearchView'

    search_entry: Gtk.SearchEntry
    pool_page: AppListView
    _files: list[DesktopFile]

    def __init__(self) -> None:
        super().__init__(pool_page = AppListView())

        # Override empty page with a more appropriate one
        self.empty_status_page.set_title(_('No results found'))
        self.empty_status_page.set_description(_('Try searching for something else'))
        self.empty_status_page.set_icon_name('system-search-symbolic')

    def connect_entry(self, search_entry: Gtk.SearchEntry):
        self.search_entry = search_entry
        self.search_entry.connect('search-changed', lambda e: self.search(e.get_text()))

    def update(self, files: list[DesktopFile]):
        self._files = files
        self.pool_page.update(files, add_pinned_chip = True)
        self.set_state(PoolState.LOADED)

    def search(self, query: str):
        if self.state == PoolState.LOADING:
            return

        results = [f for f in self._files if query.lower() in f.search_str]
        self.pool_page.update(results)

        if results:
            self.set_state(PoolState.LOADED)
        else:
            self.set_state(PoolState.EMPTY)