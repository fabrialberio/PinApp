from gi.repository import Gtk, Gio, Adw, GObject

from .desktop_entry import DesktopFile, DesktopFileFolder

@Gtk.Template(resource_path='/com/github/fabrialberio/pinapp/apps_view.ui')
class AppsView(Gtk.Box):
    __gtype_name__ = 'AppsView'

    new_file_button = Gtk.Template.Child('new_file_button')
    main_box = Gtk.Template.Child('main_box')

    DEFAULT_FOLDERS = [
        '~/.local/share/applications/',
        '/usr/share/applications/',
        #'/usr/local/share/applications/',
    ]

    def __init__(self, **kwargs):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, **kwargs)

        GObject.type_register(AppsView)
        GObject.signal_new('new-file', AppsView, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ())

        self.folders = [DesktopFileFolder(p) for p in self.DEFAULT_FOLDERS]
        self.new_file_button.connect('clicked', lambda _: self.emit('new-file'))

    def load_apps(self):
        for folder in self.folders:
            folder.get_files()

class AppsGroup(Adw.PreferencesGroup):
    __gtype_name__ = 'AppsGroup'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class AppRow(Adw.ActionRow):
    __gtype_name__ = 'AppRow'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)