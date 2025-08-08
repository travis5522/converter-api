import os
import uuid
import subprocess
import tempfile

EXPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static', 'videos')
os.makedirs(EXPORT_DIR, exist_ok=True)

SUPPORTED_FORMATS = [
    'mp4', 'wmv', 'avi', 'mov', 'webm', 'mkv',
    'mp3', 'wav', 'aac'
]
AUDIO_ONLY_FORMATS = ['mp3', 'wav', 'aac']

def get_default_video_codec(output_format):
    if output_format == 'wmv':
        return 'wmv2'
    elif output_format == 'mp4':
        return 'libx264'
    elif output_format == 'avi':
        return 'mpeg4'
    elif output_format == 'mov':
        return 'libx264'  # Use libx264 for compatibility and efficiency
    elif output_format == 'webm':
        return 'libvpx'
    elif output_format == 'mkv':
        return 'libx264'
    return 'libx264'

def get_default_audio_codec(output_format):
    if output_format == 'wmv':
        return 'wmav2'
    elif output_format == 'mp4':
        return 'aac'
    elif output_format == 'avi':
        return 'mp3'
    elif output_format == 'mov':
        return 'aac'
    elif output_format == 'webm':
        return 'libvorbis'
    elif output_format == 'mkv':
        return 'aac'
    elif output_format == 'mp3':
        return 'libmp3lame'
    elif output_format == 'wav':
        return 'pcm_s16le'
    elif output_format == 'aac':
        return 'aac'
    return 'aac'

def add_x264_quality_params(ffmpeg_cmd, video_codec, output_format):
    # Add CRF and preset for x264-based codecs to control file size and quality
    if video_codec == 'libx264' or (output_format in ['mp4', 'mov', 'mkv'] and video_codec == 'auto'):
        ffmpeg_cmd += ['-preset', 'medium', '-crf', '23']
    return ffmpeg_cmd

