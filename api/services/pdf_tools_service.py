import os
import uuid
import tempfile
import json
import fitz  # PyMuPDF
from PIL import Image
import io
import base64
import zipfile

EXPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static', 'documents')
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static', 'uploads')
PREVIEW_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static', 'previews')

os.makedirs(EXPORT_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PREVIEW_DIR, exist_ok=True)

SUPPORTED_PDF_FORMATS = ['pdf']

def upload_pdf_file(file):
    """Upload PDF file and return file_id for processing"""
    try:
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        
        # Save uploaded file
        filename = f"{file_id}.pdf"
        file_path = os.path.join(UPLOAD_DIR, filename)
        file.save(file_path)
        
        # Validate PDF by opening it
        pdf_doc = fitz.open(file_path)
        total_pages = len(pdf_doc)
        pdf_doc.close()
        
        return {
            'success': True,
            'message': 'PDF uploaded successfully',
            'file_id': file_id,
            'filename': file.filename,
            'total_pages': total_pages
        }
        
    except Exception as e:
        # Clean up file if upload failed
        if 'file_path' in locals() and os.path.exists(file_path):
            try:
                os.unlink(file_path)
            except:
                pass
        raise Exception(f"PDF upload failed: {str(e)}")

def get_pdf_pages(file_id):
    """Get PDF pages information with previews"""
    try:
        # Construct file path
        filename = f"{file_id}.pdf"
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        if not os.path.exists(file_path):
            raise Exception("PDF file not found")
        
        # Open PDF
        pdf_doc = fitz.open(file_path)
        total_pages = len(pdf_doc)
        
        pages = []
        
        for page_num in range(total_pages):
            page = pdf_doc[page_num]
            
            # Create preview image
            mat = fitz.Matrix(0.5, 0.5)  # Scale down for preview
            pix = page.get_pixmap(matrix=mat)
            
            # Convert to PIL Image
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            
            # Save preview image
            preview_filename = f"{file_id}_page_{page_num + 1}.png"
            preview_path = os.path.join(PREVIEW_DIR, preview_filename)
            img.save(preview_path, "PNG")
            
            # Create preview URL
            preview_url = f"/static/previews/{preview_filename}"
            
            pages.append({
                'page_number': page_num + 1,
                'preview_url': preview_url,
                'width': pix.width,
                'height': pix.height
            })
        
        pdf_doc.close()
        
        return {
            'success': True,
            'message': 'PDF pages retrieved successfully',
            'total_pages': total_pages,
            'pages': pages
        }
        
    except Exception as e:
        raise Exception(f"Failed to get PDF pages: {str(e)}")

def split_pdf_by_file_id(input_body):
    """Split PDF using file_id with enhanced split modes"""
    try:
        file_id = input_body['file_id']
        split_task = input_body['tasks']['split']
        options = split_task.get('options', {})
        
        # Construct file path
        filename = f"{file_id}.pdf"
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        if not os.path.exists(file_path):
            raise Exception("PDF file not found")
        
        # Get split parameters
        split_mode = options.get('split_mode', 'manual')
        output_filename = options.get('output_filename', 'split')
        selected_pages = options.get('selected_pages', [])
        page_ranges = options.get('page_ranges', [])
        pages_per_file = options.get('pages_per_file', 1)
        
        # Open PDF
        pdf_doc = fitz.open(file_path)
        total_pages = len(pdf_doc)
        
        output_files = []
        
        if split_mode == 'manual':
            # Manual selection - split each selected page into individual files
            if selected_pages:
                for page_num in selected_pages:
                    if 1 <= page_num <= total_pages:
                        new_doc = fitz.open()
                        new_doc.insert_pdf(pdf_doc, from_page=page_num-1, to_page=page_num-1)
                        
                        output_filename_gen = f"{output_filename}_page_{page_num}.pdf"
                        output_path = os.path.join(EXPORT_DIR, output_filename_gen)
                        new_doc.save(output_path)
                        new_doc.close()
                        
                        output_files.append({
                            'filename': output_filename_gen,
                            'download_url': f'/static/documents/{output_filename_gen}',
                            'pages': f'{page_num}'
                        })
        
        elif split_mode == 'page_range':
            # Split by page ranges
            if page_ranges:
                for i, page_range in enumerate(page_ranges):
                    start_page = page_range.get('start', 1)
                    end_page = page_range.get('end', total_pages)
                    
                    # Validate page range
                    if 1 <= start_page <= end_page <= total_pages:
                        new_doc = fitz.open()
                        new_doc.insert_pdf(pdf_doc, from_page=start_page-1, to_page=end_page-1)
                        
                        output_filename_gen = f"{output_filename}_range_{i+1}.pdf"
                        output_path = os.path.join(EXPORT_DIR, output_filename_gen)
                        new_doc.save(output_path)
                        new_doc.close()
                        
                        output_files.append({
                            'filename': output_filename_gen,
                            'download_url': f'/static/documents/{output_filename_gen}',
                            'pages': f'{start_page}-{end_page}'
                        })
        
        elif split_mode == 'fixed_pages':
            # Split every N pages
            for i in range(0, total_pages, pages_per_file):
                end_page = min(i + pages_per_file, total_pages)
                new_doc = fitz.open()
                new_doc.insert_pdf(pdf_doc, from_page=i, to_page=end_page-1)
                
                output_filename_gen = f"{output_filename}_part_{i//pages_per_file + 1}.pdf"
                output_path = os.path.join(EXPORT_DIR, output_filename_gen)
                new_doc.save(output_path)
                new_doc.close()
                
                output_files.append({
                    'filename': output_filename_gen,
                    'download_url': f'/static/documents/{output_filename_gen}',
                    'pages': f'{i+1}-{end_page}'
                })
        
        elif split_mode == 'odd_even':
            # Split into odd and even pages
            odd_pages = []
            even_pages = []
            
            for page_num in range(1, total_pages + 1):
                if page_num % 2 == 1:  # Odd pages
                    odd_pages.append(page_num - 1)  # Convert to 0-based index
                else:  # Even pages
                    even_pages.append(page_num - 1)  # Convert to 0-based index
            
            # Create odd pages PDF
            if odd_pages:
                odd_doc = fitz.open()
                for page_index in odd_pages:
                    odd_doc.insert_pdf(pdf_doc, from_page=page_index, to_page=page_index)
                
                odd_filename = f"{output_filename}_odd_pages.pdf"
                odd_path = os.path.join(EXPORT_DIR, odd_filename)
                odd_doc.save(odd_path)
                odd_doc.close()
                
                output_files.append({
                    'filename': odd_filename,
                    'download_url': f'/static/documents/{odd_filename}',
                    'pages': f'Odd pages ({len(odd_pages)} pages)'
                })
            
            # Create even pages PDF
            if even_pages:
                even_doc = fitz.open()
                for page_index in even_pages:
                    even_doc.insert_pdf(pdf_doc, from_page=page_index, to_page=page_index)
                
                even_filename = f"{output_filename}_even_pages.pdf"
                even_path = os.path.join(EXPORT_DIR, even_filename)
                even_doc.save(even_path)
                even_doc.close()
                
                output_files.append({
                    'filename': even_filename,
                    'download_url': f'/static/documents/{even_filename}',
                    'pages': f'Even pages ({len(even_pages)} pages)'
                })
        
        elif split_mode == 'split_half':
            # Split in half
            mid_point = (total_pages + 1) // 2
            
            # First half
            first_half_doc = fitz.open()
            first_half_doc.insert_pdf(pdf_doc, from_page=0, to_page=mid_point-1)
            
            first_half_filename = f"{output_filename}_first_half.pdf"
            first_half_path = os.path.join(EXPORT_DIR, first_half_filename)
            first_half_doc.save(first_half_path)
            first_half_doc.close()
            
            output_files.append({
                'filename': first_half_filename,
                'download_url': f'/static/documents/{first_half_filename}',
                'pages': f'1-{mid_point}'
            })
            
            # Second half
            if mid_point < total_pages:
                second_half_doc = fitz.open()
                second_half_doc.insert_pdf(pdf_doc, from_page=mid_point, to_page=total_pages-1)
                
                second_half_filename = f"{output_filename}_second_half.pdf"
                second_half_path = os.path.join(EXPORT_DIR, second_half_filename)
                second_half_doc.save(second_half_path)
                second_half_doc.close()
                
                output_files.append({
                    'filename': second_half_filename,
                    'download_url': f'/static/documents/{second_half_filename}',
                    'pages': f'{mid_point+1}-{total_pages}'
                })
        
        elif split_mode == 'extract_all':
            # Extract all pages as separate PDFs
            for page_num in range(1, total_pages + 1):
                new_doc = fitz.open()
                new_doc.insert_pdf(pdf_doc, from_page=page_num-1, to_page=page_num-1)
                
                output_filename_gen = f"{output_filename}_page_{page_num}.pdf"
                output_path = os.path.join(EXPORT_DIR, output_filename_gen)
                new_doc.save(output_path)
                new_doc.close()
                
                output_files.append({
                    'filename': output_filename_gen,
                    'download_url': f'/static/documents/{output_filename_gen}',
                    'pages': f'{page_num}'
                })
        
        pdf_doc.close()
        
        # Create ZIP file if multiple files
        if len(output_files) > 1:
            zip_filename = f"{output_filename}_split.zip"
            zip_path = os.path.join(EXPORT_DIR, zip_filename)
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for output_file in output_files:
                    file_path = os.path.join(EXPORT_DIR, output_file['filename'])
                    if os.path.exists(file_path):
                        zipf.write(file_path, output_file['filename'])
            
            return {
                'success': True,
                'message': f'PDF split successfully into {len(output_files)} files',
                'output_files': output_files,
                'zip_filename': zip_filename,
                'download_url': f'/static/documents/{zip_filename}'
            }
        else:
            # Single file - return direct download
            return {
                'success': True,
                'message': 'PDF split successfully',
                'output_files': output_files,
                'download_url': output_files[0]['download_url'] if output_files else None
            }
        
    except Exception as e:
        raise Exception(f"PDF split failed: {str(e)}")

