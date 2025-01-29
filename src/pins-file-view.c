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

#include "pins-add-key-dialog-private.h"
#include "pins-app-icon.h"
#include "pins-key-row.h"
#include "pins-locale-utils-private.h"

struct _PinsFileView
{
    AdwBin parent_instance;

    PinsDesktopFile *desktop_file;
    gchar **keys;

    AdwHeaderBar *header_bar;
    AdwWindowTitle *window_title;
    GtkScrolledWindow *scrolled_window;
    PinsAppIcon *icon;
    GtkButton *edit_icon_button;
    GtkButton *load_icon_button;
    PinsKeyRow *name_row;
    PinsKeyRow *comment_row;
    GtkSwitch *autostart_switch;
    GtkSwitch *invisible_switch;
    GtkListBox *keys_listbox;
    AdwButtonRow *add_key_button;
    GtkButton *delete_button;
    AdwBreakpoint *breakpoint;
};

G_DEFINE_TYPE (PinsFileView, pins_file_view, ADW_TYPE_BREAKPOINT_BIN);

void
pins_file_view_setup_row (PinsKeyRow *row, PinsDesktopFile *desktop_file,
                          gchar *key, gchar **all_keys, gchar **all_locales)
{
    gchar **locales = { NULL };

    if (_pins_key_has_locales (all_keys, key))
        locales = all_locales;

    pins_key_row_set_key (row, desktop_file, key, locales);
}

void
pins_file_view_update_title (PinsFileView *self)
{
    adw_window_title_set_title (
        self->window_title,
        pins_desktop_file_get_string (self->desktop_file,
                                      G_KEY_FILE_DESKTOP_KEY_NAME));
}

void
pins_file_view_focus_key_row (PinsFileView *self, gchar *key)
{
    GtkListBoxRow *row;
    gchar *current_key, *locale;

    locale = _pins_split_key_locale (key).locale;
    key = _pins_split_key_locale (key).key;

    for (int i = 0;
         (row = gtk_list_box_get_row_at_index (self->keys_listbox, i)) != NULL;
         i++)
        {
            current_key = _pins_split_key_locale (
                              pins_key_row_get_key (PINS_KEY_ROW (row)))
                              .key;

            if (!g_strcmp0 (current_key, key))
                {
                    gtk_widget_grab_focus (GTK_WIDGET (row));

                    if (locale != NULL)
                        pins_key_row_set_locale (PINS_KEY_ROW (row), locale);
                }
        }
}

void
autostart_switch_state_set_cb (PinsFileView *self, gboolean state)
{
    pins_desktop_file_set_autostart (self->desktop_file, state);
    gtk_switch_set_active (self->autostart_switch, state);
}

void
invisible_switch_state_set_cb (PinsFileView *self, gboolean state)
{
    g_warning ("state-set cb");

    pins_desktop_file_set_boolean (self->desktop_file,
                                   G_KEY_FILE_DESKTOP_KEY_NO_DISPLAY, state);
    gtk_switch_set_active (self->invisible_switch, state);
}

void
pins_file_view_key_set_cb (PinsDesktopFile *desktop_file, gchar *key,
                           PinsFileView *self)
{
    g_assert (PINS_IS_FILE_VIEW (self));

    if (!g_strv_contains ((const gchar *const *)self->keys, key))
        {
            pins_file_view_set_desktop_file (self, self->desktop_file);
            pins_file_view_focus_key_row (self, key);
        }

    if (!g_strcmp0 (key, G_KEY_FILE_DESKTOP_KEY_NAME))
        pins_file_view_update_title (self);
    else if (!g_strcmp0 (key, G_KEY_FILE_DESKTOP_KEY_NO_DISPLAY))
        {
            gboolean value = pins_desktop_file_get_boolean (
                self->desktop_file, G_KEY_FILE_DESKTOP_KEY_NO_DISPLAY);

            if (gtk_switch_get_state (self->invisible_switch) != value)
                {
                    g_signal_handlers_block_by_func (
                        self->invisible_switch, invisible_switch_state_set_cb,
                        self);

                    gtk_switch_set_active (self->invisible_switch, value);

                    g_signal_handlers_unblock_by_func (
                        self->invisible_switch, invisible_switch_state_set_cb,
                        self);
                }
        }
}

void
pins_file_view_key_removed_cb (PinsDesktopFile *desktop_file, gchar *key,
                               PinsFileView *self)
{
    pins_file_view_set_desktop_file (self, self->desktop_file);
}

