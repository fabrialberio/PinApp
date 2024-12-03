/* pins-app-icon.c
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

#include "pins-app-icon.h"

#define DEFAULT_ICON_NAME "application-x-executable"

struct _PinsAppIcon
{
    GtkWidget parent_instance;

    gint pixel_size;
};

enum
{
    PROP_0,
    PROP_PIXEL_SIZE,
    N_PROPS,
};

G_DEFINE_TYPE (PinsAppIcon, pins_app_icon, GTK_TYPE_IMAGE)

static GParamSpec *properties[N_PROPS];

void
pins_app_icon_set_icon_name (PinsAppIcon *self, gchar *icon_name)
{
    GtkIconTheme *theme
        = gtk_icon_theme_get_for_display (gdk_display_get_default ());

    if (gtk_icon_theme_has_icon (theme, icon_name)
        || gtk_icon_theme_has_icon (
            theme, g_strconcat (icon_name, "-symbolic", NULL)))
        {
            gtk_image_set_from_icon_name (GTK_IMAGE (self), icon_name);
        }
    else if (g_file_query_exists (g_file_new_for_path (icon_name),
                                  g_cancellable_get_current ()))
        {
            gtk_image_set_from_file (GTK_IMAGE (self), icon_name);
        }
    else
        {
            gtk_image_set_from_icon_name (GTK_IMAGE (self), DEFAULT_ICON_NAME);
        }
}

PinsAppIcon *
pins_app_icon_new (void)
{
    return g_object_new (PINS_TYPE_APP_ICON, NULL);
}

void
pins_app_icon_set_desktop_file (PinsAppIcon *self,
                                PinsDesktopFile *desktop_file)
{
    GError *err = NULL;
    gchar *icon_name;

    g_assert (PINS_IS_DESKTOP_FILE (desktop_file));

    icon_name = pins_desktop_file_get_string (
        desktop_file, G_KEY_FILE_DESKTOP_KEY_ICON, &err);
    if (err != NULL)
        {
            return;
        }

    pins_app_icon_set_icon_name (self, icon_name);
}

static void
pins_app_icon_dispose (GObject *object)
{
    G_OBJECT_CLASS (pins_app_icon_parent_class)->dispose (object);
}

static void
pins_app_icon_get_property (GObject *object, guint prop_id, GValue *value,
                            GParamSpec *pspec)
{
    PinsAppIcon *self = PINS_APP_ICON (object);

    switch (prop_id)
        {
        case PROP_PIXEL_SIZE:
            g_value_set_int (value, self->pixel_size);
            break;
        default:
            G_OBJECT_WARN_INVALID_PROPERTY_ID (object, prop_id, pspec);
        }
}

static void
pins_app_icon_set_property (GObject *object, guint prop_id,
                            const GValue *value, GParamSpec *pspec)
{
    PinsAppIcon *self = PINS_APP_ICON (object);

    switch (prop_id)
        {
        case PROP_PIXEL_SIZE:
            self->pixel_size = g_value_get_int (value);
            break;
        default:
            G_OBJECT_WARN_INVALID_PROPERTY_ID (object, prop_id, pspec);
        }
}

static void
pins_app_icon_class_init (PinsAppIconClass *klass)
{
    GObjectClass *object_class = G_OBJECT_CLASS (klass);

    object_class->dispose = pins_app_icon_dispose;
    object_class->get_property = pins_app_icon_get_property;
    object_class->set_property = pins_app_icon_set_property;

    properties[PROP_PIXEL_SIZE] = g_param_spec_int (
        "pixel-size", "Pixel size", "The display size of the icon in pixels.",
        0, G_MAXINT, 0, G_PARAM_READWRITE);

    g_object_class_install_properties (object_class, N_PROPS, properties);
}

static void
pins_app_icon_init (PinsAppIcon *self)
{
    gtk_image_set_from_icon_name (GTK_IMAGE (self), DEFAULT_ICON_NAME);
    gtk_widget_add_css_class (GTK_WIDGET (self), "icon-dropshadow");
}
