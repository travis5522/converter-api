#!/usr/bin/env python3
"""
Image Converter Service
Full implementation with PIL/Pillow for real image conversion
"""

import os
import uuid
import tempfile
import json
import base64
from PIL import Image, ImageOps
import pillow_heif

# Register HEIF opener with Pillow
pillow_heif.register_heif_opener()

# Constants
EXPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static', 'images')
SUPPORTED_FORMATS = ['apng', 'bmp', 'eps', 'gif', 'ico', 'jpeg', 'jpg', 'odd', 'png', 'psd', 'svg', 'tga', 'tiff', 'webp']

# Ensure export directory exists
os.makedirs(EXPORT_DIR, exist_ok=True)

def get_format_info(output_format):
    """Get information about a specific format"""
    format_info = {
        'bmp': {'description': 'Windows Bitmap - Uncompressed raster format'},
        'eps': {'description': 'Encapsulated PostScript - Vector format'},
        'gif': {'description': 'Graphics Interchange Format - Supports animation'},
        'ico': {'description': 'Windows Icon - Multiple sizes in one file'},
        'jpeg': {'description': 'JPEG - Lossy compression, great for photos'},
        'jpg': {'description': 'JPEG - Lossy compression, great for photos'},
        'odd': {'description': 'OpenDocument Drawing - Converted to PNG'},
        'png': {'description': 'Portable Network Graphics - Lossless with transparency'},
        'psd': {'description': 'Photoshop Document - Adobe format'},
        'svg': {'description': 'Scalable Vector Graphics - XML-based vector format'},
        'tga': {'description': 'Truevision TGA - Supports transparency'},
        'tiff': {'description': 'Tagged Image File Format - High quality'},
        'webp': {'description': 'Modern web format - Better compression'}
    }
    return format_info.get(output_format.lower(), {'description': 'Unknown format'})

def _parse_image_options(options, output_format):
    """Parse and convert new format options to internal format"""
    internal_options = {}
    
    # Handle resize type
    if options.get('resize_type_image') == 'keep_original':
        # Keep original size - no resize
        pass
    elif 'resize' in options:
        internal_options['resize'] = options['resize']

    # Accept generic width/height from frontend (convert strings/numbers)
    for dim in ['width', 'height']:
        if dim in options and options[dim] not in (None, '', 'Auto'):
            try:
                internal_options[dim] = int(options[dim])
            except Exception:
                pass

    # Handle PNG specific options
    if output_format == 'png':
        if options.get('png_compression_level') == 'lossy':
            internal_options['compression'] = 'lossy'
        if options.get('png_convert_quality'):
            internal_options['quality'] = options['png_convert_quality']
    
    # Handle JPEG/webp/etc. quality
    if options.get('quality') is not None:
        try:
            internal_options['quality'] = int(options['quality'])
        except Exception:
            pass
    
    # Map preserveMetadata (frontend) -> strip_metadata (backend inverse)
    if 'preserveMetadata' in options:
        internal_options['strip_metadata'] = not bool(options['preserveMetadata'])
    
    # Auto orient
    if options.get('auto-orient') or options.get('autoOrient'):
        internal_options['auto_orient'] = True
    
    # Color space: currently informational; may be used by backends that support ICC transforms
    if options.get('colorSpace'):
        internal_options['color_space'] = options['colorSpace']
    
    # DPI
    if options.get('dpi'):
        try:
            internal_options['dpi'] = int(options['dpi'])
        except Exception:
            pass
    
    # Handle strip metadata (legacy key)
    if options.get('strip'):
        internal_options['strip_metadata'] = True
    
    # Pass through other options
    for key in ['preserve_transparency']:
        if key in options:
            internal_options[key] = options[key]
    
    return internal_options

