# step2_ocr.py
# PURPOSE: Extract text from SCANNED PDF files using OCR
# TOOLS: PyMuPDF (renders PDF page → image) + pytesseract (reads text from image)
# PIPELINE: PDF → fitz.open() → page.get_pixmap() → PNG image → pytesseract.image_to_string() → text

import fitz
# fitz: this is PyMuPDF's import name
# PyMuPDF = Python bindings for the MuPDF rendering engine
# it can: open PDFs, render pages as images, extract text
# install: pip install pymupdf

import pytesseract
# pytesseract: Python wrapper around Google's Tesseract OCR engine
# OCR = Optical Character Recognition = reading text from images
# install: pip install pytesseract
# ALSO NEED: Tesseract installed as a system program (see installation above)

from PIL import Image
# PIL = Python Imaging Library (now called Pillow)
# Image: class for opening, saving, and processing image files
# install: pip install pillow

import io
# io: Python standard library for working with byte streams (data in memory)
# we use io.BytesIO to treat bytes as if they were a file

import os
# os: standard library for file and folder operations


def set_tesseract_path():
    """
    Set the path to the Tesseract executable.
    Only needed on Windows. Linux/Mac find it automatically.
    """

    if os.name == 'nt':
        # os.name == 'nt': checks if operating system is Windows
        # 'nt' = Windows NT (the Windows family)
        # 'posix' = Linux/Mac

        tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        # raw string (r'...'): backslashes are treated literally, not as escape chars
        # this is the default install path on Windows

        if os.path.exists(tesseract_path):
            # check if Tesseract is actually installed there
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            # tell pytesseract where the executable is
            print(f"Tesseract found at: {tesseract_path}")
        else:
            print("WARNING: Tesseract not found at default path.")
            print("Please install from: https://github.com/UB-Mannheim/tesseract/wiki")


def render_page_as_image(page, scale=2.0):
    """
    Render one PDF page as a PIL Image object.
    
    INPUT:  page (fitz.Page) → a single page from the PDF document
            scale (float)    → resolution multiplier (2.0 = 2x = 144 DPI)
                               higher = better OCR accuracy but slower
    
    OUTPUT: PIL Image object ready for pytesseract
    """

    mat = fitz.Matrix(scale, scale)
    # fitz.Matrix(x_scale, y_scale): creates a transformation matrix
    # scale=2.0: doubles the resolution in both X and Y directions
    # default PDF DPI is 72, so 2x = 144 DPI
    # 144 DPI is good for OCR; 300 DPI is better but slower

    pix = page.get_pixmap(matrix=mat)
    # page.get_pixmap(): renders the page as a pixel map (raster image)
    # matrix=mat: applies our 2x scaling for better resolution
    # pix: a fitz.Pixmap object containing raw pixel data

    img_bytes = pix.tobytes("png")
    # pix.tobytes("png"): convert pixmap to PNG format as bytes
    # returns: b'\x89PNG\r\n...' (raw PNG file data in memory)

    image = Image.open(io.BytesIO(img_bytes))
    # io.BytesIO(img_bytes): wrap the bytes in a file-like object
    # Image.open(...): open it as a PIL Image
    # now 'image' is a standard PIL Image that pytesseract can process

    return image
    # return the PIL Image object


def ocr_single_image(image, languages='fra+eng'):
    """
    Run OCR on a single PIL Image.
    
    INPUT:  image (PIL.Image) → the rendered page image
            languages (str)   → Tesseract language codes
                                'fra' = French, 'eng' = English
                                'fra+eng' = both (good for mixed docs)
    
    OUTPUT: text (str) → all text recognized in the image
    """

    custom_config = r'--oem 3 --psm 6'
    # Tesseract configuration string:
    # --oem 3: OCR Engine Mode 3 = use both Legacy and LSTM neural network engines
    #          (LSTM = Long Short-Term Memory, a type of neural network)
    # --psm 6: Page Segmentation Mode 6 = assume a single uniform block of text
    #          good for technical documents with dense text
    # other psm values:
    #   --psm 3 = fully automatic (default)
    #   --psm 6 = uniform text block (good for docs)
    #   --psm 11 = sparse text (good for drawings with scattered numbers)

    text = pytesseract.image_to_string(
        image,
        # the PIL Image to read
        lang=languages,
        # language model(s) to use for recognition
        config=custom_config
        # extra Tesseract settings
    )
    # image_to_string(): the main OCR function
    # sends the image to the Tesseract engine
    # Tesseract analyzes pixel patterns to recognize characters
    # returns: a string of all recognized text

    return text
    # return the OCR result string


