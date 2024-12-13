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

struct _PinsAppIterator
{
    GObject parent_instance;

    gchar **duplicates;
    GtkFilter *filter;
    GListModel *model;
};

static void list_model_iface_init (GListModelInterface *iface);

G_DEFINE_TYPE_WITH_CODE (PinsAppIterator, pins_app_iterator, G_TYPE_OBJECT,
                         G_IMPLEMENT_INTERFACE (G_TYPE_LIST_MODEL,
                                                list_model_iface_init))

enum
{
    LOADED,
    N_SIGNALS
};

static guint signals[N_SIGNALS];

PinsAppIterator *
pins_app_iterator_new (void)
{
    return g_object_new (PINS_TYPE_APP_ITERATOR, NULL);
}

static void
pins_app_iterator_update_duplicates (GListModel *model, guint position,
                                     guint removed, guint added,
                                     gpointer user_data)
{
    PinsAppIterator *self = PINS_APP_ITERATOR (user_data);
    GStrvBuilder *strv_builder = g_strv_builder_new ();

    gchar *unique_filenames[g_list_model_get_n_items (model)] = {};
    gsize n_unique_filenames = 0;

    for (int i = 0; i < g_list_model_get_n_items (model); i++)
        {
            GFile *file = G_FILE (g_file_info_get_attribute_object (
                G_FILE_INFO (g_list_model_get_item (model, i)),
                "standard::file"));

            if (g_strv_contains ((const gchar *const *)unique_filenames,
                                 g_file_get_basename (file)))
                {
                    g_strv_builder_add (strv_builder, g_file_get_path (file));
                }
            else
                {
                    unique_filenames[n_unique_filenames]
                        = g_file_get_basename (file);
                    n_unique_filenames++;
                }
        }

    self->duplicates = g_strv_builder_end (strv_builder);

    gtk_filter_changed (self->filter, GTK_FILTER_CHANGE_DIFFERENT);
}

gboolean
pins_app_iterator_filter_match_func (gpointer file_info, gpointer user_data)
{
    GFile *file;
    PinsAppIterator *self = PINS_APP_ITERATOR (user_data);
    gboolean is_desktop_file, is_duplicate = FALSE;

    g_assert (G_IS_FILE_INFO (file_info));

    file = G_FILE (
        g_file_info_get_attribute_object (file_info, "standard::file"));

    is_desktop_file = g_strcmp0 (g_file_info_get_content_type (file_info),
                                 DESKTOP_FILE_CONTENT_TYPE)
                      == 0;
    is_duplicate = g_strv_contains ((const gchar *const *)self->duplicates,
                                    g_file_get_path (file));

    return is_desktop_file && !is_duplicate;
}