def parse_page_ranges(ranges_str, total_pages):
    """Parse page ranges string into list of tuples"""
    ranges = []
    parts = ranges_str.split(',')
    
    for part in parts:
        part = part.strip()
        if '-' in part:
            # Range like "1-3"
            start, end = part.split('-')
            try:
                start_page = int(start.strip())
                end_page = int(end.strip())
                if 1 <= start_page <= end_page <= total_pages:
                    ranges.append((start_page, end_page))
            except ValueError:
                continue
        else:
            # Single page like "5"
            try:
                page_num = int(part)
                if 1 <= page_num <= total_pages:
                    ranges.append((page_num, page_num))
            except ValueError:
                continue
    
    return ranges

def merge_pdfs(files, input_body):
    """Merge multiple PDF files into one"""
    try:
        # Validate input structure
        if 'tasks' not in input_body or 'merge' not in input_body['tasks']:
            raise Exception("Invalid input structure: missing 'tasks' or 'merge'")
        
        merge_task = input_body['tasks']['merge']
        options = merge_task.get('options', {})
        
        # Get PDF files
        pdf_files = [f for f in files if f.filename.lower().endswith('.pdf')]
        if len(pdf_files) < 2:
            raise Exception("At least 2 PDF files are required for merging")
        
        # Get output filename from options or generate one
        output_filename = options.get('output_filename', str(uuid.uuid4()) + '.pdf')
        if not output_filename.endswith('.pdf'):
            output_filename += '.pdf'
        
        output_path = os.path.join(EXPORT_DIR, output_filename)
        
        # Merge PDFs
        merger = fitz.open()
        
        for pdf_file in pdf_files:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_input:
                pdf_file.save(temp_input.name)
                pdf_doc = fitz.open(temp_input.name)
                merger.insert_pdf(pdf_doc)
                pdf_doc.close()
                os.unlink(temp_input.name)
        
        merger.save(output_path)
        merger.close()
        
        return {
            'success': True,
            'message': f'Successfully merged {len(pdf_files)} PDF files',
            'output_filename': output_filename,
            'download_url': f'/download/documents/{output_filename}',
            'merged_files': len(pdf_files)
        }
        
    except Exception as e:
        raise Exception(f"PDF merge failed: {str(e)}")

def split_pdf(file, input_body):
    """Split PDF into multiple files"""
    # Save uploaded file to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_input:
        file.save(temp_input.name)
        input_path = temp_input.name

    try:
        # Validate input structure
        if 'tasks' not in input_body or 'split' not in input_body['tasks']:
            raise Exception("Invalid input structure: missing 'tasks' or 'split'")
        
        split_task = input_body['tasks']['split']
        options = split_task.get('options', {})
        
        # Get split parameters
        split_type = options.get('split_type', 'pages')  # 'pages' or 'ranges'
        pages_per_file = options.get('pages_per_file', 1)
        page_ranges = options.get('page_ranges', [])  # List of page ranges like [[1,3], [5,7]]
        
        # Open PDF
        pdf_doc = fitz.open(input_path)
        total_pages = len(pdf_doc)
        
        output_files = []
        
        if split_type == 'pages':
            # Split by number of pages per file
            for i in range(0, total_pages, pages_per_file):
                end_page = min(i + pages_per_file, total_pages)
                new_doc = fitz.open()
                new_doc.insert_pdf(pdf_doc, from_page=i, to_page=end_page-1)
                
                output_filename = str(uuid.uuid4()) + '.pdf'
                output_path = os.path.join(EXPORT_DIR, output_filename)
                new_doc.save(output_path)
                new_doc.close()
                
                output_files.append({
                    'filename': output_filename,
                    'download_url': f'/download/documents/{output_filename}',
                    'pages': f'{i+1}-{end_page}'
                })
        
        elif split_type == 'ranges':
            # Split by specified page ranges
            for i, page_range in enumerate(page_ranges):
                if len(page_range) == 2:
                    start_page, end_page = page_range
                    new_doc = fitz.open()
                    new_doc.insert_pdf(pdf_doc, from_page=start_page-1, to_page=end_page-1)
                    
                    output_filename = str(uuid.uuid4()) + '.pdf'
                    output_path = os.path.join(EXPORT_DIR, output_filename)
                    new_doc.save(output_path)
                    new_doc.close()
                    
                    output_files.append({
                        'filename': output_filename,
                        'download_url': f'/download/documents/{output_filename}',
                        'pages': f'{start_page}-{end_page}'
                    })
        
        pdf_doc.close()
        
        return {
            'success': True,
            'message': 'PDF split successfully',
            'output_files': output_files
        }
        
    except Exception as e:
        raise Exception(f"PDF split failed: {str(e)}")
    finally:
        # Clean up temporary file
        if 'input_path' in locals():
            try:
                os.unlink(input_path)
            except:
                pass

def flatten_pdf(file, input_body):
    """Flatten PDF (convert annotations and form fields to content)"""
    # Save uploaded file to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_input:
        file.save(temp_input.name)
        input_path = temp_input.name

    try:
        # Validate input structure
        if 'tasks' not in input_body or 'flatten' not in input_body['tasks']:
            raise Exception("Invalid input structure: missing 'tasks' or 'flatten'")
        
        # Open PDF
        pdf_doc = fitz.open(input_path)
        
        # Flatten annotations and form fields
        for page_num in range(len(pdf_doc)):
            page = pdf_doc[page_num]
            page.apply_redactions()
            page.flatten_annotations()
        
        # Save flattened PDF
        output_filename = str(uuid.uuid4()) + '.pdf'
        output_path = os.path.join(EXPORT_DIR, output_filename)
        pdf_doc.save(output_path)
        pdf_doc.close()
        
        return {
            'success': True,
            'message': 'PDF flattened successfully',
            'output_filename': output_filename,
            'download_url': f'/download/documents/{output_filename}'
        }
        
    except Exception as e:
        raise Exception(f"PDF flatten failed: {str(e)}")
    finally:
        # Clean up temporary file
        if 'input_path' in locals():
            try:
                os.unlink(input_path)
            except:
                pass

