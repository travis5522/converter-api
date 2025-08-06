import os
import uuid
import subprocess
import tempfile

EXPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static', 'audios')
os.makedirs(EXPORT_DIR, exist_ok=True)

def get_audio_codec_params(codec):
    """Get codec-specific parameters for audio compression"""
    codec_map = {
        'mp3': 'libmp3lame',
        'aac': 'aac',
        'opus': 'libopus',
        'vorbis': 'libvorbis',
        'flac': 'flac'
    }
    return codec_map.get(codec, 'libmp3lame')

def get_quality_bitrate(quality):
    """Get bitrate based on quality setting"""
    quality_map = {
        'high': 320,
        'medium': 192,
        'low': 128
    }
    return quality_map.get(quality, 192)

def compress_audio(file, input_body):
    """Compress audio with advanced compression settings"""
    # Save uploaded file to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_input:
        file.save(temp_input.name)
        input_path = temp_input.name

    try:
        # Validate input structure
        if 'tasks' not in input_body or 'compress' not in input_body['tasks']:
            raise Exception("Invalid input structure: missing 'tasks' or 'compress'")
        
        compress_task = input_body['tasks']['compress']
        options = compress_task.get('options', {})
        if options is None:
            options = {}
        
        # Get compression parameters with defaults - using the new structure
        compression_method = options.get('compression_method', 'percentage')
        target_size_percentage = options.get('target_size_percentage', 40)
        target_size_mb = options.get('target_size_mb', 5)
        audio_quality = options.get('audio_quality', 'medium')
        
        # Generate output filename - always MP3 for compression
        output_filename = str(uuid.uuid4()) + '.mp3'
        output_path = os.path.join(EXPORT_DIR, output_filename)
        
        # Get original file size for calculations
        input_size = os.path.getsize(input_path)
        input_size_mb = input_size / (1024 * 1024)
        
        # Build FFmpeg command for audio compression
        ffmpeg_cmd = ['ffmpeg', '-y', '-i', input_path]
        
        # Set audio codec to MP3
        ffmpeg_cmd += ['-c:a', 'libmp3lame']
        
        # Apply compression based on method
        if compression_method == 'percentage':
            # Calculate target bitrate based on percentage
            target_size_bytes = int(input_size * (target_size_percentage / 100))
            target_size_mb_calc = target_size_bytes / (1024 * 1024)
            
            # Estimate bitrate based on target size (rough calculation)
            # For MP3, roughly 1MB per minute at 128kbps
            # We'll use a more sophisticated calculation
            duration_cmd = ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration', '-of', 'csv=p=0', input_path]
            try:
                duration_result = subprocess.run(duration_cmd, capture_output=True, text=True, check=True)
                duration = float(duration_result.stdout.strip())
            except:
                duration = 180  # Default 3 minutes if we can't get duration
            
            # Calculate bitrate: (target_size_bytes * 8) / (duration * 1000)
            target_bitrate = int((target_size_bytes * 8) / (duration * 1000))
            target_bitrate = max(32, min(320, target_bitrate))  # Clamp between 32 and 320 kbps
            
            ffmpeg_cmd += ['-b:a', f'{target_bitrate}k']
            
        elif compression_method == 'mb':
            # Calculate target bitrate based on target size in MB
            duration_cmd = ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration', '-of', 'csv=p=0', input_path]
            try:
                duration_result = subprocess.run(duration_cmd, capture_output=True, text=True, check=True)
                duration = float(duration_result.stdout.strip())
            except:
                duration = 180  # Default 3 minutes if we can't get duration
            
            # Calculate bitrate: (target_size_mb * 1024 * 1024 * 8) / (duration * 1000)
            target_bitrate = int((target_size_mb * 1024 * 1024 * 8) / (duration * 1000))
            target_bitrate = max(32, min(320, target_bitrate))  # Clamp between 32 and 320 kbps
            
            ffmpeg_cmd += ['-b:a', f'{target_bitrate}k']
            
        elif compression_method == 'quality':
            # Use quality-based compression
            quality_bitrate = get_quality_bitrate(audio_quality)
            ffmpeg_cmd += ['-b:a', f'{quality_bitrate}k']
            
            # Add quality settings for MP3
            if audio_quality == 'high':
                ffmpeg_cmd += ['-q:a', '0']  # Best quality
            elif audio_quality == 'medium':
                ffmpeg_cmd += ['-q:a', '2']  # Good quality
            else:  # low
                ffmpeg_cmd += ['-q:a', '5']  # Lower quality
        
        # Output file
        ffmpeg_cmd += [output_path]
        
        # Run FFmpeg compression
        print(f"Running FFmpeg audio compression: {' '.join(ffmpeg_cmd)}")
        try:
            result = subprocess.run(
                ffmpeg_cmd, 
                check=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True, 
                timeout=300  # 5 minutes timeout for audio compression
            )
            print(f"FFmpeg audio compression completed: {result.stdout}")
        except subprocess.CalledProcessError as e:
            print(f"FFmpeg audio compression failed: {e.stderr}")
            raise Exception(f"Audio compression failed: {e.stderr}")
        except subprocess.TimeoutExpired:
            raise Exception("Audio compression timed out. The file might be too large.")
        except FileNotFoundError:
            raise Exception("FFmpeg not found. Please install FFmpeg and ensure it's in your PATH.")
        
        # Verify output file exists
        if not os.path.exists(output_path):
            raise Exception("Compression completed but output file was not created")
        
        # Get file size information
        output_size = os.path.getsize(output_path)
        output_size_mb = output_size / (1024 * 1024)
        compression_ratio = (1 - output_size / input_size) * 100 if input_size > 0 else 0
        
        # Clean up temp file
        os.remove(input_path)
        
        # Prepare response data
        response_data = {
            'success': True,
            'export_url': f"/export/audios/{output_filename}?ngrok-skip-browser-warning=true",
            'download_url': f"/download/audios/{output_filename}?ngrok-skip-browser-warning=true", 
            'ngrok_download_url': f"/ngrok-download/audios/{output_filename}?ngrok-skip-browser-warning=true",
            'filename': output_filename,
            'output_format': 'mp3',
            'compression_stats': {
                'original_size': input_size,
                'compressed_size': output_size,
                'original_size_mb': f"{input_size_mb:.2f}",
                'compressed_size_mb': f"{output_size_mb:.2f}",
                'compression_ratio': f"{compression_ratio:.1f}%",
                'size_reduction': f"{(input_size - output_size) / (1024*1024):.2f} MB"
            },
            'settings_used': {
                'compression_method': compression_method,
                'target_size_percentage': target_size_percentage if compression_method == 'target_file_size_percentage' else None,
                'target_size_mb': target_size_mb if compression_method == 'target_file_size_mb' else None,
                'audio_quality': audio_quality if compression_method == 'target_audio_quality' else None
            },
            'message': f'Audio compressed successfully. Size reduced by {compression_ratio:.1f}%'
        }
        
        print(f"Returning audio compression response with output_format: '{response_data['output_format']}'")
        return response_data
        
    except Exception as e:
        # Clean up temp file on error
        if os.path.exists(input_path):
            os.remove(input_path)
        
        raise Exception(f"Audio compression error: {str(e)}") 