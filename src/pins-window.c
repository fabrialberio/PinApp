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

#include "config.h"

#include "pins-window.h"

struct _PinsWindow
{
    AdwApplicationWindow parent_instance;

    /* Template widgets */
    GtkButton *new_file_button;
    GtkToggleButton *search_button;
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
}

static void
pins_window_init (PinsWindow *self)
{
    gtk_widget_init_template (GTK_WIDGET (self));
}
