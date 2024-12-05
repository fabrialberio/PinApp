/* pins-app-iterator.c
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

#include "pins-app-iterator.h"
#include "pins-desktop-file.h"
#include "pins-directories.h"

#define DESKTOP_FILE_CONTENT_TYPE "application/x-desktop"
#define DIR_LIST_FILE_ATTRIBUTES                                              \
    g_strjoin (",", G_FILE_ATTRIBUTE_STANDARD_CONTENT_TYPE,                   \
               G_FILE_ATTRIBUTE_STANDARD_DISPLAY_NAME,                        \
               G_FILE_ATTRIBUTE_STANDARD_EDIT_NAME, NULL)

gboolean
pins_app_iterator_filter_match_func (gpointer file_info, gpointer user_data)
{
    g_assert (G_IS_FILE_INFO (file_info));

    // TODO: Remove duplicate files
    return g_strcmp0 (g_file_info_get_content_type (file_info),
                      DESKTOP_FILE_CONTENT_TYPE)
           == 0;
}

gpointer
pins_app_iterator_map_func (gpointer file_info, gpointer user_data)
{
    PinsDesktopFile *desktop_file;
    GError *err = NULL;
    GFile *file;

    g_assert (G_IS_FILE_INFO (file_info));

    file = G_FILE (g_file_info_get_attribute_object (G_FILE_INFO (file_info),
                                                     "standard::file"));

    desktop_file = pins_desktop_file_new_from_file (file, &err);
    if (err != NULL)
        {
            g_warning ("Could not load desktop file at `%s`",
                       g_file_get_path (file));
        }

    return desktop_file;
}

int
pins_app_iterator_sort_compare_func (gconstpointer a, gconstpointer b,
                                     gpointer user_data)
{
    PinsDesktopFile *first = PINS_DESKTOP_FILE ((gpointer)a);
    PinsDesktopFile *second = PINS_DESKTOP_FILE ((gpointer)b);
    const gchar *first_name, *second_name;

    g_assert (PINS_IS_DESKTOP_FILE (first));
    g_assert (PINS_IS_DESKTOP_FILE (second));

    first_name = pins_desktop_file_get_string (
        first, G_KEY_FILE_DESKTOP_KEY_NAME, NULL);
    second_name = pins_desktop_file_get_string (
        second, G_KEY_FILE_DESKTOP_KEY_NAME, NULL);

    return g_strcmp0 (first_name, second_name);
}

GListModel *
pins_app_iterator_new_from_directory_list (GListModel *dir_list)
{
    GtkFilterListModel *filter_model;
    GtkMapListModel *map_model;
    GtkSortListModel *sort_model;

    filter_model = gtk_filter_list_model_new (
        dir_list, GTK_FILTER (gtk_custom_filter_new (
                      &pins_app_iterator_filter_match_func, NULL, NULL)));

    map_model = gtk_map_list_model_new (
        G_LIST_MODEL (filter_model), &pins_app_iterator_map_func, NULL, NULL);

    sort_model = gtk_sort_list_model_new (
        G_LIST_MODEL (map_model),
        GTK_SORTER (gtk_custom_sorter_new (pins_app_iterator_sort_compare_func,
                                           NULL, NULL)));

    return G_LIST_MODEL (sort_model);
}

GListModel *
pins_app_iterator_new_from_paths (gchar **paths)
{
    GListStore *dir_list_store;
    GtkFlattenListModel *flattened_dir_list;

    dir_list_store = g_list_store_new (GTK_TYPE_DIRECTORY_LIST);

    for (int i = 0; i < g_strv_length (paths); i++)
        {
            GFile *file = g_file_new_for_path (paths[i]);
            GtkDirectoryList *dir_list
                = gtk_directory_list_new (DIR_LIST_FILE_ATTRIBUTES, file);

            g_list_store_append (dir_list_store, dir_list);

            // TODO: Connect notify::loading signals here
        }
    flattened_dir_list
        = gtk_flatten_list_model_new (G_LIST_MODEL (dir_list_store));

    return pins_app_iterator_new_from_directory_list (
        G_LIST_MODEL (flattened_dir_list));
}
