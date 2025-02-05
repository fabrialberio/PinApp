/* pins-add-key-dialog.c
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

#include "pins-add-key-dialog-private.h"

#include <glib/gi18n.h>

enum
{
    CANCEL,
    ADD,
    N_RESPONSES,
};

static gchar *responses[N_RESPONSES] = { "cancel", "add" };

typedef struct
{
    PinsDesktopFile *desktop_file;
    AdwEntryRow *key_row;
} AddKeyRequest;

void
add_key_request_clear (gpointer data)
{
    AddKeyRequest *request = data;

    g_clear_object (&request->desktop_file);
    g_clear_object (&request->key_row);
}

void
response_cb (AdwAlertDialog *dialog, gchar *response, AddKeyRequest *request)
{
    if (!g_strcmp0 (response, responses[ADD]))
        {
            const gchar *key
                = gtk_editable_get_text (GTK_EDITABLE (request->key_row));

            pins_desktop_file_set_string (request->desktop_file, key, "");
        }
    else
        {
            GTask *task = g_object_get_data (G_OBJECT (dialog), "TASK");
            g_task_return_new_error (task, G_IO_ERROR, G_IO_ERROR_CANCELLED,
                                     "The user cancelled the request");
        }
}

void
update_response_enabled (AdwEntryRow *key_row, AdwAlertDialog *dialog)
{
    adw_alert_dialog_set_response_enabled (
        dialog, responses[ADD],
        strlen (gtk_editable_get_text (GTK_EDITABLE (key_row))) > 0);
}

static AdwAlertDialog *
_pins_add_key_dialog_new (GtkWindow *parent, PinsDesktopFile *desktop_file)
{
    AdwAlertDialog *dialog
        = ADW_ALERT_DIALOG (adw_alert_dialog_new (_ ("Add new key"), NULL));
    GtkWidget *group = adw_preferences_group_new ();
    GtkWidget *key_row = adw_entry_row_new ();
    AddKeyRequest *request = g_malloc (sizeof (AddKeyRequest));

    adw_alert_dialog_add_responses (dialog, responses[CANCEL], _ ("_Cancel"),
                                    responses[ADD], _ ("_Add"), NULL);

    adw_alert_dialog_set_close_response (dialog, responses[CANCEL]);
    adw_alert_dialog_set_response_appearance (dialog, responses[ADD],
                                              ADW_RESPONSE_SUGGESTED);
    adw_alert_dialog_set_response_enabled (dialog, responses[ADD], FALSE);

    adw_alert_dialog_set_extra_child (dialog, group);

    adw_preferences_row_set_title (ADW_PREFERENCES_ROW (key_row), _ ("Key"));
    adw_preferences_group_add (ADW_PREFERENCES_GROUP (group), key_row);

    request->desktop_file = g_object_ref (desktop_file);
    request->key_row = g_object_ref (ADW_ENTRY_ROW (key_row));

    g_signal_connect_data (dialog, "response", G_CALLBACK (response_cb),
                           request, (GClosureNotify)add_key_request_clear, 0);
    g_signal_connect_object (key_row, "changed",
                             G_CALLBACK (update_response_enabled), dialog, 0);

    return dialog;
}

void
_pins_add_key_dialog_present (GtkWindow *parent, PinsDesktopFile *desktop_file)
{
    AdwAlertDialog *dialog;

    dialog = _pins_add_key_dialog_new (parent, desktop_file);

    adw_dialog_present (ADW_DIALOG (dialog), GTK_WIDGET (parent));
}
