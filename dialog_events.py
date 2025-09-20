#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Event handlers for Dream Background Remover dialog
Handles all user interactions and UI events
"""

from gi.repository import Gtk, GLib

from dialog_threads import DreamBackgroundRemoverThreads
from i18n import _
from settings import store_settings, load_settings

class DreamBackgroundRemoverEventHandler:
    """Handles all dialog events and user interactions"""

    def __init__(self, dialog, ui, image, drawable):
        self.dialog = dialog
        self.ui = ui
        self.image = image
        self.drawable = drawable

        self.threads = DreamBackgroundRemoverThreads(ui, image, drawable)
        self.threads.set_callbacks({
            'on_success': self.close_on_success,
            'on_error': self.show_error
        })

        settings = load_settings()
        if self.ui.toggle_visibility_btn and self.ui.api_key_entry:
            is_visible = settings.get("api_key_visible", False)
            self.ui.toggle_visibility_btn.set_active(is_visible)
            self.on_toggle_visibility(self.ui.toggle_visibility_btn)

        def after_init():
            if self.ui.api_key_entry:
                self.ui.api_key_entry.select_region(0, 0)
                self.ui.api_key_entry.grab_focus()
            return False

        GLib.idle_add(after_init)

    def connect_all_signals(self):
        """Connect all UI signals to handlers"""
        if self.ui.layer_mode_radio:
            self.ui.layer_mode_radio.connect("toggled", self.on_mode_changed)
        if self.ui.file_mode_radio:
            self.ui.file_mode_radio.connect("toggled", self.on_mode_changed)

        if self.ui.model_combo:
            self.ui.model_combo.connect("changed", self.on_model_changed)

        if self.ui.toggle_visibility_btn:
            self.ui.toggle_visibility_btn.connect("toggled", self.on_toggle_visibility)

        if self.ui.cancel_btn:
            self.ui.cancel_btn.connect("clicked", self.on_cancel)
        if self.ui.remove_background_btn:
            self.ui.remove_background_btn.connect("clicked", self.on_remove_background)

        if self.ui.api_key_entry:
            self.ui.api_key_entry.connect("changed", self.on_api_key_changed)

    def on_mode_changed(self, radio_button):
        """Handle mode selection changes"""
        if not self.ui.layer_mode_radio or not self.drawable:
            return

        is_file_mode = self.ui.file_mode_radio and self.ui.file_mode_radio.get_active()
        self.ui.update_mode_description(is_file_mode)

        if self.ui.remove_background_btn:
            self.ui.remove_background_btn.set_label(_("Remove Background"))

    def on_model_changed(self, combo_box):
        """Handle model selection changes"""
        if not combo_box or not self.ui.model_description:
            return

        current_model = self.dialog.get_current_model()
        if current_model == "bria":
            description = _("Bria's Remove Background model - High Quality and More Expensive")
        else:
            description = _("851 Labs Background Remover - Fast and Inexpensive")

        self.ui.model_description.set_markup(f'<small><i>{description}</i></small>')

    def update_remove_background_button_state(self):
        """Update remove background button sensitivity based on input state"""
        if not self.ui.remove_background_btn or not self.ui.api_key_entry:
            return

        api_key = self.ui.api_key_entry.get_text().strip()
        self.ui.remove_background_btn.set_sensitive(bool(api_key))

    def on_api_key_changed(self, entry):
        """Handle API key changes"""
        self.update_remove_background_button_state()

    def on_toggle_visibility(self, button):
        """Handle API key visibility toggle"""
        if not self.ui.api_key_entry:
            return

        is_visible = button.get_active()
        self.ui.api_key_entry.set_visibility(is_visible)

        icon_name = "view-reveal-symbolic" if is_visible else "view-conceal-symbolic"
        button.get_image().set_from_icon_name(icon_name, Gtk.IconSize.BUTTON)

    def on_cancel(self, button):
        """Handle cancel button click"""
        if self.threads.is_processing():
            self.threads.cancel_processing()
        else:
            self.dialog.response(Gtk.ResponseType.CANCEL)

    def on_remove_background(self, button):
        """Handle remove background button click"""
        api_key = self.dialog.get_api_key()
        if not api_key:
            self.show_error(_("Please enter your Replicate API key"))
            return

        mode = self.dialog.get_current_mode()
        model = self.dialog.get_current_model()

        api_key_visible = self.dialog.get_api_key_visible()
        store_settings(api_key, mode, api_key_visible, model)

        self.threads.start_background_removal_thread(api_key, mode, model)

    def show_error(self, message):
        """Show error message and enable interface"""
        if self.ui.status_label:
            self.ui.status_label.set_text(message)

        self.dialog.hide_progress()
        self._enable_ui()

    def close_on_success(self):
        """Close dialog on successful completion"""
        self.dialog.response(Gtk.ResponseType.OK)

    def _enable_ui(self):
        """Re-enable UI controls"""
        if self.ui.api_key_entry:
            self.ui.api_key_entry.set_sensitive(True)
        if self.ui.toggle_visibility_btn:
            self.ui.toggle_visibility_btn.set_sensitive(True)
        if self.ui.layer_mode_radio:
            self.ui.layer_mode_radio.set_sensitive(True)
        if self.ui.file_mode_radio:
            self.ui.file_mode_radio.set_sensitive(True)
        if self.ui.model_combo:
            self.ui.model_combo.set_sensitive(True)
        if self.ui.remove_background_btn:
            self.ui.remove_background_btn.set_sensitive(True)
            self.ui.remove_background_btn.set_label(_("Remove Background"))

    def _disable_ui(self):
        """Disable UI controls during processing"""
        if self.ui.api_key_entry:
            self.ui.api_key_entry.set_sensitive(False)
        if self.ui.toggle_visibility_btn:
            self.ui.toggle_visibility_btn.set_sensitive(False)
        if self.ui.layer_mode_radio:
            self.ui.layer_mode_radio.set_sensitive(False)
        if self.ui.file_mode_radio:
            self.ui.file_mode_radio.set_sensitive(False)
        if self.ui.model_combo:
            self.ui.model_combo.set_sensitive(False)
        if self.ui.remove_background_btn:
            self.ui.remove_background_btn.set_sensitive(False)
