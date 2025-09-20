#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Threading operations for Dream Background Remover dialog
Handles all background AI processing and image operations
"""

import threading

from gi.repository import GLib

import integrator
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

    def cancel_processing(self):
        """Request cancellation of current processing"""
        self._cancel_requested = True
        self.ui.update_status(_("Cancelling..."))

    def is_processing(self):
        """Check if background removal is currently processing"""
        return self._processing

    def set_callbacks(self, callbacks):
        """Set callback functions for thread completion"""
        if not isinstance(callbacks, dict):
            raise ValueError("Callbacks must be a dictionary")
        self._callbacks = callbacks

    def start_background_removal_thread(self, api_key, mode, model):
        """Start background removal in background thread"""
        if not self.ui or self._processing:
            return

        if not self.drawable:
            self._handle_error(_("No layer available for background removal"))
            return

        self._processing = True
        self._cancel_requested = False
        self.ui.set_ui_enabled(False)

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
                GLib.idle_add(self.ui.update_status, message, percentage)
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

        except (ImportError, ValueError) as e:
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

    def _handle_cancelled(self):
        """Handle cancelled operation"""
        self._processing = False
        self.ui.update_status(_("Operation cancelled"))
        self.ui.set_ui_enabled(True)

    def _handle_error(self, error_message):
        """Handle error during processing"""
        self._processing = False
        self.ui.set_ui_enabled(True)

        if self._callbacks.get('on_error'):
            self._callbacks['on_error'](error_message)

    def _handle_success(self, pixbuf, layer_name, mode):
        """Handle successful background removal"""
        try:
            self.ui.update_status(_("Creating result..."), 0.95)

            if mode == "file":
                result = integrator.create_new_image_with_layer(pixbuf, layer_name)
            else:
                result = integrator.create_scaled_layer(self.image, pixbuf, layer_name)

            if result:
                self.ui.update_status(_("Background removal completed!"), 1.0)
            else:
                self._handle_error(_("Failed to create result image/layer"))
                return

        except Exception as e:
            error_msg = _("Error creating result: {error}").format(error=str(e))
            self._handle_error(error_msg)
            return

        self._processing = False
        self.ui.set_ui_enabled(True)

        if self._callbacks.get('on_success'):
            self._callbacks['on_success']()