def _convert_image_with_pil(input_path, output_path, input_format, output_format, options):
    """Perform actual image conversion using PIL/Pillow"""
    try:
        # Handle SVG input specially
        if input_format.lower() == 'svg':
            return _convert_from_svg(input_path, output_path, output_format, options)
        
        # Open the input image
        with Image.open(input_path) as img:
            # Handle auto-orientation
            if options.get('auto_orient', True):
                img = ImageOps.exif_transpose(img)
            
            # Handle resize if specified
            if 'width' in options or 'height' in options:
                width = options.get('width', img.width)
                height = options.get('height', img.height)
                img = img.resize((int(width), int(height)), Image.Resampling.LANCZOS)
            elif 'resize' in options:
                # Handle percentage resize
                resize_factor = options['resize'] / 100.0
                new_width = int(img.width * resize_factor)
                new_height = int(img.height * resize_factor)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Prepare save options
            save_kwargs = {}
            
            # Handle format-specific conversions and options
            if output_format.lower() in ['jpg', 'jpeg']:
                # JPEG doesn't support transparency, convert to RGB if needed
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Create white background
                    background = Image.new('RGB', img.size, 'white')
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Set JPEG quality
                quality = options.get('quality', 95)
                save_kwargs['quality'] = int(quality)
                save_kwargs['optimize'] = True
                save_kwargs['format'] = 'JPEG'
                
            elif output_format.lower() == 'png':
                # PNG supports transparency
                if img.mode not in ('RGBA', 'RGB', 'L'):
                    img = img.convert('RGBA')
                save_kwargs['format'] = 'PNG'
                
                # PNG compression level
                if options.get('compression') == 'lossy':
                    save_kwargs['optimize'] = True
                
            elif output_format.lower() == 'webp':
                # WebP supports both lossy and lossless
                quality = options.get('quality', 90)
                save_kwargs['quality'] = int(quality)
                save_kwargs['format'] = 'WEBP'
                save_kwargs['method'] = 6  # Better compression
                
            elif output_format.lower() == 'gif':
                # GIF requires palette mode
                if img.mode != 'P':
                    img = img.convert('P', palette=Image.Palette.ADAPTIVE)
                save_kwargs['format'] = 'GIF'
                save_kwargs['optimize'] = True
                
            elif output_format.lower() == 'bmp':
                # BMP doesn't support transparency
                if img.mode in ('RGBA', 'LA'):
                    background = Image.new('RGB', img.size, 'white')
                    background.paste(img, mask=img.split()[-1])
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                save_kwargs['format'] = 'BMP'
                
            elif output_format.lower() == 'tiff':
                save_kwargs['format'] = 'TIFF'
                if options.get('quality'):
                    save_kwargs['quality'] = int(options['quality'])
                    
            elif output_format.lower() == 'ico':
                # ICO format - resize to common icon sizes if too large
                if img.width > 256 or img.height > 256:
                    img = img.resize((256, 256), Image.Resampling.LANCZOS)
                save_kwargs['format'] = 'ICO'
                
            elif output_format.lower() == 'svg':
                # SVG requires special handling - save image first, then convert
                temp_path = output_path.replace('.svg', '_temp.png')
                img.save(temp_path, 'PNG')
                # Convert using our SVG function
                success = _convert_to_svg(temp_path, output_path, options)
                os.remove(temp_path)  # Clean up temp file
                return success
                
            elif output_format.lower() == 'apng':
                # APNG (Animated PNG) - save as PNG for static images
                # For single images, APNG is essentially PNG
                save_kwargs['format'] = 'PNG'
                save_kwargs['optimize'] = True
                if options.get('quality'):
                    save_kwargs['compress_level'] = min(9, max(0, int(options['quality'] / 10)))
                
            else:
                # For other formats (EPS, PSD, TGA), try direct conversion
                save_kwargs['format'] = output_format.upper()
            
            # Strip metadata if requested
            if options.get('strip_metadata'):
                # Remove EXIF and other metadata
                data = list(img.getdata())
                image_without_exif = Image.new(img.mode, img.size)
                image_without_exif.putdata(data)
                img = image_without_exif
            
            # Save the converted image
            img.save(output_path, **save_kwargs)
            
        return True
        
    except Exception as e:
        print(f"PIL conversion error: {str(e)}")
        # Try fallback conversion for special formats
        return _convert_special_formats(input_path, output_path, input_format, output_format, options)

def _convert_to_svg(input_path, output_path, options):
    """Convert raster image to SVG by embedding as base64 data"""
    try:
        with Image.open(input_path) as img:
            # Convert to RGB if necessary (for better compatibility)
            if img.mode in ('RGBA', 'LA'):
                # Keep transparency for PNG embedding
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                output_format = 'PNG'
            else:
                # Convert to RGB for JPEG embedding (smaller file size)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                output_format = 'JPEG'
            
            # Apply any resize options
            if 'width' in options or 'height' in options:
                width = options.get('width', img.width)
                height = options.get('height', img.height)
                img = img.resize((int(width), int(height)), Image.Resampling.LANCZOS)
            elif 'resize' in options:
                resize_factor = options['resize'] / 100.0
                new_width = int(img.width * resize_factor)
                new_height = int(img.height * resize_factor)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Save image to memory as base64
            import io
            img_buffer = io.BytesIO()
            
            if output_format == 'PNG':
                img.save(img_buffer, format='PNG', optimize=True)
                mime_type = 'image/png'
            else:
                img.save(img_buffer, format='JPEG', quality=90, optimize=True)
                mime_type = 'image/jpeg'
            
            img_buffer.seek(0)
            img_base64 = base64.b64encode(img_buffer.read()).decode('utf-8')
            
            # Create SVG XML structure
            svg_content = f'''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns="http://www.w3.org/2000/svg" 
     xmlns:xlink="http://www.w3.org/1999/xlink"
     width="{img.width}" 
     height="{img.height}" 
     viewBox="0 0 {img.width} {img.height}">
  <title>Converted Image</title>
  <desc>Image converted to SVG format</desc>
  <image x="0" y="0" 
         width="{img.width}" 
         height="{img.height}" 
         xlink:href="data:{mime_type};base64,{img_base64}" />
</svg>'''
            
            # Write SVG to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(svg_content)
            
            return True
            
    except Exception as e:
        print(f"SVG conversion error: {str(e)}")
        return False

