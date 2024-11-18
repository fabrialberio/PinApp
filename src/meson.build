pinapp_sources = [
  'main.c',
  'pinapp-application.c',
  'pinapp-window.c',
]

pinapp_deps = [
  dependency('gtk4'),
  dependency('libadwaita-1', version: '>= 1.4'),
]

pinapp_sources += gnome.compile_resources('pinapp-resources',
  'pinapp.gresource.xml',
  c_name: 'pinapp'
)

executable('pinapp', pinapp_sources,
  dependencies: pinapp_deps,
       install: true,
)
