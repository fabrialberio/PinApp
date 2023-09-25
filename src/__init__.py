from gi import require_version

require_version('GObject', '2.0')
require_version('Gio', '2.0')
require_version('Gtk', '4.0')
require_version('Gdk', '4.0')
require_version('Adw', '1')
require_version('Pango', '1.0')

from gi.repository import GObject, Gtk, Gdk

# Set icon search paths
from .utils import *

theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
paths = theme.get_search_path()
paths += [str(p) for p in ICON_PATHS]

theme.set_search_path(paths)

# Register all GOBject types
from .apps_page import AppRow, AppsView, PoolStateView, SearchView, AppListView, AppGridView, PinsView, InstalledView
from .file_page import FilePage, LocaleChooserRow, StringRow
from .window import PinAppWindow

GObject.type_register(AppRow)
GObject.type_register(AppsView)
GObject.type_register(AppListView)
GObject.type_register(AppGridView)
GObject.type_register(PoolStateView)
GObject.type_register(PinsView)
GObject.type_register(InstalledView)
GObject.type_register(SearchView)
GObject.type_register(StringRow)
GObject.type_register(LocaleChooserRow)
GObject.type_register(FilePage)
GObject.type_register(PinAppWindow)

GObject.signal_new('file-open', AppRow, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (GObject.TYPE_PYOBJECT,))
GObject.signal_new('file-open', AppsView, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (GObject.TYPE_PYOBJECT,))
GObject.signal_new('state-changed', PoolStateView, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ())

GObject.signal_new('file-leave', FilePage, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ())
GObject.signal_new('file-changed', FilePage, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ())
GObject.signal_new('add-string-field', FilePage, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ())
GObject.signal_new('add-bool-field', FilePage, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ())