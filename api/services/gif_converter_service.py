#!/usr/bin/env python3
"""
GIF Converter Service
Handles conversion TO GIF and FROM GIF using FFmpeg for advanced options
"""

import os
import uuid
import subprocess
import tempfile
import json

# Constants
EXPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static', 'gifs')
SUPPORTED_INPUT_FORMATS = ['mp4', 'webm', 'avi', 'mov', 'mkv', 'gif', 'apng', 'png', 'jpg', 'jpeg']
SUPPORTED_OUTPUT_FORMATS = ['gif', 'mp4', 'webm', 'apng', 'png']

# Ensure export directory exists
os.makedirs(EXPORT_DIR, exist_ok=True)

def validate_media_file(file_path):
    """Validate media file using FFprobe"""
    try:
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_format', '-show_streams', file_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            # Try to parse the JSON to ensure it's valid
            probe_data = json.loads(result.stdout)
            
            # Check if we have format information
            if 'format' in probe_data and 'streams' in probe_data:
                # Check if we have at least one video stream
                has_video = any(stream.get('codec_type') == 'video' for stream in probe_data['streams'])
                if has_video:
                    print(f"File validation successful: {probe_data['format'].get('format_name', 'unknown')} format")
                    return True
                else:
                    print("File validation failed: No video stream found")
                    return False
            else:
                print("File validation failed: Invalid probe data")
                return False
        else:
            print(f"File validation failed: FFprobe error - {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("File validation failed: FFprobe timeout")
        return False
    except json.JSONDecodeError:
        print("File validation failed: Invalid FFprobe output")
        return False
    except Exception as e:
        print(f"File validation failed: {str(e)}")
        return False

def convert_to_gif_simple(file, input_body):
    """Convert various formats TO GIF using simple single-pass method"""
    
    # Validate file before processing
    if not file or not file.filename:
        raise Exception("No valid file provided")
    
    # Get file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if not file_ext:
        file_ext = '.mp4'  # Default extension
    
    # Save uploaded file to a temporary file with proper handling
    temp_input = None
    input_path = None
    try:
        # Create temporary file with proper extension
        temp_input = tempfile.NamedTemporaryFile(delete=False, suffix=file_ext)
        input_path = temp_input.name
        
        # Reset file pointer and save content
        file.seek(0)
        content = file.read()
        
        if not content:
            raise Exception("Uploaded file appears to be empty")
        
        temp_input.write(content)
        temp_input.flush()
        os.fsync(temp_input.fileno())  # Force write to disk
        temp_input.close()
        
        # Validate the saved file
        if not os.path.exists(input_path):
            raise Exception("Failed to save uploaded file to disk")
            
        file_size = os.path.getsize(input_path)
        if file_size == 0:
            raise Exception("Saved file is empty")
        
        print(f"Successfully saved uploaded file: {input_path}")
        print(f"Original filename: {file.filename}")
        print(f"File size: {file_size} bytes")
        print(f"File extension: {file_ext}")
        
        # Validate file with FFprobe (but don't fail if validation fails - just warn)
        try:
            if not validate_media_file(input_path):
                print("⚠️  Warning: File validation failed, but proceeding with conversion attempt")
        except Exception as validation_error:
            print(f"⚠️  Warning: Could not validate file ({validation_error}), but proceeding with conversion attempt")
        
    except Exception as e:
        # Clean up on error
        if temp_input and not temp_input.closed:
            temp_input.close()
        if input_path and os.path.exists(input_path):
            try:
                os.unlink(input_path)
            except:
                pass
        raise Exception(f"Failed to save uploaded file: {str(e)}")

    try:
        # Extract conversion parameters
        convert_config = input_body['tasks']['convert']
        options = convert_config.get('options', {})
        
        # Generate unique output filename
        output_filename = str(uuid.uuid4()) + '.gif'
        output_path = os.path.join(EXPORT_DIR, output_filename)
        
        # Build simple FFmpeg command with proper GIF encoding
        ffmpeg_cmd = ['ffmpeg', '-y', '-i', input_path]
        
        # Handle timing (trim start/end)
        if options.get('trim_start'):
            ffmpeg_cmd += ['-ss', options['trim_start']]
        
        if options.get('trim_end'):
            try:
                if options.get('trim_start'):
                    ffmpeg_cmd += ['-to', options['trim_end']]
                else:
                    ffmpeg_cmd += ['-t', options['trim_end']]
            except:
                ffmpeg_cmd += ['-t', '10']  # Default 10 seconds
        
        # Video filters for GIF
        vf_filters = []
        
        # Width/Height scaling  
        width = options.get('width', 400)
        height = options.get('height')
        
        if height:
            vf_filters.append(f'scale={width}:{height}:flags=lanczos')
        else:
            vf_filters.append(f'scale={width}:-1:flags=lanczos')
        
        # FPS control
        fps = options.get('fps', 15)
        vf_filters.append(f'fps={fps}')
        
        # Apply video filters
        if vf_filters:
            ffmpeg_cmd += ['-vf', ','.join(vf_filters)]
        
        # GIF-specific encoding parameters (this is the key fix!)
        ffmpeg_cmd += ['-f', 'gif']  # Force GIF format
        
        # Loop count for GIF
        loop_count = options.get('loop_count', 0)
        if loop_count == 0:
            ffmpeg_cmd += ['-loop', '0']  # Infinite loop
        else:
            ffmpeg_cmd += ['-loop', str(loop_count)]
        
        # Ensure we're only processing video stream
        ffmpeg_cmd += ['-an']  # No audio
        
        # Add output file
        ffmpeg_cmd.append(output_path)
        
        print(f"Simple GIF conversion: {' '.join(ffmpeg_cmd)}")
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            raise Exception(f"FFmpeg conversion failed: {result.stderr}")
        
        # Check if output file exists and has content
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise Exception("Generated GIF file is empty or was not created")
        
        file_size = os.path.getsize(output_path)
        
        return {
            'success': True,
            'message': f'Successfully converted to GIF (simple method)',
            'output_file': output_filename,
            'download_url': f'/download/gifs/{output_filename}',
            'file_size': file_size,
            'original_filename': file.filename,
            'output_format': 'gif',
            'conversion_options': options,
            'gif_info': {
                'width': width,
                'fps': fps,
                'loop_count': loop_count,
                'method': 'simple'
            }
        }
        
    except Exception as e:
        raise Exception(f"Simple GIF conversion failed: {str(e)}")
    finally:
        if os.path.exists(input_path):
            os.unlink(input_path)

def convert_to_gif_basic(file, input_body):
    """Ultra-simple GIF conversion as last resort"""
    
    # Validate file before processing
    if not file or not file.filename:
        raise Exception("No valid file provided")
    
    # Get file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if not file_ext:
        file_ext = '.mp4'
    
    # Save file simply
    input_path = None
    try:
        temp_input = tempfile.NamedTemporaryFile(delete=False, suffix=file_ext)
        file.seek(0)
        temp_input.write(file.read())
        temp_input.close()
        input_path = temp_input.name
        
        # Extract basic options
        convert_config = input_body['tasks']['convert']
        options = convert_config.get('options', {})
        width = options.get('width', 320)  # Smaller default for compatibility
        fps = options.get('fps', 10)       # Lower FPS for compatibility
        
        # Generate output
        output_filename = str(uuid.uuid4()) + '.gif'
        output_path = os.path.join(EXPORT_DIR, output_filename)
        
        # Ultra-basic FFmpeg command that should always work
        ffmpeg_cmd = [
            'ffmpeg', '-y', '-i', input_path,
            '-vf', f'scale={width}:-1,fps={fps}',
            '-t', '5',  # Only convert first 5 seconds
            '-f', 'gif',
            '-an',  # No audio
            output_path
        ]
        
        print(f"Basic GIF conversion: {' '.join(ffmpeg_cmd)}")
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode != 0:
            raise Exception(f"Basic conversion failed: {result.stderr}")
        
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise Exception("Basic conversion produced empty file")
        
        file_size = os.path.getsize(output_path)
        
        return {
            'success': True,
            'message': 'Successfully converted to GIF (basic method)',
            'output_file': output_filename,
            'download_url': f'/download/gifs/{output_filename}',
            'file_size': file_size,
            'original_filename': file.filename,
            'output_format': 'gif',
            'conversion_options': options,
            'gif_info': {
                'width': width,
                'fps': fps,
                'duration': '5 seconds',
                'method': 'basic'
            }
        }
        
    finally:
        if input_path and os.path.exists(input_path):
            os.unlink(input_path)

def convert_to_gif(file, input_body):
    """Convert various formats TO GIF with multiple fallback methods"""
    
    try:
        # First try the two-pass high-quality method
        return convert_to_gif_two_pass(file, input_body)
    except Exception as e:
        print(f"Two-pass method failed: {str(e)}")
        print("Falling back to simple method...")
        
        try:
            # Fall back to simple method
            return convert_to_gif_simple(file, input_body)
        except Exception as e2:
            print(f"Simple method failed: {str(e2)}")
            print("Falling back to basic method...")
            
            # Last resort: ultra-basic method
            return convert_to_gif_basic(file, input_body)

def convert_to_gif_two_pass(file, input_body):
    """Convert various formats TO GIF with advanced options using two-pass method"""
    
    # Validate file before processing
    if not file or not file.filename:
        raise Exception("No valid file provided")
    
    # Get file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if not file_ext:
        file_ext = '.mp4'  # Default extension
    
    # Save uploaded file to a temporary file with proper handling
    temp_input = None
    try:
        temp_input = tempfile.NamedTemporaryFile(delete=False, suffix=file_ext)
        file.seek(0)  # Ensure we're at the beginning of the file
        temp_input.write(file.read())
        temp_input.flush()
        temp_input.close()
        input_path = temp_input.name
        
        # Validate the saved file
        if not os.path.exists(input_path) or os.path.getsize(input_path) == 0:
            raise Exception("Uploaded file is empty or could not be saved")
        
        print(f"Saved uploaded file to: {input_path} (size: {os.path.getsize(input_path)} bytes)")
        
        # Validate file with FFprobe
        if not validate_media_file(input_path):
            raise Exception("Uploaded file is not a valid media file or is corrupted")
        
    except Exception as e:
        if temp_input:
            temp_input.close()
        raise Exception(f"Failed to save uploaded file: {str(e)}")

    try:
        # Extract conversion parameters
        convert_config = input_body['tasks']['convert']
        options = convert_config.get('options', {})
        
        # Generate unique output filename
        output_filename = str(uuid.uuid4()) + '.gif'
        output_path = os.path.join(EXPORT_DIR, output_filename)
        
        # Generate palette file path
        palette_path = os.path.join(EXPORT_DIR, f"{str(uuid.uuid4())}_palette.png")
        
        # Video filters for GIF optimization
        vf_filters = []
        
        # Width/Height scaling
        width = options.get('width', 400)
        height = options.get('height')
        
        if height:
            vf_filters.append(f'scale={width}:{height}:flags=lanczos')
        else:
            # Maintain aspect ratio
            vf_filters.append(f'scale={width}:-1:flags=lanczos')
        
        # FPS control
        fps = options.get('fps', 15)
        vf_filters.append(f'fps={fps}')
        
        # STEP 1: Generate palette
        palette_cmd = ['ffmpeg', '-y', '-i', input_path]
        
        # Handle timing for palette generation
        if options.get('trim_start'):
            palette_cmd += ['-ss', options['trim_start']]
        
        if options.get('trim_end'):
            if options.get('trim_start'):
                palette_cmd += ['-to', options['trim_end']]
            else:
                palette_cmd += ['-t', options['trim_end']]
        
        # Palette generation filters
        palette_filters = vf_filters.copy()
        if options.get('transparency', True):
            palette_filters.append('palettegen=reserve_transparent=1')
        else:
            palette_filters.append('palettegen')
        
        palette_cmd += ['-vf', ','.join(palette_filters)]
        palette_cmd.append(palette_path)
        
        print(f"Generating palette: {' '.join(palette_cmd)}")
        result1 = subprocess.run(palette_cmd, capture_output=True, text=True, timeout=300)
        
        if result1.returncode != 0:
            raise Exception(f"Palette generation failed: {result1.stderr}")
        
        # STEP 2: Generate GIF using palette
        gif_cmd = ['ffmpeg', '-y', '-i', input_path, '-i', palette_path]
        
        # Handle timing for GIF generation
        if options.get('trim_start'):
            gif_cmd += ['-ss', options['trim_start']]
        
        if options.get('trim_end'):
            if options.get('trim_start'):
                gif_cmd += ['-to', options['trim_end']]
            else:
                gif_cmd += ['-t', options['trim_end']]
        
        # GIF generation filters - use complex filter graph
        base_filters = ','.join(vf_filters)
        if options.get('transparency', True):
            complex_filter = f"[0:v]{base_filters}[v];[v][1:v]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle"
        else:
            complex_filter = f"[0:v]{base_filters}[v];[v][1:v]paletteuse"
        
        gif_cmd += ['-filter_complex', complex_filter]
        
        # Loop count (0 = infinite loop)
        loop_count = options.get('loop_count', 0)
        if loop_count == 0:
            gif_cmd += ['-loop', '0']  # Infinite loop
        else:
            gif_cmd += ['-loop', str(loop_count)]
        
        gif_cmd.append(output_path)
        
        print(f"Generating GIF: {' '.join(gif_cmd)}")
        result2 = subprocess.run(gif_cmd, capture_output=True, text=True, timeout=300)
        
        if result2.returncode != 0:
            raise Exception(f"GIF generation failed: {result2.stderr}")
        
        # Clean up palette file
        if os.path.exists(palette_path):
            os.unlink(palette_path)
        
        # Check if output file exists and has content
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise Exception("Generated GIF file is empty or was not created")
        
        # Calculate file size
        file_size = os.path.getsize(output_path)
        
        return {
            'success': True,
            'message': f'Successfully converted to GIF',
            'output_file': output_filename,
            'download_url': f'/download/gifs/{output_filename}',
            'file_size': file_size,
            'original_filename': file.filename,
            'output_format': 'gif',
            'conversion_options': options,
            'gif_info': {
                'width': width,
                'fps': fps,
                'loop_count': loop_count,
                'two_pass': True
            }
        }
        
    except subprocess.TimeoutExpired:
        raise Exception("Conversion timeout - file may be too large or complex")
    except Exception as e:
        raise Exception(f"GIF conversion failed: {str(e)}")
    finally:
        # Clean up temporary files
        if os.path.exists(input_path):
            os.unlink(input_path)
        # Clean up palette file if it exists
        try:
            if 'palette_path' in locals() and os.path.exists(palette_path):
                os.unlink(palette_path)
        except:
            pass

def convert_from_gif(file, input_body):
    """Convert GIF to other formats"""
    
    # Save uploaded file to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.gif') as temp_input:
        file.save(temp_input.name)
        input_path = temp_input.name

    try:
        # Extract conversion parameters
        convert_config = input_body['tasks']['convert']
        output_format = convert_config['output_format'].lower()
        options = convert_config.get('options', {})
        
        if output_format not in SUPPORTED_OUTPUT_FORMATS:
            raise ValueError(f"Unsupported output format: {output_format}")
        
        # Generate unique output filename
        if output_format == 'apng':
            output_filename = str(uuid.uuid4()) + '.png'  # APNG uses .png extension
        else:
            output_filename = str(uuid.uuid4()) + f'.{output_format}'
        
        # Determine output directory based on format
        if output_format in ['mp4', 'webm']:
            output_dir = os.path.join(os.path.dirname(EXPORT_DIR), 'videos')
        elif output_format in ['png', 'apng']:
            output_dir = os.path.join(os.path.dirname(EXPORT_DIR), 'images')
        else:
            output_dir = EXPORT_DIR
        
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, output_filename)
        
        # Build FFmpeg command based on output format
        ffmpeg_cmd = ['ffmpeg', '-y', '-i', input_path]
        
        if output_format == 'mp4':
            # GIF to MP4 conversion
            fps = options.get('fps', 30)
            quality = options.get('quality', 'medium')
            
            # Video filters
            vf_filters = []
            
            # Scale if specified
            width = options.get('width')
            height = options.get('height')
            if width and height:
                vf_filters.append(f'scale={width}:{height}')
            elif width:
                vf_filters.append(f'scale={width}:-1')
            elif height:
                vf_filters.append(f'scale=-1:{height}')
            
            # Set FPS
            vf_filters.append(f'fps={fps}')
            
            if vf_filters:
                ffmpeg_cmd += ['-vf', ','.join(vf_filters)]
            
            # Codec and quality settings
            ffmpeg_cmd += ['-c:v', 'libx264', '-preset', 'medium']
            
            if quality == 'high':
                ffmpeg_cmd += ['-crf', '18']
            elif quality == 'medium':
                ffmpeg_cmd += ['-crf', '23']
            else:  # low
                ffmpeg_cmd += ['-crf', '28']
            
            # MP4 compatibility
            ffmpeg_cmd += ['-pix_fmt', 'yuv420p', '-movflags', '+faststart']
            
        elif output_format == 'webm':
            # GIF to WebM conversion
            fps = options.get('fps', 30)
            quality = options.get('quality', 'medium')
            
            vf_filters = []
            
            # Scale if specified
            width = options.get('width')
            height = options.get('height')
            if width and height:
                vf_filters.append(f'scale={width}:{height}')
            elif width:
                vf_filters.append(f'scale={width}:-1')
            elif height:
                vf_filters.append(f'scale=-1:{height}')
            
            vf_filters.append(f'fps={fps}')
            
            if vf_filters:
                ffmpeg_cmd += ['-vf', ','.join(vf_filters)]
            
            # WebM codec settings
            ffmpeg_cmd += ['-c:v', 'libvpx-vp9']
            
            if quality == 'high':
                ffmpeg_cmd += ['-crf', '15', '-b:v', '2M']
            elif quality == 'medium':
                ffmpeg_cmd += ['-crf', '23', '-b:v', '1M']
            else:  # low
                ffmpeg_cmd += ['-crf', '35', '-b:v', '500K']
            
        elif output_format == 'apng':
            # GIF to APNG conversion
            vf_filters = []
            
            # Scale if specified
            width = options.get('width')
            height = options.get('height')
            if width and height:
                vf_filters.append(f'scale={width}:{height}')
            elif width:
                vf_filters.append(f'scale={width}:-1')
            elif height:
                vf_filters.append(f'scale=-1:{height}')
            
            if vf_filters:
                ffmpeg_cmd += ['-vf', ','.join(vf_filters)]
            
            # APNG codec settings
            ffmpeg_cmd += ['-c:v', 'apng']
            
            # Compression level (0-9, higher = better compression)
            compression = options.get('compression', 6)
            ffmpeg_cmd += ['-compression_level', str(compression)]
            
        elif output_format == 'png':
            # Extract first frame as PNG
            ffmpeg_cmd += ['-vframes', '1', '-c:v', 'png']
            
            # Scale if specified
            width = options.get('width')
            height = options.get('height')
            if width or height:
                vf_filters = []
                if width and height:
                    vf_filters.append(f'scale={width}:{height}')
                elif width:
                    vf_filters.append(f'scale={width}:-1')
                elif height:
                    vf_filters.append(f'scale=-1:{height}')
                
                if vf_filters:
                    ffmpeg_cmd += ['-vf', ','.join(vf_filters)]
        
        # Output file
        ffmpeg_cmd.append(output_path)
        
        # Execute FFmpeg command
        print(f"Executing FFmpeg command: {' '.join(ffmpeg_cmd)}")
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            raise Exception(f"FFmpeg conversion failed: {result.stderr}")
        
        # Calculate file size
        file_size = os.path.getsize(output_path)
        
        # Determine download URL path based on output format
        if output_format in ['mp4', 'webm']:
            download_path = f'/download/videos/{output_filename}'
        elif output_format in ['png', 'apng']:
            download_path = f'/download/images/{output_filename}'
        else:
            download_path = f'/download/gifs/{output_filename}'
        
        return {
            'success': True,
            'message': f'Successfully converted GIF to {output_format.upper()}',
            'output_file': output_filename,
            'download_url': download_path,
            'file_size': file_size,
            'original_filename': file.filename,
            'output_format': output_format,
            'conversion_options': options
        }
        
    except subprocess.TimeoutExpired:
        raise Exception("Conversion timeout - file may be too large or complex")
    except Exception as e:
        raise Exception(f"GIF conversion failed: {str(e)}")
    finally:
        # Clean up temporary file
        if os.path.exists(input_path):
            os.unlink(input_path)

def get_gif_info(file_path):
    """Get information about a GIF file using FFprobe"""
    try:
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_format', '-show_streams', file_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            return None
    except:
        return None

def optimize_gif(input_path, output_path, options):
    """Optimize existing GIF file"""
    ffmpeg_cmd = ['ffmpeg', '-y', '-i', input_path]
    
    # Optimization filters
    vf_filters = []
    
    # Color palette optimization
    if options.get('optimize_palette', True):
        vf_filters.append('palettegen=reserve_transparent=1')
    
    # Size optimization
    if options.get('optimize_size', True):
        # Reduce FPS if too high
        max_fps = options.get('max_fps', 15)
        vf_filters.append(f'fps={max_fps}')
        
        # Scale down if too large
        max_width = options.get('max_width', 500)
        vf_filters.append(f'scale={max_width}:-1')
    
    if vf_filters:
        ffmpeg_cmd += ['-vf', ','.join(vf_filters)]
    
    # Quality settings
    compression = options.get('compression', 10)
    ffmpeg_cmd += ['-q:v', str(compression)]
    
    ffmpeg_cmd.append(output_path)
    
    result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=300)
    return result.returncode == 0