from flask import Flask, request, make_response, send_from_directory, jsonify
from flask_cors import CORS
from api.controller.video_to_video_controller import video_to_video_bp
from api.controller.video_to_audio_controller import video_to_audio_bp
from api.controller.audio_to_audio_controller import audio_to_audio_bp
from api.controller.image_converter_controller import image_converter_bp
from api.controller.document_converter_controller import document_converter_bp
from api.controller.gif_converter_controller import gif_converter_bp
import os

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'), static_url_path='/static')

# Initialize CORS
CORS(app, 
     origins=['http://localhost:8080'],
     supports_credentials=True,
     allow_headers=['*'],
     methods=['GET', 'POST', 'OPTIONS', 'HEAD'])

# Download endpoint for converted files
@app.route('/download/<file_type>/<filename>')
def download_file(file_type, filename):
    """Download converted files"""
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    
    if file_type == 'images':
        directory = os.path.join(static_dir, 'images')
    elif file_type == 'videos':
        directory = os.path.join(static_dir, 'videos')
    elif file_type == 'audios':
        directory = os.path.join(static_dir, 'audios')
    elif file_type == 'documents':
        directory = os.path.join(static_dir, 'documents')
    elif file_type == 'gifs':
        directory = os.path.join(static_dir, 'gifs')
    else:
        return {'error': 'Invalid file type'}, 400
    
    file_path = os.path.join(directory, filename)
    if not os.path.exists(file_path):
        return {'error': 'File not found'}, 404
    
    return send_from_directory(directory, filename, as_attachment=True)

# Test endpoint to verify CORS is working
@app.route('/test-cors', methods=['GET'])
def test_cors():
    """Test endpoint to verify CORS configuration"""
    return {'message': 'CORS is working correctly!', 'status': 'success'}

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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)