import os
import uuid
import subprocess
import tempfile

EXPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static', 'audios')
os.makedirs(EXPORT_DIR, exist_ok=True)

# Supported audio output formats for video-to-audio conversion
SUPPORTED_FORMATS = ['aac', 'aiff', 'alac', 'amr', 'flac', 'm4a', 'mp3', 'ogg', 'wav', 'wma']

def get_default_audio_codec(output_format):
    """Get the default FFmpeg audio codec for each output format"""
    codec_mapping = {
        'aac': 'aac',
        'aiff': 'pcm_s16be',
        'alac': 'alac',
        'amr': 'amrnb',  # AMR Narrowband
        'flac': 'flac',
        'm4a': 'aac',  # M4A typically uses AAC codec
        'mp3': 'libmp3lame',
        'ogg': 'libvorbis',
        'wav': 'pcm_s16le',
        'wma': 'wmav2'
    }
    return codec_mapping.get(output_format, 'aac')

def get_format_specific_options(output_format, ffmpeg_cmd):
    """Add format-specific FFmpeg options for optimal encoding"""
    if output_format == 'aac':
        # AAC: Good quality and compression
        ffmpeg_cmd += ['-b:a', '192k']
    elif output_format == 'mp3':
        # MP3: Good quality
        ffmpeg_cmd += ['-b:a', '192k']
    elif output_format == 'flac':
        # FLAC: Lossless compression
        ffmpeg_cmd += ['-compression_level', '5']
    elif output_format == 'ogg':
        # OGG Vorbis: Good quality
        ffmpeg_cmd += ['-q:a', '5']
    elif output_format == 'alac':
        # ALAC: Lossless
        pass  # ALAC doesn't need additional quality settings
    elif output_format == 'aiff':
        # AIFF: Uncompressed
        pass
    elif output_format == 'wav':
        # WAV: Uncompressed
        pass
    elif output_format == 'wma':
        # WMA: Set bitrate
        ffmpeg_cmd += ['-b:a', '192k']
    elif output_format == 'amr':
        # AMR: Set sample rate (AMR only supports 8kHz)
        ffmpeg_cmd += ['-ar', '8000', '-b:a', '12.2k']
    elif output_format == 'm4a':
        # M4A: AAC in MP4 container
        ffmpeg_cmd += ['-b:a', '192k']
    
    return ffmpeg_cmd

