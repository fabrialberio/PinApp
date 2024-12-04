/* pins-window.c
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

#include "pins-window.h"

#include "pins-app-list.h"
#include "pins-app-row.h"

struct _PinsWindow
{
    AdwApplicationWindow parent_instance;

    /* Template widgets */
    GtkButton *new_file_button;
    GtkToggleButton *search_button;
    PinsAppList *app_list;
};

G_DEFINE_FINAL_TYPE (PinsWindow, pins_window, ADW_TYPE_APPLICATION_WINDOW)

static void
pins_window_dispose (GObject *object)
{
    gtk_widget_dispose_template (GTK_WIDGET (object), PINS_TYPE_WINDOW);

    G_OBJECT_CLASS (pins_window_parent_class)->dispose (object);
}

static void
pins_window_class_init (PinsWindowClass *klass)
{
    GObjectClass *object_class = G_OBJECT_CLASS (klass);
    GtkWidgetClass *widget_class = GTK_WIDGET_CLASS (klass);

    object_class->dispose = pins_window_dispose;

    gtk_widget_class_set_template_from_resource (
        widget_class, "/io/github/fabrialberio/pinapp/pins-window.ui");
    g_type_ensure (PINS_TYPE_APP_LIST);
    g_type_ensure (PINS_TYPE_APP_ROW);

    gtk_widget_class_bind_template_child (widget_class, PinsWindow,
                                          new_file_button);
    gtk_widget_class_bind_template_child (widget_class, PinsWindow,
                                          search_button);
    gtk_widget_class_bind_template_child (widget_class, PinsWindow, app_list);
}

static void
pins_window_init (PinsWindow *self)
{
    GFile *file;
    GtkDirectoryList *dir_list;

    const gchar *ATTRIBUTES
        = g_strjoin (",", G_FILE_ATTRIBUTE_STANDARD_CONTENT_TYPE,
                     G_FILE_ATTRIBUTE_STANDARD_DISPLAY_NAME,
                     G_FILE_ATTRIBUTE_STANDARD_EDIT_NAME, NULL);

    gtk_widget_init_template (GTK_WIDGET (self));

    file = g_file_new_for_path ("/home/fabri/.local/share/applications");
    dir_list = gtk_directory_list_new (ATTRIBUTES, file);

    pins_app_list_set_directory_list (self->app_list, dir_list);
}
