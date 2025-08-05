import os
import uuid
import tempfile
import json
import fitz  # PyMuPDF
from PIL import Image
import io

EXPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static', 'documents')
os.makedirs(EXPORT_DIR, exist_ok=True)

SUPPORTED_PDF_FORMATS = ['pdf']

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
        
        # Create output PDF
        output_filename = str(uuid.uuid4()) + '.pdf'
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
            'message': 'PDFs merged successfully',
            'output_filename': output_filename,
            'download_url': f'/download/documents/{output_filename}'
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

def rotate_pdf(file, input_body):
    """Rotate PDF pages"""
    # Save uploaded file to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_input:
        file.save(temp_input.name)
        input_path = temp_input.name

    try:
        # Validate input structure
        if 'tasks' not in input_body or 'rotate' not in input_body['tasks']:
            raise Exception("Invalid input structure: missing 'tasks' or 'rotate'")
        
        rotate_task = input_body['tasks']['rotate']
        options = rotate_task.get('options', {})
        
        # Get rotation parameters
        angle = options.get('angle', 90)  # 90, 180, 270
        page_range = options.get('page_range', 'all')  # 'all' or specific pages
        
        # Open PDF
        pdf_doc = fitz.open(input_path)
        
        # Apply rotation
        if page_range == 'all':
            for page_num in range(len(pdf_doc)):
                page = pdf_doc[page_num]
                page.set_rotation(angle)
        else:
            # Apply to specific pages
            for page_num in page_range:
                if 0 <= page_num < len(pdf_doc):
                    page = pdf_doc[page_num]
                    page.set_rotation(angle)
        
        # Save rotated PDF
        output_filename = str(uuid.uuid4()) + '.pdf'
        output_path = os.path.join(EXPORT_DIR, output_filename)
        pdf_doc.save(output_path)
        pdf_doc.close()
        
        return {
            'success': True,
            'message': 'PDF rotated successfully',
            'output_filename': output_filename,
            'download_url': f'/download/documents/{output_filename}'
        }
        
    except Exception as e:
        raise Exception(f"PDF rotate failed: {str(e)}")
    finally:
        # Clean up temporary file
        if 'input_path' in locals():
            try:
                os.unlink(input_path)
            except:
                pass

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