gpointer
pins_app_iterator_map_func (gpointer file_info, gpointer user_data)
{
    PinsDesktopFile *desktop_file;
    GError *err = NULL;
    GFile *file;

    g_assert (G_IS_FILE_INFO (file_info));

    file = G_FILE (
        g_file_info_get_attribute_object (file_info, "standard::file"));

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

void
pins_app_iterator_set_directory_list (PinsAppIterator *self,
                                      GListModel *dir_list)
{
    GtkFilterListModel *filter_model;
    GtkMapListModel *map_model;
    GtkSortListModel *sort_model;

    g_signal_connect (G_LIST_MODEL (dir_list), "items-changed",
                      G_CALLBACK (pins_app_iterator_update_duplicates), self);

    filter_model
        = gtk_filter_list_model_new (G_LIST_MODEL (dir_list), self->filter);
    gtk_filter_list_model_set_incremental (filter_model, TRUE);

    map_model = gtk_map_list_model_new (
        G_LIST_MODEL (filter_model), &pins_app_iterator_map_func, NULL, NULL);

    sort_model = gtk_sort_list_model_new (
        G_LIST_MODEL (map_model),
        GTK_SORTER (gtk_custom_sorter_new (pins_app_iterator_sort_compare_func,
                                           NULL, NULL)));

    g_signal_connect_swapped (G_LIST_MODEL (sort_model), "items-changed",
                              G_CALLBACK (g_list_model_items_changed), self);

    self->model = G_LIST_MODEL (sort_model);
}

typedef struct
{
    PinsAppIterator *app_iterator;
    guint path_index;
    guint n_paths;
    gboolean *loaded_paths;
} dir_list_loaded_cb_data;

void
pins_app_iterator_dir_list_loaded_cb (GtkDirectoryList *self,
                                      GParamSpec *pspec,
                                      dir_list_loaded_cb_data *user_data)
{
    g_assert (PINS_IS_APP_ITERATOR (user_data->app_iterator));

    user_data->loaded_paths[user_data->path_index] = TRUE;

    for (int i = 0; i < user_data->n_paths; i++)
        {
            if (user_data->loaded_paths[i] == FALSE)
                {
                    free (user_data);
                    return;
                }
        }

    g_signal_emit (user_data->app_iterator, signals[LOADED], 0);
    free (user_data->loaded_paths);
    g_free (user_data);
}

void
pins_app_iterator_set_paths (PinsAppIterator *self, gchar **paths)
{
    guint n_paths = g_strv_length (paths);
    gboolean *loaded_paths = calloc (n_paths, sizeof (gboolean));

    GListStore *dir_list_store;
    GtkFlattenListModel *flattened_dir_list;

    dir_list_store = g_list_store_new (GTK_TYPE_DIRECTORY_LIST);

    for (int i = 0; i < n_paths; i++)
        {
            dir_list_loaded_cb_data *data;
            GFile *file = g_file_new_for_path (paths[i]);
            GtkDirectoryList *dir_list
                = gtk_directory_list_new (DIR_LIST_FILE_ATTRIBUTES, file);

            g_list_store_append (dir_list_store, dir_list);

            data = g_malloc (sizeof (dir_list_loaded_cb_data));
            data->app_iterator = self;
            data->loaded_paths = loaded_paths;
            data->n_paths = n_paths;
            data->path_index = i;

            g_signal_connect (
                dir_list, "notify::loading",
                G_CALLBACK (pins_app_iterator_dir_list_loaded_cb), data);
        }

    flattened_dir_list
        = gtk_flatten_list_model_new (G_LIST_MODEL (dir_list_store));

    pins_app_iterator_set_directory_list (self,
                                          G_LIST_MODEL (flattened_dir_list));
}

static void
pins_app_iterator_class_init (PinsAppIteratorClass *klass)
{
    signals[LOADED] = g_signal_new ("loaded", G_TYPE_FROM_CLASS (klass),
                                    G_SIGNAL_RUN_FIRST, 0, NULL, NULL, NULL,
                                    G_TYPE_NONE, 0);
}

static void
pins_app_iterator_init (PinsAppIterator *self)
{
    self->filter = GTK_FILTER (gtk_custom_filter_new (
        &pins_app_iterator_filter_match_func, self, NULL));
}

gpointer
pins_app_iterator_get_item (GListModel *list, guint position)
{
    PinsAppIterator *self = PINS_APP_ITERATOR (list);

    return g_list_model_get_item (self->model, position);
}

GType
pins_app_iterator_get_item_type (GListModel *list)
{
    return PINS_TYPE_DESKTOP_FILE;
}

guint
pins_app_iterator_get_n_items (GListModel *list)
{
    PinsAppIterator *self = PINS_APP_ITERATOR (list);

    return g_list_model_get_n_items (self->model);
}

static void
list_model_iface_init (GListModelInterface *iface)
{
    iface->get_item = pins_app_iterator_get_item;
    iface->get_item_type = pins_app_iterator_get_item_type;
    iface->get_n_items = pins_app_iterator_get_n_items;
}
