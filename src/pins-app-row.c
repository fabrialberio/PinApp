/* pins-app-row.c
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

#include "pins-app-row.h"
#include "pins-app-icon.h"

struct _PinsAppRow
{
    AdwActionRow parent_instance;
};

G_DEFINE_TYPE (PinsAppRow, pins_app_row, ADW_TYPE_ACTION_ROW)

PinsAppRow *
pins_app_row_new (void)
{
    return g_object_new (PINS_TYPE_APP_ROW, NULL);
}

void
pins_app_row_set_desktop_file (PinsAppRow *self, PinsDesktopFile *desktop_file)
{
    gchar *title, *subtitle;
    PinsAppIcon *icon = pins_app_icon_new ();

    g_assert (PINS_IS_DESKTOP_FILE (desktop_file));

    adw_action_row_add_prefix (ADW_ACTION_ROW (self), GTK_WIDGET (icon));

    pins_app_icon_set_desktop_file (icon, desktop_file);

    title = pins_desktop_file_get_string (desktop_file,
                                          G_KEY_FILE_DESKTOP_KEY_NAME, NULL);
    subtitle = pins_desktop_file_get_string (
        desktop_file, G_KEY_FILE_DESKTOP_KEY_COMMENT, NULL);

    adw_preferences_row_set_title (ADW_PREFERENCES_ROW (self), title);
    adw_action_row_set_subtitle (ADW_ACTION_ROW (self), subtitle);
}

static void
pins_app_row_class_init (PinsAppRowClass *klass)
{
    GtkWidgetClass *widget_class = GTK_WIDGET_CLASS (klass);

    gtk_widget_class_set_template_from_resource (
        widget_class, "/io/github/fabrialberio/pinapp/pins-app-row.ui");
}

static void
pins_app_row_init (PinsAppRow *self)
{
    gtk_widget_init_template (GTK_WIDGET (self));
}