def convert_video(file, input_body):
    # Save uploaded file to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_input:
        file.save(temp_input.name)
        input_path = temp_input.name

    try:
        # Validate input structure
        if 'tasks' not in input_body or 'convert' not in input_body['tasks']:
            raise Exception("Invalid input structure: missing 'tasks' or 'convert'")
        
        convert_task = input_body['tasks']['convert']
        output_format = convert_task.get('output_format', 'mp4').lower()
        
        if output_format not in SUPPORTED_FORMATS:
            raise Exception(f"Unsupported output format: {output_format}. Supported formats: {', '.join(SUPPORTED_FORMATS)}")
        
        output_filename = str(uuid.uuid4()) + f'.{output_format}'
        output_path = os.path.join(EXPORT_DIR, output_filename)

        # Build ffmpeg command based on options
        options = convert_task.get('options', {})
        if options is None:
            options = {}  # Ensure options is always a dict
        
        is_audio_only = output_format in AUDIO_ONLY_FORMATS
        ffmpeg_cmd = ['ffmpeg', '-y', '-i', input_path]

        if is_audio_only:
            # Audio-only: disable video, set audio codec
            audio_codec = options.get('audio_codec')
            if not audio_codec or audio_codec == 'auto':
                audio_codec = get_default_audio_codec(output_format)
            ffmpeg_cmd += ['-vn', '-c:a', audio_codec]
            # Audio filters (volume, fade in/out)
            af_filters = []
            if options.get('audio_filter_volume') and options['audio_filter_volume'] != 100:
                af_filters.append(f"volume={options['audio_filter_volume']/100}")
            if options.get('audio_filter_fade_in'):
                af_filters.append('afade=t=in:ss=0:d=3')
            if options.get('audio_filter_fade_out'):
                af_filters.append('afade=t=out:st=3:d=3')
            if af_filters:
                ffmpeg_cmd += ['-af', ','.join(af_filters)]
        else:
            # Video+audio: set video and audio codecs, filters, etc.
            video_codec = options.get('video_codec')
            if not video_codec or video_codec == 'auto':
                video_codec = get_default_video_codec(output_format)
            ffmpeg_cmd += ['-c:v', video_codec]
            ffmpeg_cmd = add_x264_quality_params(ffmpeg_cmd, video_codec, output_format)
            audio_codec = options.get('audio_codec')
            if not audio_codec or audio_codec == 'auto':
                audio_codec = get_default_audio_codec(output_format)
            ffmpeg_cmd += ['-c:a', audio_codec]

            # Resolution (e.g., '1920x1080')
            if options.get('resolution') and isinstance(options['resolution'], str) and 'x' in options['resolution']:
                ffmpeg_cmd += ['-s', options['resolution']]

            # Target video bitrate in kbps
            if options.get('bitrate'):
                try:
                    bitrate_kbps = int(options['bitrate'])
                    if bitrate_kbps > 0:
                        ffmpeg_cmd += ['-b:v', f"{bitrate_kbps}k"]
                except Exception:
                    pass

            # Video filters (flip, rotate, fps, etc.)
            vf_filters = []
            if options.get('video_filter_flip') and options['video_filter_flip'] != 'no-change':
                if options['video_filter_flip'] == 'horizontal':
                    vf_filters.append('hflip')
                elif options['video_filter_flip'] == 'vertical':
                    vf_filters.append('vflip')
            if options.get('video_filter_rotate') and options['video_filter_rotate'] != 'none':
                if options['video_filter_rotate'] == '90':
                    vf_filters.append('transpose=1')
                elif options['video_filter_rotate'] == '180':
                    vf_filters.append('transpose=2,transpose=2')
                elif options['video_filter_rotate'] == '270':
                    vf_filters.append('transpose=2')
            if options.get('video_fps') and options['video_fps'] != 'no-change':
                vf_filters.append(f"fps={options['video_fps']}")
            if vf_filters:
                ffmpeg_cmd += ['-vf', ','.join(vf_filters)]
            # Audio filters (volume, fade in/out)
            af_filters = []
            if options.get('audio_filter_volume') and options['audio_filter_volume'] != 100:
                af_filters.append(f"volume={options['audio_filter_volume']/100}")
            if options.get('audio_filter_fade_in'):
                af_filters.append('afade=t=in:ss=0:d=3')
            if options.get('audio_filter_fade_out'):
                af_filters.append('afade=t=out:st=3:d=3')
            if af_filters:
                ffmpeg_cmd += ['-af', ','.join(af_filters)]
            # Remove video or audio
            if options.get('video_audio_remove'):
                if options['video_audio_remove'] == 'video':
                    ffmpeg_cmd += ['-vn']
                elif options['video_audio_remove'] == 'audio':
                    ffmpeg_cmd += ['-an']
            # Cut start/end
            if options.get('cut_start') and options['cut_start'] != '00:00:00.00':
                ffmpeg_cmd += ['-ss', options['cut_start']]
            if options.get('cut_end') and options['cut_end'] != '00:00:00.00':
                ffmpeg_cmd += ['-to', options['cut_end']]
            # Explicitly set output format for some containers
            if output_format == 'webm':
                ffmpeg_cmd += ['-f', 'webm']
            elif output_format == 'mkv':
                ffmpeg_cmd += ['-f', 'matroska']
        
        # Output file
        ffmpeg_cmd += [output_path]

        # Run ffmpeg
        # print(f"Running FFmpeg command: {' '.join(ffmpeg_cmd)}")  # Debug logging
        try:
            result = subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=300)
            print(f"FFmpeg stdout: {result.stdout}")  # Debug logging
        except subprocess.CalledProcessError as e:
            print(f"FFmpeg failed with return code {e.returncode}")  # Debug logging
            print(f"FFmpeg stderr: {e.stderr}")  # Debug logging
            error_msg = f"FFmpeg conversion failed (return code {e.returncode}): {e.stderr}"
            raise Exception(error_msg)
        except FileNotFoundError:
            print("FFmpeg binary not found in PATH")  # Debug logging
            raise Exception("FFmpeg not found. Please install FFmpeg and ensure it's in your PATH.")
        except subprocess.TimeoutExpired:
            print("FFmpeg command timed out after 300 seconds")  # Debug logging
            raise Exception("Video conversion timed out. The file might be too large or complex.")
        except Exception as e:
            print(f"Unexpected FFmpeg error: {str(e)}")  # Debug logging
            raise Exception(f"Unexpected error during conversion: {str(e)}")

        # Verify output file exists
        if not os.path.exists(output_path):
            raise Exception("Conversion completed but output file was not created")

        # Clean up temp file
        os.remove(input_path)

        # Return export URL (using proper /export endpoint)
        return {
            'success': True,
            'export_url': f"/export/videos/{output_filename}?ngrok-skip-browser-warning=true",
            'download_url': f"/download/videos/{output_filename}?ngrok-skip-browser-warning=true",
            'ngrok_download_url': f"/ngrok-download/videos/{output_filename}?ngrok-skip-browser-warning=true",
            'filename': output_filename,
            'output_format': output_format,
            'message': 'Video conversion completed successfully'
        }
        
    except Exception as e:
        # Clean up temp file on error
        if os.path.exists(input_path):
            os.remove(input_path)
        raise Exception(f"Video conversion error: {str(e)}") 