def convert_video_to_audio(file, input_body):
    """Extract audio from video file and convert to specified audio format"""
    # Save uploaded file to temporary location
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_input:
        file.save(temp_input.name)
        input_path = temp_input.name

    try:
        # Parse conversion task - support both old and new format
        convert_task = input_body['tasks']['convert']
        
        # New format has input_format and output_format at same level
        if 'input_format' in convert_task and 'output_format' in convert_task:
            input_format = convert_task.get('input_format', 'mp4').lower()
            output_format = convert_task.get('output_format', 'mp3').lower()
        else:
            # Legacy format support
            input_format = 'unknown'
            output_format = convert_task.get('output_format', 'mp3').lower()
        
        # Validate output format
        if output_format not in SUPPORTED_FORMATS:
            raise Exception(f"Unsupported output format: {output_format}. Supported formats: {', '.join(SUPPORTED_FORMATS)}")
        
        # Generate output filename and path
        output_filename = str(uuid.uuid4()) + f'.{output_format}'
        output_path = os.path.join(EXPORT_DIR, output_filename)

        # Parse options and convert new format to internal format
        options = _parse_audio_options(convert_task.get('options', {}))
        
        # Build FFmpeg command - disable video stream with -vn
        ffmpeg_cmd = ['ffmpeg', '-y', '-i', input_path, '-vn']
        
        # Set audio codec
        audio_codec = options.get('audio_codec')
        if not audio_codec or audio_codec == 'auto':
            audio_codec = get_default_audio_codec(output_format)
        ffmpeg_cmd += ['-c:a', audio_codec]
        
        # Add format-specific encoding options
        ffmpeg_cmd = get_format_specific_options(output_format, ffmpeg_cmd)
        
        # Audio quality settings (if specified)
        if options.get('audio_bitrate'):
            ffmpeg_cmd += ['-b:a', f"{options['audio_bitrate']}k"]
        
        if options.get('audio_sample_rate'):
            ffmpeg_cmd += ['-ar', str(options['audio_sample_rate'])]
        
        if options.get('audio_channels'):
            ffmpeg_cmd += ['-ac', str(options['audio_channels'])]
        
        # Audio filters
        af_filters = []
        
        # Volume adjustment
        if options.get('audio_filter_volume') and options['audio_filter_volume'] != 100:
            af_filters.append(f"volume={options['audio_filter_volume']/100}")
        
        # Fade in/out effects
        if options.get('audio_filter_fade_in'):
            fade_duration = options.get('fade_in_duration', 3)
            af_filters.append(f'afade=t=in:ss=0:d={fade_duration}')
        
        if options.get('audio_filter_fade_out'):
            fade_duration = options.get('fade_out_duration', 3)
            af_filters.append(f'afade=t=out:st={fade_duration}:d={fade_duration}')
        
        # Audio reverse effect
        if options.get('audio_filter_reverse'):
            af_filters.append('areverse')
        
        # Apply audio filters if any
        if af_filters:
            ffmpeg_cmd += ['-af', ','.join(af_filters)]
        
        # Extract specific time range from video - handle both cut_start/cut_end and trim_start/trim_end
        start_time = options.get('cut_start') or options.get('trim_start')
        end_time = options.get('cut_end') or options.get('trim_end')
        
        if start_time and start_time != "00:00:00.00" and start_time != "00:00:00":
            ffmpeg_cmd += ['-ss', start_time]
        
        if end_time and end_time != "00:00:00.00" and end_time != "00:00:00":
            ffmpeg_cmd += ['-to', end_time]
        
        # Add output path
        ffmpeg_cmd += [output_path]
        
        # Execute FFmpeg conversion
        result = subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Clean up temporary file
        os.remove(input_path)
        
        # Return success response with download URL
        return {
            'success': True,
            'export_url': f"/static/audios/{output_filename}",
            'download_url': f"/download/audios/{output_filename}",
            'filename': output_filename,
            'output_format': output_format,
            'input_format': input_format,
            'codec_used': audio_codec,
            'source_type': 'video'
        }
        
    except subprocess.CalledProcessError as e:
        # Clean up on FFmpeg error
        if os.path.exists(input_path):
            os.remove(input_path)
        raise Exception(f"FFmpeg conversion error: {e.stderr.decode()}")
    
    except Exception as e:
        # Clean up on any other error
        if os.path.exists(input_path):
            os.remove(input_path)
        raise Exception(f"Conversion error: {str(e)}")

def _parse_audio_options(options):
    """Parse and convert new format options to internal format"""
    internal_options = {}
    
    # Direct mapping for most options
    option_mapping = {
        'audio_codec': 'audio_codec',
        'audio_filter_volume': 'audio_filter_volume',
        'audio_filter_fade_in': 'audio_filter_fade_in',
        'audio_filter_fade_out': 'audio_filter_fade_out',
        'audio_filter_reverse': 'audio_filter_reverse',
        'cut_start': 'cut_start',
        'cut_end': 'cut_end'
    }
    
    for old_key, new_key in option_mapping.items():
        if old_key in options:
            internal_options[new_key] = options[old_key]
    
    # Handle legacy options
    for key in ['trim_start', 'trim_end', 'audio_bitrate', 'audio_sample_rate', 'audio_channels', 'fade_in_duration', 'fade_out_duration']:
        if key in options:
            internal_options[key] = options[key]
    
    return internal_options 