def ocr_pdf_pages(pdf_path, scale=2.0, languages='fra+eng'):
    """
    OCR all pages of a PDF and return combined text.
    
    INPUT:  pdf_path (str)   → path to the PDF file
            scale (float)    → rendering resolution multiplier
            languages (str)  → Tesseract language codes
    
    OUTPUT: full_ocr_text (str) → all OCR text from all pages combined
    """

    set_tesseract_path()
    # set up Tesseract path (important on Windows)

    full_ocr_text = ""
    # empty string to collect results from all pages

    doc = fitz.open(pdf_path)
    # fitz.open(): open the PDF with PyMuPDF
    # doc: document object containing all pages

    total_pages = len(doc)
    # len(doc): number of pages in the document

    print(f"  OCR: Processing {total_pages} pages...")

    for page_num in range(total_pages):
        # range(total_pages): generates 0, 1, 2, ..., total_pages-1
        # we use this as the page index

        print(f"  OCR: Page {page_num + 1}/{total_pages}", end='\r')
        # end='\r': carriage return (overwrites same line each time)
        # shows progress without flooding the console

        page = doc[page_num]
        # doc[page_num]: access page at this index
        # returns a fitz.Page object

        image = render_page_as_image(page, scale)
        # render this page as a PIL Image at the specified resolution

        text = ocr_single_image(image, languages)
        # run OCR on the rendered image
        # text = string of all text Tesseract found on this page

        if text.strip():
            # check if OCR found any text (not just whitespace)
            full_ocr_text += f"\n--- PAGE {page_num + 1} (OCR) ---\n"
            full_ocr_text += text + "\n"
            # add page label and OCR text to our collection

    doc.close()
    # close the PDF document to free memory resources

    print(f"\n  OCR: Complete. {len(full_ocr_text)} characters extracted.")

    return full_ocr_text
    # return all OCR text from all pages


# ============================================================
# HOW TO TEST THIS FILE ALONE:
# ============================================================
if __name__ == "__main__":

    import os

    test_pdf = "input/vanne_DN100_PN40.pdf"

    if not os.path.exists(test_pdf):
        print(f"ERROR: File not found: {test_pdf}")
        exit()

    # --- TEST 1: render one page as image ---
    print("TEST 1: Rendering page 1 as image...")
    doc = fitz.open(test_pdf)
    # open the PDF

    page = doc[0]
    # get the first page (index 0)

    image = render_page_as_image(page, scale=2.0)
    # render it as a PIL Image

    image.save("output/page1_rendered.png")
    # save the rendered image to disk so you can visually inspect it

    doc.close()
    print("  Saved: output/page1_rendered.png")
    print("  → Open this file to verify the page renders correctly")

    # --- TEST 2: OCR the entire PDF ---
    print("\nTEST 2: Running OCR on entire PDF...")
    ocr_text = ocr_pdf_pages(test_pdf)
    # run OCR on all pages

    print(f"\n  First 400 characters of OCR result:")
    print(ocr_text[:400])
    # show first 400 characters

    # --- TEST 3: save OCR result ---
    with open("output/ocr_result.txt", 'w', encoding='utf-8') as f:
        f.write(ocr_text)
    print("\n  Saved full OCR result to: output/ocr_result.txt")
    print("  → Open this file to verify OCR accuracy")
