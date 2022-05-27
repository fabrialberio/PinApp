# window.py
#
# Copyright 2022 Fabri210
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

#from apps_view import AppsView

from gi.repository import Gtk, Adw

from .apps_view import AppsView
from .file_view import FileView

@Gtk.Template(resource_path='/com/github/fabrialberio/pinapp/window.ui')
class PinAppWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'PinAppWindow'

    leaflet = Gtk.Template.Child('main_leaflet')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.leaflet.append(AppsView())
        self.leaflet.append(FileView())
        self.leaflet.navigate(Adw.NavigationDirection.FORWARD)

class AboutDialog(Gtk.AboutDialog):

    def __init__(self, parent):
        Gtk.AboutDialog.__init__(self)
        self.props.program_name = 'PinApp'
        self.props.version = '0.1.0'
        self.props.authors = ['Fabrizio Alberio']
        self.props.copyright = '2022 Fabrizio Alberio'
        self.props.logo_icon_name = 'com.github.fabrialberio.pinapp'
        self.props.modal = True
        self.set_transient_for(parent)