def resize_pdf(file, input_body):
    """Resize PDF pages to specified dimensions"""
    # Save uploaded file to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_input:
        file.save(temp_input.name)
        input_path = temp_input.name

    try:
        # Validate input structure
        if 'tasks' not in input_body or 'resize' not in input_body['tasks']:
            raise Exception("Invalid input structure: missing 'tasks' or 'resize'")
        
        resize_task = input_body['tasks']['resize']
        options = resize_task.get('options', {})
        
        # Get resize parameters
        width = options.get('width')
        height = options.get('height')
        scale = options.get('scale', 1.0)
        
        if not width and not height and scale == 1.0:
            raise Exception("Either width/height or scale must be specified")
        
        # Open PDF
        pdf_doc = fitz.open(input_path)
        
        # Create new PDF with resized pages
        new_doc = fitz.open()
        
        for page_num in range(len(pdf_doc)):
            page = pdf_doc[page_num]
            
            # Calculate new dimensions
            if width and height:
                new_width, new_height = width, height
            else:
                new_width = page.rect.width * scale
                new_height = page.rect.height * scale
            
            # Create new page with new dimensions
            new_page = new_doc.new_page(width=new_width, height=new_height)
            
            # Copy content with scaling
            mat = fitz.Matrix(scale, scale)
            new_page.show_pdf_page(new_page.rect, pdf_doc, page_num, matrix=mat)
        
        # Save resized PDF
        output_filename = str(uuid.uuid4()) + '.pdf'
        output_path = os.path.join(EXPORT_DIR, output_filename)
        new_doc.save(output_path)
        new_doc.close()
        pdf_doc.close()
        
        return {
            'success': True,
            'message': 'PDF resized successfully',
            'output_filename': output_filename,
            'download_url': f'/download/documents/{output_filename}'
        }
        
    except Exception as e:
        raise Exception(f"PDF resize failed: {str(e)}")
    finally:
        # Clean up temporary file
        if 'input_path' in locals():
            try:
                os.unlink(input_path)
            except:
                pass

def unlock_pdf(file, input_body):
    """Remove password protection from PDF"""
    # Save uploaded file to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_input:
        file.save(temp_input.name)
        input_path = temp_input.name

    try:
        # Validate input structure
        if 'tasks' not in input_body or 'unlock' not in input_body['tasks']:
            raise Exception("Invalid input structure: missing 'tasks' or 'unlock'")
        
        unlock_task = input_body['tasks']['unlock']
        options = unlock_task.get('options', {})
        
        # Get password if provided
        password = options.get('password', '')
        
        # Open PDF
        try:
            pdf_doc = fitz.open(input_path)
        except:
            # Try with password
            pdf_doc = fitz.open(input_path, password=password)
        
        # Create new unprotected PDF
        new_doc = fitz.open()
        new_doc.insert_pdf(pdf_doc)
        
        # Save unprotected PDF
        output_filename = str(uuid.uuid4()) + '.pdf'
        output_path = os.path.join(EXPORT_DIR, output_filename)
        new_doc.save(output_path)
        new_doc.close()
        pdf_doc.close()
        
        return {
            'success': True,
            'message': 'PDF unlocked successfully',
            'output_filename': output_filename,
            'download_url': f'/download/documents/{output_filename}'
        }
        
    except Exception as e:
        raise Exception(f"PDF unlock failed: {str(e)}")
    finally:
        # Clean up temporary file
        if 'input_path' in locals():
            try:
                os.unlink(input_path)
            except:
                pass

def rotate_pdf(file_id, input_body):
    """Rotate PDF pages"""
    print(f"DEBUG: Starting rotate_pdf function")
    print(f"DEBUG: Input body: {input_body}")
    
    try:
        # Validate input structure
        if 'tasks' not in input_body or 'rotate' not in input_body['tasks']:
            raise Exception("Invalid input structure: missing 'tasks' or 'rotate'")
        
        rotate_task = input_body['tasks']['rotate']
        options = rotate_task.get('options', {})
        
        print(f"DEBUG: Options received: {options}")
        
        # Check if we have the new per-page rotation format or legacy format
        pages_rotations = options.get('pages', [])
        legacy_angle = options.get('angle', None)
        legacy_page_range = options.get('page_range', None)
        
        print(f"DEBUG: Pages rotations: {pages_rotations} (type: {type(pages_rotations)})")
        print(f"DEBUG: Legacy angle: {legacy_angle}, Legacy page range: {legacy_page_range}")
        
        # Open PDF
        filename = f"{file_id}.pdf"
        print(f"DEBUG: Opening PDF file: {os.path.join(UPLOAD_DIR, filename)}")
        pdf_doc = fitz.open(os.path.join(UPLOAD_DIR, filename))
        print(f"DEBUG: PDF opened successfully, total pages: {len(pdf_doc)}")
        
        # Apply rotation
        print(f"DEBUG: Starting rotation process")
        
        if pages_rotations:
            # New per-page rotation format - recompose PDF with selected pages
            print(f"DEBUG: Using new per-page rotation format - recomposing PDF with {len(pages_rotations)} page(s)")
            
            # Create a new PDF document
            new_pdf = fitz.open()
            print(f"DEBUG: Created new PDF document for recomposition")
            
            for i, page_rotation in enumerate(pages_rotations):
                page_number = page_rotation.get('page_number', 1)  # 1-based in frontend
                rotation_angle = page_rotation.get('rotation', 0)
                
                # Convert to 0-based index for PyMuPDF
                page_index = page_number - 1
                
                print(f"DEBUG: Processing page {page_number} (index {page_index}) with rotation {rotation_angle}° - position {i + 1} in output")
                
                if 0 <= page_index < len(pdf_doc):
                    # Get the source page
                    source_page = pdf_doc[page_index]
                    original_rotation = source_page.rotation
                    
                    # Insert page into new document
                    new_pdf.insert_pdf(pdf_doc, from_page=page_index, to_page=page_index)
                    
                    # Get the newly inserted page
                    new_page = new_pdf[i]
                    
                    # Apply the rotation (add to existing rotation)
                    new_rotation = (original_rotation + rotation_angle) % 360
                    new_page.set_rotation(new_rotation)
                    
                    print(f"DEBUG: Page {page_number} -> Output position {i + 1} - Original rotation: {original_rotation}°, Added: {rotation_angle}°, Final: {new_rotation}°")
                else:
                    print(f"DEBUG: Warning - Page {page_number} is out of range (PDF has {len(pdf_doc)} pages), skipping")
            
            # Close original PDF and use the new one
            pdf_doc.close()
            pdf_doc = new_pdf
            print(f"DEBUG: PDF recomposition complete - final document has {len(pdf_doc)} pages")
                    
        elif legacy_angle is not None:
            # Legacy format with single angle and page range
            print(f"DEBUG: Using legacy rotation format - angle: {legacy_angle}°, range: {legacy_page_range}")
            
            if legacy_page_range == 'all' or legacy_page_range is None:
                print(f"DEBUG: Rotating all pages ({len(pdf_doc)} pages)")
                for page_num in range(len(pdf_doc)):
                    page = pdf_doc[page_num]
                    original_rotation = page.rotation
                    page.set_rotation(legacy_angle)
                    print(f"DEBUG: Page {page_num + 1} - Original rotation: {original_rotation}°, New rotation: {legacy_angle}°")
            else:
                print(f"DEBUG: Rotating specific pages: {legacy_page_range}")
                # Apply to specific pages
                for page_num in legacy_page_range:
                    if 0 <= page_num < len(pdf_doc):
                        page = pdf_doc[page_num]
                        original_rotation = page.rotation
                        page.set_rotation(legacy_angle)
                        print(f"DEBUG: Page {page_num + 1} - Original rotation: {original_rotation}°, New rotation: {legacy_angle}°")
                    else:
                        print(f"DEBUG: Warning - Page {page_num + 1} is out of range (PDF has {len(pdf_doc)} pages)")
        else:
            # No rotation specified
            print(f"DEBUG: No rotation parameters found in input")
            raise Exception("No rotation parameters specified. Expected either 'pages' array or 'angle' parameter.")
        
        # Save rotated PDF
        output_filename = str(uuid.uuid4()) + '.pdf'
        output_path = os.path.join(EXPORT_DIR, output_filename)
        print(f"DEBUG: Saving rotated PDF to: {output_path}")
        
        try:
            pdf_doc.save(output_path)
            print(f"DEBUG: PDF saved successfully")
        except Exception as e:
            print(f"DEBUG: Error saving PDF: {str(e)}")
            raise Exception(f"Failed to save rotated PDF: {str(e)}")
        
        pdf_doc.close()
        print(f"DEBUG: PDF document closed")
        
        # Prepare result message based on operation type
        if pages_rotations:
            operation_message = f'PDF recomposed successfully with {len(pages_rotations)} page(s)'
        else:
            operation_message = 'PDF rotated successfully'
        
        result = {
            'success': True,
            'message': operation_message,
            'output_filename': output_filename,
            'download_url': f'/download/documents/{output_filename}',
            'pages_processed': len(pages_rotations) if pages_rotations else len(pdf_doc)
        }
        
        print(f"DEBUG: Returning result: {result}")
        return result
        
    except Exception as e:
        print(f"DEBUG: Exception occurred: {str(e)}")
        raise Exception(f"PDF rotate failed: {str(e)}")
    finally:
        # Clean up temporary file
        print(f"DEBUG: Cleaning up temporary files")
        # if 'filename' in locals():
        #     try:
        #         os.unlink(os.path.join(UPLOAD_DIR, filename))
        #         print(f"DEBUG: Temporary file {os.path.join(UPLOAD_DIR, filename)} deleted successfully")
        #     except Exception as cleanup_error:
        #         print(f"DEBUG: Failed to delete temporary file {os.path.join(UPLOAD_DIR, filename)}: {str(cleanup_error)}")
        #         pass

