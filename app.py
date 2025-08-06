from flask import Flask, request, make_response, send_file, send_from_directory, jsonify
from flask_cors import CORS
from api.controller.video_to_video_controller import video_to_video_bp
from api.controller.video_to_audio_controller import video_to_audio_bp
from api.controller.audio_to_audio_controller import audio_to_audio_bp
from api.controller.image_converter_controller import image_converter_bp
from api.controller.document_converter_controller import document_converter_bp
from api.controller.gif_converter_controller import gif_converter_bp
from api.controller.video_tools_controller import video_tools_bp
from api.controller.image_tools_controller import image_tools_bp
from api.controller.pdf_tools_controller import pdf_tools_bp
from api.controller.archive_converter_controller import archive_converter_bp
from api.controller.video_compression_controller import video_compression_bp
from api.controller.audio_compression_controller import audio_compression_bp
import os
import mimetypes
from flask import Response

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'), static_url_path='/static')

# Configure file upload limits (allow up to 500MB uploads)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static')

# Initialize CORS
CORS(app)

# Error handler for file size limit exceeded
@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large error"""
    return jsonify({
        'error': 'File too large',
        'message': f'File size exceeds maximum allowed size of {app.config["MAX_CONTENT_LENGTH"] // (1024*1024)}MB'
    }), 413

# Middleware to handle ngrok browser warning
@app.before_request
def handle_ngrok_headers():
    """Skip ngrok browser warning by checking for ngrok headers"""
    # For ngrok free accounts, check if this is the browser warning page
    if request.headers.get('ngrok-skip-browser-warning') == 'any':
        return  # Continue with request
    
    # Add debug logging for ngrok requests
    if any(host in request.host for host in ['ngrok.io', 'ngrok-free.app', 'ngrok.app']):
        print(f"Ngrok request to: {request.method} {request.url}")
        print(f"Headers: {dict(request.headers)}")
        
        # Check if this looks like ngrok's browser warning
        user_agent = request.headers.get('User-Agent', '')
        if 'Mozilla' in user_agent and request.method == 'GET' and not request.headers.get('ngrok-skip-browser-warning'):
            print("Warning: This might be ngrok's browser warning page")
    
    # Handle OPTIONS requests for CORS preflight
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS, HEAD'
        response.headers['Access-Control-Allow-Headers'] = '*'
        response.headers['ngrok-skip-browser-warning'] = 'true'
        return response

@app.after_request
def after_request(response):
    """Add headers to all responses"""
    # Add ngrok header to skip browser warning
    response.headers['ngrok-skip-browser-warning'] = 'true'
    
    # Ensure CORS headers are present for all responses
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS, HEAD'
    response.headers['Access-Control-Allow-Headers'] = '*'
    response.headers['Access-Control-Expose-Headers'] = 'Content-Disposition'
    
    # Only add cache control if it's not a download endpoint
    # Download endpoints set their own cache control headers
    if not (request.endpoint and ('download' in request.endpoint or 'export' in request.endpoint)):
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    
    return response

# Test endpoint to verify CORS is working
@app.route('/test-cors', methods=['GET'])
def test_cors():
    """Test endpoint to verify CORS configuration"""
    return {'message': 'CORS is working correctly!', 'status': 'success'}

# Health check endpoint to verify FFmpeg installation
@app.route('/health/ffmpeg', methods=['GET'])
def check_ffmpeg():
    """Check if FFmpeg is installed and accessible"""
    try:
        import subprocess
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0] if result.stdout else 'Unknown version'
            return {
                'status': 'success',
                'message': 'FFmpeg is available',
                'version': version_line
            }
        else:
            return {
                'status': 'error',
                'message': 'FFmpeg command failed',
                'stderr': result.stderr
            }, 500
    except FileNotFoundError:
        return {
            'status': 'error',
            'message': 'FFmpeg not found - please install FFmpeg'
        }, 500
    except subprocess.TimeoutExpired:
        return {
            'status': 'error',
            'message': 'FFmpeg command timed out'
        }, 500
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error checking FFmpeg: {str(e)}'
        }, 500

# Debug endpoint to check request details
@app.route('/debug/request', methods=['GET', 'POST'])
def debug_request():
    """Debug endpoint to check how requests are being received"""
    return {
        'method': request.method,
        'url': request.url,
        'headers': dict(request.headers),
        'args': dict(request.args),
        'form': dict(request.form),
        'files': list(request.files.keys()),
        'remote_addr': request.remote_addr,
        'host': request.host
    }

# Test download endpoints
@app.route('/test/download-endpoints', methods=['GET'])
def test_download_endpoints():
    """Test if download endpoints are working and list available files"""
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    
    result = {
        'endpoints': {
            'export': '/export/<file_type>/<filename>',
            'download': '/download/<file_type>/<filename>', 
            'ngrok_download': '/ngrok-download/<file_type>/<filename>'
        },
        'available_files': {}
    }
    
    # Check each directory for available files
    for file_type in ['videos', 'images', 'audios', 'documents', 'gifs']:
        directory = os.path.join(static_dir, file_type)
        if os.path.exists(directory):
            files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
            result['available_files'][file_type] = files
        else:
            result['available_files'][file_type] = []
    
    return jsonify(result)

# Enhanced export endpoint with proper CORS headers
@app.route('/export/<file_type>/<filename>')
def export_file(file_type, filename):
    """Export converted files with proper CORS headers (alternative to static serving)"""
    return _serve_file(file_type, filename, as_attachment=False)

# Download endpoint - forces file download
@app.route('/download/<file_type>/<filename>')
def download_file(file_type, filename):
    """Download converted files with forced download headers"""
    return _serve_file(file_type, filename, as_attachment=True)

# Ngrok-specific download endpoint with enhanced headers
@app.route('/ngrok-download/<file_type>/<filename>')
def ngrok_download_file(file_type, filename):
    """Download files with ngrok-specific headers and optimizations"""
    return _serve_file(file_type, filename, as_attachment=True, ngrok_optimized=True)

def _serve_file(file_type, filename, as_attachment=True, ngrok_optimized=False):
    """Helper function to serve files with proper headers"""
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    
    # Map file types to directories
    type_mapping = {
        'images': 'images',
        'videos': 'videos', 
        'audios': 'audios',
        'documents': 'documents',
        'gifs': 'gifs',
        'archives': 'archives'
    }
    
    if file_type not in type_mapping:
        return jsonify({'error': 'Invalid file type'}), 400
    
    directory = os.path.join(static_dir, type_mapping[file_type])
    file_path = os.path.join(directory, filename)
    
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    
    # Get file info
    file_size = os.path.getsize(file_path)
    
    # Detect MIME type
    mime_type, _ = mimetypes.guess_type(filename)
    if not mime_type:
        mime_type = 'application/octet-stream'
    
    try:
        # Create response
        response = send_file(
            file_path,
            as_attachment=as_attachment,
            download_name=filename,
            mimetype=mime_type
        )
        
        # Add standard headers
        response.headers['Content-Length'] = str(file_size)
        response.headers['Accept-Ranges'] = 'bytes'
        
        # Add ngrok-specific headers
        if ngrok_optimized:
            response.headers['ngrok-skip-browser-warning'] = 'true'
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        
        # Force download headers
        if as_attachment:
            response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
            
        # Add CORS headers for downloads
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Expose-Headers'] = 'Content-Disposition, Content-Length'
        
        return response
        
    except Exception as e:
        return jsonify({'error': f'Error serving file: {str(e)}'}), 500

# Test endpoint for error handling
@app.route('/test-error-handling', methods=['POST'])
def test_error_handling():
    """Test endpoint to verify error handling"""
    # Test the exact payload that was causing issues
    input_body_raw = request.form.get('input_body')
    if not input_body_raw:
        return jsonify({
            'error': 'Missing input data',
            'message': 'No input_body provided'
        }), 400
    
    try:
        import json
        input_body = json.loads(input_body_raw)
        
        # Validate input structure
        if not isinstance(input_body, dict):
            return jsonify({
                'error': 'Invalid input format',
                'message': 'input_body must be a valid JSON object'
            }), 400
        
        if 'tasks' not in input_body:
            return jsonify({
                'error': 'Missing tasks',
                'message': 'input_body must contain a "tasks" object'
            }), 400
        
        if 'convert' not in input_body['tasks']:
            return jsonify({
                'error': 'Missing convert task',
                'message': 'tasks must contain a "convert" object'
            }), 400
        
        # Test options handling
        options = input_body['tasks']['convert'].get('options', {})
        if options is None:
            options = {}
        
        return jsonify({
            'success': True,
            'message': 'Error handling test passed',
            'options_received': options,
            'options_type': type(options).__name__
        })
        
    except json.JSONDecodeError as e:
        return jsonify({
            'error': 'Invalid JSON',
            'message': f'Failed to parse input_body: {str(e)}'
        }), 400
        
    except Exception as e:
        return jsonify({
            'error': 'Test failed',
            'message': str(e)
        }), 500

# Register blueprints for each conversion type
app.register_blueprint(video_to_video_bp, url_prefix='/api/video_video')
app.register_blueprint(video_to_audio_bp, url_prefix='/api/video_audio')
app.register_blueprint(audio_to_audio_bp, url_prefix='/api/audio_audio')
app.register_blueprint(image_converter_bp, url_prefix='/api/image')
app.register_blueprint(document_converter_bp, url_prefix='/api/document')
app.register_blueprint(gif_converter_bp, url_prefix='/api/gif')
app.register_blueprint(video_compression_bp, url_prefix='/api/video_compression')
app.register_blueprint(audio_compression_bp, url_prefix='/api/audio_compression')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)