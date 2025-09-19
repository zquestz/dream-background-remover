#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Replicate API integration for Dream Background Remover plugin
Handles communication with Replicate's background removal API
"""

import os
import tempfile

from gi.repository import GdkPixbuf
from i18n import _

try:
    from replicate.client import Client
    from replicate.exceptions import ModelError, ReplicateError
    REPLICATE_AVAILABLE = True
except ImportError:
    REPLICATE_AVAILABLE = False
    print("Warning: replicate package not installed. Run: pip install replicate")

BACKGROUND_REMOVER_MODEL = "851-labs/background-remover:a029dff38972b5fda4ec5d75d7d1cd25aeff621d2cf4946a41055d7db66b80bc"

class ReplicateAPI:
    """Handles Replicate API communication for background removal"""

    def __init__(self, api_key):
        """
        Initialize the Replicate API client

        Args:
            api_key (str): Replicate API key from user settings
        """
        if not REPLICATE_AVAILABLE:
            raise ImportError(_("Replicate package not installed. Please run: pip install replicate"))

        if not api_key or not api_key.strip():
            raise ValueError(_("API key is required"))

        self.client = Client(api_token=api_key.strip())
        self.api_key = api_key.strip()

    def remove_background(self, drawable, progress_callback=None):
        """
        Remove background from a GIMP drawable using Replicate API

        Args:
            drawable (Gimp.Drawable): GIMP drawable to process
            progress_callback (callable): Optional callback for progress updates
                Should return True to continue, False to cancel

        Returns:
            tuple: (GdkPixbuf.Pixbuf, str) - (result_pixbuf, error_message)
                   If successful: (pixbuf, None)
                   If failed: (None, error_message)
        """
        if not drawable:
            return None, _("No drawable provided")

        temp_path = None

        try:
            if progress_callback and not progress_callback(_("Preparing image for upload..."), 0.1):
                return None, _("Operation cancelled")

            from integrator import export_drawable_to_bytes

            image_bytes = export_drawable_to_bytes(drawable)
            if not image_bytes:
                return None, _("Failed to export image data")

            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                temp_path = temp_file.name
                temp_file.write(image_bytes)

            if progress_callback and not progress_callback(_("Uploading image to Replicate..."), 0.3):
                return None, _("Operation cancelled")

            with open(temp_path, 'rb') as image_file:
                try:
                    output = self.client.run(
                        BACKGROUND_REMOVER_MODEL,
                        input={"image": image_file}
                    )

                    if progress_callback and not progress_callback(_("Processing image..."), 0.7):
                        return None, _("Operation cancelled")

                    if not output:
                        return None, _("No output received from API")

                    if progress_callback and not progress_callback(_("Downloading result..."), 0.9):
                        return None, _("Operation cancelled")

                    result_bytes = b''.join(chunk for chunk in output)

                    if not result_bytes:
                        return None, _("No image data in API response")

                    pixbuf = self._bytes_to_pixbuf(result_bytes)
                    if not pixbuf:
                        return None, _("Failed to convert result to image")

                    if progress_callback:
                        progress_callback(_("Background removal complete!"), 1.0)

                    return pixbuf, None

                except ModelError as e:
                    error_msg = _("Model error: {error}").format(error=str(e))
                    if hasattr(e, 'prediction') and e.prediction:
                        if hasattr(e.prediction, 'logs') and e.prediction.logs:
                            error_msg += f"\n{_('Logs')}: {e.prediction.logs}"
                    return None, error_msg

                except ReplicateError as e:
                    return None, _("Replicate API error: {error}").format(error=str(e))

        except Exception as e:
            return None, _("Unexpected error: {error}").format(error=str(e))

        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass

    def _bytes_to_pixbuf(self, image_bytes):
        """
        Convert image bytes to GdkPixbuf

        Args:
            image_bytes (bytes): Image data

        Returns:
            GdkPixbuf.Pixbuf: Pixbuf object, or None if conversion failed
        """
        try:
            loader = GdkPixbuf.PixbufLoader()
            loader.write(image_bytes)
            loader.close()

            pixbuf = loader.get_pixbuf()
            return pixbuf

        except Exception as e:
            print(f"Error converting bytes to pixbuf: {e}")
            return None
