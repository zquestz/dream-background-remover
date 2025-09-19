#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Threading operations for Dream Background Remover dialog
Handles all background AI processing and image operations
"""

import integrator
import threading

from api import ReplicateAPI
from gi.repository import GLib
from i18n import _

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

    def start_background_removal_thread(self, api_key, mode):
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
            args=(api_key, mode)
        )
        thread.daemon = True
        thread.start()

    def _background_removal_worker(self, api_key, mode):
        """Remove background in background thread"""
        try:
            if self._cancel_requested:
                GLib.idle_add(self._handle_cancelled)
                return

            api = ReplicateAPI(api_key)

            def progress_callback(message, percentage=None):
                if self._cancel_requested:
                    return False
                GLib.idle_add(self._update_status, message, percentage)
                return True

            GLib.idle_add(self._update_status, _("Preparing image for upload..."))

            if self._cancel_requested:
                GLib.idle_add(self._handle_cancelled)
                return

            result_pixbuf, error_msg = api.remove_background(
                drawable=self.drawable,
                progress_callback=progress_callback
            )

            if self._cancel_requested:
                GLib.idle_add(self._handle_cancelled)
                return

            if result_pixbuf:
                GLib.idle_add(self._handle_background_removed, result_pixbuf, mode)
            else:
                GLib.idle_add(self._handle_error, error_msg or _("No image data received from API"))

        except Exception as e:
            if not self._cancel_requested:
                error_msg = str(e)
                GLib.idle_add(self._handle_error, error_msg)

    def _handle_background_removed(self, pixbuf, mode):
        """Handle background removal result on main thread"""
        try:
            if self._cancel_requested:
                self._handle_cancelled()
                return

            if mode == "file":
                self._update_status(_("Creating new image file..."))

                layer_name = self.drawable.get_name() if self.drawable else _("Background Removed")
                new_image = integrator.create_new_image_with_layer(
                    pixbuf,
                    f"{layer_name} - {_('Background Removed')}"
                )

                if not new_image:
                    self._handle_error(_("Failed to create new image file"))
                    return

                success_message = _("New image created with background removed!")

            else:
                self._update_status(_("Creating new layer..."))

                layer_name = self.drawable.get_name() if self.drawable else _("Layer")
                new_layer = integrator.create_background_removed_layer(
                    self.image,
                    pixbuf,
                    f"{layer_name} - {_('Background Removed')}"
                )

                if not new_layer:
                    self._handle_error(_("Failed to create new layer"))
                    return

                success_message = _("New layer created with background removed!")

            self._update_status(success_message)
            self._schedule_success_callback(success_message)

        except Exception as e:
            self._handle_error(_("Error processing result: {error}").format(error=str(e)))

    def _handle_cancelled(self):
        """Handle cancellation on main thread"""
        self._processing = False
        self._cancel_requested = False
        self._enable_ui()
        self._update_status(_("Operation cancelled"))

    def _disable_ui(self):
        """Disable UI elements during processing"""
        if self.ui.remove_background_btn:
            self.ui.remove_background_btn.set_sensitive(False)
        if self.ui.api_key_entry:
            self.ui.api_key_entry.set_sensitive(False)
        if self.ui.layer_mode_radio:
            self.ui.layer_mode_radio.set_sensitive(False)
        if self.ui.file_mode_radio:
            self.ui.file_mode_radio.set_sensitive(False)
        if self.ui.toggle_visibility_btn:
            self.ui.toggle_visibility_btn.set_sensitive(False)

        if self.ui.cancel_btn:
            self.ui.cancel_btn.set_label(_("Cancel"))
            self.ui.cancel_btn.set_sensitive(True)

        if self.ui.progress_bar:
            self.ui.progress_bar.set_visible(True)
            self.ui.progress_bar.set_fraction(0.0)

    def _enable_ui(self):
        """Re-enable UI elements after processing"""
        if self.ui.remove_background_btn:
            self.ui.remove_background_btn.set_sensitive(True)
        if self.ui.api_key_entry:
            self.ui.api_key_entry.set_sensitive(True)
        if self.ui.layer_mode_radio:
            self.ui.layer_mode_radio.set_sensitive(True)
        if self.ui.file_mode_radio:
            self.ui.file_mode_radio.set_sensitive(True)
        if self.ui.toggle_visibility_btn:
            self.ui.toggle_visibility_btn.set_sensitive(True)

        if self.ui.cancel_btn:
            self.ui.cancel_btn.set_label(_("Cancel"))

        if self.ui.progress_bar:
            self.ui.progress_bar.set_visible(False)

    def _update_status(self, message, percentage=None):
        """Update status message on UI thread"""
        if self.ui.status_label:
            self.ui.status_label.set_text(message)

        if self.ui.progress_bar and percentage is not None:
            self.ui.progress_bar.set_fraction(percentage)

    def _handle_error(self, error_message):
        """Handle error on main thread"""
        self._processing = False
        self._cancel_requested = False
        self._enable_ui()

        if 'on_error' in self._callbacks:
            self._callbacks['on_error'](error_message)

    def _schedule_success_callback(self, success_message=None):
        """Schedule success callback after brief delay"""
        def success_timeout():
            self._processing = False
            self._cancel_requested = False
            self._enable_ui()

            if 'on_success' in self._callbacks:
                self._callbacks['on_success'](success_message)

            return False

        GLib.timeout_add(500, success_timeout)

    def cleanup(self):
        """Clean up resources and cancel any ongoing operations"""
        self._cancel_requested = True
        self._processing = False
