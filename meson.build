project(
  'PinApp',
  version: '1.2.1',
  meson_version: '>= 0.59.0',
  default_options: [
    'warning_level=2',
    'werror=false',],)

gnome = import('gnome')
i18n = import('i18n')

subdir('data')
subdir('src')
subdir('po')

gnome.post_install(
  glib_compile_schemas: true,
  gtk_update_icon_cache: true,
  update_desktop_database: true,)