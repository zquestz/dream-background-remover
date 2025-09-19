#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Dream Background Remover - AI Background Removal GIMP Plugin
A GIMP plugin for AI-powered background removal using Replicate's background removal API
"""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gimp', '3.0')
gi.require_version('GimpUi', '3.0')
gi.require_version('GLib', '2.0')
gi.require_version('GdkPixbuf', '2.0')
import sys

from dialog import DreamBackgroundRemoverDialog
from gi.repository import Gimp, GimpUi, Gtk, GLib
from i18n import _, DOMAIN

PLUGIN_NAME = "dream-background-remover"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "AI-powered background removal with Replicate"

class DreamBackgroundRemover(Gimp.PlugIn):
    """Main plugin class"""

    def do_set_i18n(self, procname):
        """Enable localization"""
        return DOMAIN

    def do_query_procedures(self):
        """Register the plugin procedure"""
        return ['dream-background-remover']

    def do_create_procedure(self, name):
        """Create the plugin procedure"""
        if name == 'dream-background-remover':
            procedure = Gimp.ImageProcedure.new(
                self,
                name,
                Gimp.PDBProcType.PLUGIN,
                self.run_dream_background_remover,
                None
            )
            procedure.set_image_types("RGB*, GRAY*, INDEXED*")
            procedure.set_sensitivity_mask(
                Gimp.ProcedureSensitivityMask.DRAWABLE
            )
            procedure.set_documentation(
                _("AI-powered background removal with Replicate"),
                _("Remove backgrounds from images using AI. Choose to create a new layer "
                  "in the current image or generate a new image file with the background removed."),
                name
            )
            procedure.set_menu_label(_("Dream Background Remover..."))
            procedure.set_attribution("Josh Ellithorpe", "Josh Ellithorpe", "2025")
            procedure.add_menu_path("<Image>/Filters/AI")

            return procedure
        return None

    def run_dream_background_remover(self, procedure, run_mode, image, drawables, config, run_data):
        """Run the Dream Background Remover plugin"""
        if run_mode == Gimp.RunMode.INTERACTIVE:
            try:
                if not image:
                    error_msg = _("No image available. Please open an image first.")
                    Gimp.message(error_msg)
                    return procedure.new_return_values(Gimp.PDBStatusType.EXECUTION_ERROR, GLib.Error())

                if not drawables or len(drawables) == 0:
                    error_msg = _("No layer selected. Please select a layer to process.")
                    Gimp.message(error_msg)
                    return procedure.new_return_values(Gimp.PDBStatusType.EXECUTION_ERROR, GLib.Error())

                drawable = drawables[0]

                if drawable.get_width() <= 0 or drawable.get_height() <= 0:
                    error_msg = _("Invalid layer dimensions. Please select a valid layer.")
                    Gimp.message(error_msg)
                    return procedure.new_return_values(Gimp.PDBStatusType.EXECUTION_ERROR, GLib.Error())

                GimpUi.init("dream-background-remover")

                dialog = DreamBackgroundRemoverDialog(procedure, image, drawable)
                dialog.show_all()

                response = dialog.run()
                dialog.destroy()

                if response == Gtk.ResponseType.OK:
                    return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())
                else:
                    return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())

            except Exception as e:
                error_msg = _("Error running Dream Background Remover: {error}").format(error=str(e))
                print(error_msg)
                Gimp.message(error_msg)
                return procedure.new_return_values(Gimp.PDBStatusType.EXECUTION_ERROR, GLib.Error())

        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

if __name__ == '__main__':
    Gimp.main(DreamBackgroundRemover.__gtype__, sys.argv)
