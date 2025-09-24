#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GIMP integration functions for Dream Background Remover plugin
Handles all GIMP-specific operations for background removal results
"""

import os
import tempfile

from gi.repository import GdkPixbuf, Gimp, Gio
from i18n import _

MAX_LAYER_NAME_LENGTH = 64


def create_new_image_with_layer(pixbuf, layer_name):
    """
    Create a new GIMP image with background removed content

    Args:
        pixbuf (GdkPixbuf.Pixbuf): Pixbuf with background removed
        layer_name (str): Name for the new layer

    Returns:
        Gimp.Image: The created image, or None if failed
    """
    if not pixbuf:
        print("No pixbuf provided for new image")
        return None

    try:
        width = pixbuf.get_width()
        height = pixbuf.get_height()

        image = Gimp.Image.new(width, height, Gimp.ImageBaseType.RGB)

        if not pixbuf.get_has_alpha():
            pixbuf = pixbuf.add_alpha(False, 0, 0, 0)

        layer = Gimp.Layer.new_from_pixbuf(
            image,
            _truncate_layer_name(layer_name),
            pixbuf,
            100,
            Gimp.LayerMode.NORMAL,
            0,
            1
        )

        image.insert_layer(layer, None, 0)
        display = Gimp.Display.new(image)

        if display:
            Gimp.displays_flush()

        print(f"Created new image with layer: {layer_name}")
        return image

    except Exception as e:
        print(f"Error creating new image: {e}")
        return None


def create_scaled_layer(image, pixbuf, layer_name):
    """
    Create a new layer with pixbuf content, scaled to match image dimensions

    Args:
        image (Gimp.Image): Existing image to add layer to
        pixbuf (GdkPixbuf.Pixbuf): Pixbuf content for the layer
            (will be scaled if needed)
        layer_name (str): Name for the new layer

    Returns:
        Gimp.Layer: The created layer, or None if failed
    """
    if not image:
        print("No image provided for background removed layer")
        return None

    if not pixbuf:
        print("No pixbuf provided for background removed layer")
        return None

    try:
        img_width = image.get_width()
        img_height = image.get_height()
        pixbuf_width = pixbuf.get_width()
        pixbuf_height = pixbuf.get_height()

        if pixbuf_width != img_width or pixbuf_height != img_height:
            pixbuf = pixbuf.scale_simple(
                img_width, img_height, GdkPixbuf.InterpType.BILINEAR
            )

        if not pixbuf.get_has_alpha():
            pixbuf = pixbuf.add_alpha(False, 0, 0, 0)

        new_layer = Gimp.Layer.new_from_pixbuf(
            image,
            _truncate_layer_name(layer_name),
            pixbuf,
            100,
            Gimp.LayerMode.NORMAL,
            0,
            1
        )

        image.insert_layer(new_layer, None, 0)
        image.set_selected_layers([new_layer])

        Gimp.displays_flush()

        print(f"Created background removed layer: {layer_name}")
        return new_layer

    except Exception as e:
        print(f"Error creating background removed layer: {e}")
        return None


def export_drawable_to_bytes(drawable):
    """
    Export a GIMP drawable to PNG bytes for API processing

    Args:
        drawable (Gimp.Drawable): Drawable to export

    Returns:
        bytes: PNG image data, or None if failed
    """
    if not drawable:
        print("No drawable provided for export")
        return None

    duplicate = None
    temp_path = None

    try:
        image = drawable.get_image()
        if not image:
            print("Drawable has no associated image")
            return None

        duplicate = image.duplicate()
        duplicate.flatten()

        with tempfile.NamedTemporaryFile(
            suffix='.png', delete=False
        ) as temp_file:
            temp_path = temp_file.name

        temp_gfile = Gio.File.new_for_path(temp_path)

        success = Gimp.file_save(
            Gimp.RunMode.NONINTERACTIVE,
            duplicate,
            temp_gfile,
            None
        )

        if not success:
            print("Failed to save drawable to temporary file")
            return None

        with open(temp_path, 'rb') as f:
            image_data = f.read()

        print(f"Exported drawable to {len(image_data)} bytes")
        return image_data

    except Exception as e:
        print(f"Error exporting drawable: {e}")
        return None
    finally:
        if duplicate:
            duplicate.delete()
        if temp_path:
            try:
                os.remove(temp_path)
            except Exception:
                pass


def _truncate_layer_name(name):
    """
    Truncate layer name to fit GIMP's limitations

    Args:
        name (str): Original layer name

    Returns:
        str: Truncated layer name
    """
    if not name:
        return _("Background Removed")

    if len(name) <= MAX_LAYER_NAME_LENGTH:
        return name

    return name[:MAX_LAYER_NAME_LENGTH-3] + "..."
