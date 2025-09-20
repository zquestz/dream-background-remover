#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Event handlers for Dream Background Remover dialog
Handles all user interactions and UI events
"""

from gi.repository import Gtk, GLib

from dialog_threads import DreamBackgroundRemoverThreads
from i18n import _
from settings import store_settings

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

        if self.ui.toggle_visibility_btn:
            self.on_toggle_visibility(self.ui.toggle_visibility_btn)

        def after_init():
            if self.ui.api_key_entry:
                self.ui.api_key_entry.select_region(0, 0)
            if self.ui.model_combo:
                self.ui.model_combo.grab_focus()

            self.update_remove_background_button_state()

        GLib.idle_add(after_init)

    def close_on_success(self):
        """Close dialog on successful completion"""
        self.dialog.response(Gtk.ResponseType.OK)

    def connect_all_signals(self):
        """Connect all UI signals to handlers"""
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

    def on_api_key_changed(self, _entry):
        """Handle API key changes"""
        self.update_remove_background_button_state()

    def on_cancel(self, _button):
        """Handle cancel button click"""
        if self.threads.is_processing():
            self.threads.cancel_processing()
        else:
            self.dialog.response(Gtk.ResponseType.CANCEL)

    def on_model_changed(self, combo_box):
        """Handle model selection changes"""
        if not combo_box:
            return

        current_model = self.dialog.get_current_model()
        self.ui.update_model_description(current_model)

    def on_remove_background(self, _button):
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

    def on_toggle_visibility(self, button):
        """Handle API key visibility toggle"""
        if not self.ui.api_key_entry:
            return

        self.ui.toggle_api_key_visibility(button)

    def show_error(self, message):
        """Show error message and enable interface"""
        if self.ui.status_label:
            self.ui.status_label.set_text(message)

        self.ui.hide_progress()
        self.ui.set_ui_enabled(True)

    def update_remove_background_button_state(self):
        """Update remove background button sensitivity based on input state"""
        if not self.ui.api_key_entry:
            return

        api_key = self.ui.api_key_entry.get_text().strip()
        self.ui.update_remove_background_button_state(api_key)
