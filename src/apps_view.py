from gi.repository import Gtk, Gio, Adw, GObject
from pathlib import Path

from .desktop_entry import DesktopEntry, DesktopEntryFolder

@Gtk.Template(resource_path='/com/github/fabrialberio/pinapp/apps_view.ui')
class AppsView(Gtk.Box):
    __gtype_name__ = 'AppsView'

    new_file_button = Gtk.Template.Child('new_file_button')

    search_button = Gtk.Template.Child('search_button')
    search_bar = Gtk.Template.Child('search_bar')
    search_entry = Gtk.Template.Child('search_entry')

    user_button = Gtk.Template.Child('user_button')
    user_group = Gtk.Template.Child('user_group')
    system_group = Gtk.Template.Child('system_group')
    flatpak_group = Gtk.Template.Child('flatpak_group')

    def __init__(self, **kwargs):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, **kwargs)

        self.new_file_button.connect('clicked', lambda _: self.emit('file-new'))
        self.search_bar.set_key_capture_widget(self.get_root())
        self.search_bar.connect_entry(self.search_entry)

        self.user_button.connect('toggled', self._on_user_button_toggled)
        self.user_button.set_active(True)
        self.user_group.set_visible(True)

        GObject.type_register(AppsView)
        GObject.signal_new('file-new', AppsView, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ())
        GObject.signal_new('file-open', AppsView, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (GObject.TYPE_PYOBJECT,))

        GObject.type_register(AppsGroup)
        GObject.signal_new('file-open', AppsGroup, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (GObject.TYPE_PYOBJECT,))

        GObject.type_register(AppRow)
        GObject.signal_new('file-open', AppRow, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (GObject.TYPE_PYOBJECT,))

        self._update_group(
            self.user_group, 
            DesktopEntryFolder(DesktopEntryFolder.USER_APPLICATIONS))
        self._update_group(
            self.system_group, 
            DesktopEntryFolder(DesktopEntryFolder.SYSTEM_APPLICATIONS))
        self._update_group(
            self.flatpak_group, 
            DesktopEntryFolder(DesktopEntryFolder.FLATPAK_SYSTEM_APPLICATIONS))


    def update_user_group(self):
        self.search_bar.set_search_mode(False)

        if self.user_button.get_active() == True:
            self._update_group(
                self.user_group, 
                DesktopEntryFolder(DesktopEntryFolder.USER_APPLICATIONS))

    def _on_user_button_toggled(self, button):
        if self.user_button.get_active() == True:
            self.update_user_group()



    def _update_group(self, preferences_group: Adw.PreferencesGroup, folder: DesktopEntryFolder):
        listbox = (
            preferences_group
            .get_first_child()  # Main group GtkBox
            .get_last_child()   # GtkBox containing the listbox
            .get_first_child()) # GtkListbox

        old_children: list[Gtk.Widget] = []

        i = 0
        while listbox.get_row_at_index(i) is not None:
            old_children.append(listbox.get_row_at_index(i))
            i += 1

        for c in old_children:
            preferences_group.remove(c)

        folder.get_files()
        for file in folder.files:
            app_row = AppRow(file)
            app_row.connect('file_open', lambda _, f: self.emit('file-open', f))
            preferences_group.add(app_row)

class AppsGroup(Adw.PreferencesGroup):
    __gtype_name__ = 'AppsGroup'

    def __init__(self, folder: DesktopEntryFolder):        
        super().__init__(description = folder.path)

        self.folder = folder
        self.folder.get_files()

        for file in self.folder.files:
            app_row = AppRow(file)
            app_row.connect('file-open', lambda _, f: self.emit('file-open', f))

            self.add(app_row)


class AppRow(Adw.ActionRow):
    __gtype_name__ = 'AppRow'

    def __init__(self, file: DesktopEntry):
        super().__init__(
            title = file.appsection.Name.get(),
            subtitle = file.appsection.Comment.get(),
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