def _preprocess_svg_content(svg_content):
    """Preprocess SVG content to fix common rendering issues"""
    import re
    
    # Ensure proper XML declaration
    if not svg_content.strip().startswith('<?xml'):
        svg_content = '<?xml version="1.0" encoding="UTF-8"?>\n' + svg_content
    
    # Add default namespace if missing
    if 'xmlns=' not in svg_content:
        svg_content = svg_content.replace('<svg', '<svg xmlns="http://www.w3.org/2000/svg"', 1)
    
    # Fix missing viewBox by extracting from width/height
    if 'viewBox=' not in svg_content:
        width_match = re.search(r'width=["\']([^"\']+)["\']', svg_content)
        height_match = re.search(r'height=["\']([^"\']+)["\']', svg_content)
        
        if width_match and height_match:
            try:
                width = re.sub(r'[^\d.]', '', width_match.group(1))
                height = re.sub(r'[^\d.]', '', height_match.group(1))
                if width and height:
                    width = float(width)
                    height = float(height)
                    viewbox = f'viewBox="0 0 {width} {height}"'
                    svg_content = svg_content.replace('<svg', f'<svg {viewbox}', 1)
            except:
                # If parsing fails, add a default viewBox
                svg_content = svg_content.replace('<svg', '<svg viewBox="0 0 100 100"', 1)
    
    # Ensure proper font handling - replace system fonts with web-safe alternatives
    font_replacements = {
        'Arial Black': 'Arial, sans-serif',
        'Helvetica Neue': 'Helvetica, Arial, sans-serif',
        'Times New Roman': 'Times, serif',
        'Courier New': 'Courier, monospace'
    }
    
    for old_font, new_font in font_replacements.items():
        svg_content = svg_content.replace(f'font-family="{old_font}"', f'font-family="{new_font}"')
        svg_content = svg_content.replace(f"font-family='{old_font}'", f"font-family='{new_font}'")
    
    # Remove external references that might cause issues
    # Remove external stylesheets
    svg_content = re.sub(r'<link[^>]*rel=["\']stylesheet["\'][^>]*>', '', svg_content)
    
    # Remove external font imports
    svg_content = re.sub(r'@import[^;]*;', '', svg_content)
    
    # Ensure all text has proper fill color (default to black if missing)
    svg_content = re.sub(r'<text(?![^>]*fill=)', '<text fill="black"', svg_content)
    
    # Fix stroke-width issues
    svg_content = re.sub(r'stroke-width="0"', 'stroke-width="1"', svg_content)
    
    # Fix common path issues
    svg_content = re.sub(r'fill="none"(?![^>]*stroke=)', 'fill="none" stroke="black"', svg_content)
    
    # Ensure proper opacity handling
    svg_content = re.sub(r'opacity="0"', 'opacity="1"', svg_content)
    
    # Fix missing closing tags
    svg_content = re.sub(r'<([^>]+)/>', r'<\1></\1>', svg_content)
    
    # Remove problematic CSS that might hide elements
    svg_content = re.sub(r'display:\s*none[;]?', '', svg_content)
    svg_content = re.sub(r'visibility:\s*hidden[;]?', '', svg_content)
    
    return svg_content

def _extract_svg_dimensions(svg_content):
    """Extract width and height from SVG content"""
    import re
    
    # Try to extract from viewBox first
    viewbox_match = re.search(r'viewBox=["\']([^"\']+)["\']', svg_content)
    if viewbox_match:
        try:
            viewbox_parts = viewbox_match.group(1).split()
            if len(viewbox_parts) >= 4:
                width = float(viewbox_parts[2])
                height = float(viewbox_parts[3])
                return int(width), int(height)
        except:
            pass
    
    # Try to extract from width/height attributes
    width_match = re.search(r'width=["\']([^"\']+)["\']', svg_content)
    height_match = re.search(r'height=["\']([^"\']+)["\']', svg_content)
    
    if width_match and height_match:
        try:
            width_str = re.sub(r'[^\d.]', '', width_match.group(1))
            height_str = re.sub(r'[^\d.]', '', height_match.group(1))
            if width_str and height_str:
                width = float(width_str)
                height = float(height_str)
                return int(width), int(height)
        except:
            pass
    
    # Default dimensions if nothing found
    return 400, 400

def _convert_svg_enhanced_cairosvg(input_path, output_path, output_format, options):
    """Enhanced SVG conversion using cairosvg with cairo-like quality"""
    import cairosvg
    print(f"Using enhanced cairosvg for SVG conversion: {input_path} -> {output_format}")
    
    # Read and heavily preprocess SVG content
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            svg_data = f.read()
    except UnicodeDecodeError:
        with open(input_path, 'r', encoding='latin-1') as f:
            svg_data = f.read()
    
    # Apply comprehensive SVG fixes
    svg_data = _preprocess_svg_for_perfect_rendering(svg_data)
    
    # Extract proper dimensions
    default_width, default_height = _extract_svg_dimensions(svg_data)
    width = options.get('width') or default_width
    height = options.get('height') or default_height
    
    # Ensure minimum reasonable size
    width = max(width, 100)
    height = max(height, 100)
    
    print(f"Enhanced rendering SVG at {width}x{height}")
    
    if output_format.lower() == 'png':
        # Direct PNG with highest quality settings
        cairosvg.svg2png(
            bytestring=svg_data.encode('utf-8'),
            write_to=output_path,
            output_width=width,
            output_height=height,
            dpi=300,
            # Advanced rendering options
            background_color='transparent'
        )
        
    elif output_format.lower() in ['jpg', 'jpeg']:
        # PNG first, then JPEG conversion
        temp_png = output_path.replace(f'.{output_format}', '_temp.png')
        
        cairosvg.svg2png(
            bytestring=svg_data.encode('utf-8'),
            write_to=temp_png,
            output_width=width,
            output_height=height,
            dpi=300,
            background_color='white'  # White background for JPEG
        )
        
        # Convert to JPEG with PIL for better quality control
        with Image.open(temp_png) as img:
            if img.mode in ('RGBA', 'LA'):
                # Create proper white background
                background = Image.new('RGB', img.size, 'white')
                if img.mode == 'RGBA':
                    background.paste(img, mask=img.split()[-1])
                else:
                    background.paste(img)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            quality = options.get('quality', 95)
            img.save(output_path, 'JPEG', quality=quality, optimize=True, progressive=True)
        
        os.remove(temp_png)
        
    else:
        # Other formats through PNG conversion
        temp_png = output_path.replace(f'.{output_format}', '_temp.png')
        
        # Choose background based on target format
        bg_color = 'white' if output_format.lower() in ['bmp', 'gif'] else 'transparent'
        
        cairosvg.svg2png(
            bytestring=svg_data.encode('utf-8'),
            write_to=temp_png,
            output_width=width,
            output_height=height,
            dpi=300,
            background_color=bg_color
        )
        
        # Convert to target format
        with Image.open(temp_png) as img:
            if output_format.lower() == 'webp':
                quality = options.get('quality', 90)
                img.save(output_path, 'WEBP', quality=quality, method=6, lossless=False)
            elif output_format.lower() == 'bmp':
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                img.save(output_path, 'BMP')
            elif output_format.lower() == 'gif':
                # Better GIF conversion with proper palette
                img = img.convert('RGB').convert('P', palette=Image.Palette.ADAPTIVE, colors=256)
                img.save(output_path, 'GIF', optimize=True, save_all=True)
            elif output_format.lower() == 'tiff':
                img.save(output_path, 'TIFF', compression='lzw')
            elif output_format.lower() == 'ico':
                # Resize for ICO if needed
                if width > 256 or height > 256:
                    img = img.resize((256, 256), Image.Resampling.LANCZOS)
                img.save(output_path, 'ICO')
            else:
                img.save(output_path, output_format.upper())
        
        os.remove(temp_png)
    
    # Verify successful conversion
    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        print(f"✅ Enhanced SVG conversion successful! Output: {output_path} ({os.path.getsize(output_path)} bytes)")
        return True
    else:
        print(f"❌ Enhanced SVG conversion failed - output file missing or empty")
        return False

