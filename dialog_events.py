#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Event handlers for Dream Background Remover dialog
Handles all user interactions and UI events
"""

from dialog_threads import DreamBackgroundRemoverThreads
from gi.repository import Gtk, GLib
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

        layer_name = self.drawable.get_name() if self.drawable else _("Current Layer")
        is_file_mode = self.ui.file_mode_radio and self.ui.file_mode_radio.get_active()

        self.ui.update_mode_description(layer_name, is_file_mode)

        self.dialog._update_mode_description()

        if self.ui.remove_background_btn:
            if is_file_mode:
                self.ui.remove_background_btn.set_label(_("Create New Image"))
            else:
                self.ui.remove_background_btn.set_label(_("Remove Background"))

    def update_remove_background_button_state(self):
        """Update remove background button sensitivity based on input state"""
        if not self.ui.api_key_entry or not self.ui.remove_background_btn:
            return

        has_api_key = bool(self.ui.api_key_entry.get_text().strip())
        has_drawable = self.drawable is not None

        self.ui.remove_background_btn.set_sensitive(has_api_key and has_drawable)

    def on_toggle_visibility(self, button):
        """Toggle API key visibility"""
        if not self.ui.api_key_entry:
            return

        if button.get_active():
            self.ui.api_key_entry.set_visibility(True)
            button.set_image(Gtk.Image.new_from_icon_name("view-reveal-symbolic", Gtk.IconSize.BUTTON))
            button.set_tooltip_text(_("Hide API key"))
        else:
            self.ui.api_key_entry.set_visibility(False)
            button.set_image(Gtk.Image.new_from_icon_name("view-conceal-symbolic", Gtk.IconSize.BUTTON))
            button.set_tooltip_text(_("Show API key"))

    def on_api_key_changed(self, entry):
        """Handle API key changes"""
        self.update_remove_background_button_state()

    def on_cancel(self, button):
        """Handle cancel button"""
        if self.threads.is_processing():
            self.threads.cancel_processing()
            return

        self.dialog.response(Gtk.ResponseType.CANCEL)

    def on_remove_background(self, button):
        """Handle remove background button - main AI processing entry point"""
        api_key = self.ui.api_key_entry.get_text().strip() if self.ui.api_key_entry else ""

        if not api_key:
            self.show_error(_("Please enter your Replicate API key"))
            return

        if not self.drawable:
            self.show_error(_("No layer selected. Please select a layer to process."))
            return

        if self.drawable.get_width() <= 0 or self.drawable.get_height() <= 0:
            self.show_error(_("Invalid layer dimensions. Please select a valid layer."))
            return

        self.store_current_settings()

        is_file_mode = self.ui.file_mode_radio and self.ui.file_mode_radio.get_active()
        mode = "file" if is_file_mode else "layer"

        if self.ui.status_label:
            self.ui.status_label.set_text(_("Preparing image for background removal..."))

        self.ui.set_processing_state(True)

        self.threads.start_background_removal_thread(api_key, mode)

    def close_on_success(self, message=None):
        """Close dialog after successful background removal"""
        if message and self.ui.status_label:
            self.ui.show_success_state(message)
            GLib.timeout_add(1000, lambda: self.dialog.response(Gtk.ResponseType.OK))
        else:
            self.dialog.response(Gtk.ResponseType.OK)
        return False

    def show_error(self, message):
        """Show error message"""
        if self.ui:
            self.ui.show_error_state(message)

        dialog = Gtk.MessageDialog(
            parent=self.dialog,
            modal=True,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=_("Background Removal Error"),
            secondary_text=message
        )
        dialog.run()
        dialog.destroy()

    def set_status(self, message):
        """Update status message"""
        if self.ui.status_label:
            self.ui.status_label.set_text(message)

    def update_progress(self, message, fraction=None):
        """Update progress display"""
        self.dialog.update_progress(message, fraction)

    def hide_progress(self):
        """Hide progress display"""
        self.dialog.hide_progress()

    def store_current_settings(self):
        """Store current settings to config file"""
        if not self.ui.api_key_entry or not self.ui.layer_mode_radio or not self.ui.toggle_visibility_btn:
            return

        api_key = self.ui.api_key_entry.get_text().strip()
        mode = "file" if (self.ui.file_mode_radio and self.ui.file_mode_radio.get_active()) else "layer"
        api_key_visible = self.ui.toggle_visibility_btn.get_active()

        store_settings(api_key, mode, api_key_visible)
