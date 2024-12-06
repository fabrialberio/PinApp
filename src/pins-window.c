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

#include "pins-app-view.h"
#include "pins-directories.h"

struct _PinsWindow
{
    AdwApplicationWindow parent_instance;

    /* Template widgets */
    GtkButton *new_file_button;
    GtkToggleButton *search_button;
    GtkSearchBar *search_bar;
    GtkSearchEntry *search_entry;
    PinsAppView *app_view;
    PinsAppView *search_view;
};

G_DEFINE_FINAL_TYPE (PinsWindow, pins_window, ADW_TYPE_APPLICATION_WINDOW)

void
pins_window_reload_apps (PinsWindow *self)
{
    PinsAppIterator *app_iterator = pins_app_iterator_new ();
    pins_app_iterator_set_paths (app_iterator, pins_all_app_paths ());

    pins_app_view_set_app_iterator (self->app_view, app_iterator);
    pins_app_view_set_app_list (self->app_view, pins_app_list_new ());

    pins_app_view_set_app_iterator (self->search_view, app_iterator);
    pins_app_view_set_app_list (self->search_view, pins_app_list_new ());
}

static void
pins_window_dispose (GObject *object)
{
    PinsWindow *self = PINS_WINDOW (object);

    gtk_widget_dispose_template (GTK_WIDGET (object), PINS_TYPE_WINDOW);

    g_clear_object (&self->new_file_button);
    g_clear_object (&self->search_button);
    g_clear_object (&self->search_bar);
    g_clear_object (&self->search_entry);
    g_clear_object (&self->app_view);
    g_clear_object (&self->search_view);

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
    g_type_ensure (PINS_TYPE_APP_VIEW);

    gtk_widget_class_bind_template_child (widget_class, PinsWindow,
                                          new_file_button);
    gtk_widget_class_bind_template_child (widget_class, PinsWindow,
                                          search_button);
    gtk_widget_class_bind_template_child (widget_class, PinsWindow,
                                          search_bar);
    gtk_widget_class_bind_template_child (widget_class, PinsWindow,
                                          search_entry);
    gtk_widget_class_bind_template_child (widget_class, PinsWindow, app_view);
    gtk_widget_class_bind_template_child (widget_class, PinsWindow,
                                          search_view);
}

static void
pins_window_init (PinsWindow *self)
{
    GtkIconTheme *theme;

    gtk_widget_init_template (GTK_WIDGET (self));

    theme = gtk_icon_theme_get_for_display (
        gtk_widget_get_display (GTK_WIDGET (self)));

    // This is noticeably slow
    pins_icon_theme_inject_search_paths (theme);

    gtk_search_bar_connect_entry (self->search_bar,
                                  GTK_EDITABLE (self->search_entry));
    pins_app_view_set_search_entry (self->search_view, self->search_entry);

    pins_window_reload_apps (self);
}
