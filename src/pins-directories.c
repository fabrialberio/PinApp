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
    return g_strjoin ("/", g_get_home_dir (), ".local/share", NULL);
}

gchar *
pins_user_app_path (void)
{
    return g_strjoin ("/", pins_user_data_path (), "applications", NULL);
}

gchar **
pins_system_app_paths (void)
{
    // clang-format off
    const gchar *paths[]
        = { "/run/host/usr/share/applications",
            "/usr/share/applications",
            "/var/lib/flatpak/exports/share/applications",
            g_strjoin ("/", pins_user_data_path (),
                       "flatpak/exports/share", "applications", NULL),
            "/var/lib/snapd/desktop/applications",
            NULL };
    // clang-format on

    GStrvBuilder *strv_builder = g_strv_builder_new ();

    g_strv_builder_addv (strv_builder, paths);
    g_strv_builder_addv (strv_builder,
                         (const gchar **)g_get_system_data_dirs ());

    return g_strv_builder_end (strv_builder);
}

gchar **
pins_all_app_paths (void)
{
    GStrvBuilder *strv_builder = g_strv_builder_new ();

    g_strv_builder_add (strv_builder, pins_user_app_path ());
    g_strv_builder_addv (strv_builder,
                         (const gchar **)pins_system_app_paths ());

    return g_strv_builder_end (strv_builder);
}

void
pins_icon_theme_inject_search_paths (GtkIconTheme *theme)
{
    // clang-format off
    const gchar * paths[]
        = { "/run/host/usr/share/icons",
            "/var/lib/flatpak/exports/share/icons",
            g_strjoin ("/", pins_user_data_path (),
                        "flatpak/exports/share", "icons", NULL), 
            NULL };
    // clang-format on

    GStrvBuilder *strv_builder = g_strv_builder_new ();
    g_strv_builder_addv (strv_builder, paths);
    g_strv_builder_addv (strv_builder,
                         (const gchar **)g_get_system_data_dirs ());
    g_strv_builder_addv (
        strv_builder, (const gchar **)gtk_icon_theme_get_search_path (theme));

    gtk_icon_theme_set_search_path (
        theme, (const gchar *const *)g_strv_builder_end (strv_builder));
}