def protect_pdf(file, input_body):
    """Add password protection to PDF"""
    # Save uploaded file to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_input:
        file.save(temp_input.name)
        input_path = temp_input.name

    try:
        # Validate input structure
        if 'tasks' not in input_body or 'protect' not in input_body['tasks']:
            raise Exception("Invalid input structure: missing 'tasks' or 'protect'")
        
        protect_task = input_body['tasks']['protect']
        options = protect_task.get('options', {})
        
        # Get protection parameters
        user_password = options.get('user_password', '')
        owner_password = options.get('owner_password', '')
        permissions = options.get('permissions', 0)  # PDF permissions
        
        # Open PDF
        pdf_doc = fitz.open(input_path)
        
        # Set encryption
        if user_password or owner_password:
            pdf_doc.save(
                input_path,
                encryption=fitz.PDF_ENCRYPT_AES_256,
                user_pw=user_password,
                owner_pw=owner_password,
                permissions=permissions
            )
        
        # Save protected PDF
        output_filename = str(uuid.uuid4()) + '.pdf'
        output_path = os.path.join(EXPORT_DIR, output_filename)
        pdf_doc.save(output_path)
        pdf_doc.close()
        
        return {
            'success': True,
            'message': 'PDF protected successfully',
            'output_filename': output_filename,
            'download_url': f'/download/documents/{output_filename}'
        }
        
    except Exception as e:
        raise Exception(f"PDF protection failed: {str(e)}")
    finally:
        # Clean up temporary file
        if 'input_path' in locals():
            try:
                os.unlink(input_path)
            except:
                pass

def extract_image_from_pdf(file, input_body):
    """Extract images from PDF pages"""
    # Save uploaded file to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_input:
        file.save(temp_input.name)
        input_path = temp_input.name

    try:
        # Validate input structure
        if 'tasks' not in input_body or 'extract_image' not in input_body['tasks']:
            raise Exception("Invalid input structure: missing 'tasks' or 'extract_image'")
        
        extract_task = input_body['tasks']['extract_image']
        options = extract_task.get('options', {})
        
        # Get extraction parameters
        page_number = options.get('page_number', 0)  # 0-based
        image_format = options.get('image_format', 'png')
        
        # Open PDF
        pdf_doc = fitz.open(input_path)
        
        if page_number >= len(pdf_doc):
            raise Exception(f"Page number {page_number} is out of range")
        
        # Get page
        page = pdf_doc[page_number]
        
        # Extract images
        image_list = page.get_images()
        extracted_images = []
        
        for img_index, img in enumerate(image_list):
            xref = img[0]
            pix = fitz.Pixmap(pdf_doc, xref)
            
            if pix.n - pix.alpha < 4:  # GRAY or RGB
                img_data = pix.tobytes("png")
            else:  # CMYK: convert to RGB first
                pix1 = fitz.Pixmap(fitz.csRGB, pix)
                img_data = pix1.tobytes("png")
                pix1 = None
            
            # Save image
            output_filename = str(uuid.uuid4()) + f'.{image_format}'
            output_path = os.path.join(EXPORT_DIR, output_filename)
            
            with open(output_path, 'wb') as f:
                f.write(img_data)
            
            extracted_images.append({
                'filename': output_filename,
                'download_url': f'/download/images/{output_filename}',
                'index': img_index
            })
            
            pix = None
        
        pdf_doc.close()
        
        return {
            'success': True,
            'message': f'Extracted {len(extracted_images)} images from page {page_number + 1}',
            'extracted_images': extracted_images
        }
        
    except Exception as e:
        raise Exception(f"Image extraction failed: {str(e)}")
    finally:
        # Clean up temporary file
        if 'input_path' in locals():
            try:
                os.unlink(input_path)
            except:
                pass

