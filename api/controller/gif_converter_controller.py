from flask import Blueprint, request, jsonify
from api.services.gif_converter_service import convert_to_gif, convert_from_gif
import json

gif_converter_bp = Blueprint('gif_converter', __name__)

@gif_converter_bp.route('/gif-convert', methods=['POST'])
def gif_convert():
    """
    General GIF conversion endpoint.
    Supports converting TO GIF or FROM GIF based on target format.
    
    Advanced options include:
    - Trim start/end times
    - Width/height settings
    - Loop count control
    - FPS optimization
    - Compression settings
    - Transparency preservation
    - Background optimization
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
                            'output_format': 'gif',
                            'options': {
                                'trim_start': '00:00:05.00',
                                'trim_end': '00:00:15.00',
                                'width': 400,
                                'fps': 15,
                                'loop_count': 0,
                                'compression': 10,
                                'transparency': True,
                                'optimize_background': True
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
                'message': 'Expected structure: {"tasks": {"convert": {"output_format": "gif", "options": {}}}}'
            }), 400
        
        output_format = input_body['tasks']['convert'].get('output_format', '').lower()
        
        # Determine if converting TO GIF or FROM GIF
        if output_format == 'gif':
            result = convert_to_gif(file, input_body)
        else:
            result = convert_from_gif(file, input_body)
        
        return jsonify(result)
        
    except json.JSONDecodeError:
        return jsonify({
            'error': 'Invalid JSON in input_body',
            'message': 'The input_body parameter must be valid JSON'
        }), 400
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'message': 'GIF conversion failed'
        }), 500

@gif_converter_bp.route('/video-to-gif', methods=['POST'])
def video_to_gif():
    """Convert Video to GIF - specific endpoint"""
    file = request.files.get('file')
    input_body_raw = request.form.get('input_body')
    
    if not file:
        return jsonify({'error': 'Missing video file'}), 400
    
    try:
        # Parse options if provided, otherwise use defaults
        options = {}
        if input_body_raw:
            input_data = json.loads(input_body_raw)
            options = input_data.get('tasks', {}).get('convert', {}).get('options', {})
        
        # Create input_body with GIF as target
        input_body = {
            'tasks': {
                'convert': {
                    'output_format': 'gif',
                    'options': {
                        'fps': options.get('fps', 15),
                        'width': options.get('width', 400),
                        'compression': options.get('compression', 10),
                        'loop_count': options.get('loop_count', 0),
                        **options  # Include any additional options
                    }
                }
            }
        }
        result = convert_to_gif(file, input_body)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@gif_converter_bp.route('/mp4-to-gif', methods=['POST'])
def mp4_to_gif():
    """Convert MP4 to GIF - specific endpoint"""
    file = request.files.get('file')
    input_body_raw = request.form.get('input_body')
    
    if not file:
        return jsonify({'error': 'Missing MP4 file'}), 400
    
    try:
        options = {}
        if input_body_raw:
            input_data = json.loads(input_body_raw)
            options = input_data.get('tasks', {}).get('convert', {}).get('options', {})
        
        input_body = {
            'tasks': {
                'convert': {
                    'output_format': 'gif',
                    'options': {
                        'fps': options.get('fps', 15),
                        'width': options.get('width', 400),
                        'compression': options.get('compression', 10),
                        'loop_count': options.get('loop_count', 0),
                        **options
                    }
                }
            }
        }
        result = convert_to_gif(file, input_body)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@gif_converter_bp.route('/webm-to-gif', methods=['POST'])
def webm_to_gif():
    """Convert WEBM to GIF - specific endpoint"""
    file = request.files.get('file')
    input_body_raw = request.form.get('input_body')
    
    if not file:
        return jsonify({'error': 'Missing WEBM file'}), 400
    
    try:
        options = {}
        if input_body_raw:
            input_data = json.loads(input_body_raw)
            options = input_data.get('tasks', {}).get('convert', {}).get('options', {})
        
        input_body = {
            'tasks': {
                'convert': {
                    'output_format': 'gif',
                    'options': {
                        'fps': options.get('fps', 15),
                        'width': options.get('width', 400),
                        'compression': options.get('compression', 10),
                        'loop_count': options.get('loop_count', 0),
                        **options
                    }
                }
            }
        }
        result = convert_to_gif(file, input_body)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@gif_converter_bp.route('/apng-to-gif', methods=['POST'])
def apng_to_gif():
    """Convert APNG (Animated PNG) to GIF - specific endpoint"""
    file = request.files.get('file')
    input_body_raw = request.form.get('input_body')
    
    if not file:
        return jsonify({'error': 'Missing APNG file'}), 400
    
    try:
        options = {}
        if input_body_raw:
            input_data = json.loads(input_body_raw)
            options = input_data.get('tasks', {}).get('convert', {}).get('options', {})
        
        input_body = {
            'tasks': {
                'convert': {
                    'output_format': 'gif',
                    'options': {
                        'fps': options.get('fps', 15),
                        'width': options.get('width', 400),
                        'compression': options.get('compression', 10),
                        'loop_count': options.get('loop_count', 0),
                        'transparency': options.get('transparency', True),
                        **options
                    }
                }
            }
        }
        result = convert_to_gif(file, input_body)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@gif_converter_bp.route('/gif-to-mp4', methods=['POST'])
def gif_to_mp4():
    """Convert GIF to MP4 - specific endpoint"""
    file = request.files.get('file')
    input_body_raw = request.form.get('input_body')
    
    if not file:
        return jsonify({'error': 'Missing GIF file'}), 400
    
    try:
        options = {}
        if input_body_raw:
            input_data = json.loads(input_body_raw)
            options = input_data.get('tasks', {}).get('convert', {}).get('options', {})
        
        input_body = {
            'tasks': {
                'convert': {
                    'output_format': 'mp4',
                    'options': {
                        'fps': options.get('fps', 30),
                        'width': options.get('width'),
                        'height': options.get('height'),
                        'quality': options.get('quality', 'medium'),
                        **options
                    }
                }
            }
        }
        result = convert_from_gif(file, input_body)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@gif_converter_bp.route('/gif-to-apng', methods=['POST'])
def gif_to_apng():
    """Convert GIF to APNG (Animated PNG) - specific endpoint"""
    file = request.files.get('file')
    input_body_raw = request.form.get('input_body')
    
    if not file:
        return jsonify({'error': 'Missing GIF file'}), 400
    
    try:
        options = {}
        if input_body_raw:
            input_data = json.loads(input_body_raw)
            options = input_data.get('tasks', {}).get('convert', {}).get('options', {})
        
        input_body = {
            'tasks': {
                'convert': {
                    'output_format': 'apng',
                    'options': {
                        'fps': options.get('fps'),
                        'width': options.get('width'),
                        'height': options.get('height'),
                        'compression': options.get('compression', 6),
                        **options
                    }
                }
            }
        }
        result = convert_from_gif(file, input_body)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@gif_converter_bp.route('/image-to-gif', methods=['POST'])
def image_to_gif():
    """Convert multiple images to GIF animation - specific endpoint"""
    files = request.files.getlist('files')  # Multiple files
    input_body_raw = request.form.get('input_body')
    
    if not files:
        return jsonify({'error': 'Missing image files'}), 400
    
    try:
        options = {}
        if input_body_raw:
            input_data = json.loads(input_body_raw)
            options = input_data.get('tasks', {}).get('convert', {}).get('options', {})
        
        input_body = {
            'tasks': {
                'convert': {
                    'output_format': 'gif',
                    'options': {
                        'fps': options.get('fps', 2),  # Slower for image sequences
                        'width': options.get('width', 400),
                        'loop_count': options.get('loop_count', 0),
                        'duration_per_frame': options.get('duration_per_frame', 0.5),
                        **options
                    }
                }
            }
        }
        
        # For now, use the first file - in future this could handle multiple files
        result = convert_to_gif(files[0], input_body)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@gif_converter_bp.route('/formats', methods=['GET'])
def get_supported_formats():
    """Get list of supported GIF conversion formats"""
    from api.services.gif_converter_service import SUPPORTED_INPUT_FORMATS, SUPPORTED_OUTPUT_FORMATS
    
    return jsonify({
        'input_formats': SUPPORTED_INPUT_FORMATS,
        'output_formats': SUPPORTED_OUTPUT_FORMATS,
        'conversion_types': {
            'to_gif': ['mp4', 'webm', 'avi', 'mov', 'mkv', 'apng', 'png', 'jpg'],
            'from_gif': ['mp4', 'webm', 'apng', 'png']
        },
        'special_endpoints': [
            '/video-to-gif',
            '/mp4-to-gif',
            '/webm-to-gif',
            '/apng-to-gif',
            '/gif-to-mp4',
            '/gif-to-apng',
            '/image-to-gif'
        ]
    })

@gif_converter_bp.route('/validate-file', methods=['POST'])
def validate_file():
    """Validate if uploaded file is a valid media file"""
    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'No file provided'}), 400
    
    try:
        from api.services.gif_converter_service import validate_media_file
        import tempfile
        import os
        
        # Save file temporarily for validation
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            file.seek(0)
            temp_file.write(file.read())
            temp_file.flush()
            
            # Validate the file
            is_valid = validate_media_file(temp_file.name)
            file_size = os.path.getsize(temp_file.name)
            
            # Clean up
            os.unlink(temp_file.name)
            
            return jsonify({
                'valid': is_valid,
                'filename': file.filename,
                'file_size': file_size,
                'message': 'File is valid for conversion' if is_valid else 'File is not a valid media file'
            })
            
    except Exception as e:
        return jsonify({
            'error': 'File validation failed',
            'message': str(e)
        }), 500

@gif_converter_bp.route('/health', methods=['GET'])
def health_check():
    """Check if GIF conversion service is available and dependencies are installed"""
    try:
        import subprocess
        # Check if FFmpeg is available
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=5)
        ffmpeg_available = result.returncode == 0
        ffmpeg_version = result.stdout.split('\n')[0] if ffmpeg_available else None
    except:
        ffmpeg_available = False
        ffmpeg_version = None
    
    try:
        # Check if FFprobe is available
        result = subprocess.run(['ffprobe', '-version'], capture_output=True, text=True, timeout=5)
        ffprobe_available = result.returncode == 0
    except:
        ffprobe_available = False
    
    try:
        from PIL import Image
        pil_available = True
    except ImportError:
        pil_available = False
    
    return jsonify({
        'status': 'healthy' if (ffmpeg_available and ffprobe_available) else 'degraded',
        'dependencies': {
            'ffmpeg': ffmpeg_available,
            'ffprobe': ffprobe_available,
            'pillow': pil_available
        },
        'versions': {
            'ffmpeg': ffmpeg_version
        },
        'capabilities': {
            'video_to_gif': ffmpeg_available,
            'gif_to_video': ffmpeg_available,
            'gif_optimization': ffmpeg_available,
            'file_validation': ffprobe_available,
            'image_to_gif': pil_available
        },
        'endpoints': {
            'validate_file': '/validate-file - POST endpoint to validate media files before conversion'
        }
    })