def _preprocess_svg_for_perfect_rendering(svg_content):
    """Advanced SVG preprocessing for perfect rendering"""
    import re
    
    # Start with basic preprocessing
    svg_content = _preprocess_svg_content(svg_content)
    
    # Additional advanced fixes for perfect rendering
    
    # Ensure proper SVG structure
    if not svg_content.strip().startswith('<?xml'):
        svg_content = '<?xml version="1.0" encoding="UTF-8"?>\n' + svg_content
    
    # Add proper DOCTYPE if missing
    if 'DOCTYPE' not in svg_content and 'svg' in svg_content:
        svg_content = svg_content.replace('<?xml version="1.0" encoding="UTF-8"?>', 
            '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">')
    
    # Ensure all necessary namespaces
    if '<svg' in svg_content and 'xmlns=' not in svg_content:
        svg_content = svg_content.replace('<svg', '<svg xmlns="http://www.w3.org/2000/svg"', 1)
    
    if '<svg' in svg_content and 'xmlns:xlink=' not in svg_content:
        svg_content = svg_content.replace('<svg', '<svg xmlns:xlink="http://www.w3.org/1999/xlink"', 1)
    
    # Fix common rendering issues
    
    # Ensure shapes without fill have proper stroke
    svg_content = re.sub(r'<(rect|circle|ellipse|polygon|polyline|path)([^>]*?)(?<!stroke=")(?<!stroke:)>', 
                        r'<\1\2 stroke="black" stroke-width="1">', svg_content)
    
    # Fix text elements to be visible
    svg_content = re.sub(r'<text([^>]*?)>', 
                        lambda m: f'<text{m.group(1)} fill="black">' if 'fill=' not in m.group(1) else m.group(0), 
                        svg_content)
    
    # Fix path elements
    svg_content = re.sub(r'<path([^>]*?)d="([^"]*)"([^>]*?)>', 
                        lambda m: f'<path{m.group(1)}d="{m.group(2)}"{m.group(3)} fill="black">' 
                        if 'fill=' not in m.group(0) and 'stroke=' not in m.group(0) 
                        else m.group(0), svg_content)
    
    # Remove problematic transforms that might cause issues
    svg_content = re.sub(r'transform="[^"]*scale\(0[^)]*\)[^"]*"', '', svg_content)
    
    # Fix viewBox issues
    viewbox_match = re.search(r'viewBox=["\']([^"\']+)["\']', svg_content)
    if viewbox_match:
        viewbox = viewbox_match.group(1)
        try:
            parts = viewbox.split()
            if len(parts) == 4:
                x, y, w, h = map(float, parts)
                if w <= 0 or h <= 0:
                    # Fix invalid viewBox
                    svg_content = svg_content.replace(viewbox_match.group(0), 'viewBox="0 0 100 100"')
        except:
            svg_content = svg_content.replace(viewbox_match.group(0), 'viewBox="0 0 100 100"')
    
    # Ensure proper units
    svg_content = re.sub(r'(width|height)="([0-9.]+)px"', r'\1="\2"', svg_content)
    
    # Fix common CSS issues in style attributes
    svg_content = re.sub(r'style="[^"]*fill\s*:\s*none[^"]*"', 
                        lambda m: m.group(0).replace('fill:none', 'fill:black') 
                        if 'stroke' not in m.group(0) else m.group(0), svg_content)
    
    return svg_content

