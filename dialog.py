#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Dream Background Remover Dialog - Main coordinator
"""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GimpUi', '3.0')

from dialog_events import DreamBackgroundRemoverEventHandler
from dialog_gtk import DreamBackgroundRemoverUI
from gi.repository import GimpUi
from i18n import _
from settings import load_settings

class DreamBackgroundRemoverDialog(GimpUi.Dialog):
    """Main dialog window for the Dream Background Remover plugin"""

    def __init__(self, procedure, image, drawable):
        super().__init__(
            title=_("Dream Background Remover - AI Background Removal"),
            role="dream-background-remover-dialog",
            use_header_bar=True
        )

        self.procedure = procedure
        self.image = image
        self.drawable = drawable

        self.set_default_size(500, 400)
        self.set_resizable(True)

        self.ui = DreamBackgroundRemoverUI()
        self.events = DreamBackgroundRemoverEventHandler(self, self.ui, image, drawable)

        self._initialize()

    def _initialize(self):
        """Initialize the dialog"""
        self.ui.build_interface(self)
        self.events.connect_all_signals()
        self._set_initial_mode()
        self._load_settings()

    def _set_initial_mode(self):
        """Set initial mode and update UI accordingly - will be overridden by settings if available"""
        if self.ui.source_info_label and self.image and self.drawable:
            layer_name = self.drawable.get_name() if self.drawable else _("Current Layer")
            width = self.drawable.get_width()
            height = self.drawable.get_height()
            info_text = _("Source: {name} ({width}×{height}px)").format(
                name=layer_name, width=width, height=height
            )
            self.ui.source_info_label.set_text(info_text)

    def _load_settings(self):
        """Load settings from config file"""
        try:
            settings = load_settings()

            if settings.get("api_key") and self.ui.api_key_entry:
                self.ui.api_key_entry.set_text(str(settings["api_key"]))

            if settings.get("api_key_visible") and self.ui.toggle_visibility_btn:
                self.ui.toggle_visibility_btn.set_active(True)

            stored_mode = settings.get("mode", "layer")
            if stored_mode == "file" and self.ui.file_mode_radio:
                self.ui.file_mode_radio.set_active(True)
            else:
                if self.ui.layer_mode_radio:
                    self.ui.layer_mode_radio.set_active(True)

            self._update_mode_description()

            try:
                self.events.on_mode_changed(None)
            except Exception as e:
                print(f"Error triggering mode change: {e}")

        except Exception as e:
            print(f"Error loading settings: {e}")

    def _update_mode_description(self):
        """Update the mode description based on current selection"""
        if not self.ui.mode_description:
            return

        layer_name = self.drawable.get_name() if self.drawable else _("Current Layer")

        if self.get_current_mode() == "file":
            description = _("Remove background from '{layer}' and create a new image file").format(layer=layer_name)
        else:
            description = _("Remove background from '{layer}' and create a new layer").format(layer=layer_name)

        self.ui.mode_description.set_text(description)

    def get_current_mode(self):
        """Get the currently selected mode"""
        if self.ui.file_mode_radio and self.ui.file_mode_radio.get_active():
            return "file"
        return "layer"

    def get_api_key(self):
        """Get the API key from the UI"""
        if self.ui.api_key_entry:
            return self.ui.api_key_entry.get_text().strip()
        return ""

    def get_api_key_visible(self):
        """Get the API key visibility state"""
        if self.ui.toggle_visibility_btn:
            return self.ui.toggle_visibility_btn.get_active()
        return False

    def update_progress(self, message, fraction=None):
        """Update progress display"""
        if self.ui.status_label:
            self.ui.status_label.set_text(message)

        if self.ui.progress_bar:
            if fraction is not None:
                self.ui.progress_bar.set_fraction(fraction)
                self.ui.progress_bar.set_visible(True)
            else:
                self.ui.progress_bar.pulse()
                self.ui.progress_bar.set_visible(True)

    def hide_progress(self):
        """Hide progress display"""
        if self.ui.progress_bar:
            self.ui.progress_bar.set_visible(False)
        if self.ui.status_label:
            self.ui.status_label.set_text(_("Ready"))
