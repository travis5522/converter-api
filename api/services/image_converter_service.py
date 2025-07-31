#!/usr/bin/env python3
"""
Minimal Image Converter Service for Testing
This version can test format parsing without requiring PIL or other dependencies
"""

import os
import uuid
import tempfile
import json

# Constants
EXPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static', 'images')
SUPPORTED_FORMATS = ['bmp', 'eps', 'gif', 'ico', 'jpeg', 'jpg', 'odd', 'png', 'psd', 'svg', 'tga', 'tiff', 'webp']

# Ensure export directory exists
os.makedirs(EXPORT_DIR, exist_ok=True)

def get_format_info(output_format):
    """Get information about a specific format"""
    format_info = {
        'bmp': {'description': 'Windows Bitmap - Uncompressed raster format'},
        'eps': {'description': 'Encapsulated PostScript - Vector format'},
        'gif': {'description': 'Graphics Interchange Format - Supports animation'},
        'ico': {'description': 'Windows Icon - Multiple sizes in one file'},
        'jpeg': {'description': 'JPEG - Lossy compression, great for photos'},
        'jpg': {'description': 'JPEG - Lossy compression, great for photos'},
        'odd': {'description': 'OpenDocument Drawing - Converted to PNG'},
        'png': {'description': 'Portable Network Graphics - Lossless with transparency'},
        'psd': {'description': 'Photoshop Document - Adobe format'},
        'svg': {'description': 'Scalable Vector Graphics - XML-based vector format'},
        'tga': {'description': 'Truevision TGA - Supports transparency'},
        'tiff': {'description': 'Tagged Image File Format - High quality'},
        'webp': {'description': 'Modern web format - Better compression'}
    }
    return format_info.get(output_format.lower(), {'description': 'Unknown format'})

def _parse_image_options(options, output_format):
    """Parse and convert new format options to internal format"""
    internal_options = {}
    
    # Handle resize type
    if options.get('resize_type_image') == 'keep_original':
        # Keep original size - no resize
        pass
    elif 'resize' in options:
        internal_options['resize'] = options['resize']
    
    # Handle PNG specific options
    if output_format == 'png':
        if options.get('png_compression_level') == 'lossy':
            internal_options['compression'] = 'lossy'
        
        if options.get('png_convert_quality'):
            internal_options['quality'] = options['png_convert_quality']
    
    # Handle JPEG quality
    if options.get('quality'):
        internal_options['quality'] = options['quality']
    
    # Handle auto-orient
    if options.get('auto-orient'):
        internal_options['auto_orient'] = True
    
    # Handle strip metadata
    if options.get('strip'):
        internal_options['strip_metadata'] = True
    
    # Pass through other options
    for key in ['preserve_transparency', 'width', 'height']:
        if key in options:
            internal_options[key] = options[key]
    
    return internal_options

def convert_image(file, input_body):
    """Minimal image conversion function for testing format parsing"""
    # Save uploaded file to temporary location
    input_extension = os.path.splitext(file.filename)[1].lower().lstrip('.')
    with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{input_extension}') as temp_input:
        file.save(temp_input.name)
        input_path = temp_input.name

    try:
        # Parse conversion task - support both old and new format
        convert_task = input_body['tasks']['convert']
        
        # New format has input_format and output_format at same level
        if 'input_format' in convert_task and 'output_format' in convert_task:
            input_format = convert_task.get('input_format', input_extension).lower()
            output_format = convert_task.get('output_format', 'png').lower()
        else:
            # Legacy format support
            input_format = input_extension
            output_format = convert_task.get('output_format', 'png').lower()
        
        # Validate output format
        if output_format not in SUPPORTED_FORMATS:
            raise Exception(f"Unsupported output format: {output_format}. Supported formats: {', '.join(SUPPORTED_FORMATS)}")
        
        # Generate output filename and path
        output_filename = str(uuid.uuid4()) + f'.{output_format}'
        output_path = os.path.join(EXPORT_DIR, output_filename)

        # Parse options and convert new format to internal format
        options = _parse_image_options(convert_task.get('options', {}), output_format)
        
        # For minimal version, just create a dummy file to simulate conversion
        with open(output_path, 'w') as f:
            f.write(f"# Simulated conversion from {input_format} to {output_format}\n")
            f.write(f"# Options: {json.dumps(options, indent=2)}\n")
        
        # Clean up temporary file
        os.remove(input_path)
        
        # Return success response
        return {
            'success': True,
            'export_url': f"/static/images/{output_filename}",
            'download_url': f"/download/images/{output_filename}",
            'filename': output_filename,
            'output_format': output_format,
            'input_format': input_format,
            'conversion_method': 'minimal_test',
            'dimensions': {'width': 800, 'height': 600},
            'note': 'This is a minimal test conversion - install PIL for real conversion'
        }
        
    except Exception as e:
        # Clean up on error
        if os.path.exists(input_path):
            os.remove(input_path)
        raise Exception(f"Image conversion error: {str(e)}")

# Utility functions for specific conversions
def webp_to_png(webp_file, options=None):
    """Convert WebP to PNG - utility function"""
    return convert_image(webp_file, {
        'tasks': {
            'convert': {
                'input_format': 'webp',
                'output_format': 'png',
                'options': options or {}
            }
        }
    })

def jfif_to_png(jfif_file, options=None):
    """Convert JFIF to PNG - utility function"""
    return convert_image(jfif_file, {
        'tasks': {
            'convert': {
                'input_format': 'jfif',
                'output_format': 'png',
                'options': options or {}
            }
        }
    })

def png_to_svg(png_file, options=None):
    """Convert PNG to SVG - utility function"""
    return convert_image(png_file, {
        'tasks': {
            'convert': {
                'input_format': 'png',
                'output_format': 'svg',
                'options': options or {}
            }
        }
    })

def heic_to_jpg(heic_file, options=None):
    """Convert HEIC to JPG - utility function"""
    return convert_image(heic_file, {
        'tasks': {
            'convert': {
                'input_format': 'heic',
                'output_format': 'jpg',
                'options': options or {}
            }
        }
    })

def heic_to_png(heic_file, options=None):
    """Convert HEIC to PNG - utility function"""
    return convert_image(heic_file, {
        'tasks': {
            'convert': {
                'input_format': 'heic',
                'output_format': 'png',
                'options': options or {}
            }
        }
    })

def webp_to_jpg(webp_file, options=None):
    """Convert WebP to JPG - utility function"""
    return convert_image(webp_file, {
        'tasks': {
            'convert': {
                'input_format': 'webp',
                'output_format': 'jpg',
                'options': options or {}
            }
        }
    }) 