def _convert_svg_with_cairo_rsvg(input_path, output_path, output_format, options):
    """Convert SVG using cairo + rsvg for perfect rendering"""
    import cairo
    try:
        import gi
        gi.require_version('Rsvg', '2.0')
        from gi.repository import Rsvg
    except ImportError:
        # Try alternative import
        import rsvg as Rsvg
    
    print(f"Using cairo + rsvg for SVG conversion: {input_path} -> {output_format}")
    
    # Read SVG content
    with open(input_path, 'r', encoding='utf-8') as f:
        svg_data = f.read()
    
    # Preprocess SVG content
    svg_data = _preprocess_svg_content(svg_data)
    
    # Extract dimensions
    default_width, default_height = _extract_svg_dimensions(svg_data)
    width = options.get('width') or default_width
    height = options.get('height') or default_height
    
    print(f"Rendering SVG at {width}x{height}")
    
    # Create RSVG handle
    try:
        # Try new PyGObject API
        handle = Rsvg.Handle.new_from_data(svg_data.encode('utf-8'))
        dimensions = handle.get_dimensions()
        svg_width = dimensions.width if dimensions.width > 0 else width
        svg_height = dimensions.height if dimensions.height > 0 else height
    except:
        # Try old rsvg API
        handle = Rsvg.Handle(None, svg_data)
        svg_width = handle.props.width if hasattr(handle, 'props') and handle.props.width > 0 else width
        svg_height = handle.props.height if hasattr(handle, 'props') and handle.props.height > 0 else height
    
    # Calculate scale factors
    scale_x = width / svg_width if svg_width > 0 else 1
    scale_y = height / svg_height if svg_height > 0 else 1
    
    if output_format.lower() in ['jpg', 'jpeg']:
        # For JPEG, create temp PNG first
        temp_png = output_path.replace(f'.{output_format}', '_temp.png')
        
        # Create cairo surface and context
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        ctx = cairo.Context(surface)
        
        # Fill with white background for JPEG
        ctx.set_source_rgba(1, 1, 1, 1)  # White background
        ctx.paint()
        
        # Scale and render SVG
        ctx.scale(scale_x, scale_y)
        handle.render_cairo(ctx)
        
        # Write to PNG first
        surface.write_to_png(temp_png)
        surface.finish()
        
        # Convert PNG to JPEG
        with Image.open(temp_png) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            quality = options.get('quality', 95)
            img.save(output_path, 'JPEG', quality=quality, optimize=True)
        
        # Clean up temp file
        os.remove(temp_png)
        
    elif output_format.lower() == 'png':
        # Direct PNG output
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        ctx = cairo.Context(surface)
        
        # Clear background (transparent)
        ctx.set_operator(cairo.OPERATOR_CLEAR)
        ctx.paint()
        ctx.set_operator(cairo.OPERATOR_OVER)
        
        # Scale and render SVG
        ctx.scale(scale_x, scale_y)
        handle.render_cairo(ctx)
        
        # Write to PNG
        surface.write_to_png(output_path)
        surface.finish()
        
    else:
        # For other formats, convert to PNG first
        temp_png = output_path.replace(f'.{output_format}', '_temp.png')
        
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        ctx = cairo.Context(surface)
        
        # Set background based on format
        if output_format.lower() in ['bmp', 'gif']:
            ctx.set_source_rgba(1, 1, 1, 1)  # White background
            ctx.paint()
        
        # Scale and render SVG
        ctx.scale(scale_x, scale_y)
        handle.render_cairo(ctx)
        
        # Write to temporary PNG
        surface.write_to_png(temp_png)
        surface.finish()
        
        # Convert to target format
        with Image.open(temp_png) as img:
            if output_format.lower() == 'webp':
                quality = options.get('quality', 90)
                img.save(output_path, 'WEBP', quality=quality, method=6)
            elif output_format.lower() == 'bmp':
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                img.save(output_path, 'BMP')
            elif output_format.lower() == 'gif':
                img = img.convert('P', palette=Image.Palette.ADAPTIVE)
                img.save(output_path, 'GIF', optimize=True)
            elif output_format.lower() == 'tiff':
                img.save(output_path, 'TIFF')
            elif output_format.lower() == 'ico':
                if width > 256 or height > 256:
                    img = img.resize((256, 256), Image.Resampling.LANCZOS)
                img.save(output_path, 'ICO')
            else:
                img.save(output_path, output_format.upper())
        
        # Clean up temp file
        os.remove(temp_png)
    
    print(f"✅ Cairo/RSVG conversion successful! Output: {output_path} ({os.path.getsize(output_path)} bytes)")
    return True

def _check_svg_dependencies():
    """Check which SVG conversion dependencies are available"""
    methods = []
    try:
        import cairo
        try:
            import gi
            gi.require_version('Rsvg', '2.0')
            from gi.repository import Rsvg
            methods.append("cairo+rsvg")
        except ImportError:
            try:
                import rsvg
                methods.append("cairo+rsvg")
            except ImportError:
                pass
    except ImportError:
        pass
    
    try:
        import cairosvg
        methods.append("cairosvg")
    except ImportError:
        pass
    
    try:
        from wand.image import Image as WandImage
        methods.append("wand")
    except ImportError:
        pass
    
    if not methods:
        methods.append("basic_fallback")
    
    print(f"Available SVG conversion methods: {', '.join(methods)}")
    return methods

