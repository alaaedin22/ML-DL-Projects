# step1_pdf_extraction.py
# PURPOSE: Extract text from digital (non-scanned) PDF files
# TOOL: pdfplumber
# PIPELINE: PDF file → pdfplumber.open() → page.extract_text() → raw string

import pdfplumber
# pdfplumber: library that reads PDF files and extracts their embedded text
# works ONLY on digital PDFs (not scanned images)
# install: pip install pdfplumber


def extract_text_from_pdf(pdf_path):
    """
    Extract all text from a digital PDF file.
    
    INPUT:  pdf_path (str) → path to the PDF file
                             example: "input/vanne_DN100_PN40.pdf"
    
    OUTPUT: full_text (str) → all text from all pages joined together
                              example: "DN100 PN40\nInox 316L\nDiametre: 100mm"
    """

    full_text = ""
    # initialize an empty string
    # this variable will grow as we add text from each page

    with pdfplumber.open(pdf_path) as pdf:
        # pdfplumber.open(pdf_path): open the PDF file
        # 'with' = context manager: automatically closes the file when done
        # 'as pdf': the opened PDF object is named 'pdf'
        # pdf.pages = list of all page objects inside the PDF

        for page_number, page in enumerate(pdf.pages):
            # enumerate(pdf.pages): loop through pages WITH their index number
            # page_number: 0, 1, 2, 3... (starts at 0)
            # page: the current page object

            text = page.extract_text()
            # page.extract_text(): reads all embedded text from this page
            # returns a string if text found
            # returns None if the page has no embedded text (scanned page)

            if text:
                # check: is text not None AND not empty string?
                # if the PDF page is a scanned image, text will be None
                # we skip those pages here (they go to Step 2 for OCR)

                full_text += f"--- PAGE {page_number + 1} ---\n"
                # add a page separator label
                # page_number + 1 because we want to show 1, 2, 3 (not 0, 1, 2)
                # f"..." = f-string: inserts variable value into the string

                full_text += text + "\n\n"
                # append the page text to our collection
                # "\n\n" = two newlines = blank line between pages

    return full_text
    # return the complete text string
    # if PDF was fully scanned, this will be an empty string ""


def is_text_sufficient(text, min_chars=50):
    """
    Check if extracted text is long enough to be useful.
    
    INPUT:  text (str)       → the extracted text string
            min_chars (int)  → minimum characters needed (default: 50)
    
    OUTPUT: bool → True if text is sufficient, False if too short
    """

    cleaned = text.strip()
    # strip(): remove whitespace and newlines from start and end
    # example: "  \n  hello  \n  " → "hello"

    return len(cleaned) >= min_chars
    # len(cleaned): count the number of characters
    # >= min_chars: check if it meets the minimum
    # returns True or False


# ============================================================
# HOW TO TEST THIS FILE ALONE:
# ============================================================
if __name__ == "__main__":
    # this block runs ONLY when you run this file directly:
    # command: python step1_pdf_extraction.py
    # does NOT run when this file is imported by another file

    import os
    # os: standard Python library for file/folder operations

    # --- TEST 1: file exists check ---
    test_pdf = "input/vanne_DN100_PN40.pdf"
    # path to the test PDF file

    if not os.path.exists(test_pdf):
        # os.path.exists(): returns True if file exists, False if not
        print(f"ERROR: File not found: {test_pdf}")
        print("Please put a PDF file at: input/vanne_DN100_PN40.pdf")
        exit()
        # exit(): stop the program immediately

    print("TEST 1: File exists ✓")

    # --- TEST 2: extract text ---
    print("\nTEST 2: Extracting text...")
    text = extract_text_from_pdf(test_pdf)
    # call our main function on the test PDF

    print(f"  Characters extracted: {len(text)}")
    # show how many characters were found

    print(f"  First 300 characters:\n{text[:300]}")
    # text[:300] = first 300 characters of the string (string slicing)

    # --- TEST 3: sufficiency check ---
    if is_text_sufficient(text):
        print("\nTEST 3: Text is sufficient ✓ (no OCR needed)")
    else:
        print("\nTEST 3: Text too short ✗ (OCR will be needed in Step 2)")