def extract_all_images_from_pdf(file):
    """Extract all images from all pages of PDF and return as ZIP file"""
    print(f"[DEBUG] Starting image extraction for file: {file.filename}")
    
    # Save uploaded file to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_input:
        file.save(temp_input.name)
        input_path = temp_input.name
        print(f"[DEBUG] File saved to temporary path: {input_path}")

    try:
        # Open PDF
        print("[DEBUG] Opening PDF document...")
        pdf_doc = fitz.open(input_path)
        total_pages = len(pdf_doc)
        print(f"[DEBUG] PDF opened successfully. Total pages: {total_pages}")
        
        # Create ZIP file
        zip_filename = str(uuid.uuid4()) + '.zip'
        zip_path = os.path.join(EXPORT_DIR, zip_filename)
        print(f"[DEBUG] Creating ZIP file: {zip_path}")
        
        extracted_count = 0
        total_images_found = 0
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Extract images from each page
            for page_num in range(total_pages):
                print(f"[DEBUG] Processing page {page_num + 1}/{total_pages}")
                page = pdf_doc[page_num]
                
                # Get images from page
                image_list = page.get_images()
                page_image_count = len(image_list)
                print(f"[DEBUG] Found {page_image_count} images on page {page_num + 1}")
                total_images_found += page_image_count
                
                for img_index, img in enumerate(image_list):
                    print(f"[DEBUG] Processing image {img_index + 1}/{page_image_count} on page {page_num + 1}")
                    xref = img[0]
                    pix = fitz.Pixmap(pdf_doc, xref)
                    
                    try:
                        # Handle different image formats with robust alpha channel removal
                        print(f"[DEBUG] Image format: n={pix.n}, alpha={pix.alpha}")
                        
                        if pix.n == 1:  # GRAY
                            print(f"[DEBUG] Image is GRAY format")
                            img_data = pix.tobytes("jpeg")
                        elif pix.n == 3:  # RGB
                            print(f"[DEBUG] Image is RGB format")
                            img_data = pix.tobytes("jpeg")
                        elif pix.n == 4:  # RGBA or CMYK
                            if pix.alpha:  # RGBA
                                print(f"[DEBUG] Image is RGBA format, removing alpha channel")
                                # Create RGB version without alpha - more robust approach
                                try:
                                    # First try direct RGB conversion
                                    rgb_pix = fitz.Pixmap(fitz.csRGB, pix)
                                    img_data = rgb_pix.tobytes("jpeg")
                                    rgb_pix = None
                                except Exception as rgb_error:
                                    print(f"[DEBUG] Direct RGB conversion failed: {rgb_error}")
                                    # Fallback: convert to PIL Image and back to remove alpha
                                    import io
                                    from PIL import Image
                                    
                                    # Convert to PIL Image
                                    img_bytes = pix.tobytes("png")
                                    pil_img = Image.open(io.BytesIO(img_bytes))
                                    
                                    # Convert to RGB (removes alpha)
                                    if pil_img.mode in ('RGBA', 'LA', 'P'):
                                        pil_img = pil_img.convert('RGB')
                                    
                                    # Convert back to bytes
                                    img_buffer = io.BytesIO()
                                    pil_img.save(img_buffer, format='JPEG', quality=95)
                                    img_data = img_buffer.getvalue()
                                    img_buffer.close()
                            else:  # CMYK
                                print(f"[DEBUG] Image is CMYK format, converting to RGB")
                                rgb_pix = fitz.Pixmap(fitz.csRGB, pix)
                                img_data = rgb_pix.tobytes("jpeg")
                                rgb_pix = None
                        else:
                            print(f"[DEBUG] Unknown image format (n={pix.n}), converting to RGB")
                            # Convert to RGB as fallback
                            rgb_pix = fitz.Pixmap(fitz.csRGB, pix)
                            img_data = rgb_pix.tobytes("jpeg")
                            rgb_pix = None
                        
                        # Create filename for ZIP
                        img_filename = f"page_{page_num + 1}_image_{img_index + 1}.jpg"
                        print(f"[DEBUG] Adding to ZIP: {img_filename}")
                        
                        # Add to ZIP file
                        zip_file.writestr(img_filename, img_data)
                        extracted_count += 1
                        
                        print(f"[DEBUG] Image {img_index + 1} on page {page_num + 1} processed successfully")
                        
                    except Exception as img_error:
                        print(f"[DEBUG] Error processing image {img_index + 1} on page {page_num + 1}: {img_error}")
                        # Continue with next image instead of failing completely
                        continue
                    finally:
                        pix = None
        
        pdf_doc.close()
        print(f"[DEBUG] PDF document closed")
        print(f"[DEBUG] Total images found: {total_images_found}")
        print(f"[DEBUG] Total images extracted: {extracted_count}")
        
        if extracted_count == 0:
            print("[DEBUG] No images found in the PDF")
            raise Exception("No images found in the PDF")
        
        print(f"[DEBUG] ZIP file created successfully: {zip_path}")
        print(f"[DEBUG] Extraction completed successfully")
        
        return {
            'success': True,
            'message': f'Extracted {extracted_count} images from {total_pages} pages',
            'zip_filename': zip_filename,
            'download_url': f'/download/documents/{zip_filename}',
            'extracted_count': extracted_count,
            'total_pages': total_pages
        }
        
    except Exception as e:
        print(f"[DEBUG] Error occurred: {str(e)}")
        raise Exception(f"Image extraction failed: {str(e)}")
    finally:
        # Clean up temporary file
        if 'input_path' in locals():
            try:
                os.unlink(input_path)
                print(f"[DEBUG] Temporary file cleaned up: {input_path}")
            except:
                print(f"[DEBUG] Failed to clean up temporary file: {input_path}")
                pass

def remove_pdf_pages(file, input_body):
    """Remove specific pages from PDF"""
    # Save uploaded file to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_input:
        file.save(temp_input.name)
        input_path = temp_input.name

    try:
        # Validate input structure
        if 'tasks' not in input_body or 'remove_pages' not in input_body['tasks']:
            raise Exception("Invalid input structure: missing 'tasks' or 'remove_pages'")
        
        remove_task = input_body['tasks']['remove_pages']
        options = remove_task.get('options', {})
        
        # Get removal parameters
        pages_to_remove = options.get('pages_to_remove', [])  # List of page numbers (1-based)
        
        if not pages_to_remove:
            raise Exception("No pages specified for removal")
        
        # Open PDF
        pdf_doc = fitz.open(input_path)
        total_pages = len(pdf_doc)
        
        # Convert to 0-based indexing
        pages_to_remove = [p - 1 for p in pages_to_remove if 1 <= p <= total_pages]
        
        if not pages_to_remove:
            raise Exception("No valid pages to remove")
        
        # Create new PDF without specified pages
        new_doc = fitz.open()
        
        for page_num in range(total_pages):
            if page_num not in pages_to_remove:
                new_doc.insert_pdf(pdf_doc, from_page=page_num, to_page=page_num)
        
        # Save modified PDF
        output_filename = str(uuid.uuid4()) + '.pdf'
        output_path = os.path.join(EXPORT_DIR, output_filename)
        new_doc.save(output_path)
        new_doc.close()
        pdf_doc.close()
        
        return {
            'success': True,
            'message': f'Removed {len(pages_to_remove)} pages from PDF',
            'output_filename': output_filename,
            'download_url': f'/download/documents/{output_filename}'
        }
        
    except Exception as e:
        raise Exception(f"PDF page removal failed: {str(e)}")
    finally:
        # Clean up temporary file
        if 'input_path' in locals():
            try:
                os.unlink(input_path)
            except:
                pass

def remove_pages_by_file_id(file_id, page_ids):
    """Remove specific pages from PDF using file_id and page_ids"""
    try:
        # Construct file path
        filename = f"{file_id}.pdf"
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        if not os.path.exists(file_path):
            raise Exception("PDF file not found")
        
        # Open PDF
        pdf_doc = fitz.open(file_path)
        total_pages = len(pdf_doc)
        
        # Convert page_ids to 0-based indexing and validate
        pages_to_remove = []
        for page_id in page_ids:
            if isinstance(page_id, int) and 1 <= page_id <= total_pages:
                pages_to_remove.append(page_id - 1)
        
        if not pages_to_remove:
            raise Exception("No valid pages to remove")
        
        # Create new PDF without specified pages
        new_doc = fitz.open()
        
        for page_num in range(total_pages):
            if page_num not in pages_to_remove:
                new_doc.insert_pdf(pdf_doc, from_page=page_num, to_page=page_num)
        
        # Save modified PDF
        output_filename = str(uuid.uuid4()) + '.pdf'
        output_path = os.path.join(EXPORT_DIR, output_filename)
        new_doc.save(output_path)
        new_doc.close()
        pdf_doc.close()
        
        return {
            'success': True,
            'message': f'Removed {len(pages_to_remove)} pages from PDF',
            'output_filename': output_filename,
            'download_url': f'/download/documents/{output_filename}'
        }
        
    except Exception as e:
        raise Exception(f"PDF page removal failed: {str(e)}")

