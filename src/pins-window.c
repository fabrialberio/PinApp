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

#include "pins-app-iterator.h"
#include "pins-app-view.h"
#include "pins-directories.h"
#include "pins-file-view.h"

struct _PinsWindow
{
    AdwApplicationWindow parent_instance;

    AdwNavigationView *navigation_view;
    PinsAppView *app_view;
    PinsFileView *file_view;
};

G_DEFINE_FINAL_TYPE (PinsWindow, pins_window, ADW_TYPE_APPLICATION_WINDOW)

enum
{
    PAGE_APPS,
    PAGE_FILE,
    N_PAGES,
};

static gchar *pages[N_PAGES] = {
    "apps-page",
    "file-page",
};

PinsDesktopFile *
pins_window_get_current_desktop_file (PinsWindow *self)
{
    AdwNavigationPage *file_page = adw_navigation_view_find_page (
        self->navigation_view, pages[PAGE_FILE]);
    PinsFileView *file_view
        = PINS_FILE_VIEW (adw_navigation_page_get_child (file_page));

    return pins_file_view_get_desktop_file (file_view);
}

void
pins_window_save_current_desktop_file (PinsWindow *self)
{
    PinsDesktopFile *desktop_file
        = pins_window_get_current_desktop_file (self);

    if (desktop_file != NULL)
        {
            pins_desktop_file_save (desktop_file, NULL);
        }
}

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
    g_type_ensure (PINS_TYPE_APP_VIEW);
    g_type_ensure (PINS_TYPE_FILE_VIEW);

    gtk_widget_class_bind_template_child (widget_class, PinsWindow,
                                          navigation_view);
    gtk_widget_class_bind_template_child (widget_class, PinsWindow, app_view);
    gtk_widget_class_bind_template_child (widget_class, PinsWindow, file_view);
}

void
pins_window_file_deleted_cb (PinsDesktopFile *desktop_file, PinsWindow *self)
{
    g_assert (PINS_IS_WINDOW (self));
    g_assert (PINS_IS_DESKTOP_FILE (desktop_file));

    if (pins_window_get_current_desktop_file (self) != NULL)
        {
            adw_navigation_view_pop (self->navigation_view);
        }
}

void
pins_window_load_file (PinsWindow *self, PinsDesktopFile *desktop_file)
{
    g_assert (PINS_IS_WINDOW (self));
    g_assert (PINS_IS_DESKTOP_FILE (desktop_file));

    if (pins_window_get_current_desktop_file (self) != NULL)
        {
            g_signal_handlers_disconnect_by_func (
                pins_window_get_current_desktop_file (self),
                pins_window_file_deleted_cb, self);
        }

    pins_file_view_set_desktop_file (self->file_view, desktop_file);

    g_signal_connect_object (desktop_file, "file-removed",
                             G_CALLBACK (pins_window_file_deleted_cb), self,
                             0);

    adw_navigation_view_push_by_tag (self->navigation_view, pages[PAGE_FILE]);
}

void
pins_window_file_page_hiding_cb (AdwNavigationPage *self,
                                 PinsWindow *user_data)
{
    g_assert (PINS_IS_WINDOW (user_data));

    pins_window_save_current_desktop_file (user_data);
}

void
pins_window_close_request_cb (PinsWindow *self, gpointer user_data)
{
    g_assert (PINS_IS_WINDOW (self));

    pins_window_save_current_desktop_file (self);

    gtk_window_close (GTK_WINDOW (self));
}

static void
pins_window_init (PinsWindow *self)
{
    GtkIconTheme *theme;
    PinsAppIterator *app_iterator;

    gtk_widget_init_template (GTK_WIDGET (self));

    theme = gtk_icon_theme_get_for_display (
        gtk_widget_get_display (GTK_WIDGET (self)));

    // This is noticeably slow
    pins_icon_theme_inject_search_paths (theme);

    app_iterator = pins_app_iterator_new ();
    pins_app_iterator_set_paths (app_iterator, pins_all_app_paths ());

    pins_app_view_set_app_iterator (self->app_view, app_iterator);

    g_signal_connect_object (self->app_view, "activate",
                             G_CALLBACK (pins_window_load_file), self,
                             G_CONNECT_SWAPPED);

    g_signal_connect_object (
        adw_navigation_view_find_page (self->navigation_view,
                                       pages[PAGE_FILE]),
        "hiding", G_CALLBACK (pins_window_file_page_hiding_cb), self, 0);
    g_signal_connect_object (self, "close-request",
                             G_CALLBACK (pins_window_close_request_cb), NULL,
                             0);
}
