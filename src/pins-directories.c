/* pins-directories.h
 *
 * Copyright 2024 Fabrizio
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#include "pins-directories.h"

gchar *
pins_user_data_path (void)
{
    return g_build_filename (g_get_home_dir (), ".local/share", NULL);
}

gchar *
pins_desktop_file_user_path (void)
{
    return g_build_filename (pins_user_data_path (), "applications", NULL);
}

gchar *
pins_desktop_file_autostart_path (void)
{
    return g_build_filename (g_get_home_dir (), ".config/autostart", NULL);
}

gchar **
pins_search_paths (void)
{
    GStrvBuilder *builder = g_strv_builder_new ();

    g_strv_builder_add_many (builder, "/usr/share", "/run/host/usr/share",
                             "/var/lib/flatpak/exports/share",
                             g_build_filename (pins_user_data_path (),
                                               "flatpak/exports/share", NULL),
                             "/var/lib/snapd/desktop/", NULL);

    return g_strv_builder_end (builder);
}

gchar **
pins_desktop_file_search_paths (void)
{
    GStrvBuilder *builder = g_strv_builder_new ();
    g_auto (GStrv) search_paths = pins_search_paths ();

    for (int i = 0; i < g_strv_length (search_paths); i++)
        g_strv_builder_add (
            builder, g_build_filename (search_paths[i], "applications", NULL));

    g_strv_builder_add (builder, pins_desktop_file_user_path ());

    return g_strv_builder_end (builder);
}

void
pins_environ_inject_search_paths (void)
{
    g_setenv ("XDG_DATA_DIRS",
              g_strjoin (":", g_getenv ("XDG_DATA_DIRS"),
                         g_strjoinv (":", pins_search_paths ()), NULL),
              TRUE);
}
