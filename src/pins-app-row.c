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
#include "pins-locale-utils-private.h"

struct _PinsAppRow
{
    AdwActionRow parent_instance;

    PinsAppIcon *icon;
};

G_DEFINE_TYPE (PinsAppRow, pins_app_row, ADW_TYPE_ACTION_ROW)

PinsAppRow *
pins_app_row_new (void)
{
    return g_object_new (PINS_TYPE_APP_ROW, NULL);
}

void
pins_app_row_update_appearance (PinsAppRow *self,
                                PinsDesktopFile *desktop_file)
{
    gchar *title_key, *subtitle_key;

    pins_app_icon_set_desktop_file (self->icon, desktop_file);

    title_key = _pins_join_key_locale (
        G_KEY_FILE_DESKTOP_KEY_NAME,
        pins_desktop_file_get_locale_for_key (desktop_file,
                                              G_KEY_FILE_DESKTOP_KEY_NAME));

    subtitle_key = _pins_join_key_locale (
        G_KEY_FILE_DESKTOP_KEY_COMMENT,
        pins_desktop_file_get_locale_for_key (desktop_file,
                                              G_KEY_FILE_DESKTOP_KEY_COMMENT));

    adw_preferences_row_set_title (
        ADW_PREFERENCES_ROW (self),
        pins_desktop_file_get_string (desktop_file, title_key));
    adw_action_row_set_subtitle (
        ADW_ACTION_ROW (self),
        pins_desktop_file_get_string (desktop_file, subtitle_key));
}

void
pins_app_row_key_set_cb (PinsDesktopFile *self, gchar *key,
                         PinsAppRow *user_data)
{
    g_assert (PINS_IS_APP_ROW (user_data));

    pins_app_row_update_appearance (user_data, self);
}

void
pins_app_row_set_desktop_file (PinsAppRow *self, PinsDesktopFile *desktop_file)
{
    g_assert (PINS_IS_DESKTOP_FILE (desktop_file));

    g_signal_connect_object (desktop_file, "key-set",
                             G_CALLBACK (pins_app_row_key_set_cb), self, 0);

    pins_app_row_update_appearance (self, desktop_file);
}

static void
pins_app_row_dispose (GObject *object)
{
    gtk_widget_dispose_template (GTK_WIDGET (object), PINS_TYPE_APP_ROW);

    G_OBJECT_CLASS (pins_app_row_parent_class)->dispose (object);
}

static void
pins_app_row_class_init (PinsAppRowClass *klass)
{
    GObjectClass *object_class = G_OBJECT_CLASS (klass);
    GtkWidgetClass *widget_class = GTK_WIDGET_CLASS (klass);

    object_class->dispose = pins_app_row_dispose;

    gtk_widget_class_set_template_from_resource (
        widget_class, "/io/github/fabrialberio/pinapp/pins-app-row.ui");
    gtk_widget_class_bind_template_child (widget_class, PinsAppRow, icon);

    g_type_ensure (PINS_TYPE_APP_ICON);
}

static void
pins_app_row_init (PinsAppRow *self)
{
    gtk_widget_init_template (GTK_WIDGET (self));
}