void
pins_file_view_update_title_visible_cb (GtkAdjustment *adjustment,
                                        PinsFileView *self)
{
    g_assert (PINS_IS_FILE_VIEW (self));

    adw_header_bar_set_show_title (self->header_bar,
                                   gtk_adjustment_get_value (adjustment) > 0);
}

void
pins_file_view_setup_keys_listbox (PinsFileView *self)
{
    gchar **locales = _pins_locales_from_keys (self->keys);
    gchar **added_keys
        = g_malloc0_n (g_strv_length (self->keys) + 1, sizeof (gchar *));
    gsize n_added_keys = 0;

    gtk_list_box_remove_all (self->keys_listbox);

    pins_file_view_setup_row (self->name_row, self->desktop_file,
                              G_KEY_FILE_DESKTOP_KEY_NAME, self->keys,
                              locales);
    pins_file_view_setup_row (self->comment_row, self->desktop_file,
                              G_KEY_FILE_DESKTOP_KEY_COMMENT, self->keys,
                              locales);

    added_keys[0] = G_KEY_FILE_DESKTOP_KEY_NAME;
    added_keys[1] = G_KEY_FILE_DESKTOP_KEY_COMMENT;
    n_added_keys = 2;

    for (int i = 0; i < g_strv_length (self->keys); i++)
        {
            gchar *current_key = _pins_split_key_locale (self->keys[i]).key;
            PinsKeyRow *row;

            if (g_strv_contains ((const gchar *const *)added_keys,
                                 current_key))
                continue;

            row = pins_key_row_new ();
            pins_file_view_setup_row (row, self->desktop_file, current_key,
                                      self->keys, locales);

            added_keys[n_added_keys] = current_key;
            n_added_keys++;

            gtk_list_box_append (self->keys_listbox, GTK_WIDGET (row));
        }

    g_strfreev (locales);
    g_free (added_keys); /// TODO: Using g_strfreev results in free error
}

void
pins_file_view_set_desktop_file (PinsFileView *self,
                                 PinsDesktopFile *desktop_file)
{
    if (self->desktop_file != NULL)
        {
            g_signal_handlers_disconnect_by_func (
                self->desktop_file, pins_file_view_key_set_cb, self);
            g_signal_handlers_disconnect_by_func (
                self->desktop_file, pins_file_view_key_removed_cb, self);
            g_signal_handlers_disconnect_by_func (
                self->desktop_file, autostart_switch_state_set_cb, self);
            g_signal_handlers_disconnect_by_func (
                self->desktop_file, invisible_switch_state_set_cb, self);
        }

    self->desktop_file = g_object_ref (desktop_file);
    self->keys = pins_desktop_file_get_keys (self->desktop_file);

    pins_file_view_update_title (self);
    pins_app_icon_set_desktop_file (self->icon, self->desktop_file);
    gtk_switch_set_active (
        self->autostart_switch,
        pins_desktop_file_is_autostart (self->desktop_file));
    gtk_switch_set_active (
        self->invisible_switch,
        pins_desktop_file_get_boolean (self->desktop_file,
                                       G_KEY_FILE_DESKTOP_KEY_NO_DISPLAY));

    g_signal_connect_object (self->desktop_file, "key-set",
                             G_CALLBACK (pins_file_view_key_set_cb), self, 0);
    g_signal_connect_object (self->desktop_file, "key-removed",
                             G_CALLBACK (pins_file_view_key_removed_cb), self,
                             0);
    g_signal_connect_object (self->autostart_switch, "state-set",
                             G_CALLBACK (autostart_switch_state_set_cb), self,
                             G_CONNECT_SWAPPED);
    g_signal_connect_object (self->invisible_switch, "state-set",
                             G_CALLBACK (invisible_switch_state_set_cb), self,
                             G_CONNECT_SWAPPED);

    gtk_widget_set_visible (
        GTK_WIDGET (self->delete_button),
        pins_desktop_file_is_user_only (self->desktop_file));

    pins_file_view_setup_keys_listbox (self);
}

