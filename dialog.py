#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Dream Background Remover Dialog - Main coordinator
"""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GimpUi', '3.0')

from gi.repository import GimpUi

from dialog_events import DreamBackgroundRemoverEventHandler
from dialog_gtk import DreamBackgroundRemoverUI
from i18n import _
from settings import load_settings, DEFAULT_MODEL

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

        self.set_resizable(True)

        self.ui = DreamBackgroundRemoverUI()
        self.events = DreamBackgroundRemoverEventHandler(self, self.ui, image, drawable)

        self._initialize()

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

    def get_current_mode(self):
        """Get the currently selected mode"""
        if self.ui.file_mode_radio and self.ui.file_mode_radio.get_active():
            return "file"
        return "layer"

    def get_current_model(self):
        """Get the currently selected model"""
        if self.ui.model_combo:
            model_id = self.ui.model_combo.get_active_id()
            if model_id:
                return model_id
        return DEFAULT_MODEL

    def _initialize(self):
        """Initialize the dialog"""
        self.ui.build_interface(self)
        self.events.connect_all_signals()
        self._update_source_info()
        self._load_settings()

    def _load_settings(self):
        """Load settings from config file"""
        try:
            settings = load_settings()

            if settings.get("api_key") and self.ui.api_key_entry:
                self.ui.api_key_entry.set_text(str(settings["api_key"]))

            if "api_key_visible" in settings and self.ui.toggle_visibility_btn:
                self.ui.toggle_visibility_btn.set_active(bool(settings["api_key_visible"]))

            stored_mode = settings.get("mode", "layer")
            if stored_mode == "file" and self.ui.file_mode_radio:
                self.ui.file_mode_radio.set_active(True)
            else:
                if self.ui.layer_mode_radio:
                    self.ui.layer_mode_radio.set_active(True)

            stored_model = settings.get("model", DEFAULT_MODEL)
            if self.ui.model_combo and isinstance(stored_model, str):
                self.ui.model_combo.set_active_id(stored_model)

        except Exception as e:
            print(f"Error loading settings: {e}")

    def _update_source_info(self):
        """Update the source image information display"""
        if self.ui.source_info_label and self.image and self.drawable:
            layer_name = self.drawable.get_name() if self.drawable else _("Current Layer")
            width = self.drawable.get_width()
            height = self.drawable.get_height()
            info_text = _("{name} ({width}×{height}px)").format(
                name=layer_name, width=width, height=height
            )
            self.ui.source_info_label.set_text(info_text)
