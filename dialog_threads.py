#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Threading operations for Dream Background Remover dialog
Handles all background AI processing and image operations
"""

import integrator
import threading

from gi.repository import GLib

from api import ReplicateAPI
from i18n import _
from settings import get_model_name

class DreamBackgroundRemoverThreads:
    """Handles all background threading operations"""

    def __init__(self, ui, image, drawable):
        if not ui:
            raise ValueError("UI object is required")

        self.ui = ui
        self.image = image
        self.drawable = drawable
        self._callbacks = {}
        self._processing = False
        self._cancel_requested = False

    def set_callbacks(self, callbacks):
        """Set callback functions for thread completion"""
        if not isinstance(callbacks, dict):
            return

        self._callbacks = callbacks

    def is_processing(self):
        """Check if background removal is currently processing"""
        return self._processing

    def cancel_processing(self):
        """Request cancellation of current processing"""
        self._cancel_requested = True
        self._update_status(_("Cancelling..."))

    def start_background_removal_thread(self, api_key, mode, model):
        """Start background removal in background thread"""
        if not self.ui or self._processing:
            return

        if not self.drawable:
            self._handle_error(_("No layer available for background removal"))
            return

        self._processing = True
        self._cancel_requested = False
        self._disable_ui()

        thread = threading.Thread(
            target=self._background_removal_worker,
            args=(api_key, mode, model)
        )
        thread.daemon = True
        thread.start()

    def _background_removal_worker(self, api_key, mode, model):
        """Remove background in background thread"""
        try:
            if self._cancel_requested:
                GLib.idle_add(self._handle_cancelled)
                return

            api = ReplicateAPI(api_key)
            model_name = get_model_name(model)

            def progress_callback(message, percentage=None):
                if self._cancel_requested:
                    return False
                GLib.idle_add(self._update_status, message, percentage)
                return True

            pixbuf, error = api.remove_background(self.drawable, model_name, progress_callback)

            if self._cancel_requested:
                GLib.idle_add(self._handle_cancelled)
                return

            if error:
                GLib.idle_add(self._handle_error, error)
                return

            if not pixbuf:
                GLib.idle_add(self._handle_error, _("Failed to process image"))
                return

            layer_name = self._generate_layer_name()
            GLib.idle_add(self._handle_success, pixbuf, layer_name, mode)

        except ImportError as e:
            GLib.idle_add(self._handle_error, str(e))
        except ValueError as e:
            GLib.idle_add(self._handle_error, str(e))
        except Exception as e:
            error_msg = _("Unexpected error during background removal: {error}").format(error=str(e))
            GLib.idle_add(self._handle_error, error_msg)

    def _generate_layer_name(self):
        """Generate a name for the new layer"""
        if self.drawable:
            original_name = self.drawable.get_name()
            return _("{original} (Background Removed)").format(original=original_name)
        return _("Background Removed")

    def _handle_success(self, pixbuf, layer_name, mode):
        """Handle successful background removal"""
        try:
            self._update_status(_("Creating result..."), 0.95)

            if mode == "file":
                result = integrator.create_new_image_with_layer(pixbuf, layer_name)
            else:
                result = integrator.create_background_removed_layer(self.image, pixbuf, layer_name)

            if result:
                self._update_status(_("Background removal completed!"), 1.0)
            else:
                self._handle_error(_("Failed to create result image/layer"))
                return

        except Exception as e:
            error_msg = _("Error creating result: {error}").format(error=str(e))
            self._handle_error(error_msg)
            return

        self._processing = False
        self._enable_ui()

        if self._callbacks.get('on_success'):
            self._callbacks['on_success']()

    def _handle_error(self, error_message):
        """Handle error during processing"""
        self._processing = False
        self._enable_ui()

        if self._callbacks.get('on_error'):
            self._callbacks['on_error'](error_message)

    def _handle_cancelled(self):
        """Handle cancelled operation"""
        self._processing = False
        self._update_status(_("Operation cancelled"))
        self._enable_ui()

    def _update_status(self, message, percentage=None):
        """Update status display"""
        if self.ui.status_label:
            self.ui.status_label.set_text(message)

        if self.ui.progress_bar:
            if percentage is not None:
                self.ui.progress_bar.set_fraction(percentage)
                self.ui.progress_bar.set_visible(True)
            else:
                self.ui.progress_bar.pulse()
                self.ui.progress_bar.set_visible(True)

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