def extract_pdf_pages(file, input_body):
    """Extract specific pages from PDF"""
    # Save uploaded file to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_input:
        file.save(temp_input.name)
        input_path = temp_input.name

    try:
        # Validate input structure
        if 'tasks' not in input_body or 'extract_pages' not in input_body['tasks']:
            raise Exception("Invalid input structure: missing 'tasks' or 'extract_pages'")
        
        extract_task = input_body['tasks']['extract_pages']
        options = extract_task.get('options', {})
        
        # Get extraction parameters
        page_ranges = options.get('page_ranges', [])  # List of page ranges like [[1,3], [5,7]]
        
        if not page_ranges:
            raise Exception("No page ranges specified for extraction")
        
        # Open PDF
        pdf_doc = fitz.open(input_path)
        total_pages = len(pdf_doc)
        
        extracted_files = []
        
        # Extract each page range
        for i, page_range in enumerate(page_ranges):
            if len(page_range) == 2:
                start_page, end_page = page_range
                
                # Validate page range
                if start_page < 1 or end_page > total_pages or start_page > end_page:
                    continue
                
                # Create new PDF with extracted pages
                new_doc = fitz.open()
                new_doc.insert_pdf(pdf_doc, from_page=start_page-1, to_page=end_page-1)
                
                # Save extracted PDF
                output_filename = str(uuid.uuid4()) + '.pdf'
                output_path = os.path.join(EXPORT_DIR, output_filename)
                new_doc.save(output_path)
                new_doc.close()
                
                extracted_files.append({
                    'filename': output_filename,
                    'download_url': f'/download/documents/{output_filename}',
                    'pages': f'{start_page}-{end_page}'
                })
        
        pdf_doc.close()
        
        return {
            'success': True,
            'message': f'Extracted {len(extracted_files)} page ranges from PDF',
            'extracted_files': extracted_files
        }
        
    except Exception as e:
        raise Exception(f"PDF page extraction failed: {str(e)}")
    finally:
        # Clean up temporary file
        if 'input_path' in locals():
            try:
                os.unlink(input_path)
            except:
                pass

def extract_pages_by_file_id(file_id, page_ranges, merge_output=False, compression_level='none', password=''):
    """Extract pages from PDF using file_id"""
    try:
        # Construct file path
        filename = f"{file_id}.pdf"
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        if not os.path.exists(file_path):
            raise Exception("PDF file not found")
        
        # Open PDF
        try:
            if password:
                pdf_doc = fitz.open(file_path, password=password)
            else:
                pdf_doc = fitz.open(file_path)
        except:
            raise Exception("Failed to open PDF. Check if password is correct.")
        
        total_pages = len(pdf_doc)
        
        # Validate page ranges
        valid_pages = []
        for page_num in page_ranges:
            if isinstance(page_num, int) and 1 <= page_num <= total_pages:
                valid_pages.append(page_num - 1)  # Convert to 0-based index
            else:
                raise Exception(f"Invalid page number: {page_num}. Must be between 1 and {total_pages}")
        
        if not valid_pages:
            raise Exception("No valid pages to extract")
        
        # Remove duplicates and sort
        valid_pages = sorted(list(set(valid_pages)))
        
        if merge_output:
            # Extract all selected pages into one PDF
            new_doc = fitz.open()
            for page_index in valid_pages:
                new_doc.insert_pdf(pdf_doc, from_page=page_index, to_page=page_index)
            
            # Save merged PDF with compression if specified
            output_filename = str(uuid.uuid4()) + '.pdf'
            output_path = os.path.join(EXPORT_DIR, output_filename)
            
            if compression_level != 'none':
                # Apply compression based on level
                if compression_level == 'low':
                    new_doc.save(output_path, garbage=1, deflate=True)
                elif compression_level == 'medium':
                    new_doc.save(output_path, garbage=2, deflate=True)
                elif compression_level == 'high':
                    new_doc.save(output_path, garbage=3, deflate=True, clean=True)
                else:
                    new_doc.save(output_path)
            else:
                new_doc.save(output_path)
            new_doc.close()
            
            pdf_doc.close()
            
            return {
                'success': True,
                'message': f'Extracted {len(valid_pages)} pages into single PDF',
                'output_filename': output_filename,
                'download_url': f'/download/documents/{output_filename}'
            }
        else:
            # Extract each page as separate PDF and create a ZIP file
            extracted_files = []
            temp_files = []  # Track temporary files for cleanup
            
            try:
                for page_index in valid_pages:
                    new_doc = fitz.open()
                    new_doc.insert_pdf(pdf_doc, from_page=page_index, to_page=page_index)
                    
                    # Save individual PDF with compression if specified
                    output_filename = str(uuid.uuid4()) + '.pdf'
                    output_path = os.path.join(EXPORT_DIR, output_filename)
                    
                    if compression_level != 'none':
                        # Apply compression based on level
                        if compression_level == 'low':
                            new_doc.save(output_path, garbage=1, deflate=True)
                        elif compression_level == 'medium':
                            new_doc.save(output_path, garbage=2, deflate=True)
                        elif compression_level == 'high':
                            new_doc.save(output_path, garbage=3, deflate=True, clean=True)
                        else:
                            new_doc.save(output_path)
                    else:
                        new_doc.save(output_path)
                    new_doc.close()
                    
                    temp_files.append(output_path)
                    
                    extracted_files.append({
                        'filename': output_filename,
                        'download_url': f'/download/documents/{output_filename}',
                        'page': page_index + 1
                    })
                
                # Create ZIP file containing all extracted PDFs
                zip_filename = str(uuid.uuid4()) + '.zip'
                zip_path = os.path.join(EXPORT_DIR, zip_filename)
                
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for i, file_path in enumerate(temp_files):
                        # Add file to ZIP with descriptive name
                        page_num = valid_pages[i] + 1
                        zip_name = f'page_{page_num}.pdf'
                        zipf.write(file_path, zip_name)
                
                pdf_doc.close()
                
                return {
                    'success': True,
                    'message': f'Extracted {len(extracted_files)} pages as separate PDFs in ZIP file',
                    'download_url': f'/download/documents/{zip_filename}',
                    'extracted_files': extracted_files,
                    'zip_filename': zip_filename
                }
                
            finally:
                # Clean up individual PDF files after creating ZIP
                for temp_file in temp_files:
                    try:
                        if os.path.exists(temp_file):
                            os.unlink(temp_file)
                    except:
                        pass
        
    except Exception as e:
        raise Exception(f"PDF page extraction failed: {str(e)}")

