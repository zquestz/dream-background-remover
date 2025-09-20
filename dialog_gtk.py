#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GTK UI components for Dream Background Remover dialog
Handles all GTK interface creation and layout
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from i18n import _
from settings import AVAILABLE_MODELS, get_model_display_name

class DreamBackgroundRemoverUI:
    """Handles all GTK UI creation and layout"""

    def __init__(self):
        self.api_key_entry = None
        self.toggle_visibility_btn = None

        self.layer_mode_radio = None
        self.file_mode_radio = None
        self.mode_description = None

        self.model_combo = None
        self.model_description = None

        self.source_info_label = None

        self.cancel_btn = None
        self.remove_background_btn = None

        self.status_label = None
        self.progress_bar = None

    def build_interface(self, parent_dialog):
        """Build the main plugin interface"""
        if not parent_dialog:
            return

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        main_box.set_margin_top(16)
        main_box.set_margin_bottom(16)
        main_box.set_margin_start(16)
        main_box.set_margin_end(16)

        try:
            api_key_section = self._create_api_key_section()
            main_box.pack_start(api_key_section, False, False, 0)

            source_section = self._create_source_info_section()
            main_box.pack_start(source_section, False, False, 0)

            model_section = self._create_model_section()
            main_box.pack_start(model_section, False, False, 0)

            mode_section = self._create_mode_section()
            main_box.pack_start(mode_section, False, False, 0)

            buttons_section = self._create_buttons_section()
            main_box.pack_start(buttons_section, False, False, 0)

            status_section = self._create_status_section()
            main_box.pack_start(status_section, False, False, 0)

            parent_dialog.get_content_area().add(main_box)
        except Exception as e:
            print(f"Error building interface: {e}")

    def _create_api_key_section(self):
        """Create API key input section"""
        section_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        title_label = Gtk.Label()
        title_label.set_markup(f"<b>{_('Replicate API Key')}</b>")
        title_label.set_halign(Gtk.Align.START)
        section_box.pack_start(title_label, False, False, 0)

        key_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        self.api_key_entry = Gtk.Entry()
        self.api_key_entry.set_placeholder_text(_("Enter your Replicate API key..."))
        self.api_key_entry.set_visibility(False)
        self.api_key_entry.set_input_purpose(Gtk.InputPurpose.PASSWORD)
        key_container.pack_start(self.api_key_entry, True, True, 0)

        self.toggle_visibility_btn = Gtk.ToggleButton()
        self.toggle_visibility_btn.set_image(
            Gtk.Image.new_from_icon_name("view-conceal-symbolic", Gtk.IconSize.BUTTON)
        )
        self.toggle_visibility_btn.set_tooltip_text(_("Show/Hide API key"))
        key_container.pack_start(self.toggle_visibility_btn, False, False, 0)

        section_box.pack_start(key_container, False, False, 0)

        help_label = Gtk.Label()
        help_url = "https://replicate.com/"
        help_text = _('Get your API key from <a href="{url}">Replicate</a>').format(url=help_url)
        help_label.set_markup(f'<small>{help_text}</small>')
        help_label.set_halign(Gtk.Align.START)
        help_label.set_line_wrap(True)
        section_box.pack_start(help_label, False, False, 0)

        return section_box

    def _create_source_info_section(self):
        """Create source image information section"""
        section_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        title_label = Gtk.Label()
        title_label.set_markup(f"<b>{_('Source Image')}</b>")
        title_label.set_halign(Gtk.Align.START)
        section_box.pack_start(title_label, False, False, 0)

        self.source_info_label = Gtk.Label()
        self.source_info_label.set_halign(Gtk.Align.START)
        self.source_info_label.set_xalign(0.0)
        self.source_info_label.set_justify(Gtk.Justification.LEFT)
        self.source_info_label.set_line_wrap(True)
        self.source_info_label.set_text(_("No image selected"))
        section_box.pack_start(self.source_info_label, False, False, 0)

        return section_box

    def _create_model_section(self):
        """Create model selection section"""
        section_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        title_label = Gtk.Label()
        title_label.set_markup(f"<b>{_('AI Model')}</b>")
        title_label.set_halign(Gtk.Align.START)
        section_box.pack_start(title_label, False, False, 0)

        self.model_combo = Gtk.ComboBoxText()
        for model_key in AVAILABLE_MODELS.keys():
            display_name = get_model_display_name(model_key)
            self.model_combo.append(model_key, display_name)

        section_box.pack_start(self.model_combo, False, False, 0)

        self.model_description = Gtk.Label()
        self.model_description.set_halign(Gtk.Align.START)
        self.model_description.set_line_wrap(True)
        self.model_description.set_markup(f'<small><i>{_("Choose the AI model for background removal")}</i></small>')
        section_box.pack_start(self.model_description, False, False, 0)

        return section_box

    def _create_mode_section(self):
        """Create mode selection section"""
        section_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        title_label = Gtk.Label()
        title_label.set_markup(f"<b>{_('Output Mode')}</b>")
        title_label.set_halign(Gtk.Align.START)
        section_box.pack_start(title_label, False, False, 0)

        radio_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        self.layer_mode_radio = Gtk.RadioButton.new_with_label(None, _("Create Layer"))
        radio_box.pack_start(self.layer_mode_radio, False, False, 0)

        self.file_mode_radio = Gtk.RadioButton.new_with_label_from_widget(
            self.layer_mode_radio, _("Create File")
        )
        radio_box.pack_start(self.file_mode_radio, False, False, 0)

        section_box.pack_start(radio_box, False, False, 0)

        self.mode_description = Gtk.Label()
        self.mode_description.set_halign(Gtk.Align.START)
        self.mode_description.set_line_wrap(True)
        self.mode_description.set_text(_("Choose how to handle the result"))
        section_box.pack_start(self.mode_description, False, False, 0)

        return section_box

    def _create_buttons_section(self):
        """Create action buttons section"""
        buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        buttons_box.set_halign(Gtk.Align.CENTER)

        self.cancel_btn = Gtk.Button.new_with_label(_("Cancel"))
        buttons_box.pack_start(self.cancel_btn, False, False, 0)

        self.remove_background_btn = Gtk.Button.new_with_label(_("Remove Background"))
        self.remove_background_btn.get_style_context().add_class("suggested-action")
        buttons_box.pack_start(self.remove_background_btn, False, False, 0)

        return buttons_box

    def _create_status_section(self):
        """Create status and progress section"""
        section_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        self.status_label = Gtk.Label()
        self.status_label.set_text(_("Ready"))
        self.status_label.set_halign(Gtk.Align.START)
        section_box.pack_start(self.status_label, False, False, 0)

        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_visible(False)
        section_box.pack_start(self.progress_bar, False, False, 0)

        return section_box

    def update_mode_description(self, is_file_mode=False):
        """Update the mode description text"""
        if not self.mode_description:
            return

        if is_file_mode:
            description = _("Create a new image file with background removed")
        else:
            description = _("Create a new layer with background removed")

        self.mode_description.set_text(description)

    def set_processing_state(self, processing=True):
        """Enable/disable UI elements during processing"""
        sensitive = not processing

        if self.api_key_entry:
            self.api_key_entry.set_sensitive(sensitive)
        if self.toggle_visibility_btn:
            self.toggle_visibility_btn.set_sensitive(sensitive)
        if self.layer_mode_radio:
            self.layer_mode_radio.set_sensitive(sensitive)
        if self.file_mode_radio:
            self.file_mode_radio.set_sensitive(sensitive)
        if self.model_combo:
            self.model_combo.set_sensitive(sensitive)
        if self.remove_background_btn:
            self.remove_background_btn.set_sensitive(sensitive)
