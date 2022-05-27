from gi.repository import Gtk, Gio, Adw, GObject

from .desktop_entry import DesktopFile

@Gtk.Template(resource_path='/com/github/fabrialberio/pinapp/file_view.ui')
class FileView(Gtk.Box):
    __gtype_name__ = 'FileView'
    
    back_button = Gtk.Template.Child('back_button')
    save_button = Gtk.Template.Child('save_button')

    def __init__(self, **kwargs):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, **kwargs)

        GObject.type_register(FileView)
        GObject.signal_new('go-back', FileView, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ())
        GObject.signal_new('save', FileView, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ())

        self.back_button.connect('clicked', lambda _: self.emit('go-back'))
        self.save_button.connect('clicked', lambda _: self.emit('save'))
    
    def load_file(self, file: DesktopFile): ...