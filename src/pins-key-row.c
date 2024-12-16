/* pins-key-row.c
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

#include <glib/gi18n.h>

#include "pins-key-row.h"

struct _PinsKeyRow
{
    AdwEntryRow parent_instance;

    PinsDesktopFile *desktop_file;
    gchar *key;

    GtkButton *reset_button;
    GtkButton *remove_button;
    GtkMenuButton *locale_button;
    GtkPopover *locale_popover;
    GtkListView *locale_list_view;
};

G_DEFINE_TYPE (PinsKeyRow, pins_key_row, ADW_TYPE_ENTRY_ROW)

PinsKeyRow *
pins_key_row_new (void)
{
    return g_object_new (PINS_TYPE_KEY_ROW, NULL);
}

void
pins_key_row_update_appearance (PinsKeyRow *self)
{
    gboolean reset_button_visible = FALSE, remove_button_visible = FALSE;
    const gchar *editable_value = gtk_editable_get_text (GTK_EDITABLE (self));

    reset_button_visible
        = pins_desktop_file_is_key_edited (self->desktop_file, self->key)
          && pins_desktop_file_has_backup_for_key (self->desktop_file,
                                                   self->key);

    remove_button_visible
        = strlen (editable_value) == 0
          && !pins_desktop_file_has_backup_for_key (self->desktop_file,
                                                    self->key)
          && pins_desktop_file_has_key (self->desktop_file, self->key);

    gtk_widget_set_visible (GTK_WIDGET (self->reset_button),
                            reset_button_visible);
    gtk_widget_set_visible (GTK_WIDGET (self->remove_button),
                            remove_button_visible);
}

void
pins_key_row_text_changed_cb (GtkEditable *editable, PinsKeyRow *self)
{
    g_assert (PINS_IS_KEY_ROW (self));

    pins_desktop_file_set_string (self->desktop_file, self->key,
                                  gtk_editable_get_text (editable));

    pins_key_row_update_appearance (self);
}

void
pins_key_row_locale_changed_cb (GtkMenuButton *self, gchar *selected_locale)
{
    AdwButtonContent *button_content
        = ADW_BUTTON_CONTENT (gtk_menu_button_get_child (self));

    if (selected_locale != NULL)
        {
            adw_button_content_set_label (button_content, selected_locale);
        }
    else
        {
            adw_button_content_set_label (button_content, "");
        }
}

void
pins_key_row_locale_menu_item_activated_cb (GtkListView *self, guint position,
                                            gpointer user_data)
{
    /// TODO: Actually set locale
    g_warning ("Selected row at %d", position);
}

void
pins_key_row_set_key (PinsKeyRow *self, PinsDesktopFile *desktop_file,
                      gchar *key, gchar **locales)
{
    self->desktop_file = desktop_file;
    self->key = key;

    adw_preferences_row_set_title (ADW_PREFERENCES_ROW (self), key);
    gtk_editable_set_text (
        GTK_EDITABLE (self),
        pins_desktop_file_get_string (self->desktop_file, self->key, NULL));
    pins_key_row_update_appearance (self);

    g_signal_connect_object (GTK_EDITABLE (self), "changed",
                             G_CALLBACK (pins_key_row_text_changed_cb), self,
                             0);

    if (g_strv_length (locales) > 0)
        {
            GStrvBuilder *locales_strv_builder = g_strv_builder_new ();
            GtkSingleSelection *selection_model;

            gtk_widget_set_visible (GTK_WIDGET (self->locale_button), TRUE);

            g_strv_builder_add (locales_strv_builder, _ ("( Unlocalized )"));
            g_strv_builder_addv (locales_strv_builder,
                                 (const gchar **)locales);

            selection_model = gtk_single_selection_new (G_LIST_MODEL (
                gtk_string_list_new ((const char *const *)g_strv_builder_end (
                    locales_strv_builder))));

            gtk_list_view_set_model (self->locale_list_view,
                                     GTK_SELECTION_MODEL (selection_model));
        }
    else
        {
            gtk_widget_set_visible (GTK_WIDGET (self->locale_button), FALSE);
        }
}

static void
pins_key_row_dispose (GObject *object)
{
    gtk_widget_dispose_template (GTK_WIDGET (object), PINS_TYPE_KEY_ROW);

    G_OBJECT_CLASS (pins_key_row_parent_class)->dispose (object);
}

static void
pins_key_row_class_init (PinsKeyRowClass *klass)
{
    GObjectClass *object_class = G_OBJECT_CLASS (klass);
    GtkWidgetClass *widget_class = GTK_WIDGET_CLASS (klass);

    object_class->dispose = pins_key_row_dispose;

    gtk_widget_class_set_template_from_resource (
        widget_class, "/io/github/fabrialberio/pinapp/pins-key-row.ui");
    gtk_widget_class_bind_template_child (widget_class, PinsKeyRow,
                                          reset_button);
    gtk_widget_class_bind_template_child (widget_class, PinsKeyRow,
                                          remove_button);
    gtk_widget_class_bind_template_child (widget_class, PinsKeyRow,
                                          locale_button);
    gtk_widget_class_bind_template_child (widget_class, PinsKeyRow,
                                          locale_popover);
    gtk_widget_class_bind_template_child (widget_class, PinsKeyRow,
                                          locale_list_view);
}

void
pins_key_row_reset_key_cb (PinsKeyRow *self, gpointer user_data)
{
    g_assert (PINS_IS_KEY_ROW (self));

    pins_desktop_file_reset_key (self->desktop_file, self->key);

    gtk_editable_set_text (
        GTK_EDITABLE (self),
        pins_desktop_file_get_string (self->desktop_file, self->key, NULL));

    pins_key_row_update_appearance (self);
}

void
pins_key_row_locale_menu_item_setup_cb (GtkSignalListItemFactory *self,
                                        GtkListItem *item, gpointer user_data)
{
    GtkBuilder *builder = gtk_builder_new_from_resource (
        "/io/github/fabrialberio/pinapp/pins-key-row-locale-menu-item.ui");
    GtkBox *row
        = GTK_BOX (gtk_builder_get_object (builder, "locale_menu_item"));

    gtk_list_item_set_child (item, GTK_WIDGET (row));
}

void
pins_key_row_locale_menu_item_bind_cb (GtkSignalListItemFactory *self,
                                       GtkListItem *item, gpointer user_data)
{
    GtkWidget *row = gtk_list_item_get_child (item);
    GtkLabel *label = GTK_LABEL (gtk_widget_get_first_child (row));
    GtkImage *icon = GTK_IMAGE (gtk_widget_get_last_child (row));
    gchar *locale = (gchar *)gtk_string_object_get_string (
        gtk_list_item_get_item (item));

    gtk_label_set_label (label, locale);

    /// TODO: Update check icon visibility
    gtk_widget_set_visible (GTK_WIDGET (icon), FALSE);
}

static void
pins_key_row_init (PinsKeyRow *self)
{
    GtkListItemFactory *factory = gtk_signal_list_item_factory_new ();

    gtk_widget_init_template (GTK_WIDGET (self));

    g_signal_connect_object (self->reset_button, "clicked",
                             G_CALLBACK (pins_key_row_reset_key_cb), self,
                             G_CONNECT_SWAPPED);
    g_signal_connect_object (self->remove_button, "clicked",
                             G_CALLBACK (pins_key_row_reset_key_cb), self,
                             G_CONNECT_SWAPPED);

    g_signal_connect_object (
        factory, "setup", G_CALLBACK (pins_key_row_locale_menu_item_setup_cb),
        NULL, 0);
    g_signal_connect_object (
        factory, "bind", G_CALLBACK (pins_key_row_locale_menu_item_bind_cb),
        NULL, 0);

    gtk_list_view_set_factory (self->locale_list_view, factory);

    g_signal_connect (self->locale_list_view, "activate",
                      G_CALLBACK (pins_key_row_locale_menu_item_activated_cb),
                      NULL);
}
