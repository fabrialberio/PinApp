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

struct _PinsFileView
{
    AdwBin parent_instance;

    PinsDesktopFile *desktop_file;

    PinsAppIcon *icon;
};

G_DEFINE_TYPE (PinsFileView, pins_file_view, ADW_TYPE_BIN);

void
pins_file_view_set_desktop_file (PinsFileView *self,
                                 PinsDesktopFile *desktop_file)
{
    /// TODO: Implement

    gchar *name = pins_desktop_file_get_string (desktop_file, "Name", NULL);

    pins_app_icon_set_desktop_file (self->icon, desktop_file);

    g_warning ("Loading desktop file with name: %s", name);
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

    gtk_widget_class_bind_template_child (widget_class, PinsFileView, icon);
}

static void
pins_file_view_init (PinsFileView *self)
{
    gtk_widget_init_template (GTK_WIDGET (self));
}
