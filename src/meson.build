pinapp_sources = [
    'main.c',
    'pins-app-icon.c',
    'pins-app-row.c',
    'pins-application.c',
    'pins-desktop-file.c',
    'pins-window.c',
]

pinapp_deps = [
    dependency('gtk4'),
    dependency('libadwaita-1', version: '>= 1.4'),
]

pinapp_sources += gnome.compile_resources('pins-resources', 'pins.gresource.xml', c_name: 'pins')

executable(
    'pinapp',
    pinapp_sources,
    dependencies: pinapp_deps,
    install: true,
)
