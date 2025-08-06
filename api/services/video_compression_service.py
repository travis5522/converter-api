import os
import uuid
import subprocess
import tempfile

EXPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static', 'videos')
os.makedirs(EXPORT_DIR, exist_ok=True)

def get_video_codec_params(codec):
    """Get codec-specific parameters for video compression"""
    codec_map = {
        'h264': 'libx264',
        'h265': 'libx265', 
        'vp8': 'libvpx',
        'vp9': 'libvpx-vp9',
        'av1': 'libaom-av1'
    }
    return codec_map.get(codec, 'libx264')

def get_audio_codec_params(codec):
    """Get codec-specific parameters for audio compression"""
    codec_map = {
        'aac': 'aac',
        'mp3': 'libmp3lame',
        'opus': 'libopus',
        'vorbis': 'libvorbis'
    }
    return codec_map.get(codec, 'aac')

def parse_resolution(resolution_str):
    """Parse resolution string to width and height"""
    if not resolution_str or resolution_str == 'original':
        return None, None
    
    try:
        width, height = resolution_str.split('x')
        return int(width), int(height)
    except:
        return None, None

def compress_video(file, input_body):
    """Compress video with advanced compression settings"""
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
        
        # Get compression parameters with defaults
        video_codec = options.get('videoCodec', 'h264')
        video_bitrate = options.get('videoBitrate', 2000)  # kbps
        compression_level = options.get('compressionLevel', 23)  # CRF value
        resolution = options.get('resolution', 'original')
        frame_rate = options.get('frameRate', 'original')
        remove_audio = options.get('removeAudio', False)
        audio_codec = options.get('audioCodec', 'aac')
        audio_bitrate = options.get('audioBitrate', 128)  # kbps
        two_pass = options.get('twoPassEncoding', False)
        optimize_web = options.get('optimizeForWeb', True)
        
        # Generate output filename - ALWAYS preserve original extension for compression
        input_ext = os.path.splitext(file.filename)[1].lower()
        print(f"Original filename: {file.filename}, extracted extension: '{input_ext}'")
        # For compression, always keep the same extension as the original file
        # If no extension found, default to .mp4
        if not input_ext:
            input_ext = '.mp4'
            print(f"No extension found, defaulting to: {input_ext}")
        output_format = input_ext
        output_filename = str(uuid.uuid4()) + output_format
        output_path = os.path.join(EXPORT_DIR, output_filename)
        print(f"Final output format: '{output_format}', filename: {output_filename}")
        
        # Adjust codec based on output format for compatibility
        # For compression, we need to ensure the codec is compatible with the original format
        if output_format == '.webm':
            video_codec = 'vp8' if video_codec not in ['vp8', 'vp9'] else video_codec
            audio_codec = 'vorbis' if audio_codec not in ['vorbis', 'opus'] else audio_codec
        elif output_format == '.avi':
            video_codec = 'h264' if video_codec not in ['h264', 'h265'] else video_codec
            audio_codec = 'mp3' if audio_codec not in ['mp3', 'aac'] else audio_codec
        elif output_format == '.mov':
            video_codec = 'h264' if video_codec not in ['h264', 'h265'] else video_codec
            audio_codec = 'aac' if audio_codec not in ['aac', 'mp3'] else audio_codec
        elif output_format == '.mkv':
            # MKV is a container format, can use various codecs
            video_codec = 'h264' if video_codec not in ['h264', 'h265', 'vp8', 'vp9'] else video_codec
            audio_codec = 'aac' if audio_codec not in ['aac', 'mp3', 'vorbis', 'opus'] else audio_codec
        elif output_format == '.flv':
            video_codec = 'h264' if video_codec not in ['h264', 'h265'] else video_codec
            audio_codec = 'mp3' if audio_codec not in ['mp3', 'aac'] else audio_codec
        elif output_format == '.wmv':
            video_codec = 'h264' if video_codec not in ['h264', 'h265'] else video_codec
            audio_codec = 'mp3' if audio_codec not in ['mp3', 'aac'] else audio_codec
        elif output_format == '.m4v':
            video_codec = 'h264' if video_codec not in ['h264', 'h265'] else video_codec
            audio_codec = 'aac' if audio_codec not in ['aac', 'mp3'] else audio_codec
        elif output_format == '.3gp':
            video_codec = 'h264' if video_codec not in ['h264', 'h265'] else video_codec
            audio_codec = 'aac' if audio_codec not in ['aac', 'mp3'] else audio_codec
        # For any other format, use the user-selected codecs or defaults
        
        # Build FFmpeg command for compression
        ffmpeg_cmd = ['ffmpeg', '-y', '-i', input_path]
        
        # Video codec and compression settings
        video_codec_param = get_video_codec_params(video_codec)
        ffmpeg_cmd += ['-c:v', video_codec_param]
        
        # Compression level (CRF - lower is better quality, higher is smaller file)
        if video_codec in ['h264', 'h265']:
            ffmpeg_cmd += ['-crf', str(compression_level)]
            # Add preset for encoding speed vs compression efficiency
            ffmpeg_cmd += ['-preset', 'medium']
        elif video_codec in ['vp8', 'vp9']:
            # For VP8/VP9, use quality-based encoding
            ffmpeg_cmd += ['-crf', str(compression_level), '-b:v', '0']
        
        # Video bitrate (if not using CRF-only encoding)
        if video_codec not in ['h264', 'h265'] or two_pass:
            ffmpeg_cmd += ['-b:v', f'{video_bitrate}k']
        
        # Resolution scaling
        width, height = parse_resolution(resolution)
        vf_filters = []
        if width and height:
            vf_filters.append(f'scale={width}:{height}')
        
        # Frame rate
        if frame_rate != 'original' and frame_rate:
            try:
                fps_value = int(frame_rate)
                vf_filters.append(f'fps={fps_value}')
            except:
                pass  # Keep original frame rate if invalid
        
        # Apply video filters
        if vf_filters:
            ffmpeg_cmd += ['-vf', ','.join(vf_filters)]
        
        # Audio handling
        if remove_audio:
            ffmpeg_cmd += ['-an']  # Remove audio
        else:
            audio_codec_param = get_audio_codec_params(audio_codec)
            ffmpeg_cmd += ['-c:a', audio_codec_param]
            ffmpeg_cmd += ['-b:a', f'{audio_bitrate}k']
            
            # Audio quality settings
            if audio_codec == 'aac':
                ffmpeg_cmd += ['-profile:a', 'aac_low']
            elif audio_codec == 'mp3':
                ffmpeg_cmd += ['-q:a', '2']  # High quality MP3
        
        # Web optimization (apply appropriate optimization based on format)
        if optimize_web:
            if output_format == '.mp4':
                ffmpeg_cmd += ['-movflags', '+faststart']  # Move metadata to beginning for MP4
            elif output_format == '.webm':
                ffmpeg_cmd += ['-dash', '1']  # Enable DASH for WebM
            elif output_format == '.mkv':
                ffmpeg_cmd += ['-fflags', '+genpts']  # Generate presentation timestamps for MKV
        
        # Two-pass encoding for better quality/size ratio
        if two_pass and not remove_audio:
            # First pass
            pass1_cmd = ffmpeg_cmd + ['-pass', '1', '-f', 'null', '/dev/null']
            try:
                subprocess.run(pass1_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=600)
            except subprocess.CalledProcessError as e:
                raise Exception(f"Two-pass encoding failed on first pass: {e.stderr}")
            
            # Second pass
            ffmpeg_cmd += ['-pass', '2']
        
        # Output file
        ffmpeg_cmd += [output_path]
        
        # Run FFmpeg compression
        print(f"Running FFmpeg compression: {' '.join(ffmpeg_cmd)}")
        try:
            result = subprocess.run(
                ffmpeg_cmd, 
                check=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True, 
                timeout=600  # 10 minutes timeout for compression
            )
            print(f"FFmpeg compression completed: {result.stdout}")
        except subprocess.CalledProcessError as e:
            print(f"FFmpeg compression failed: {e.stderr}")
            raise Exception(f"Video compression failed: {e.stderr}")
        except subprocess.TimeoutExpired:
            raise Exception("Video compression timed out. The file might be too large.")
        except FileNotFoundError:
            raise Exception("FFmpeg not found. Please install FFmpeg and ensure it's in your PATH.")
        
        # Verify output file exists
        if not os.path.exists(output_path):
            raise Exception("Compression completed but output file was not created")
        
        # Get file size information
        input_size = os.path.getsize(input_path)
        output_size = os.path.getsize(output_path)
        compression_ratio = (1 - output_size / input_size) * 100 if input_size > 0 else 0
        
        # Clean up temp file
        os.remove(input_path)
        
        # Clean up two-pass encoding files
        log_files = [f'ffmpeg2pass-0.log', f'ffmpeg2pass-0.log.mbtree']
        for log_file in log_files:
            if os.path.exists(log_file):
                try:
                    os.remove(log_file)
                except:
                    pass  # Ignore cleanup errors
        
        response_data = {
            'success': True,
            'export_url': f"/export/videos/{output_filename}?ngrok-skip-browser-warning=true",
            'download_url': f"/download/videos/{output_filename}?ngrok-skip-browser-warning=true", 
            'ngrok_download_url': f"/ngrok-download/videos/{output_filename}?ngrok-skip-browser-warning=true",
            'filename': output_filename,
            'output_format': output_format.lstrip('.'),
            'compression_stats': {
                'original_size': input_size,
                'compressed_size': output_size,
                'compression_ratio': f"{compression_ratio:.1f}%",
                'size_reduction': f"{(input_size - output_size) / (1024*1024):.1f} MB"
            },
            'settings_used': {
                'video_codec': video_codec,
                'video_bitrate': video_bitrate,
                'compression_level': compression_level,
                'resolution': resolution,
                'audio_codec': audio_codec if not remove_audio else 'removed',
                'audio_bitrate': audio_bitrate if not remove_audio else 0,
                'two_pass': two_pass,
                'web_optimized': optimize_web
            },
            'message': f'Video compressed successfully. Size reduced by {compression_ratio:.1f}%'
        }
        
        print(f"Returning response with output_format: '{response_data['output_format']}'")
        return response_data
        
    except Exception as e:
        # Clean up temp file on error
        if os.path.exists(input_path):
            os.remove(input_path)
        
        # Clean up two-pass encoding files on error
        log_files = [f'ffmpeg2pass-0.log', f'ffmpeg2pass-0.log.mbtree']
        for log_file in log_files:
            if os.path.exists(log_file):
                try:
                    os.remove(log_file)
                except:
                    pass
        
        raise Exception(f"Video compression error: {str(e)}") 