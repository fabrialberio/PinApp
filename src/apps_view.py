from gi.repository import Gtk, Gio, Adw, GObject
from pathlib import Path

from .desktop_entry import DesktopEntry
from .folders import UserFolders, SystemFolders, FolderGroup, DesktopEntryFolder

class AppRow(Adw.ActionRow):
    __gtype_name__ = 'AppRow'

    def __init__(self, file: DesktopEntry):
        self.file = file
        self.file.load()
        
        super().__init__(
            title = self.file.appsection.Name.get(),
            subtitle = self.file.appsection.Comment.get(),
            activatable = True,)

        icon = Gtk.Image(
            pixel_size=32,
            margin_top=6,
            margin_bottom=6,
            css_classes=['icon-dropshadow'])
        
        icon_name = file.appsection.Icon.get()
        if icon_name == None:
            icon.set_from_icon_name('image-missing')
        elif Path(icon_name).exists():
            icon.set_from_file(icon_name)
        else:
            icon.set_from_icon_name(icon_name)

        self.add_prefix(icon)

        self.add_suffix(Gtk.Image(
            icon_name='go-next-symbolic',
            opacity=.6))

        self.connect('activated', lambda _: self.emit('file-open', file))

class AppCategory(Adw.Bin):
    __gtype_name__ = 'AppCategory'

    class State:
        FILLED = 0
        EMPTY = 1
        ERROR = 2
        LOADING = 3

    def __init__(self, folders: FolderGroup) -> None:
        super().__init__()

        self.folders = folders
        self.state = self.State.LOADING

        self.listbox: Gtk.ListBox

        self.empty_page = Adw.StatusPage(
            vexpand=True,
            hexpand=True,
            title=_('This folder is empty'),
            icon_name='folder-open-symbolic'
        )
        if self.folders.writable:
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
            hexpand=True,
            title=_('Error loading apps'),
            icon_name='dialog-error-symbolic'
        )

        self.loading_page = Adw.StatusPage(
            vexpand=True,
            hexpand=True,
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
    
    def update_apps(self):
        if self.folders.exists:
            self._set_state(self.State.LOADING)

            def fill_group():
                if not self.folders.empty:
                    self.listbox = Gtk.ListBox(
                        selection_mode=Gtk.SelectionMode.NONE,
                        css_classes=['boxed-list'])
                
                    for file in self.folders.files:
                        row = AppRow(file)
                        row.connect('file-open', lambda _, f: self.emit('file-open', f))
                        self.listbox.append(row)
            
                    self._set_state(self.State.FILLED)
                else:
                    self._set_state(self.State.EMPTY)

            self.folders.get_files_async(callback=fill_group)
        else:
            self._set_state(self.State.ERROR)

    def _set_state(self, state: 'AppCategory.State'):
        if state == self.State.FILLED:
            self.set_child(self.listbox)
        elif state == self.State.EMPTY:
            self.set_child(self.empty_page)
        elif state == self.State.ERROR:
            self.set_child(self.error_page)
        elif state == self.State.LOADING:
            self.set_child(self.loading_page)
        
        self.state = state


@Gtk.Template(resource_path='/io/github/fabrialberio/pinapp/apps_view.ui')
class AppsView(Gtk.Box):
    __gtype_name__ = 'AppsView'

    new_file_button = Gtk.Template.Child('new_file_button')

    user_button = Gtk.Template.Child('user_button')
    user_bin = Gtk.Template.Child('user_bin')
    system_bin = Gtk.Template.Child('system_bin')

    def __init__(self, **kwargs):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, **kwargs)

        GObject.type_register(AppsView)
        GObject.signal_new('file-open', AppsView, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (GObject.TYPE_PYOBJECT,))

        GObject.type_register(AppRow)
        GObject.signal_new('file-open', AppRow, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (GObject.TYPE_PYOBJECT,))

        GObject.type_register(AppCategory)
        GObject.signal_new('file-open', AppCategory, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (GObject.TYPE_PYOBJECT,))
        GObject.signal_new('file-new', AppCategory, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ())

        self.user_apps = AppCategory(UserFolders())
        self.system_apps = AppCategory(SystemFolders())
        self.user_bin.set_child(self.user_apps)
        self.system_bin.set_child(self.system_apps)

        self.user_apps.connect('file-new', lambda _: self.new_file())
        self.new_file_button.connect('clicked', lambda _: self.new_file())
        
        self.user_apps.connect('file-open', lambda _, f: self.emit('file-open', f))
        self.system_apps.connect('file-open', lambda _, f: self.emit('file-open', f))

        self.update_all_apps()

    @property
    def loading(self):
        return any(map(
            lambda a: a.state == AppCategory.State.LOADING,
            (self.user_apps, self.system_apps)))

    @property
    def visible(self):
        return isinstance(self.get_parent().get_visible_child(), AppsView)

    def new_file(self):
        if not self.visible:
            return

        builder = Gtk.Builder.new_from_resource('/io/github/fabrialberio/pinapp/apps_view_dialogs.ui')
        dialog = builder.get_object('filename_dialog')
        name_entry = builder.get_object('name_entry')

        def path_is_valid() -> bool:
            path = name_entry.get_text()
            if '/' in path:
                return False
            else:
                return True

        name_entry.connect('changed', lambda _: dialog.set_response_enabled(
            'create',
            path_is_valid()))

        def callback(widget, resp):
            if resp == 'create':
                path = DesktopEntryFolder.USER / Path(f'{Path(name_entry.get_text())}.desktop')
                file = DesktopEntry.new_with_defaults(path)

                self.emit('file-open', file)

        dialog.connect('response', callback)
        dialog.set_transient_for(self.get_root())
        dialog.show()

    def update_user_apps(self):
        self.user_apps.update_apps()

    def update_all_apps(self):
        self.user_apps.update_apps()
        self.system_apps.update_apps()