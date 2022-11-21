from gi.repository import Gtk, Adw, Pango

from enum import Enum

from .folders import FolderGroup, UserFolders, SystemFolders
from .desktop_entry import DesktopEntry
from .utils import *

class AppRow(Adw.ActionRow):
    __gtype_name__ = 'AppRow'

    def __init__(self, file: DesktopEntry):
        self.file = file
        self.file.load()

        super().__init__(
            title = escape_xml(self.file.appsection.Name.as_str()),
            title_lines = 1,
            subtitle = escape_xml(self.file.appsection.Comment.as_str()),
            subtitle_lines = 2,
            activatable = True,)

        icon = Gtk.Image(
            pixel_size=32,
            margin_top=6,
            margin_bottom=6,
            css_classes=['icon-dropshadow'])
        icon = set_icon_from_name(icon, file.appsection.Icon.as_str())

        if self.file.path.parent in [FLATPAK_SYSTEM_APPS, FLATPAK_USER_APPS]:
            self.add_chip(icon_name='flatpak-symbolic', color_css='chip-blue')
        if self.file.appsection.NoDisplay.as_bool() == True:
            icon.set_opacity(.2)
        if self.file.appsection.Terminal.as_bool() == True:
            self.add_chip(icon_name='utilities-terminal-symbolic', color_css='chip-gray')
            
        self.add_prefix(icon)

        self.add_suffix(Gtk.Image(
            icon_name='go-next-symbolic',
            opacity=.6))

        self.connect('activated', lambda _: self.emit('file-open', file))

    def add_chip(self, icon_name: str = None, label: str=None, color_css='chip-gray'):
        chip = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            valign=Gtk.Align.CENTER,
            spacing=8,
            css_classes=['chip-box', color_css],
        )
        if icon_name != None:
            chip.append(Gtk.Image(
                pixel_size=16,
                icon_name=icon_name))

        if label != None:
            label_attrs = Pango.AttrList()
            font_desc = Pango.FontDescription()
            font_desc.set_weight(Pango.Weight.BOLD)
            font_desc.set_variant(Pango.Variant.ALL_SMALL_CAPS)
            label_attrs.insert(Pango.AttrFontDesc.new(font_desc))

            chip.append(Gtk.Label(
                label=label,
                attributes=label_attrs))

        self.add_suffix(chip)

class State(Enum):
    FILLED = 'filled'
    EMPTY = 'empty'
    ERROR = 'error'
    LOADING = 'loading'

class AppsView(Adw.Bin):
    '''A widget that handles status pages for states'''
    __gtype_name__ = 'AppsPage'

    writable: bool
    state: State

    empty_page: Adw.StatusPage
    error_page: Adw.StatusPage
    loading_page: Adw.StatusPage
    filled_page: Gtk.Widget

    def __init__(self, writable: bool) -> None:
        super().__init__()

        self.writable = writable

        self._init_widgets()
        self._set_state(State.EMPTY)

    def _init_widgets(self):
        self.empty_page = Adw.StatusPage(
            vexpand=True,
            title=_('No apps found'),
            icon_name='folder-open-symbolic'
        )
        if self.writable:
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
            title=_('Loading apps...'),
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

    def _set_state(self, state: 'AppsView.State'):
        if state == State.FILLED:
            self.set_child(self.filled_page)
        elif state == State.EMPTY:
            self.set_child(self.empty_page)
        elif state == State.ERROR:
            self.set_child(self.error_page)
        elif state == State.LOADING:
            self.set_child(self.loading_page)
        
        self.state = state

    def load_apps(self, loading_ok=True):
        raise NotImplementedError

class FolderGroupView(AppsView):
    '''A widget that handles status pages for states and represents apps in a FolderGroup'''
    __gtype_name__ = 'FolderView'

    def __init__(self, folder_group: FolderGroup) -> None:
        self.folder_group = folder_group
        super().__init__(self.folder_group.writable)

    def load_apps(self, loading_ok=True):
        if self.state == State.LOADING or loading_ok:
            return

        if self.folder_group.any_exists:
            self._set_state(State.LOADING)

            def fill_group():
                if not self.folder_group.empty:
                    listbox = Gtk.ListBox(
                        selection_mode=Gtk.SelectionMode.NONE,
                        css_classes=['boxed-list'])
                
                    for file in self.folder_group.files:
                        row = AppRow(file)
                        row.connect('file-open', lambda _, f: self.emit('file-open', f))
                        listbox.append(row)

                    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                    box.append(listbox)

                    self.filled_page = Gtk.ScrolledWindow(
                        vexpand=True,
                        child=Adw.Clamp(
                            margin_top=24,
                            margin_bottom=24,
                            margin_start=12,
                            margin_end=12,
                            child = box))
                    self._set_state(State.FILLED)
                else:
                    self._set_state(State.EMPTY)

            self.folder_group.get_files_async(callback=fill_group)
        else:
            self._set_state(State.ERROR)

class SearchView(AppsView):
    __gtype_name__ = 'SearchView'

    def __init__(self) -> None:
        super().__init__(writable=False)

    def load_apps(self, loading_ok=True):
        if self.state == State.LOADING or loading_ok:
            ...


    def search(self, query: str):
        ...

class PinsView(FolderGroupView):
    __gtype_name__ = 'PinsView'

    def __init__(self) -> None:
        super().__init__(UserFolders())

        self.load_apps()

class InstalledView(FolderGroupView):
    __gtype_name__ = 'InstalledView'

    def __init__(self) -> None:
        super().__init__(SystemFolders())

        self.load_apps()