from gi.repository import Gtk, Gio, Adw, GObject

from .desktop_entry import DesktopFile, DesktopFileFolder

@Gtk.Template(resource_path='/com/github/fabrialberio/pinapp/apps_view.ui')
class AppsView(Gtk.Box):
    __gtype_name__ = 'AppsView'

    new_file_button = Gtk.Template.Child('new_file_button')
    main_view = Gtk.Template.Child('main_clamp')

    def __init__(self, **kwargs):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, **kwargs)
        self.folders = DesktopFileFolder.list_from_recognized()

        self.new_file_button.connect('clicked', lambda _: self.emit('file-new'))

        GObject.type_register(AppsView)
        GObject.signal_new('file-new', AppsView, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ())
        GObject.signal_new('file-open', AppsView, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (GObject.TYPE_PYOBJECT,))

        GObject.type_register(AppsGroup)
        GObject.signal_new('file-open', AppsGroup, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (GObject.TYPE_PYOBJECT,))

        GObject.type_register(AppRow)
        GObject.signal_new('file-open', AppRow, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (GObject.TYPE_PYOBJECT,))

        self.build_ui()

    def build_ui(self):
        box = Gtk.Box(
            orientation = Gtk.Orientation.VERTICAL,
            margin_top = 24,
            margin_bottom = 24,
            margin_start = 12,
            margin_end = 12,
            spacing = 24,)

        for folder in self.folders:
            apps_group = AppsGroup(folder)
            apps_group.connect('file-open', lambda _, file: self.emit('file-open', file))
            box.append(apps_group)

        self.main_view.set_child(box)


class AppsGroup(Adw.PreferencesGroup):
    __gtype_name__ = 'AppsGroup'

    def __init__(self, folder: DesktopFileFolder):        
        super().__init__(description = folder.path)

        self.folder = folder
        self.folder.get_files()

        for file in self.folder.files:
            app_row = AppRow(file)
            app_row.connect('file-open', lambda _, f: self.emit('file-open', f))

            self.add(app_row)


class AppRow(Adw.ActionRow):
    __gtype_name__ = 'AppRow'

    def __init__(self, file: DesktopFile):
        super().__init__(
            title = file.appsection.Name.get(),
            subtitle = file.appsection.Comment.get(),
            activatable = True,)

        self.add_prefix(Gtk.Image(
            icon_name = file.appsection.Icon.get() or 'image-missing',
            css_classes=['icon-dropshadow'],))

        self.add_suffix(Gtk.Image(
            icon_name='go-next-symbolic',
            opacity=.6))

        self.connect('activated', lambda _: self.emit('file-open', file))
