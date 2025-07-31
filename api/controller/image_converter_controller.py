from flask import Blueprint, request, jsonify
from api.services.image_converter_service import convert_image
import json

image_converter_bp = Blueprint('image_converter', __name__)

@image_converter_bp.route('/image-convert', methods=['POST'])
def image_convert():
    """
    Convert image files between different formats.
    
    Supports: BMP, EPS, GIF, ICO, JPEG, JPG, ODD, PNG, PSD, SVG, TGA, TIFF, WebP
    
    Special conversions included:
    - WEBP to PNG
    - JFIF to PNG  
    - PNG to SVG
    - HEIC to JPG
    - HEIC to PNG
    - WEBP to JPG
    - SVG Converter
    """
    file = request.files.get('file')
    input_body_raw = request.form.get('input_body')
    
    if not file or not input_body_raw:
        return jsonify({
            'error': 'Missing file or input data',
            'message': 'Both "file" and "input_body" are required',
            'example': {
                'input_body': {
                    'tasks': {
                        'convert': {
                            'output_format': 'png',
                            'options': {
                                'quality': 95,
                                'resize': [800, 600],
                                'preserve_transparency': True
                            }
                        }
                    }
                }
            }
        }), 400
    
    try:
        input_body = json.loads(input_body_raw)
        
        # Validate input structure
        if 'tasks' not in input_body or 'convert' not in input_body['tasks']:
            return jsonify({
                'error': 'Invalid input structure',
                'message': 'Expected structure: {"tasks": {"convert": {"output_format": "png", "options": {}}}}'
            }), 400
        
        # Perform the conversion
        result = convert_image(file, input_body)
        return jsonify(result)
        
    except json.JSONDecodeError:
        return jsonify({
            'error': 'Invalid JSON in input_body',
            'message': 'The input_body parameter must be valid JSON'
        }), 400
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'message': 'Image conversion failed'
        }), 500

@image_converter_bp.route('/webp-to-png', methods=['POST'])
def webp_to_png():
    """Convert WebP to PNG - specific endpoint"""
    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'Missing WebP file'}), 400
    
    try:
        # Use default conversion with PNG output
        input_body = {
            'tasks': {
                'convert': {
                    'output_format': 'png',
                    'options': {
                        'preserve_transparency': True
                    }
                }
            }
        }
        result = convert_image(file, input_body)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@image_converter_bp.route('/jfif-to-png', methods=['POST'])
def jfif_to_png():
    """Convert JFIF to PNG - specific endpoint"""
    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'Missing JFIF file'}), 400
    
    try:
        input_body = {
            'tasks': {
                'convert': {
                    'output_format': 'png',
                    'options': {}
                }
            }
        }
        result = convert_image(file, input_body)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@image_converter_bp.route('/png-to-svg', methods=['POST'])
def png_to_svg():
    """Convert PNG to SVG - specific endpoint"""
    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'Missing PNG file'}), 400
    
    try:
        input_body = {
            'tasks': {
                'convert': {
                    'output_format': 'svg',
                    'options': {}
                }
            }
        }
        result = convert_image(file, input_body)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@image_converter_bp.route('/heic-to-jpg', methods=['POST'])
def heic_to_jpg():
    """Convert HEIC to JPG - specific endpoint"""
    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'Missing HEIC file'}), 400
    
    try:
        input_body = {
            'tasks': {
                'convert': {
                    'output_format': 'jpg',
                    'options': {
                        'quality': 95
                    }
                }
            }
        }
        result = convert_image(file, input_body)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@image_converter_bp.route('/heic-to-png', methods=['POST'])
def heic_to_png():
    """Convert HEIC to PNG - specific endpoint"""
    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'Missing HEIC file'}), 400
    
    try:
        input_body = {
            'tasks': {
                'convert': {
                    'output_format': 'png',
                    'options': {
                        'preserve_transparency': True
                    }
                }
            }
        }
        result = convert_image(file, input_body)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@image_converter_bp.route('/webp-to-jpg', methods=['POST'])
def webp_to_jpg():
    """Convert WebP to JPG - specific endpoint"""
    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'Missing WebP file'}), 400
    
    try:
        input_body = {
            'tasks': {
                'convert': {
                    'output_format': 'jpg',
                    'options': {
                        'quality': 95
                    }
                }
            }
        }
        result = convert_image(file, input_body)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@image_converter_bp.route('/svg-convert', methods=['POST'])
def svg_convert():
    """SVG Converter - convert SVG to raster formats"""
    file = request.files.get('file')
    output_format = request.form.get('output_format', 'png')
    width = request.form.get('width', 1024)
    height = request.form.get('height', 1024)
    
    if not file:
        return jsonify({'error': 'Missing SVG file'}), 400
    
    try:
        input_body = {
            'tasks': {
                'convert': {
                    'output_format': output_format.lower(),
                    'options': {
                        'width': int(width),
                        'height': int(height)
                    }
                }
            }
        }
        result = convert_image(file, input_body)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@image_converter_bp.route('/formats', methods=['GET'])
def get_supported_formats():
    """Get list of supported image formats"""
    from api.services.image_converter_service import SUPPORTED_FORMATS, get_format_info
    
    formats_info = {}
    for fmt in SUPPORTED_FORMATS:
        formats_info[fmt] = get_format_info(fmt)
    
    return jsonify({
        'supported_formats': SUPPORTED_FORMATS,
        'format_details': formats_info,
        'special_endpoints': [
            '/webp-to-png',
            '/jfif-to-png', 
            '/png-to-svg',
            '/heic-to-jpg',
            '/heic-to-png',
            '/webp-to-jpg',
            '/svg-convert'
        ]
    })

@image_converter_bp.route('/health', methods=['GET'])
def health_check():
    """Check if image conversion service is available and dependencies are installed"""
    try:
        from PIL import Image
        pil_available = True
    except ImportError:
        pil_available = False
    
    try:
        from wand.image import Image as WandImage
        wand_available = True
    except ImportError:
        wand_available = False
    
    try:
        import cairosvg
        cairo_available = True
    except ImportError:
        cairo_available = False
    
    return jsonify({
        'status': 'healthy' if pil_available else 'degraded',
        'dependencies': {
            'pillow': pil_available,
            'imagemagick_wand': wand_available,
            'cairosvg': cairo_available
        },
        'capabilities': {
            'basic_formats': pil_available,
            'advanced_formats': wand_available,
            'svg_conversion': cairo_available or wand_available
        }
    })