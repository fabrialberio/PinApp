from gi.repository import Gtk, Gio, Adw, GObject

from .desktop_entry import DesktopFile

@Gtk.Template(resource_path='/com/github/fabrialberio/pinapp/file_view.ui')
class FileView(Gtk.Box):
    __gtype_name__ = 'FileView'
    
    back_button = Gtk.Template.Child('back_button')
    save_button = Gtk.Template.Child('save_button')

    app_icon = Gtk.Template.Child('app_icon')
    app_name = Gtk.Template.Child('app_name')
    app_comment = Gtk.Template.Child('app_comment')

    main_view = Gtk.Template.Child('main_box')


    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)

        self.file = None

        GObject.type_register(FileView)
        GObject.signal_new('file-back', FileView, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ())
        GObject.signal_new('file-save', FileView, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ())
        GObject.signal_new('file-edit', FileView, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ())

        self.back_button.connect('clicked', lambda _: self.emit('file-back'))
        self.save_button.connect('clicked', lambda _: self.emit('file-save'))
    
    def load_file(self, file: DesktopFile):
        self.file = file
        self.build_ui()

    def build_ui(self):
        if self.file:
            self.save_button.set_sensitive(True)
        else:
            self.save_button.set_sensitive(False)

class EntryRow(Adw.ActionRow):
    def __init__(self, title) -> None:
        super().__init__()