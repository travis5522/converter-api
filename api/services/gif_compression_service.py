import os
import tempfile
import shutil
from datetime import datetime
from PIL import Image, ImageSequence

def compress_gif(file, input_body):
    """
    Compress GIF files with advanced options
    
    Args:
        file: Uploaded GIF file
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
        
        # Get original file size
        original_size = os.path.getsize(input_path)
        
        # Get compression options from input_body
        tasks = input_body.get('tasks', {})
        compress_task = tasks.get('compress', {})
        options = compress_task.get('options', {})
        
        # Get GIF compression options
        gif_undo_optimization = options.get('gif_undo_optimization', False)
        gif_compression_level = options.get('gif_compression_level', 75)
        gif_compress_reduce_frames = options.get('gif_compress_reduce_frames', 'no-change')
        gif_optimize_transparency = options.get('gif_optimize_transparency', False)
        gif_color = options.get('gif_color', 'reduce')
        gif_compress_number_of_colors = options.get('gif_compress_number_of_colors', 256)
        
        # Open GIF with PIL
        with Image.open(input_path) as img:
            # Extract frames and durations
            frames = []
            durations = []
            
            # Get frame duration (in milliseconds)
            try:
                frame_duration = img.info.get('duration', 100)  # Default 100ms if not specified
            except:
                frame_duration = 100
            
            # Process each frame
            for i, frame in enumerate(ImageSequence.Iterator(img)):
                # Apply frame reduction logic
                if gif_compress_reduce_frames == 'no-change':
                    include_frame = True
                elif gif_compress_reduce_frames == 'remove-duplicate':
                    # Simple duplicate removal (compare with previous frame)
                    if i > 0 and frames:
                        # Convert both frames to same mode for comparison
                        prev_frame = frames[-1].convert('RGB')
                        curr_frame = frame.convert('RGB')
                        # Simple comparison - in practice, you might want more sophisticated detection
                        include_frame = not (prev_frame.tobytes() == curr_frame.tobytes())
                    else:
                        include_frame = True
                elif gif_compress_reduce_frames == 'drop-2nd':
                    include_frame = (i % 2 == 0)  # Keep every other frame
                elif gif_compress_reduce_frames == 'drop-3rd':
                    include_frame = (i % 3 != 2)  # Drop every 3rd frame
                elif gif_compress_reduce_frames == 'drop-4th':
                    include_frame = (i % 4 != 3)  # Drop every 4th frame
                elif gif_compress_reduce_frames == 'drop-5th':
                    include_frame = (i % 5 != 4)  # Drop every 5th frame
                else:
                    include_frame = True
                
                if include_frame:
                    # Convert frame to RGB if needed for processing
                    if frame.mode == 'P' and 'transparency' in frame.info:
                        # Preserve transparency in palette mode
                        processed_frame = frame.convert('RGBA')
                    else:
                        processed_frame = frame.convert('RGB')
                    
                    # Apply color reduction
                    if gif_color == 'reduce':
                        # Reduce number of colors using quantization
                        processed_frame = processed_frame.quantize(colors=gif_compress_number_of_colors, method=2)
                    elif gif_color == 'reduce-dither':
                        # Reduce colors with dithering
                        processed_frame = processed_frame.quantize(colors=gif_compress_number_of_colors, method=2, dither=1)
                    elif gif_color == 'single-table':
                        # Use a single color table for all frames (will be applied during save)
                        processed_frame = processed_frame.quantize(colors=gif_compress_number_of_colors, method=2)
                    
                    frames.append(processed_frame)
                    
                    # Adjust duration based on frame dropping
                    if gif_compress_reduce_frames in ['drop-2nd', 'drop-3rd', 'drop-4th', 'drop-5th']:
                        # Increase duration proportionally to maintain animation speed
                        drop_factor = {
                            'drop-2nd': 2,
                            'drop-3rd': 1.5,  # Dropping every 3rd means keeping 2/3
                            'drop-4th': 1.33,  # Keeping 3/4
                            'drop-5th': 1.25   # Keeping 4/5
                        }.get(gif_compress_reduce_frames, 1)
                        adjusted_duration = int(frame_duration * drop_factor)
                    else:
                        adjusted_duration = frame_duration
                    
                    durations.append(adjusted_duration)
            
            if not frames:
                raise Exception("No frames to save after processing")
            
            # Prepare save options
            save_kwargs = {
                'format': 'GIF',
                'save_all': True,
                'append_images': frames[1:] if len(frames) > 1 else [],
                'duration': durations,
                'loop': 0,  # Infinite loop
                'optimize': not gif_undo_optimization
            }
            
            # Apply transparency optimization
            if gif_optimize_transparency:
                save_kwargs['transparency'] = 0
                save_kwargs['disposal'] = 2  # Restore to background
            
            # Set compression level (affects optimization)
            if gif_compression_level < 25:
                save_kwargs['optimize'] = False  # Minimal optimization for higher quality
            elif gif_compression_level > 90:
                save_kwargs['optimize'] = True
                save_kwargs['colors'] = min(gif_compress_number_of_colors, 128)  # More aggressive
            
            # Save compressed GIF
            frames[0].save(output_path, **save_kwargs)
        
        # Check if output file exists and has size > 0
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise Exception("Compression failed - output file is empty or missing")
        
        # Create static directory if it doesn't exist
        static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static', 'gifs')
        os.makedirs(static_dir, exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"gif_compressed_{timestamp}_{output_filename}"
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
            download_url = f"{base_url}/static/gifs/{unique_filename}"
        except:
            # Fallback to relative URL if request context is not available
            download_url = f"/static/gifs/{unique_filename}"
        
        # Calculate compression stats
        compression_ratio = (1 - (file_size / original_size)) * 100
        size_reduction = original_size - file_size
        
        # Prepare response data
        response_data = {
            'success': True,
            'message': f'GIF compressed successfully with {len(frames)} frames',
            'download_url': download_url,
            'export_url': download_url,
            'file_size': file_size,
            'output_format': 'gif',
            'input_format': 'gif',
            'compression_stats': {
                'original_size': original_size,
                'compressed_size': file_size,
                'compression_ratio': f"{compression_ratio:.1f}%",
                'size_reduction': f"{size_reduction} bytes",
                'frames_processed': len(frames)
            },
            'settings_used': {
                'gif_undo_optimization': gif_undo_optimization,
                'gif_compression_level': gif_compression_level,
                'gif_compress_reduce_frames': gif_compress_reduce_frames,
                'gif_optimize_transparency': gif_optimize_transparency,
                'gif_color': gif_color,
                'gif_compress_number_of_colors': gif_compress_number_of_colors
            }
        }
        
        print(f"GIF compression successful. Output format: {response_data['output_format']}")
        
        # Clean up temporary directory
        shutil.rmtree(temp_dir)
        
        return response_data
        
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        if 'temp_dir' in locals() and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        raise Exception(f"GIF compression failed: {str(e)}") 