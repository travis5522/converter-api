import os
import uuid
import subprocess
import tempfile
from PIL import Image
import json

EXPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static', 'videos')
os.makedirs(EXPORT_DIR, exist_ok=True)

SUPPORTED_VIDEO_FORMATS = ['mp4', 'avi', 'mov', 'webm', 'mkv', 'wmv']

def crop_video(file, input_body):
    """Crop video to specified dimensions"""
    # Save uploaded file to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_input:
        file.save(temp_input.name)
        input_path = temp_input.name

    try:
        # Validate input structure
        if 'tasks' not in input_body or 'crop' not in input_body['tasks']:
            raise Exception("Invalid input structure: missing 'tasks' or 'crop'")
        
        crop_task = input_body['tasks']['crop']
        options = crop_task.get('options', {})
        
        # Get crop parameters
        x = options.get('x', 0)
        y = options.get('y', 0)
        width = options.get('width')
        height = options.get('height')
        
        if not width or not height:
            raise Exception("Crop dimensions (width and height) are required")
        
        # Get output format
        output_format = options.get('output_format', 'mp4').lower()
        if output_format not in SUPPORTED_VIDEO_FORMATS:
            raise Exception(f"Unsupported output format: {output_format}")
        
        output_filename = str(uuid.uuid4()) + f'.{output_format}'
        output_path = os.path.join(EXPORT_DIR, output_filename)
        
        # Build ffmpeg command for cropping
        ffmpeg_cmd = [
            'ffmpeg', '-y', '-i', input_path,
            '-vf', f'crop={width}:{height}:{x}:{y}',
            '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
            '-c:a', 'aac', '-b:a', '128k',
            output_path
        ]
        
        # Execute ffmpeg command
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            raise Exception(f"FFmpeg error: {result.stderr}")
        
        return {
            'success': True,
            'message': 'Video cropped successfully',
            'output_filename': output_filename,
            'download_url': f'/download/videos/{output_filename}'
        }
        
    except Exception as e:
        raise Exception(f"Crop video failed: {str(e)}")
    finally:
        # Clean up temporary file
        if 'input_path' in locals():
            try:
                os.unlink(input_path)
            except:
                pass

def trim_video(file, input_body):
    """Trim video to specified time range"""
    # Save uploaded file to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_input:
        file.save(temp_input.name)
        input_path = temp_input.name

    try:
        # Validate input structure
        if 'tasks' not in input_body or 'trim' not in input_body['tasks']:
            raise Exception("Invalid input structure: missing 'tasks' or 'trim'")
        
        trim_task = input_body['tasks']['trim']
        options = trim_task.get('options', {})
        
        # Get trim parameters
        start_time = options.get('start_time', 0)
        duration = options.get('duration')
        end_time = options.get('end_time')
        
        if not duration and not end_time:
            raise Exception("Either duration or end_time must be specified")
        
        # Get output format
        output_format = options.get('output_format', 'mp4').lower()
        if output_format not in SUPPORTED_VIDEO_FORMATS:
            raise Exception(f"Unsupported output format: {output_format}")
        
        output_filename = str(uuid.uuid4()) + f'.{output_format}'
        output_path = os.path.join(EXPORT_DIR, output_filename)
        
        # Build ffmpeg command for trimming
        ffmpeg_cmd = ['ffmpeg', '-y', '-i', input_path]
        
        if end_time:
            # Use end_time if provided
            ffmpeg_cmd.extend(['-ss', str(start_time), '-to', str(end_time)])
        else:
            # Use duration if provided
            ffmpeg_cmd.extend(['-ss', str(start_time), '-t', str(duration)])
        
        ffmpeg_cmd.extend([
            '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
            '-c:a', 'aac', '-b:a', '128k',
            output_path
        ])
        
        # Execute ffmpeg command
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            raise Exception(f"FFmpeg error: {result.stderr}")
        
        return {
            'success': True,
            'message': 'Video trimmed successfully',
            'output_filename': output_filename,
            'download_url': f'/download/videos/{output_filename}'
        }
        
    except Exception as e:
        raise Exception(f"Trim video failed: {str(e)}")
    finally:
        # Clean up temporary file
        if 'input_path' in locals():
            try:
                os.unlink(input_path)
            except:
                pass 