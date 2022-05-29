from gi.repository import Gtk, Gio, Adw, GObject

from .desktop_entry import DesktopFile, DesktopFileFolder

@Gtk.Template(resource_path='/com/github/fabrialberio/pinapp/apps_view.ui')
class AppsView(Gtk.Box):
    __gtype_name__ = 'AppsView'

    new_file_button = Gtk.Template.Child('new_file_button')
    main_view = Gtk.Template.Child('main_clamp')

    DEFAULT_FOLDERS = [
        '~/.local/share/applications/',
        '/usr/share/applications/',
        #'/usr/local/share/applications/',
    ]

    def __init__(self, **kwargs):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, **kwargs)

        GObject.type_register(AppsView)
        GObject.signal_new('file-new', AppsView, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ())

        self.folders = [DesktopFileFolder(p) for p in self.DEFAULT_FOLDERS]
        self.new_file_button.connect('clicked', lambda _: self.emit('file-new'))

        self.build_ui()


    def load_apps(self):
        for folder in self.folders:
            folder.get_files()

        self.build_ui()

    def build_ui(self):
        box = Gtk.Box(
            orientation = Gtk.Orientation.VERTICAL,
            margin_top = 6,
            margin_bottom = 6,
            margin_start = 12,
            margin_end = 12,
            spacing = 12,
        )

        for folder in self.folders:
            box.append(AppsGroup(folder))

        self.main_view.set_child(box)


class AppsGroup(Adw.PreferencesGroup):
    __gtype_name__ = 'AppsGroup'

    def __init__(self, folder: DesktopFileFolder):
        super().__init__(
            title = str(folder.path),
        )

        self.folder = folder
        self.folder.get_files()

        for file in self.folder.files:
            app_row = AppRow(file)
            app_row.connect('activated', lambda _: self.emit('file-open', file))

            self.add(app_row)
        
        

class AppRow(Adw.ActionRow):
    __gtype_name__ = 'AppRow'

    def __init__(self, file: DesktopFile):
        super().__init__(
            icon_name = file.app_dict.get(DesktopFile.ICON_KEY),
            title = file.app_dict.get(DesktopFile.APP_NAME_KEY),
            subtitle = file.app_dict.get(DesktopFile.COMMENT_KEY),
        )