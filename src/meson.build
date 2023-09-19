pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
moduledir = join_paths(pkgdatadir, 'pinapp')

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', join_paths(get_option('prefix'), get_option('localedir')))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'pinapp.in',
  output: 'pinapp',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir')
)

subdir('ui')

pinapp_sources = [
  '__init__.py',
  'apps_page.py',
  'desktop_file.py',
  'file_page.py',
  'file_pools.py',
  'main.py',
  'utils.py',
  'window.py',
]

install_data(pinapp_sources, install_dir: moduledir)
