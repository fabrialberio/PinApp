/* pins-file-view.c
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

#include "pins-file-view.h"

#include "pins-app-icon.h"
#include "pins-key-row.h"

struct _PinsFileView
{
    AdwBin parent_instance;

    PinsAppIcon *icon;
    PinsKeyRow *name_row;
    PinsKeyRow *comment_row;
    GtkListBox *keys_listbox;
};

G_DEFINE_TYPE (PinsFileView, pins_file_view, ADW_TYPE_BIN);

void
pins_file_view_set_desktop_file (PinsFileView *self,
                                 PinsDesktopFile *desktop_file)
{
    gchar **keys;

    gtk_list_box_remove_all (self->keys_listbox);

    pins_app_icon_set_desktop_file (self->icon, desktop_file);

    pins_key_row_set_key (self->name_row, desktop_file,
                          G_KEY_FILE_DESKTOP_KEY_NAME);
    pins_key_row_set_key (self->comment_row, desktop_file,
                          G_KEY_FILE_DESKTOP_KEY_COMMENT);

    keys = pins_desktop_file_get_keys (desktop_file);

    for (int i = 0; keys[i] != NULL; i++)
        {
            PinsKeyRow *row = pins_key_row_new ();
            pins_key_row_set_key (row, desktop_file, keys[i]);

            gtk_list_box_append (self->keys_listbox, GTK_WIDGET (row));
        }
}

static void
pins_file_view_dispose (GObject *object)
{
    gtk_widget_dispose_template (GTK_WIDGET (object), PINS_TYPE_FILE_VIEW);

    G_OBJECT_CLASS (pins_file_view_parent_class)->dispose (object);
}

static void
pins_file_view_class_init (PinsFileViewClass *klass)
{
    GObjectClass *object_class = G_OBJECT_CLASS (klass);
    GtkWidgetClass *widget_class = GTK_WIDGET_CLASS (klass);

    object_class->dispose = pins_file_view_dispose;

    gtk_widget_class_set_template_from_resource (
        widget_class, "/io/github/fabrialberio/pinapp/pins-file-view.ui");
    g_type_ensure (PINS_TYPE_APP_ICON);
    g_type_ensure (PINS_TYPE_KEY_ROW);

    gtk_widget_class_bind_template_child (widget_class, PinsFileView, icon);
    gtk_widget_class_bind_template_child (widget_class, PinsFileView,
                                          name_row);
    gtk_widget_class_bind_template_child (widget_class, PinsFileView,
                                          comment_row);
    gtk_widget_class_bind_template_child (widget_class, PinsFileView,
                                          keys_listbox);
}

static void
pins_file_view_init (PinsFileView *self)
{
    gtk_widget_init_template (GTK_WIDGET (self));
}
