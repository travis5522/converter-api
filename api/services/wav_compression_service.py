import os
import subprocess
import tempfile
import shutil
from datetime import datetime

def get_wav_compression_params(compression_level):
    """
    Get FFmpeg parameters based on compression level
    """
    if compression_level == 'low':
        # Low compression - high quality, larger file
        return {
            'bitrate': '320k',
            'sample_rate': '44100',
            'channels': '2'
        }
    elif compression_level == 'medium':
        # Medium compression - balanced quality and size
        return {
            'bitrate': '192k',
            'sample_rate': '44100',
            'channels': '2'
        }
    elif compression_level == 'strong':
        # Strong compression - smaller file, some quality loss
        return {
            'bitrate': '128k',
            'sample_rate': '22050',
            'channels': '2'
        }
    else:
        # Default to medium
        return {
            'bitrate': '192k',
            'sample_rate': '44100',
            'channels': '2'
        }

def compress_wav(file, input_body):
    """
    Compress WAV audio files using FFmpeg
    
    Args:
        file: Uploaded WAV file
        input_body: JSON with compression options
    
    Returns:
        dict: Result with success status and download URL
    """
    try:
        # Create temporary directory for processing
        temp_dir = tempfile.mkdtemp()
        input_path = os.path.join(temp_dir, file.filename)
        output_filename = f"compressed_{file.filename}"
        output_path = os.path.join(temp_dir, output_filename)
        
        # Save uploaded file
        file.save(input_path)
        
        # Get compression options from input_body
        tasks = input_body.get('tasks', {})
        compress_task = tasks.get('compress', {})
        options = compress_task.get('options', {})
        
        # Get compression parameters
        compression_level = options.get('wav_compression_level', 'medium')
        compression_params = get_wav_compression_params(compression_level)
        
        # Build FFmpeg command for WAV compression
        ffmpeg_cmd = [
            'ffmpeg',
            '-i', input_path,
            '-c:a', 'pcm_s16le',  # WAV format
            '-ar', compression_params['sample_rate'],
            '-ac', compression_params['channels'],
            '-y',  # Overwrite output file
            output_path
        ]
        
        print(f"FFmpeg command: {' '.join(ffmpeg_cmd)}")
        
        # Execute FFmpeg command
        result = subprocess.run(
            ffmpeg_cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )
        
        if result.returncode != 0:
            print(f"FFmpeg error: {result.stderr}")
            raise Exception(f"FFmpeg compression failed: {result.stderr}")
        
        # Check if output file exists and has size > 0
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise Exception("Compression failed - output file is empty or missing")
        
        # Create static directory if it doesn't exist
        static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static', 'audios')
        os.makedirs(static_dir, exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"wav_compressed_{timestamp}_{output_filename}"
        final_path = os.path.join(static_dir, unique_filename)
        
        # Move compressed file to static directory
        shutil.move(output_path, final_path)
        
        # Get file size
        file_size = os.path.getsize(final_path)
        
        # Create download URL (use absolute URL for cross-domain requests)
        # Try to get the base URL from the request context
        try:
            from flask import request
            base_url = request.url_root.rstrip('/')
            # Force HTTPS for ngrok URLs to avoid CORS redirect issues
            if 'ngrok' in base_url and base_url.startswith('http://'):
                base_url = base_url.replace('http://', 'https://')
            download_url = f"{base_url}/static/audios/{unique_filename}"
        except:
            # Fallback to relative URL if request context is not available
            download_url = f"/static/audios/{unique_filename}"
        
        # Prepare response data
        response_data = {
            'success': True,
            'message': f'WAV file compressed successfully with {compression_level} compression level',
            'download_url': download_url,
            'export_url': download_url,
            'file_size': file_size,
            'output_format': 'wav',
            'wav_compression_level': compression_level
        }
        
        print(f"WAV compression successful. Output format: {response_data['output_format']}")
        
        # Clean up temporary directory
        shutil.rmtree(temp_dir)
        
        return response_data
        
    except subprocess.CalledProcessError as e:
        print(f"Subprocess error: {str(e)}")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        raise Exception(f"Compression process failed: {str(e)}")
        
    except subprocess.TimeoutExpired:
        print("Compression timeout")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        raise Exception("Compression timed out")
        
    except FileNotFoundError:
        print("FFmpeg not found")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        raise Exception("FFmpeg is not installed or not in PATH")
        
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        raise Exception(f"Compression failed: {str(e)}") 