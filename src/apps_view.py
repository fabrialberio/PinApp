from gi.repository import Gtk, Gio, Adw

@Gtk.Template(resource_path='/com/github/fabrialberio/pinapp/apps_view.ui')
class AppsView(Gtk.Box):
    __gtype_name__ = 'AppsView'
    
    def __init__(self, leaflet, **kwargs):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, **kwargs)

        self.leaflet = leaflet
        print(self.leaflet)