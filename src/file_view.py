from gi.repository import Gtk, Gio, Adw

@Gtk.Template(resource_path='/com/github/fabrialberio/pinapp/file_view.ui')
class FileView(Gtk.Box):
    __gtype_name__ = 'FileView'
    
    def __init__(self, **kwargs):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, **kwargs)