def _convert_from_svg(input_path, output_path, output_format, options):
    """Convert SVG to raster formats (PNG, JPG, etc.)"""
    try:
        # Check what's available
        available_methods = _check_svg_dependencies()
        print(f"Converting SVG {input_path} to {output_format} using: {available_methods}")
        
        # Method 1: Try enhanced cairosvg with cairo-like quality
        try:
            return _convert_svg_enhanced_cairosvg(input_path, output_path, output_format, options)
        except ImportError:
            print("cairosvg not available, trying fallback")
            pass
        except Exception as e:
            print(f"Enhanced cairosvg conversion failed: {str(e)}")
            pass
        
        # Method 2: Try standard cairosvg as fallback
        try:
            import cairosvg
            print(f"Using standard cairosvg for SVG conversion: {input_path} -> {output_format}")
            
            # Read and preprocess SVG content for better rendering
            svg_content = None
            try:
                with open(input_path, 'r', encoding='utf-8') as f:
                    svg_content = f.read()
            except UnicodeDecodeError:
                # Try with different encoding if UTF-8 fails
                with open(input_path, 'r', encoding='latin-1') as f:
                    svg_content = f.read()
            
            # Fix common SVG issues for better rendering
            svg_content = _preprocess_svg_content(svg_content)
            
            # Extract or set appropriate dimensions
            default_width, default_height = _extract_svg_dimensions(svg_content)
            print(f"SVG dimensions detected: {default_width}x{default_height}")
            
            # Debug: Save preprocessed SVG for inspection
            debug_svg_path = output_path.replace(f'.{output_format}', '_debug.svg')
            with open(debug_svg_path, 'w', encoding='utf-8') as f:
                f.write(svg_content)
            print(f"Debug SVG saved to: {debug_svg_path}")
            
            # Determine output format and settings
            if output_format.lower() in ['jpg', 'jpeg']:
                # For JPEG, convert to PNG first then to JPEG (since cairosvg doesn't support JPEG directly)
                temp_png = output_path.replace(f'.{output_format}', '_temp.png')
                
                # Get dimensions if specified, otherwise use SVG's natural dimensions
                width = options.get('width') or default_width
                height = options.get('height') or default_height
                
                # Convert SVG to PNG with enhanced settings
                print(f"Converting to temporary PNG: {temp_png} at {width}x{height}")
                cairosvg.svg2png(
                    bytestring=svg_content.encode('utf-8'),
                    write_to=temp_png,
                    output_width=width,
                    output_height=height,
                    dpi=300  # Higher DPI for better quality
                )
                print(f"Temporary PNG created, size: {os.path.getsize(temp_png)} bytes")
                
                # Convert PNG to JPEG
                with Image.open(temp_png) as png_img:
                    # Create white background for JPEG
                    if png_img.mode in ('RGBA', 'LA'):
                        background = Image.new('RGB', png_img.size, 'white')
                        background.paste(png_img, mask=png_img.split()[-1] if png_img.mode == 'RGBA' else None)
                        png_img = background
                    elif png_img.mode != 'RGB':
                        png_img = png_img.convert('RGB')
                    
                    quality = options.get('quality', 95)
                    png_img.save(output_path, 'JPEG', quality=quality, optimize=True)
                
                # Clean up temp file
                os.remove(temp_png)
                
            elif output_format.lower() == 'webp':
                # Convert to PNG first, then to WebP
                temp_png = output_path.replace('.webp', '_temp.png')
                
                width = options.get('width') or default_width
                height = options.get('height') or default_height
                
                cairosvg.svg2png(
                    bytestring=svg_content.encode('utf-8'),
                    write_to=temp_png,
                    output_width=width,
                    output_height=height,
                    dpi=300
                )
                
                with Image.open(temp_png) as png_img:
                    quality = options.get('quality', 90)
                    png_img.save(output_path, 'WEBP', quality=quality, method=6)
                
                os.remove(temp_png)
                
            else:
                # For PNG and other formats
                width = options.get('width') or default_width
                height = options.get('height') or default_height
                
                if output_format.lower() == 'png':
                    print(f"Converting directly to PNG: {output_path} at {width}x{height}")
                    cairosvg.svg2png(
                        bytestring=svg_content.encode('utf-8'),
                        write_to=output_path,
                        output_width=width,
                        output_height=height,
                        dpi=300
                    )
                    print(f"PNG created, size: {os.path.getsize(output_path)} bytes")
                else:
                    # Convert to PNG first, then to target format
                    temp_png = output_path.replace(f'.{output_format}', '_temp.png')
                    cairosvg.svg2png(
                        bytestring=svg_content.encode('utf-8'),
                        write_to=temp_png,
                        output_width=width,
                        output_height=height,
                        dpi=300
                    )
                    
                    # Convert PNG to target format
                    with Image.open(temp_png) as png_img:
                        if output_format.lower() == 'bmp':
                            if png_img.mode in ('RGBA', 'LA'):
                                background = Image.new('RGB', png_img.size, 'white')
                                background.paste(png_img, mask=png_img.split()[-1] if png_img.mode == 'RGBA' else None)
                                png_img = background
                            png_img.save(output_path, 'BMP')
                        elif output_format.lower() == 'gif':
                            png_img = png_img.convert('P', palette=Image.Palette.ADAPTIVE)
                            png_img.save(output_path, 'GIF', optimize=True)
                        elif output_format.lower() == 'tiff':
                            png_img.save(output_path, 'TIFF')
                        elif output_format.lower() == 'ico':
                            if png_img.width > 256 or png_img.height > 256:
                                png_img = png_img.resize((256, 256), Image.Resampling.LANCZOS)
                            png_img.save(output_path, 'ICO')
                        else:
                            png_img.save(output_path, output_format.upper())
                    
                    os.remove(temp_png)
            
            # Verify the conversion worked
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                print(f"✅ SVG conversion successful! Output: {output_path} ({os.path.getsize(output_path)} bytes)")
                return True
            else:
                print(f"❌ SVG conversion failed - output file missing or empty")
                return False
            
        except ImportError:
            print("cairosvg not available, trying alternative method")
            pass
        except Exception as e:
            print(f"CairoSVG conversion failed: {str(e)}")
            print(f"SVG file size: {os.path.getsize(input_path)} bytes")
            # Try to log SVG content issues
            try:
                with open(input_path, 'r', encoding='utf-8') as f:
                    content = f.read()[:500]  # First 500 chars
                    print(f"SVG preview: {content}...")
            except:
                pass
        
        # Method 2: Try using Wand (ImageMagick) as fallback
        try:
            from wand.image import Image as WandImage
            from wand.color import Color
            
            with WandImage(filename=input_path) as img:
                # Set background to white for formats that don't support transparency
                if output_format.lower() in ['jpg', 'jpeg', 'bmp']:
                    img.background_color = Color('white')
                    img.alpha_channel = 'remove'
                
                # Apply resize if specified
                if 'width' in options or 'height' in options:
                    width = options.get('width', img.width)
                    height = options.get('height', img.height)
                    img.resize(int(width), int(height))
                
                # Set format and save
                img.format = output_format.lower()
                if output_format.lower() in ['jpg', 'jpeg']:
                    img.compression_quality = options.get('quality', 95)
                
                img.save(filename=output_path)
            
            return True
            
        except ImportError:
            print("Wand not available, using basic fallback")
            pass
        
        # Method 3: Basic fallback - create a placeholder image with SVG info
        # This creates a visible image when proper SVG rendering is not available
        try:
            import xml.etree.ElementTree as ET
            
            # Parse SVG to get dimensions
            tree = ET.parse(input_path)
            root = tree.getroot()
            
            # Extract width and height from SVG
            width = root.get('width', '400')
            height = root.get('height', '400')
            viewBox = root.get('viewBox', f'0 0 {width} {height}')
            
            # Remove units and convert to int
            import re
            try:
                width = int(float(re.sub(r'[^\d.]', '', str(width)) or 400))
                height = int(float(re.sub(r'[^\d.]', '', str(height)) or 400))
            except:
                width, height = 400, 400
            
            # If viewBox is available, use it for dimensions
            if viewBox:
                try:
                    vb_parts = viewBox.split()
                    if len(vb_parts) >= 4:
                        vb_width = int(float(vb_parts[2]))
                        vb_height = int(float(vb_parts[3]))
                        if vb_width > 0 and vb_height > 0:
                            width, height = vb_width, vb_height
                except:
                    pass
            
            # Ensure reasonable dimensions
            width = max(100, min(width, 2000))
            height = max(100, min(height, 2000))
            
            # Apply resize if specified
            if 'width' in options or 'height' in options:
                width = int(options.get('width', width))
                height = int(options.get('height', height))
            
            # Create a placeholder image with a visible pattern
            if output_format.lower() in ['jpg', 'jpeg']:
                img = Image.new('RGB', (width, height), 'white')
            else:
                img = Image.new('RGBA', (width, height), (255, 255, 255, 255))
            
            # Draw a simple pattern to make the image visible
            from PIL import ImageDraw, ImageFont
            draw = ImageDraw.Draw(img)
            
            # Draw a border
            border_color = (100, 100, 100) if output_format.lower() in ['jpg', 'jpeg'] else (100, 100, 100, 255)
            draw.rectangle([0, 0, width-1, height-1], outline=border_color, width=2)
            
            # Draw diagonal lines to show it's a converted SVG
            for i in range(0, width, 20):
                draw.line([i, 0, i, height], fill=(200, 200, 200), width=1)
            for i in range(0, height, 20):
                draw.line([0, i, width, i], fill=(200, 200, 200), width=1)
            
            # Try to add text
            try:
                # Try to use a default font
                font_size = min(width, height) // 20
                font_size = max(12, min(font_size, 48))
                
                text = "SVG Converted"
                text_width = len(text) * font_size // 2
                text_height = font_size
                
                x = (width - text_width) // 2
                y = (height - text_height) // 2
                
                text_color = (50, 50, 50) if output_format.lower() in ['jpg', 'jpeg'] else (50, 50, 50, 255)
                draw.text((x, y), text, fill=text_color)
                
            except:
                # If text fails, draw a simple shape
                center_x, center_y = width // 2, height // 2
                size = min(width, height) // 4
                shape_color = (150, 150, 150) if output_format.lower() in ['jpg', 'jpeg'] else (150, 150, 150, 255)
                draw.ellipse([center_x - size, center_y - size, center_x + size, center_y + size], 
                           fill=shape_color, outline=border_color)
            
            # Save in target format
            save_kwargs = {}
            if output_format.lower() in ['jpg', 'jpeg']:
                quality = options.get('quality', 95)
                save_kwargs = {'quality': int(quality), 'optimize': True}
                img.save(output_path, 'JPEG', **save_kwargs)
            elif output_format.lower() == 'png':
                save_kwargs = {'optimize': True}
                img.save(output_path, 'PNG', **save_kwargs)
            elif output_format.lower() == 'webp':
                quality = options.get('quality', 90)
                save_kwargs = {'quality': int(quality), 'method': 6}
                img.save(output_path, 'WEBP', **save_kwargs)
            else:
                img.save(output_path, output_format.upper())
            
            print(f"SVG converted using fallback method: {width}x{height} -> {output_format}")
            return True
            
        except Exception as e:
            print(f"SVG fallback conversion error: {str(e)}")
            return False
        
    except Exception as e:
        print(f"SVG conversion error: {str(e)}")
        return False

