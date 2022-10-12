from gi.repository import Gtk, Gio, Adw, GObject

from pathlib import Path

from .folders import FolderGroup, UserFolders, SystemFolders
from .desktop_entry import DesktopEntry
from .utils import escape_xml, set_icon_from_name

class AppRow(Adw.ActionRow):
    __gtype_name__ = 'AppRow'

    def __init__(self, file: DesktopEntry):
        self.file = file
        self.file.load()
        
        super().__init__(
            title = escape_xml(self.file.appsection.Name.as_str()),
            subtitle = escape_xml(self.file.appsection.Comment.as_str()),
            subtitle_lines = 2,
            activatable = True,)

        icon = Gtk.Image(
            pixel_size=32,
            margin_top=6,
            margin_bottom=6,
            opacity=.2 if file.appsection.NoDisplay.get() == True else 1,
            css_classes=['icon-dropshadow'])
        icon = set_icon_from_name(icon, file.appsection.Icon.get())


        self.add_prefix(icon)

        self.add_suffix(Gtk.Image(
            icon_name='go-next-symbolic',
            opacity=.6))

        self.connect('activated', lambda _: self.emit('file-open', file))

class AppsPage(Adw.Bin):
    __gtype_name__ = 'AppsPage'

    class State:
        FILLED = 'filled'
        EMPTY = 'empty'
        ERROR = 'error'
        LOADING = 'loading'

    def __init__(self, folder_group: FolderGroup) -> None:
        super().__init__()

        self.folder_group = folder_group
        self.state: AppsPage.State

        self._init_widgets()
        self._set_state(self.State.EMPTY)

    def load_apps(self, loading_ok=True):
        if self.state == self.State.LOADING or loading_ok:
            return

        if self.folder_group.any_exists:
            self._set_state(self.State.LOADING)

            def fill_group():
                if not self.folder_group.empty:
                    self.listbox = Gtk.ListBox(
                        selection_mode=Gtk.SelectionMode.NONE,
                        css_classes=['boxed-list'])
                
                    for file in self.folder_group.files:
                        row = AppRow(file)
                        row.connect('file-open', lambda _, f: self.emit('file-open', f))
                        self.listbox.append(row)
            
                    self._set_state(self.State.FILLED)
                else:
                    self._set_state(self.State.EMPTY)

            self.folder_group.get_files_async(callback=fill_group)
        else:
            self._set_state(self.State.ERROR)

    def _init_widgets(self):
        self.empty_page = Adw.StatusPage(
            vexpand=True,
            title=_('No apps found'),
            icon_name='folder-open-symbolic'
        )
        if self.folder_group.writable:
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

    def _set_state(self, state: 'AppsPage.State'):

        if state == self.State.FILLED:
            box = Gtk.Box(
                orientation=Gtk.Orientation.VERTICAL)
            box.append(self.listbox)

            self.set_child(
                Gtk.ScrolledWindow(
                    vexpand=True,
                    child=Adw.Clamp(
                        margin_top=24,
                        margin_bottom=24,
                        margin_start=12,
                        margin_end=12,
                        child = box)))
        elif state == self.State.EMPTY:
            self.set_child(self.empty_page)
        elif state == self.State.ERROR:
            self.set_child(self.error_page)
        elif state == self.State.LOADING:
            self.set_child(self.loading_page)
        
        self.state = state


class PinsView(AppsPage):
    __gtype_name__ = 'PinsView'

    def __init__(self) -> None:
        super().__init__(UserFolders())

        self.load_apps()

class InstalledView(AppsPage):
    __gtype_name__ = 'InstalledView'

    def __init__(self) -> None:
        super().__init__(SystemFolders())

        self.load_apps()