PinsDesktopFile *
pins_file_view_get_desktop_file (PinsFileView *self)
{
    return self->desktop_file;
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

    gtk_widget_class_bind_template_child (widget_class, PinsFileView,
                                          header_bar);
    gtk_widget_class_bind_template_child (widget_class, PinsFileView,
                                          window_title);
    gtk_widget_class_bind_template_child (widget_class, PinsFileView,
                                          scrolled_window);
    gtk_widget_class_bind_template_child (widget_class, PinsFileView, icon);
    gtk_widget_class_bind_template_child (widget_class, PinsFileView,
                                          edit_icon_button);
    gtk_widget_class_bind_template_child (widget_class, PinsFileView,
                                          load_icon_button);
    gtk_widget_class_bind_template_child (widget_class, PinsFileView,
                                          name_row);
    gtk_widget_class_bind_template_child (widget_class, PinsFileView,
                                          comment_row);
    gtk_widget_class_bind_template_child (widget_class, PinsFileView,
                                          autostart_switch);
    gtk_widget_class_bind_template_child (widget_class, PinsFileView,
                                          invisible_switch);
    gtk_widget_class_bind_template_child (widget_class, PinsFileView,
                                          keys_listbox);
    gtk_widget_class_bind_template_child (widget_class, PinsFileView,
                                          add_key_button);
    gtk_widget_class_bind_template_child (widget_class, PinsFileView,
                                          delete_button);
    gtk_widget_class_bind_template_child (widget_class, PinsFileView,
                                          breakpoint);
}

void
edit_icon_button_clicked_cb (PinsFileView *self)
{
    if (!pins_desktop_file_has_key (self->desktop_file,
                                    G_KEY_FILE_DESKTOP_KEY_ICON))
        {
            pins_desktop_file_set_string (self->desktop_file,
                                          G_KEY_FILE_DESKTOP_KEY_ICON, "");
        }

    pins_file_view_focus_key_row (self, G_KEY_FILE_DESKTOP_KEY_ICON);
}

void
load_icon_dialog_closed_cb (GObject *dialog, GAsyncResult *res,
                            gpointer user_data)
{
    PinsFileView *self = PINS_FILE_VIEW (user_data);
    GFile *file
        = gtk_file_dialog_open_finish (GTK_FILE_DIALOG (dialog), res, NULL);

    pins_desktop_file_set_string (self->desktop_file,
                                  G_KEY_FILE_DESKTOP_KEY_ICON,
                                  g_file_get_path (file));
}

void
load_icon_button_clicked_cb (PinsFileView *self)
{
    GtkFileDialog *dialog = gtk_file_dialog_new ();

    gtk_file_dialog_set_title (dialog, _ ("Load icon"));
    gtk_file_dialog_open (dialog,
                          GTK_WINDOW (gtk_widget_get_root (GTK_WIDGET (self))),
                          NULL, load_icon_dialog_closed_cb, self);
}

void
add_key_button_clicked_cb (PinsFileView *self)
{
    _pins_add_key_dialog_present (
        GTK_WINDOW (gtk_widget_get_root (GTK_WIDGET (self))),
        self->desktop_file);
}

void
remove_button_clicked_cb (PinsFileView *self)
{
    pins_desktop_file_delete (self->desktop_file);
}

void
breakpoint_apply_cb (PinsFileView *self)
{
    gtk_widget_remove_css_class (GTK_WIDGET (self->name_row), "title-1-row");
    gtk_widget_add_css_class (GTK_WIDGET (self->name_row), "title-2-row");
}

void
breakpoint_unapply_cb (PinsFileView *self)
{
    gtk_widget_remove_css_class (GTK_WIDGET (self->name_row), "title-2-row");
    gtk_widget_add_css_class (GTK_WIDGET (self->name_row), "title-1-row");
}

static void
pins_file_view_init (PinsFileView *self)
{
    gtk_widget_init_template (GTK_WIDGET (self));

    g_signal_connect_object (self->edit_icon_button, "clicked",
                             G_CALLBACK (edit_icon_button_clicked_cb), self,
                             G_CONNECT_SWAPPED);
    g_signal_connect_object (self->load_icon_button, "clicked",
                             G_CALLBACK (load_icon_button_clicked_cb), self,
                             G_CONNECT_SWAPPED);

    g_signal_connect_object (self->add_key_button, "activated",
                             G_CALLBACK (add_key_button_clicked_cb), self,
                             G_CONNECT_SWAPPED);
    g_signal_connect_object (self->delete_button, "clicked",
                             G_CALLBACK (remove_button_clicked_cb), self,
                             G_CONNECT_SWAPPED);

    g_signal_connect_object (self->breakpoint, "apply",
                             G_CALLBACK (breakpoint_apply_cb), self,
                             G_CONNECT_SWAPPED);
    g_signal_connect_object (self->breakpoint, "unapply",
                             G_CALLBACK (breakpoint_unapply_cb), self,
                             G_CONNECT_SWAPPED);

    g_signal_connect_object (
        gtk_scrolled_window_get_vadjustment (self->scrolled_window),
        "value-changed", G_CALLBACK (pins_file_view_update_title_visible_cb),
        self, 0);
}
