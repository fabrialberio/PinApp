from enum import Enum

from gi.repository import Gtk, Adw, Pango
from xml.sax.saxutils import escape

from .utils import *
from .file_pools import USER_POOL, SYSTEM_POOL, DesktopFilePool, WritableDesktopFilePool
from .desktop_file import DesktopFile

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
            chips: list[AppChip] = []):
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


        if self.file.desktop_entry.NoDisplay.get(default=False):
            icon.set_opacity(.2)
        if self.file.desktop_entry.X_Flatpak.get(default = False):
            self.add_chip(AppChip.Flatpak())
        if self.file.desktop_entry.X_SnapInstanceName.get(default = False):
            self.add_chip(AppChip.Snap())
        if self.file.desktop_entry.Terminal.get(default=False):
            self.add_chip(AppChip.Terminal())

        for c in chips:
            self.add_chip(c)

        self.connect('activated', lambda _: self.emit('file-open', file))

    def add_chip(self, chip: AppChip):
        self.chip_box.append(chip)


    # Used for sorting apps by name in SearchView
    def __lt__(self, other) -> bool:
        if isinstance(other, AppRow):
            return self.file.desktop_entry.Name.get(default='') < other.file.desktop_entry.Name.get(default='')
        else:
            raise TypeError(f"'<' not supported between instances of {type(self)} and {type(other)}")

class State(Enum):
    FILLED = 'filled'
    EMPTY = 'empty'
    ERROR = 'error'
    LOADING = 'loading'

class AppsView(Adw.Bin):
    '''A widget that handles status pages for states'''
    __gtype_name__ = 'AppsPage'

    def __init__(self, show_new_file_button: bool, description: str = '') -> None:
        super().__init__()

        self.show_new_file_button = show_new_file_button
        self.description = description
        self.state = State.EMPTY

        self._init_widgets()

    def _init_widgets(self):
        self.empty_page = Adw.StatusPage(
            vexpand=True,
            title=_('No apps found'),
            icon_name='folder-open-symbolic'
        )
        if self.show_new_file_button:
            button = Gtk.Button(
                halign=Gtk.Align.CENTER,
                css_classes=['suggested-action', 'pill'],
                child=Adw.ButtonContent(
                    label=_('Add new app'),
                    icon_name='list-add-symbolic'))
            
            button.connect('clicked', lambda _: self.emit('file-new'))
            self.empty_page.set_child(button)
        else:
            self.empty_page.set_description(_('Applications you install will appear here'))

        self.error_page = Adw.StatusPage(
            vexpand=True,
            title=_('Error loading apps'),
            icon_name='dialog-error-symbolic'
        )

        self.loading_page = Adw.StatusPage(
            vexpand=True,
            title=_('Loading apps…'),
            icon_name='go-back-symbolic')
        box = (self.loading_page
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

    def update_filled_page(self, rows: list[Gtk.ListBoxRow], sort=False):
        if sort and isinstance(rows[0], AppRow):
            rows = sorted(rows)

        listbox = Gtk.ListBox(
            selection_mode=Gtk.SelectionMode.NONE,
            css_classes=['boxed-list'])

        for row in rows:
            listbox.append(row)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.append(Adw.PreferencesGroup(
            description=self.description
        ))
        box.append(listbox)
        
        self.filled_page = Gtk.ScrolledWindow(
            vexpand=True,
            child=Adw.Clamp(
                margin_top=24,
                margin_bottom=24,
                margin_start=12,
                margin_end=12,
                child = box))

    def set_state(self, state: State):
        if state == self.state:
            return

        if state == State.FILLED:
            self.set_child(self.filled_page)
        elif state == State.EMPTY:
            self.set_child(self.empty_page)
        elif state == State.ERROR:
            self.set_child(self.error_page)
        elif state == State.LOADING:
            self.set_child(self.loading_page)

        self.state = state
        self.emit('state-changed')

class DesktopFilePoolView(AppsView):
    '''A widget that handles status pages for states and represents apps in a FolderGroup'''
    __gtype_name__ = 'FolderView'

    def __init__(self, pool: DesktopFilePool, description: str = '') -> None:
        self.pool = pool
        self.description = description
        super().__init__(isinstance(self.pool, WritableDesktopFilePool), self.description)

    def load_apps(self, loading_ok=True):
        if self.state == State.LOADING or loading_ok:
            return

        if self.pool._dirs:
            self.set_state(State.LOADING)

            def fill_group(files: list[DesktopFile]):
                if files:
                    rows = []

                    for file in files:
                        row = AppRow(file)
                        row.connect('file-open', lambda _, f: self.emit('file-open', f))
                        rows.append(row)

                    rows = sorted(rows)

                    self.update_filled_page(rows)
                    self.set_state(State.FILLED)
                else:
                    self.set_state(State.EMPTY)

            self.pool.files_async(callback=fill_group)
        else:
            self.set_state(State.ERROR)

class PinsView(DesktopFilePoolView):
    __gtype_name__ = 'PinsView'

    def __init__(self) -> None:
        super().__init__(USER_POOL)

class InstalledView(DesktopFilePoolView):
    __gtype_name__ = 'InstalledView'

    def __init__(self) -> None:
        super().__init__(SYSTEM_POOL)

class SearchView(AppsView):
    '''Adds all apps from both PinsView and InstalledView, adds chips to them and filters them on search'''
    __gtype_name__ = 'SearchView'

    source_views: list[DesktopFilePoolView]
    pools: list[DesktopFilePool]
    rows: list[AppRow] = []
    search_entry: Gtk.SearchEntry

    def __init__(self) -> None:
        super().__init__(show_new_file_button=False)

        # Override empty page with a more appropriate one
        self.empty_page = Adw.StatusPage(
            vexpand=True,
            title=_('No results found'),
            description=_('Try searching for something else'),
            icon_name='system-search-symbolic')

    def connect_entry(self, search_entry: Gtk.SearchEntry):
        self.search_entry = search_entry
        self.search_entry.connect('search-changed', lambda e: self.search(e.get_text()))

    def set_source_views(self, source_views: list[DesktopFilePoolView]):
        self.source_views = source_views

        self.pools = [v.pool for v in self.source_views]

        def state_changed_cb(view: DesktopFilePoolView):
            '''Updates search_map when all source_views are loaded'''
            if view.state == State.LOADING:
                self.set_state(State.LOADING)
            if all(map(lambda v: v.state != State.LOADING, self.source_views)):
                self.load_apps()
                self.search(self.search_entry.get_text())

        for v in self.source_views:
            v.connect('state-changed', state_changed_cb)


    def load_apps(self):
        self.rows = []
        self.set_state(State.LOADING)
        for g in self.pools:
            for f in g.files():
                row = AppRow(f)
                row.connect('file-open', lambda _, f: self.emit('file-open', f))
                if g == USER_POOL:
                    row.add_chip(AppChip.Pinned())

                self.rows.append(row)

        self.update_filled_page(self.rows, sort=True)
        self.set_state(State.FILLED)

    def search(self, query: str):
        if self.state == State.LOADING:
            return

        any_visible = False

        for r in self.rows:
            if query.lower() in r.file.search_str:
                r.set_visible(True)
                any_visible = True
            else:
                r.set_visible(False)

        if any_visible:
            self.set_state(State.FILLED)
        else:
            self.set_state(State.EMPTY)
