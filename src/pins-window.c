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
#include "pins-app-row.h"

struct _PinsWindow
{
    AdwApplicationWindow parent_instance;

    /* Template widgets */
    GtkButton *new_file_button;
    GtkToggleButton *search_button;
    AdwPreferencesGroup *box;
};

G_DEFINE_FINAL_TYPE (PinsWindow, pins_window, ADW_TYPE_APPLICATION_WINDOW)

static void
pins_window_class_init (PinsWindowClass *klass)
{
    GtkWidgetClass *widget_class = GTK_WIDGET_CLASS (klass);

    gtk_widget_class_set_template_from_resource (
        widget_class, "/io/github/fabrialberio/pinapp/pins-window.ui");
    gtk_widget_class_bind_template_child (widget_class, PinsWindow,
                                          new_file_button);
    gtk_widget_class_bind_template_child (widget_class, PinsWindow,
                                          search_button);
    gtk_widget_class_bind_template_child (widget_class, PinsWindow, box);
}

static void
pins_window_init (PinsWindow *self)
{
    PinsAppRow *row;
    PinsDesktopFile *desktop_file;
    GKeyFile *key_file;
    gchar *name;

    gtk_widget_init_template (GTK_WIDGET (self));

    row = pins_app_row_new ();

    desktop_file = pins_desktop_file_new_from_file (
        g_file_new_for_path (
            "/home/fabri/Progetti/App "
            "GNOME/Pins/data/io.github.fabrialberio.pinapp.desktop.in"),
        NULL);

    g_warning ("user_path");

    pins_app_row_set_desktop_file (row, desktop_file);

    adw_preferences_group_add (self->box, GTK_WIDGET (row));
}