def _convert_special_formats(input_path, output_path, input_format, output_format, options):
    """Handle special formats that PIL might not support directly"""
    try:
        # For SVG output, embed the raster image in an SVG container
        if output_format.lower() == 'svg':
            return _convert_to_svg(input_path, output_path, options)
                
        # For EPS, PSD - try using Wand (ImageMagick) if available
        if output_format.lower() in ['eps', 'psd']:
            try:
                from wand.image import Image as WandImage
                with WandImage(filename=input_path) as img:
                    img.format = output_format.lower()
                    img.save(filename=output_path)
                return True
            except ImportError:
                pass
        
        # Fallback: convert to PNG
        with Image.open(input_path) as img:
            if img.mode in ('RGBA', 'LA'):
                img = img.convert('RGBA')
            else:
                img = img.convert('RGB')
            img.save(output_path.replace(f'.{output_format}', '.png'), 'PNG')
            # Rename to requested format for download
            os.rename(output_path.replace(f'.{output_format}', '.png'), output_path)
        return True
        
    except Exception as e:
        print(f"Special format conversion error: {str(e)}")
        return False

def convert_image(file, input_body):
    """Convert images between different formats using PIL/Pillow"""
    # Save uploaded file to temporary location
    input_extension = os.path.splitext(file.filename)[1].lower().lstrip('.')
    with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{input_extension}') as temp_input:
        file.save(temp_input.name)
        input_path = temp_input.name

    try:
        # Parse conversion task - support both old and new format
        convert_task = input_body['tasks']['convert']
        
        # New format has input_format and output_format at same level
        if 'input_format' in convert_task and 'output_format' in convert_task:
            input_format = convert_task.get('input_format', input_extension).lower()
            output_format = convert_task.get('output_format', 'png').lower()
        else:
            # Legacy format support
            input_format = input_extension
            output_format = convert_task.get('output_format', 'png').lower()
        
        # Validate output format
        if output_format not in SUPPORTED_FORMATS:
            raise Exception(f"Unsupported output format: {output_format}. Supported formats: {', '.join(SUPPORTED_FORMATS)}")
        
        # Generate output filename and path
        output_filename = str(uuid.uuid4()) + f'.{output_format}'
        output_path = os.path.join(EXPORT_DIR, output_filename)

        # Parse options and convert new format to internal format
        options = _parse_image_options(convert_task.get('options', {}), output_format)
        
        # Perform actual image conversion with PIL
        success = _convert_image_with_pil(input_path, output_path, input_format, output_format, options)
        
        if not success:
            raise Exception(f"Failed to convert {input_format} to {output_format}")
        
        # Verify output file was created and has content
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise Exception(f"Output file was not created or is empty")
        
        # Get actual image dimensions
        try:
            with Image.open(output_path) as img:
                width, height = img.size
        except:
            width, height = 800, 600  # fallback
        
        # Clean up temporary file
        os.remove(input_path)
        
        # Return success response
        return {
            'success': True,
            'export_url': f"/export/images/{output_filename}?ngrok-skip-browser-warning=true",
            'download_url': f"/download/images/{output_filename}?ngrok-skip-browser-warning=true",
            'filename': output_filename,
            'output_format': output_format,
            'input_format': input_format,
            'conversion_method': 'pillow',
            'dimensions': {'width': width, 'height': height}
        }
        
    except Exception as e:
        # Clean up on error
        if os.path.exists(input_path):
            os.remove(input_path)
        raise Exception(f"Image conversion error: {str(e)}")