def split_pdfs_by_file_ids(input_body):
    """Split multiple PDFs using file_ids with enhanced split modes and split configurations"""
    try:
        # Validate input structure
        if 'tasks' not in input_body or 'split' not in input_body['tasks']:
            raise Exception("Invalid input structure: missing 'tasks' or 'split'")
        
        split_task = input_body['tasks']['split']
        options = split_task.get('options', {})
        
        # Get split parameters
        split_mode = options.get('split_mode', 'manual')
        output_filename = options.get('output_filename', 'split')
        split_configurations = options.get('split_configurations', [])
        selected_pages = options.get('pages', [])
        page_ranges = options.get('page_ranges', [])
        pages_per_file = options.get('pages_per_file', 1)
        
        # Check if we have split configurations (new method) or pages (old method)
        if split_configurations:
            # New method using split configurations
            if not isinstance(split_configurations, list):
                raise Exception("Split configurations must be a list")
            
            if len(split_configurations) == 0:
                raise Exception("At least one split configuration must be specified")
            
            output_files = []
            
            # Process each split configuration
            for config_index, config in enumerate(split_configurations):
                if not isinstance(config, dict):
                    raise Exception(f"Split configuration at index {config_index} must be a dictionary")
                
                config_id = config.get('id', f'config_{config_index}')
                config_title = config.get('title', f'Split {config_index + 1}')
                config_pages = config.get('pages', [])
                
                if not isinstance(config_pages, list):
                    raise Exception(f"Pages in split configuration {config_index} must be a list")
                
                if len(config_pages) == 0:
                    continue  # Skip empty configurations
                
                # Create a new PDF document for this configuration
                new_doc = fitz.open()
                
                # Add pages from each file in the order specified
                for page_info in config_pages:
                    if not isinstance(page_info, dict):
                        raise Exception(f"Page data in configuration {config_index} must be a dictionary")
                    
                    file_id = page_info.get('file_id')
                    page_number = page_info.get('page_number', 1)
                    rotation = page_info.get('rotation', 0)
                    
                    if not file_id:
                        raise Exception(f"Missing file_id in page data for configuration {config_index}")
                    
                    # Construct file path
                    filename = f"{file_id}.pdf"
                    file_path = os.path.join(UPLOAD_DIR, filename)
                    
                    if not os.path.exists(file_path):
                        raise Exception(f"PDF file not found for file_id: {file_id}")
                    
                    # Open source PDF
                    source_doc = fitz.open(file_path)
                    total_pages = len(source_doc)
                    
                    # Validate page number
                    if 1 <= page_number <= total_pages:
                        # Insert the page
                        new_doc.insert_pdf(source_doc, from_page=page_number-1, to_page=page_number-1)
                        
                        # Apply rotation if specified
                        if rotation != 0:
                            # Get the last inserted page (which is the one we just added)
                            last_page = new_doc[-1]
                            # Set rotation (rotation should be 0, 90, 180, or 270)
                            last_page.set_rotation(rotation)
                    
                    source_doc.close()
                
                # Save the new document
                if len(new_doc) > 0:
                    # Create a safe filename from the title
                    safe_title = "".join(c for c in config_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    safe_title = safe_title.replace(' ', '_')
                    
                    output_filename_gen = f"{output_filename}_{safe_title}_{config_index + 1}.pdf"
                    output_path = os.path.join(EXPORT_DIR, output_filename_gen)
                    new_doc.save(output_path)
                    
                    output_files.append({
                        'filename': output_filename_gen,
                        'download_url': f'/static/documents/{output_filename_gen}',
                        'title': config_title,
                        'pages': len(new_doc),
                        'config_id': config_id
                    })
                
                new_doc.close()
            
            # Create ZIP file if multiple files
            if len(output_files) > 1:
                zip_filename = f"{output_filename}_split.zip"
                zip_path = os.path.join(EXPORT_DIR, zip_filename)
                
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for output_file in output_files:
                        file_path = os.path.join(EXPORT_DIR, output_file['filename'])
                        if os.path.exists(file_path):
                            zipf.write(file_path, output_file['filename'])
                
                return {
                    'success': True,
                    'message': f'PDFs split successfully into {len(output_files)} files',
                    'output_files': output_files,
                    'zip_filename': zip_filename,
                    'download_url': f'/static/documents/{zip_filename}'
                }
            else:
                # Single file - return direct download
                return {
                    'success': True,
                    'message': 'PDFs split successfully',
                    'output_files': output_files,
                    'download_url': output_files[0]['download_url'] if output_files else None
                }
        
        else:
            # Fallback to old method using pages array
            if not selected_pages:
                raise Exception("No pages specified for splitting")
            
            # Validate pages data
            if not isinstance(selected_pages, list):
                raise Exception("Pages data must be a list")
            
            if len(selected_pages) == 0:
                raise Exception("At least one page must be specified for splitting")
            
            # Validate each page entry
            for i, page_info in enumerate(selected_pages):
                if not isinstance(page_info, dict):
                    raise Exception(f"Page data at index {i} must be a dictionary")
                
                if 'file_id' not in page_info:
                    raise Exception(f"Missing file_id in page data at index {i}")
                
                if 'page_number' in page_info and not isinstance(page_info['page_number'], int):
                    raise Exception(f"page_number must be an integer in page data at index {i}")
            
            # Group pages by file_id
            files_data = {}
            for page_info in selected_pages:
                file_id = page_info.get('file_id')
                page_number = page_info.get('page_number', 1)
                
                if file_id not in files_data:
                    files_data[file_id] = []
                files_data[file_id].append(page_number)
            
            output_files = []
            
            # Process each file
            for file_id, page_numbers in files_data.items():
                # Construct file path
                filename = f"{file_id}.pdf"
                file_path = os.path.join(UPLOAD_DIR, filename)
                
                if not os.path.exists(file_path):
                    raise Exception(f"PDF file not found for file_id: {file_id}")
                
                # Open PDF
                pdf_doc = fitz.open(file_path)
                total_pages = len(pdf_doc)
                
                # Validate page numbers
                valid_pages = [p for p in page_numbers if 1 <= p <= total_pages]
                if not valid_pages:
                    pdf_doc.close()
                    continue
                
                if split_mode == 'manual':
                    # Manual selection - split each selected page into individual files
                    for page_num in valid_pages:
                        new_doc = fitz.open()
                        new_doc.insert_pdf(pdf_doc, from_page=page_num-1, to_page=page_num-1)
                        
                        output_filename_gen = f"{output_filename}_file_{file_id}_page_{page_num}.pdf"
                        output_path = os.path.join(EXPORT_DIR, output_filename_gen)
                        new_doc.save(output_path)
                        new_doc.close()
                        
                        output_files.append({
                            'filename': output_filename_gen,
                            'download_url': f'/static/documents/{output_filename_gen}',
                            'pages': f'{page_num}',
                            'file_id': file_id
                        })
                
                elif split_mode == 'page_range':
                    # Split by page ranges
                    if page_ranges:
                        for i, page_range in enumerate(page_ranges):
                            start_page = page_range.get('start', 1)
                            end_page = page_range.get('end', total_pages)
                            
                            # Validate page range
                            if 1 <= start_page <= end_page <= total_pages:
                                new_doc = fitz.open()
                                new_doc.insert_pdf(pdf_doc, from_page=start_page-1, to_page=end_page-1)
                                
                                output_filename_gen = f"{output_filename}_file_{file_id}_range_{i+1}.pdf"
                                output_path = os.path.join(EXPORT_DIR, output_filename_gen)
                                new_doc.save(output_path)
                                new_doc.close()
                                
                                output_files.append({
                                    'filename': output_filename_gen,
                                    'download_url': f'/static/documents/{output_filename_gen}',
                                    'pages': f'{start_page}-{end_page}',
                                    'file_id': file_id
                                })
                
                elif split_mode == 'fixed_pages':
                    # Split every N pages
                    for i in range(0, total_pages, pages_per_file):
                        end_page = min(i + pages_per_file, total_pages)
                        new_doc = fitz.open()
                        new_doc.insert_pdf(pdf_doc, from_page=i, to_page=end_page-1)
                        
                        output_filename_gen = f"{output_filename}_file_{file_id}_part_{i//pages_per_file + 1}.pdf"
                        output_path = os.path.join(EXPORT_DIR, output_filename_gen)
                        new_doc.save(output_path)
                        new_doc.close()
                        
                        output_files.append({
                            'filename': output_filename_gen,
                            'download_url': f'/static/documents/{output_filename_gen}',
                            'pages': f'{i+1}-{end_page}',
                            'file_id': file_id
                        })
                
                elif split_mode == 'odd_even':
                    # Split into odd and even pages
                    odd_pages = []
                    even_pages = []
                    
                    for page_num in range(1, total_pages + 1):
                        if page_num % 2 == 1:  # Odd pages
                            odd_pages.append(page_num - 1)  # Convert to 0-based index
                        else:  # Even pages
                            even_pages.append(page_num - 1)  # Convert to 0-based index
                    
                    # Create odd pages PDF
                    if odd_pages:
                        odd_doc = fitz.open()
                        for page_index in odd_pages:
                            odd_doc.insert_pdf(pdf_doc, from_page=page_index, to_page=page_index)
                        
                        odd_filename = f"{output_filename}_file_{file_id}_odd_pages.pdf"
                        odd_path = os.path.join(EXPORT_DIR, odd_filename)
                        odd_doc.save(odd_path)
                        odd_doc.close()
                        
                        output_files.append({
                            'filename': odd_filename,
                            'download_url': f'/static/documents/{odd_filename}',
                            'pages': f'Odd pages ({len(odd_pages)} pages)',
                            'file_id': file_id
                        })
                    
                    # Create even pages PDF
                    if even_pages:
                        even_doc = fitz.open()
                        for page_index in even_pages:
                            even_doc.insert_pdf(pdf_doc, from_page=page_index, to_page=page_index)
                        
                        even_filename = f"{output_filename}_file_{file_id}_even_pages.pdf"
                        even_path = os.path.join(EXPORT_DIR, even_filename)
                        even_doc.save(even_path)
                        even_doc.close()
                        
                        output_files.append({
                            'filename': even_filename,
                            'download_url': f'/static/documents/{even_filename}',
                            'pages': f'Even pages ({len(even_pages)} pages)',
                            'file_id': file_id
                        })
                
                elif split_mode == 'split_half':
                    # Split in half
                    mid_point = (total_pages + 1) // 2
                    
                    # First half
                    first_half_doc = fitz.open()
                    first_half_doc.insert_pdf(pdf_doc, from_page=0, to_page=mid_point-1)
                    
                    first_half_filename = f"{output_filename}_file_{file_id}_first_half.pdf"
                    first_half_path = os.path.join(EXPORT_DIR, first_half_filename)
                    first_half_doc.save(first_half_path)
                    first_half_doc.close()
                    
                    output_files.append({
                        'filename': first_half_filename,
                        'download_url': f'/static/documents/{first_half_filename}',
                        'pages': f'1-{mid_point}',
                        'file_id': file_id
                    })
                    
                    # Second half
                    if mid_point < total_pages:
                        second_half_doc = fitz.open()
                        second_half_doc.insert_pdf(pdf_doc, from_page=mid_point, to_page=total_pages-1)
                        
                        second_half_filename = f"{output_filename}_file_{file_id}_second_half.pdf"
                        second_half_path = os.path.join(EXPORT_DIR, second_half_filename)
                        second_half_doc.save(second_half_path)
                        second_half_doc.close()
                        
                        output_files.append({
                            'filename': second_half_filename,
                            'download_url': f'/static/documents/{second_half_filename}',
                            'pages': f'{mid_point+1}-{total_pages}',
                            'file_id': file_id
                        })
                
                elif split_mode == 'extract_all':
                    # Extract all pages as separate PDFs
                    for page_num in range(1, total_pages + 1):
                        new_doc = fitz.open()
                        new_doc.insert_pdf(pdf_doc, from_page=page_num-1, to_page=page_num-1)
                        
                        output_filename_gen = f"{output_filename}_file_{file_id}_page_{page_num}.pdf"
                        output_path = os.path.join(EXPORT_DIR, output_filename_gen)
                        new_doc.save(output_path)
                        new_doc.close()
                        
                        output_files.append({
                            'filename': output_filename_gen,
                            'download_url': f'/static/documents/{output_filename_gen}',
                            'pages': f'{page_num}',
                            'file_id': file_id
                        })
                
                pdf_doc.close()
            
            # Create ZIP file if multiple files
            if len(output_files) > 1:
                zip_filename = f"{output_filename}_split.zip"
                zip_path = os.path.join(EXPORT_DIR, zip_filename)
                
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for output_file in output_files:
                        file_path = os.path.join(EXPORT_DIR, output_file['filename'])
                        if os.path.exists(file_path):
                            zipf.write(file_path, output_file['filename'])
                
                return {
                    'success': True,
                    'message': f'PDFs split successfully into {len(output_files)} files',
                    'output_files': output_files,
                    'zip_filename': zip_filename,
                    'download_url': f'/static/documents/{zip_filename}'
                }
            else:
                # Single file - return direct download
                return {
                    'success': True,
                    'message': 'PDFs split successfully',
                    'output_files': output_files,
                    'download_url': output_files[0]['download_url'] if output_files else None
                }
        
    except Exception as e:
        raise Exception(f"PDF split failed: {str(e)}")

def merge_pdfs_by_file_ids(input_body):
    """Merge PDFs using file_ids with support for page selection and rotation"""
    try:
        # Validate input structure
        if 'tasks' not in input_body or 'merge' not in input_body['tasks']:
            raise Exception("Invalid input structure: missing 'tasks' or 'merge'")
        
        merge_task = input_body['tasks']['merge']
        options = merge_task.get('options', {})
        
        # Get page selection data
        pages_data = options.get('pages', [])
        if not pages_data:
            raise Exception("No pages specified for merging")
        
        # Validate pages data
        if not isinstance(pages_data, list):
            raise Exception("Pages data must be a list")
        
        if len(pages_data) == 0:
            raise Exception("At least one page must be specified for merging")
        
        # Validate each page entry
        for i, page_info in enumerate(pages_data):
            if not isinstance(page_info, dict):
                raise Exception(f"Page data at index {i} must be a dictionary")
            
            if 'file_id' not in page_info:
                raise Exception(f"Missing file_id in page data at index {i}")
            
            if 'page_number' in page_info and not isinstance(page_info['page_number'], int):
                raise Exception(f"page_number must be an integer in page data at index {i}")
            
            if 'rotation' in page_info and not isinstance(page_info['rotation'], int):
                raise Exception(f"rotation must be an integer in page data at index {i}")
        
        # Get output filename from options or generate one
        output_filename = options.get('output_filename', str(uuid.uuid4()) + '.pdf')
        if not output_filename.endswith('.pdf'):
            output_filename += '.pdf'
        
        output_path = os.path.join(EXPORT_DIR, output_filename)
        
        # Merge PDFs
        merger = fitz.open()
        
        for page_info in pages_data:
            file_id = page_info.get('file_id')
            page_number = page_info.get('page_number', 1)
            rotation = page_info.get('rotation', 0)
            
            if not file_id:
                raise Exception("Missing file_id in page data")
            
            # Construct file path
            filename = f"{file_id}.pdf"
            file_path = os.path.join(UPLOAD_DIR, filename)
            
            if not os.path.exists(file_path):
                raise Exception(f"PDF file not found for file_id: {file_id}")
            
            # Open PDF
            pdf_doc = fitz.open(file_path)
            total_pages = len(pdf_doc)
            
            # Validate page number
            if page_number < 1 or page_number > total_pages:
                pdf_doc.close()
                raise Exception(f"Invalid page number {page_number} for file {file_id} (total pages: {total_pages})")
            
            # Get the specific page (0-indexed)
            page_index = page_number - 1
            page = pdf_doc[page_index]
            
            # Apply rotation if specified
            if rotation != 0:
                # Create a new document with just this rotated page
                temp_doc = fitz.open()
                temp_doc.insert_pdf(pdf_doc, from_page=page_index, to_page=page_index)
                
                # Apply rotation to the page
                temp_doc[0].set_rotation(rotation)
                
                # Insert the rotated page into the merger
                merger.insert_pdf(temp_doc)
                temp_doc.close()
            else:
                # Insert the page without rotation
                merger.insert_pdf(pdf_doc, from_page=page_index, to_page=page_index)
            
            pdf_doc.close()
        
        # Get compression level from options
        compression_level = options.get('compression_level', 'none')
        
        # Save merged PDF with compression if specified
        if compression_level != 'none':
            if compression_level == 'low':
                merger.save(output_path, garbage=1, deflate=True)
            elif compression_level == 'medium':
                merger.save(output_path, garbage=2, deflate=True)
            elif compression_level == 'high':
                merger.save(output_path, garbage=3, deflate=True, clean=True)
            else:
                merger.save(output_path)
        else:
            merger.save(output_path)
        
        merger.close()
        
        return {
            'success': True,
            'message': f'Successfully merged {len(pages_data)} pages',
            'output_filename': output_filename,
            'download_url': f'/download/documents/{output_filename}',
            'merged_pages': len(pages_data),
            'compression_level': compression_level
        }
        
    except Exception as e:
        raise Exception(f"PDF merge failed: {str(e)}")