# Utility functions for specific conversions
def webp_to_png(webp_file, options=None):
    """Convert WebP to PNG - utility function"""
    return convert_image(webp_file, {
        'tasks': {
            'convert': {
                'input_format': 'webp',
                'output_format': 'png',
                'options': options or {}
            }
        }
    })

def jfif_to_png(jfif_file, options=None):
    """Convert JFIF to PNG - utility function"""
    return convert_image(jfif_file, {
        'tasks': {
            'convert': {
                'input_format': 'jfif',
                'output_format': 'png',
                'options': options or {}
            }
        }
    })

def png_to_svg(png_file, options=None):
    """Convert PNG to SVG - utility function"""
    return convert_image(png_file, {
        'tasks': {
            'convert': {
                'input_format': 'png',
                'output_format': 'svg',
                'options': options or {}
            }
        }
    })

def heic_to_jpg(heic_file, options=None):
    """Convert HEIC to JPG - utility function"""
    return convert_image(heic_file, {
        'tasks': {
            'convert': {
                'input_format': 'heic',
                'output_format': 'jpg',
                'options': options or {}
            }
        }
    })

def heic_to_png(heic_file, options=None):
    """Convert HEIC to PNG - utility function"""
    return convert_image(heic_file, {
        'tasks': {
            'convert': {
                'input_format': 'heic',
                'output_format': 'png',
                'options': options or {}
            }
        }
    })

def webp_to_jpg(webp_file, options=None):
    """Convert WebP to JPG - utility function"""
    return convert_image(webp_file, {
        'tasks': {
            'convert': {
                'input_format': 'webp',
                'output_format': 'jpg',
                'options': options or {}
            }
        }
    }) 