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

    # step3_llm.py
# PURPOSE: Send extracted text to Mistral LLM and get structured JSON specs
# TOOL: Ollama (local LLM server) running Mistral 7B model
# PIPELINE: raw text → HTTP POST to localhost:11434 → Mistral analyzes → JSON string → Python dict
# REQUIREMENT: Ollama must be running (ollama serve) and mistral must be pulled (ollama pull mistral)

import requests
# requests: library for making HTTP calls (like calling an API)
# install: pip install requests
# we use this to talk to Ollama's local API

import json
# json: Python standard library for JSON parsing
# json.loads(): converts JSON string → Python dict
# json.dumps(): converts Python dict → JSON string

import time
# time: standard library for time operations
# time.time(): returns current time in seconds (used to measure duration)

import re
# re: regular expressions library
# used to find and extract JSON from LLM response text


def check_ollama_running():
    """
    Check if Ollama server is running and accessible.
    
    OUTPUT: bool → True if Ollama is running, False if not
    """

    try:
        # try: attempt to execute code that might fail
        # if it fails, go to the except block instead of crashing

        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        # GET request to Ollama's tags endpoint
        # /api/tags: lists all downloaded models
        # timeout=5: give up after 5 seconds if no response

        return response.status_code == 200
        # status_code 200 = HTTP OK = server responded successfully
        # returns True if 200, False otherwise

    except requests.exceptions.ConnectionError:
        # ConnectionError: raised when the connection is refused
        # happens when Ollama is not running
        return False
        # return False: Ollama is not running

    except requests.exceptions.Timeout:
        # Timeout: raised when server doesn't respond within timeout period
        return False


def check_model_available(model_name="mistral"):
    """
    Check if the specified model is downloaded in Ollama.
    
    INPUT:  model_name (str) → name of the model to check
    OUTPUT: bool → True if model is available, False if not downloaded
    """

    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        # get list of all installed models from Ollama

        if response.status_code == 200:
            data = response.json()
            # parse the JSON response
            # data looks like: {"models": [{"name": "mistral:latest"}, ...]}

            models = data.get("models", [])
            # get the "models" list, default to empty list if not found

            model_names = [m["name"] for m in models]
            # list comprehension: extract just the "name" field from each model dict
            # m["name"] = "mistral:latest" (Ollama adds ":latest" tag)

            return any(model_name in name for name in model_names)
            # any(): returns True if ANY item in the iteration is True
            # check if model_name ("mistral") appears in any of the model names
            # "mistral" in "mistral:latest" → True

    except:
        # bare except: catches ANY exception
        # used here for a simple availability check
        return False

    return False


def build_engineering_prompt(raw_text):
    """
    Build a precise prompt for the LLM to extract engineering specs.
    
    INPUT:  raw_text (str) → extracted text from the PDF
    OUTPUT: prompt (str)   → the complete prompt to send to the LLM
    """

    prompt = f"""You are an expert mechanical engineer specializing in industrial valves and piping systems.

Analyze the following technical document and extract ALL engineering specifications you can find.

IMPORTANT RULES:
1. Return ONLY a valid JSON object, nothing else
2. No explanations, no markdown, no code blocks
3. Use null for any value not found in the text
4. All dimensions must be in millimeters (convert if needed)
5. All pressures must be in bar (convert if needed)

Required JSON structure:
{{
    "part_name": "full name of the part",
    "part_number": "part number or reference code or null",
    "diameter_mm": numeric value in mm or null,
    "outer_diameter_mm": numeric value in mm or null,
    "pressure_bar": numeric pressure value or null,
    "material": "material grade string or null",
    "length_mm": numeric length in mm or null,
    "wall_thickness_mm": numeric thickness in mm or null,
    "tolerance_mm": numeric tolerance value or null,
    "temperature_max_C": numeric max temperature or null,
    "temperature_min_C": numeric min temperature or null,
    "weight_kg": numeric weight or null,
    "standard": "applicable standard (e.g. EN558, ISO) or null",
    "connection_type": "connection type (e.g. flanged, threaded) or null",
    "valve_type": "type of valve (e.g. ball, gate, butterfly) or null"
}}

TECHNICAL DOCUMENT TEXT:
{raw_text}

JSON OUTPUT:"""
    # f-string: the {raw_text} and {{}} work differently:
    # {raw_text}: inserts the variable value
    # {{}} and }}: literal curly braces in f-strings need to be doubled
    # the triple-quoted f"""...""" allows multi-line string
    # "JSON OUTPUT:" at the end guides the LLM to start its response immediately

    return prompt


def extract_json_from_response(llm_response):
    """
    Extract valid JSON from the LLM's response text.
    Handles cases where LLM adds extra text around the JSON.
    
    INPUT:  llm_response (str) → raw text from the LLM
    OUTPUT: dict → parsed Python dictionary of specifications
    """

    text = llm_response.strip()
    # strip(): remove leading/trailing whitespace and newlines

    # Method 1: try to parse directly (ideal case - LLM returned only JSON)
    try:
        return json.loads(text)
        # json.loads(): parse JSON string → Python dict
        # if LLM returned clean JSON, this works immediately
    except json.JSONDecodeError:
        pass
        # pass: do nothing, continue to next method

    # Method 2: remove markdown code blocks
    # LLM sometimes wraps JSON in ```json ... ```
    if "```json" in text:
        # check if markdown JSON block exists
        text = text.split("```json")[1]
        # split by "```json": take everything AFTER it
        # [1] = second element (after the split point)
        text = text.split("```")[0]
        # split by "```": take everything BEFORE the closing backticks
        # [0] = first element
        try:
            return json.loads(text.strip())
            # try parsing the cleaned text
        except json.JSONDecodeError:
            pass

    # Method 3: use regex to find JSON object in the text
    json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    # regex pattern explanation:
    # \{ : literal opening curly brace
    # [^{}]* : any characters that are NOT { or } (zero or more)
    # (?:\{[^{}]*\}[^{}]*)* : allow one level of nested {} (non-capturing group)
    # \} : literal closing curly brace
    # this pattern matches JSON-like structures with optional one level of nesting

    matches = re.findall(json_pattern, text, re.DOTALL)
    # re.findall(): find ALL matches of the pattern in text
    # re.DOTALL: makes '.' match newlines too (important for multi-line JSON)
    # returns: list of matched strings

    for match in matches:
        # try each match found by regex
        try:
            return json.loads(match)
            # try to parse this match as JSON
            # if it works, return it immediately
        except json.JSONDecodeError:
            continue
            # continue: skip to next match

    raise ValueError(f"Could not extract valid JSON from LLM response:\n{llm_response[:500]}")
    # if ALL methods failed, raise an error
    # ValueError: appropriate error type for invalid value
    # show first 500 chars of the response for debugging


def query_llm(prompt, model="mistral", timeout=180):
    """
    Send a prompt to the Ollama LLM and get the response.
    
    INPUT:  prompt (str)  → the complete prompt string
            model (str)   → which model to use ("mistral" or "llama3")
            timeout (int) → max seconds to wait for response
    
    OUTPUT: str → the LLM's response text
    """

    payload = {
        "model": model,
        # which model to use: "mistral", "llama3", "llama2", etc.

        "prompt": prompt,
        # the full prompt text

        "stream": False,
        # stream=False: wait for COMPLETE response before returning
        # stream=True would give tokens one by one (like ChatGPT typing)

        "options": {
            "temperature": 0.1,
            # temperature: controls randomness of LLM output
            # 0.0 = completely deterministic (same input → same output always)
            # 1.0 = very random and creative
            # 0.1 = mostly deterministic with tiny variation
            # for data extraction, we want LOW temperature (consistent results)

            "num_predict": 1000
            # num_predict: maximum number of tokens to generate
            # 1 token ≈ 0.75 words
            # 1000 tokens is enough for our JSON response
        }
    }

    start_time = time.time()
    # record when we started the request

    response = requests.post(
        "http://localhost:11434/api/generate",
        # Ollama's generate endpoint
        # localhost:11434 = the local Ollama server address

        json=payload,
        # json=: automatically serializes the dict to JSON and sets Content-Type header

        timeout=timeout
        # max wait time in seconds
    )

    end_time = time.time()
    duration = end_time - start_time
    # calculate how long the LLM took to respond

    print(f"  LLM response received in {duration:.1f} seconds")
    # {duration:.1f}: format float to 1 decimal place
    # example: "  LLM response received in 23.4 seconds"

    if response.status_code != 200:
        # check if HTTP request succeeded
        raise RuntimeError(f"Ollama API error: status {response.status_code}, body: {response.text}")
        # RuntimeError: error for runtime failures

    result = response.json()
    # parse the HTTP response body as JSON
    # Ollama returns: {"response": "...", "done": true, "total_duration": ...}

    return result["response"]
    # extract just the LLM's text response
    # this is what Mistral generated in response to our prompt


def extract_specs_with_llm(raw_text, model="mistral"):
    """
    Main function: send PDF text to LLM, get structured specs dict.
    
    INPUT:  raw_text (str) → text extracted from PDF
            model (str)    → LLM model to use
    
    OUTPUT: dict → engineering specifications
    """

    # --- pre-flight checks ---
    if not check_ollama_running():
        raise RuntimeError(
            "Ollama is not running!\n"
            "Start it with: ollama serve\n"
            "Or download from: https://ollama.ai"
        )
    # raise an error with clear instructions if Ollama isn't running

    if not check_model_available(model):
        raise RuntimeError(
            f"Model '{model}' not found in Ollama!\n"
            f"Download it with: ollama pull {model}"
        )
    # raise an error if the model isn't downloaded

    # --- build and send prompt ---
    print(f"  Building prompt for {model}...")
    prompt = build_engineering_prompt(raw_text)
    # create the full prompt string

    print(f"  Prompt length: {len(prompt)} characters")
    print(f"  Sending to {model} via Ollama...")

    llm_response = query_llm(prompt, model=model)
    # send to Ollama, get back the LLM's text

    # --- parse response ---
    print("  Parsing LLM response...")
    specs = extract_json_from_response(llm_response)
    # extract and parse the JSON from the response

    print(f"  Successfully extracted {len(specs)} specification fields")
    # len(specs) = number of keys in the dictionary

    return specs
    # return the final Python dictionary


# ============================================================
# HOW TO TEST THIS FILE ALONE:
# ============================================================
if __name__ == "__main__":

    # --- TEST 1: check if Ollama is running ---
    print("TEST 1: Checking Ollama...")
    if check_ollama_running():
        print("  Ollama is running ✓")
    else:
        print("  Ollama is NOT running ✗")
        print("  Run: ollama serve")
        exit()

    # --- TEST 2: check if mistral is available ---
    print("\nTEST 2: Checking Mistral model...")
    if check_model_available("mistral"):
        print("  Mistral is available ✓")
    else:
        print("  Mistral NOT found ✗")
        print("  Run: ollama pull mistral")
        exit()

    # --- TEST 3: test with sample engineering text ---
    print("\nTEST 3: Testing LLM extraction with sample text...")

    sample_text = """
    VANNE A BILLE DN100 PN40
    Référence: VB-100-40-316L
    
    SPECIFICATIONS TECHNIQUES:
    - Diamètre nominal: DN100 (100mm)
    - Pression nominale: PN40 (40 bar)
    - Matériau corps: Inox 316L
    - Longueur face-à-face: 229 mm (selon EN558)
    - Epaisseur de paroi: 8 mm
    - Tolérance dimensionnelle: ±0.5 mm
    - Température maximale: 200°C
    - Température minimale: -20°C
    - Poids: 12.5 kg
    - Connexion: Brides PN40
    - Norme applicable: EN558 / ISO 5211
    """
    # sample text that simulates what would be extracted from a real PDF
    # this is a French technical spec sheet for a DN100 ball valve

    specs = extract_specs_with_llm(sample_text)
    # run the extraction

    print("\n  Extracted specifications:")
    for key, value in specs.items():
        # loop through all key-value pairs
        print(f"    {key:30s}: {value}")
        # {key:30s}: format string with minimum 30 character width
        # this right-aligns the values for clean display

    # --- TEST 4: verify key fields ---
    print("\nTEST 4: Verifying key fields...")
    assert specs.get("diameter_mm") == 100, f"Expected 100, got {specs.get('diameter_mm')}"
    # assert: raises AssertionError if condition is False
    # used for automated testing: verify expected values

    assert specs.get("pressure_bar") == 40, f"Expected 40, got {specs.get('pressure_bar')}"
    assert specs.get("material") is not None, "Material should not be None"

    print("  All key fields verified ✓")

    # step4_json.py
# PURPOSE: Save extracted specs to JSON file and load them back
# TOOL: Python standard json library
# PIPELINE: Python dict → json.dump() → .json file  |  .json file → json.load() → Python dict

import json
# json: Python's built-in JSON library
# no installation needed, comes with Python

import os
# os: standard library for file and folder operations

from datetime import datetime
# datetime: standard library for date and time operations
# used to add a timestamp to our saved JSON


def save_specs_to_json(specs, output_path):
    """
    Save the specs dictionary to a JSON file.
    Adds metadata (timestamp, source info) before saving.
    
    INPUT:  specs (dict)       → engineering specifications dictionary
            output_path (str)  → file path where to save (e.g., "output/specs.json")
    
    OUTPUT: str → the output_path (for chaining/confirmation)
    """

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    # os.makedirs(): create directories (folders) if they don't exist
    # os.path.dirname(output_path): get the folder part of the path
    #   example: "output/specs.json" → "output"
    # exist_ok=True: don't raise error if folder already exists

    enriched_specs = {
        "metadata": {
            # metadata = information ABOUT the data (not the specs themselves)
            "extraction_timestamp": datetime.now().isoformat(),
            # datetime.now(): current date and time
            # .isoformat(): format as ISO 8601 string: "2024-01-15T14:30:00.000000"

            "project": "OpenIndustry Algeria",
            # project identifier

            "pipeline_version": "1.0",
            # version tag for tracking

            "output_file": output_path
            # record what file this data will be saved to
        },
        "specifications": specs
        # the actual engineering specs under "specifications" key
    }
    # wrapping specs in a larger dict adds useful context information

    with open(output_path, 'w', encoding='utf-8') as f:
        # open(): open file for writing
        # 'w': write mode (creates file if not exists, OVERWRITES if exists)
        # encoding='utf-8': support French characters (é, à, °)

        json.dump(enriched_specs, f, indent=4, ensure_ascii=False)
        # json.dump(): serialize Python dict to JSON and write to file
        # enriched_specs: the dict to serialize
        # f: the file object to write to
        # indent=4: use 4-space indentation for human-readable formatting
        # ensure_ascii=False: write Unicode chars as-is (not as \u00e9 etc.)
        #   without this: "Diamètre" becomes "Diam\u00e8tre"
        #   with this:    "Diamètre" stays "Diamètre"

    file_size = os.path.getsize(output_path)
    # os.path.getsize(): get file size in bytes

    print(f"  JSON saved: {output_path} ({file_size} bytes)")

    return output_path
    # return the path so caller knows where it was saved


def load_specs_from_json(json_path):
    """
    Load specs from a JSON file back into a Python dictionary.
    
    INPUT:  json_path (str) → path to the JSON file
    OUTPUT: dict → the specifications dictionary
    """

    if not os.path.exists(json_path):
        # check if the file actually exists before trying to open it
        raise FileNotFoundError(f"JSON file not found: {json_path}")
        # FileNotFoundError: built-in Python error for missing files

    with open(json_path, 'r', encoding='utf-8') as f:
        # open for reading ('r' mode)

        data = json.load(f)
        # json.load(): read JSON from file → Python dict
        # (opposite of json.dump())

    if "specifications" in data:
        # check if we saved with metadata wrapper (our format)
        return data["specifications"]
        # return just the specs part, not the metadata wrapper

    return data
    # if no wrapper, return the whole dict (backward compatibility)


def print_specs_table(specs):
    """
    Print the specs in a nicely formatted table.
    
    INPUT:  specs (dict) → engineering specifications
    """

    print("\n" + "=" * 50)
    print("  EXTRACTED ENGINEERING SPECIFICATIONS")
    print("=" * 50)

    for key, value in specs.items():
        # loop through all key-value pairs in the dict

        if value is not None:
            # only print fields that have a value (not null/None)

            print(f"  {key:<30} {value}")
            # f-string formatting:
            # {key:<30}: left-align key in 30-character wide field
            # {value}: print the value right after
            # example: "  diameter_mm                  100"

    print("=" * 50)


# ============================================================
# HOW TO TEST THIS FILE ALONE:
# ============================================================
if __name__ == "__main__":

    # --- TEST 1: save a sample spec dict ---
    print("TEST 1: Saving specs to JSON...")

    sample_specs = {
        "part_name": "Vanne à bille DN100 PN40",
        "part_number": "VB-100-40-316L",
        "diameter_mm": 100,
        "outer_diameter_mm": 116,
        "pressure_bar": 40,
        "material": "Inox_316L",
        "length_mm": 229,
        "wall_thickness_mm": 8,
        "tolerance_mm": 0.5,
        "temperature_max_C": 200,
        "temperature_min_C": -20,
        "weight_kg": 12.5,
        "standard": "EN558",
        "connection_type": "flanged",
        "valve_type": "ball"
    }
    # a complete sample specs dictionary

    output_path = save_specs_to_json(sample_specs, "output/test_specs.json")
    print(f"  Saved to: {output_path} ✓")

    # --- TEST 2: load it back and verify ---
    print("\nTEST 2: Loading specs back from JSON...")
    loaded_specs = load_specs_from_json("output/test_specs.json")
    # load the file we just saved

    assert loaded_specs["diameter_mm"] == 100, "diameter_mm mismatch!"
    assert loaded_specs["material"] == "Inox_316L", "material mismatch!"
    print("  Loaded and verified ✓")

    # --- TEST 3: display table ---
    print("\nTEST 3: Display table:")
    print_specs_table(loaded_specs)

    # --- TEST 4: open the file manually ---
    print("\nTEST 4: Manual verification")
    print("  → Open output/test_specs.json in any text editor")
    print("  → Verify the JSON structure looks correct")
    # step5_dxf.py
# PURPOSE: Generate a 2D engineering DXF drawing from JSON specs
# TOOL: ezdxf
# PIPELINE: specs dict → ezdxf creates document → add geometry (circles, lines, text) → save .dxf

import ezdxf
# ezdxf: Python library to create and read DXF CAD files
# DXF = Drawing Exchange Format (Autodesk standard, readable everywhere)
# install: pip install ezdxf

from ezdxf import units
# units: module inside ezdxf for setting measurement units

from ezdxf.enums import TextEntityAlignment
# TextEntityAlignment: enum for text alignment options (LEFT, CENTER, RIGHT, etc.)

import json
# for reading specs from JSON file

import os
# for file/folder operations


def setup_dxf_document():
    """
    Create and configure a new DXF document with proper settings and layers.
    
    OUTPUT: tuple (doc, msp)
            doc → the DXF document object
            msp → the modelspace (drawing canvas)
    """

    doc = ezdxf.new(dxfversion='R2010')
    # ezdxf.new(): create a new empty DXF document in memory
    # dxfversion='R2010': use AutoCAD 2010 DXF format
    # other options: 'R12', 'R2000', 'R2004', 'R2007', 'R2010', 'R2013', 'R2018'
    # R2010 is a good balance: widely compatible, supports modern features

    doc.units = units.MM
    # set the document's measurement unit to millimeters
    # units.MM: the enum value for millimeters
    # all coordinates we enter will be treated as millimeters

    msp = doc.modelspace()
    # modelspace(): get the modelspace object
    # modelspace = the main drawing area in DXF
    # this is where all geometry (lines, circles, text) is placed
    # think of it as the infinite drawing canvas

    doc.linetypes.load_ltypefile("acadiso.lin")
    # try to load standard linetype definitions
    # "acadiso.lin" = the ISO linetype file with CENTER, DASHED, HIDDEN types
    # if this fails, we handle it gracefully

    # --- define layers ---
    # layers organize drawing elements like folders
    # each layer has a color and can be turned on/off in CAD software

    layers_config = [
        # list of (name, color_number) tuples
        ("GEOMETRY", 7),
        # 7 = white (appears black on white background)
        # GEOMETRY: main outlines of the part

        ("CENTERLINE", 1),
        # 1 = red
        # CENTERLINE: symmetry axes

        ("HIDDEN", 8),
        # 8 = dark gray
        # HIDDEN: lines hidden behind other geometry

        ("DIMENSIONS", 3),
        # 3 = green
        # DIMENSIONS: dimension annotations with arrows

        ("TEXT", 2),
        # 2 = yellow
        # TEXT: labels and title block text

        ("TITLE_BLOCK", 4),
        # 4 = cyan
        # TITLE_BLOCK: the information frame at drawing bottom

        ("HATCHING", 9),
        # 9 = light blue
        # HATCHING: cross-hatch patterns for material cross-sections
    ]

    for layer_name, color in layers_config:
        # loop through each (name, color) pair

        doc.layers.add(layer_name, dxfattribs={"color": color})
        # doc.layers.add(): create a new layer in the document
        # layer_name: the name string
        # dxfattribs={"color": color}: set the layer's color

    return doc, msp
    # return both the document and modelspace objects


def draw_front_view(msp, cx, cy, bore_radius, wall_thickness):
    """
    Draw the front view of the valve (circular cross-section view).
    Shows: bore circle, outer body circle, flange bolt holes (optional).
    
    INPUT:  msp (Modelspace) → the drawing canvas
            cx, cy (float)   → center X and Y coordinates
            bore_radius (float) → inner bore radius in mm
            wall_thickness (float) → pipe wall thickness in mm
    """

    outer_radius = bore_radius + wall_thickness
    # outer radius = bore (inner) radius + wall thickness
    # example: bore=50, wall=8 → outer=58mm

    # --- draw bore circle (inner) ---
    msp.add_circle(
        center=(cx, cy),
        # center point as (x, y) tuple
        # our valve is centered at (cx, cy) = (0, 0)

        radius=bore_radius,
        # bore_radius = 50mm for DN100

        dxfattribs={
            "layer": "GEOMETRY",
            # put this circle on the GEOMETRY layer
            "lineweight": 50
            # lineweight: line thickness in hundredths of mm
            # 50 = 0.50mm line width (standard for visible edges)
        }
    )

    # --- draw outer body circle ---
    msp.add_circle(
        center=(cx, cy),
        radius=outer_radius,
        # outer_radius = 58mm (bore + wall)

        dxfattribs={
            "layer": "GEOMETRY",
            "lineweight": 50
        }
    )

    # --- draw centerlines through center ---
    extend = outer_radius + 15
    # how far the centerline extends beyond the circle
    # +15mm past the outer circle edge

    # horizontal centerline (X-axis)
    msp.add_line(
        start=(-extend + cx, cy),
        # start point: extend mm to the LEFT of center
        end=(extend + cx, cy),
        # end point: extend mm to the RIGHT of center
        dxfattribs={
            "layer": "CENTERLINE",
            "linetype": "CENTER",
            # CENTER linetype = dash-dot-dash pattern
            "lineweight": 13
            # 13 = 0.13mm = thin line (standard for centerlines)
        }
    )

    # vertical centerline (Y-axis)
    msp.add_line(
        start=(cx, -extend + cy),
        # extend mm BELOW center
        end=(cx, extend + cy),
        # extend mm ABOVE center
        dxfattribs={
            "layer": "CENTERLINE",
            "linetype": "CENTER",
            "lineweight": 13
        }
    )

    return outer_radius
    # return outer_radius so other functions can use it


def draw_side_view(msp, cx, cy, outer_radius, bore_radius, length, x_offset):
    """
    Draw the side view of the valve (rectangular profile view).
    Shows: outer body, bore (hidden lines), flanges, centerline.
    
    INPUT:  msp           → drawing canvas
            cx, cy        → reference center coordinates
            outer_radius  → outer body radius in mm
            bore_radius   → bore radius in mm
            length        → face-to-face length in mm
            x_offset      → horizontal offset for side view from front view
    """

    # calculate rectangle corners
    x_left = cx + x_offset - length / 2
    # left edge: offset from center minus half the length
    # x_offset = horizontal displacement from front view center
    # length/2: half the face-to-face length

    x_right = cx + x_offset + length / 2
    # right edge: offset from center plus half the length

    y_top = cy + outer_radius
    # top edge: center Y plus outer radius

    y_bottom = cy - outer_radius
    # bottom edge: center Y minus outer radius

    # --- draw outer body rectangle ---
    msp.add_lwpolyline(
        # add_lwpolyline(): draw a lightweight polyline (connected line segments)
        # LW = LightWeight: more efficient storage than regular polyline

        [(x_left, y_bottom),
         (x_right, y_bottom),
         (x_right, y_top),
         (x_left, y_top)],
        # list of corner points:
        # bottom-left → bottom-right → top-right → top-left

        close=True,
        # close=True: connect last point back to first (closes the rectangle)
        # without this: only 3 sides drawn (open shape)

        dxfattribs={
            "layer": "GEOMETRY",
            "lineweight": 50
        }
    )

    # --- draw bore as hidden lines (dashed) ---
    # bore appears as horizontal dashed lines in side view
    msp.add_line(
        start=(x_left, cy + bore_radius),
        # top of bore at left face
        end=(x_right, cy + bore_radius),
        # top of bore at right face
        dxfattribs={
            "layer": "HIDDEN",
            "linetype": "DASHED",
            # DASHED linetype = dashed line pattern
            "lineweight": 25
            # 25 = 0.25mm = medium line
        }
    )

    msp.add_line(
        start=(x_left, cy - bore_radius),
        # bottom of bore
        end=(x_right, cy - bore_radius),
        dxfattribs={
            "layer": "HIDDEN",
            "linetype": "DASHED",
            "lineweight": 25
        }
    )

    # --- draw horizontal centerline through side view ---
    msp.add_line(
        start=(x_left - 10, cy),
        # extend 10mm past the left face
        end=(x_right + 10, cy),
        # extend 10mm past the right face
        dxfattribs={
            "layer": "CENTERLINE",
            "linetype": "CENTER",
            "lineweight": 13
        }
    )

    # --- add flange end indicators ---
    # flanges are the flat connection faces at each end
    flange_thickness = 20
    # flange thickness in mm (approximate for PN40)

    # left flange
    msp.add_lwpolyline(
        [(x_left - flange_thickness, y_bottom - 10),
         (x_left, y_bottom - 10),
         (x_left, y_top + 10),
         (x_left - flange_thickness, y_top + 10)],
        # flange extends 10mm beyond the body height on each side

        close=True,
        dxfattribs={"layer": "GEOMETRY", "lineweight": 35}
    )

    # right flange
    msp.add_lwpolyline(
        [(x_right, y_bottom - 10),
         (x_right + flange_thickness, y_bottom - 10),
         (x_right + flange_thickness, y_top + 10),
         (x_right, y_top + 10)],
        close=True,
        dxfattribs={"layer": "GEOMETRY", "lineweight": 35}
    )

    return x_left, x_right, y_top, y_bottom
    # return the rectangle bounds for use by dimension functions


def add_dimensions(msp, cx, cy, bore_radius, outer_radius, 
                   length, x_offset, x_left, x_right, y_top, y_bottom,
                   tolerance):
    """
    Add dimension annotations to the drawing.
    Shows: diameter, length, with tolerance values.
    
    DIMENSIONS in engineering drawings = annotations with:
    - extension lines (go to the edge of the feature)
    - dimension line (between extension lines with arrows)
    - dimension text (the actual measurement value)
    """

    dim_offset = 20
    # how far dimension lines are placed from the part edge (mm)

    # --- diameter dimension (front view) ---
    msp.add_text(
        f"∅{int(bore_radius * 2)} ±{tolerance}",
        # "∅100 ±0.5" for DN100 with 0.5mm tolerance
        # ∅ = diameter symbol (Unicode character U+2205)
        # int(): convert to integer (no decimal for mm display)
        # bore_radius * 2 = diameter = 100mm

        dxfattribs={
            "insert": (cx + bore_radius + 15, cy + bore_radius + 10),
            # position: outside the bore circle, offset right and up
            "height": 5,
            # text height in mm
            "layer": "DIMENSIONS",
            "color": 3
            # color 3 = green for dimension text
        }
    )

    # --- leader line for diameter (diagonal line pointing to circle) ---
    msp.add_line(
        start=(cx + bore_radius * 0.707, cy + bore_radius * 0.707),
        # start at 45° on the bore circle
        # cos(45°) = sin(45°) = 0.707
        # at 45° angle: x = r*cos(45°), y = r*sin(45°)

        end=(cx + bore_radius + 13, cy + bore_radius + 8),
        # end near the dimension text

        dxfattribs={"layer": "DIMENSIONS", "lineweight": 13}
    )

    # --- length dimension (side view) ---
    dim_y = y_bottom - dim_offset
    # Y position of the length dimension line (below the part)

    # left extension line
    msp.add_line(
        start=(x_left, y_bottom),
        # from bottom-left corner of the rectangle
        end=(x_left, dim_y - 5),
        # down to just below the dimension line
        dxfattribs={"layer": "DIMENSIONS", "lineweight": 13}
    )

    # right extension line
    msp.add_line(
        start=(x_right, y_bottom),
        end=(x_right, dim_y - 5),
        dxfattribs={"layer": "DIMENSIONS", "lineweight": 13}
    )

    # main dimension line (horizontal)
    msp.add_line(
        start=(x_left, dim_y),
        end=(x_right, dim_y),
        dxfattribs={"layer": "DIMENSIONS", "lineweight": 13}
    )

    # dimension text (length value)
    mid_x = (x_left + x_right) / 2
    # mid_x = midpoint between left and right = center of dimension line

    msp.add_text(
        f"L = {int(length)} mm",
        # "L = 229 mm" for DN100 PN40

        dxfattribs={
            "insert": (mid_x, dim_y - 8),
            # centered below the dimension line
            "height": 4,
            # slightly smaller text for dimensions
            "layer": "DIMENSIONS",
            "halign": 4
            # halign 4 = center alignment
        }
    )

    # --- height dimension (side view) ---
    dim_x_right = x_right + 30
    # X position of height dimension (to the right of side view)

    # bottom extension line
    msp.add_line(
        start=(x_right, y_bottom),
        end=(dim_x_right + 5, y_bottom),
        dxfattribs={"layer": "DIMENSIONS", "lineweight": 13}
    )

    # top extension line
    msp.add_line(
        start=(x_right, y_top),
        end=(dim_x_right + 5, y_top),
        dxfattribs={"layer": "DIMENSIONS", "lineweight": 13}
    )

    # vertical dimension line
    msp.add_line(
        start=(dim_x_right, y_bottom),
        end=(dim_x_right, y_top),
        dxfattribs={"layer": "DIMENSIONS", "lineweight": 13}
    )

    # height dimension text
    mid_y = (y_top + y_bottom) / 2
    msp.add_text(
        f"∅{int(outer_radius * 2)}",
        # outer diameter = "∅116" for DN100 with 8mm wall

        dxfattribs={
            "insert": (dim_x_right + 5, mid_y),
            "height": 4,
            "layer": "DIMENSIONS"
        }
    )


def add_title_block(msp, specs, drawing_width):
    """
    Add a title block at the bottom of the drawing.
    Title block = the bordered information box standard on all engineering drawings.
    Contains: part name, material, scale, date, project name, tolerances.
    
    INPUT:  msp (Modelspace)  → drawing canvas
            specs (dict)      → engineering specifications
            drawing_width     → total width of the drawing for positioning
    """

    tb_x = -drawing_width / 2
    # left edge of title block: half the drawing width to the left of center

    tb_y = -150
    # Y position: 150mm below the drawing center

    tb_width = drawing_width
    # title block same width as the drawing

    tb_height = 60
    # title block height: 60mm

    # --- outer border ---
    msp.add_lwpolyline(
        [(tb_x, tb_y - tb_height),
         (tb_x + tb_width, tb_y - tb_height),
         (tb_x + tb_width, tb_y),
         (tb_x, tb_y)],
        close=True,
        dxfattribs={"layer": "TITLE_BLOCK", "lineweight": 70}
        # lineweight 70 = 0.70mm = thick border line
    )

    # --- internal dividing lines ---
    # horizontal line dividing title block into rows
    msp.add_line(
        start=(tb_x, tb_y - 20),
        end=(tb_x + tb_width, tb_y - 20),
        dxfattribs={"layer": "TITLE_BLOCK", "lineweight": 25}
    )
    msp.add_line(
        start=(tb_x, tb_y - 40),
        end=(tb_x + tb_width, tb_y - 40),
        dxfattribs={"layer": "TITLE_BLOCK", "lineweight": 25}
    )

    # vertical divider at midpoint
    msp.add_line(
        start=(tb_x + tb_width / 2, tb_y - 40),
        end=(tb_x + tb_width / 2, tb_y),
        dxfattribs={"layer": "TITLE_BLOCK", "lineweight": 25}
    )

    # --- title block text content ---
    part_name = specs.get("part_name", "UNKNOWN PART")
    material = specs.get("material", "N/A")
    pressure = specs.get("pressure_bar", "N/A")
    diameter = specs.get("diameter_mm", "N/A")
    standard = specs.get("standard", "N/A")
    tolerance = specs.get("tolerance_mm", "N/A")

    from datetime import datetime
    date_str = datetime.now().strftime("%Y-%m-%d")
    # strftime(): format datetime as string
    # "%Y-%m-%d" = "2024-01-15" format

    # row 1: part name (large text)
    msp.add_text(
        part_name,
        dxfattribs={
            "insert": (tb_x + 5, tb_y - 12),
            # 5mm from left edge, 12mm from top of title block
            "height": 8,
            # 8mm = large title text
            "layer": "TEXT"
        }
    )

    # row 2 left: material
    msp.add_text(
        f"MATERIAL: {material}",
        dxfattribs={
            "insert": (tb_x + 5, tb_y - 32),
            "height": 5,
            "layer": "TEXT"
        }
    )

    # row 2 right: pressure rating
    msp.add_text(
        f"PRESSURE: PN{pressure} bar",
        dxfattribs={
            "insert": (tb_x + tb_width / 2 + 5, tb_y - 32),
            "height": 5,
            "layer": "TEXT"
        }
    )

    # row 3: project, standard, tolerance, date
    msp.add_text(
        f"PROJECT: OpenIndustry Algeria",
        dxfattribs={
            "insert": (tb_x + 5, tb_y - 52),
            "height": 4,
            "layer": "TEXT"
        }
    )

    msp.add_text(
        f"STD: {standard}  |  TOL: ±{tolerance}mm  |  DATE: {date_str}",
        dxfattribs={
            "insert": (tb_x + tb_width * 0.35, tb_y - 52),
            "height": 4,
            "layer": "TEXT"
        }
    )


def generate_dxf_from_specs(specs, output_dxf_path):
    """
    MAIN FUNCTION: Generate complete 2D DXF engineering drawing from specs.
    
    INPUT:  specs (dict)         → engineering specifications
            output_dxf_path (str) → where to save the DXF file
    
    OUTPUT: str → the output_dxf_path (confirmation)
    """

    os.makedirs(os.path.dirname(output_dxf_path), exist_ok=True)
    # create output directory if it doesn't exist

    # --- extract specs with safe defaults ---
    diameter = float(specs.get("diameter_mm", 100))
    # float(): convert to floating-point number
    # safe default: 100mm if not specified

    bore_radius = diameter / 2
    # bore radius = half the diameter

    wall = float(specs.get("wall_thickness_mm", 8))
    # wall thickness with default of 8mm

    length = float(specs.get("length_mm", 229))
    # face-to-face length

    tolerance = specs.get("tolerance_mm", 0.5)
    # dimensional tolerance

    # --- setup document ---
    doc, msp = setup_dxf_document()
    # create DXF document with layers configured

    # --- define view positions ---
    front_cx, front_cy = 0, 0
    # front view centered at origin

    outer_radius = bore_radius + wall
    # outer radius of valve body

    side_view_offset = diameter * 3
    # place side view 3 diameters to the right of front view
    # for DN100: 100 * 3 = 300mm to the right
    # ensures views don't overlap and have space for dimensions

    # --- draw front view ---
    print("  Drawing front view...")
    outer_r = draw_front_view(msp, front_cx, front_cy, bore_radius, wall)
    # draw the circular cross-section view

    # --- draw side view ---
    print("  Drawing side view...")
    x_left, x_right, y_top, y_bottom = draw_side_view(
        msp, front_cx, front_cy,
        outer_radius, bore_radius, length,
        side_view_offset
        # pass all needed parameters
    )

    # --- add dimensions ---
    print("  Adding dimension annotations...")
    add_dimensions(
        msp, front_cx, front_cy,
        bore_radius, outer_radius,
        length, side_view_offset,
        x_left, x_right, y_top, y_bottom,
        tolerance
    )

    # --- add part labels ---
    part_name = specs.get("part_name", "VALVE")
    material = specs.get("material", "N/A")
    pressure = specs.get("pressure_bar", "N/A")

    # front view label
    msp.add_text(
        "FRONT VIEW",
        dxfattribs={
            "insert": (front_cx - 20, -(outer_radius + 20)),
            # below the front view circle
            "height": 4,
            "layer": "TEXT"
        }
    )

    # side view label
    msp.add_text(
        "SIDE VIEW",
        dxfattribs={
            "insert": (front_cx + side_view_offset - 20, -(outer_radius + 20)),
            # below the side view rectangle
            "height": 4,
            "layer": "TEXT"
        }
    )

    # material callout annotation
    msp.add_text(
        f"MAT: {material}",
        dxfattribs={
            "insert": (front_cx - outer_radius - 30, front_cy + 10),
            # to the left of the front view
            "height": 4,
            "layer": "TEXT"
        }
    )

    # --- add title block ---
    print("  Adding title block...")
    drawing_total_width = side_view_offset + length / 2 + 60
    # total width = from left edge to right edge of all views + margins

    add_title_block(msp, specs, drawing_total_width)

    # --- save the file ---
    doc.saveas(output_dxf_path)
    # write all geometry to the DXF file
    # saveas(): saves to the specified path

    file_size = os.path.getsize(output_dxf_path)
    print(f"  DXF saved: {output_dxf_path} ({file_size:,} bytes)")
    # {:,}: format number with thousands separator (e.g., 45,231)

    return output_dxf_path


# ============================================================
# HOW TO TEST THIS FILE ALONE:
# ============================================================
if __name__ == "__main__":

    os.makedirs("output", exist_ok=True)
    # make sure output folder exists

    sample_specs = {
        "part_name": "Vanne à bille DN100 PN40",
        "part_number": "VB-100-40-316L",
        "diameter_mm": 100,
        "pressure_bar": 40,
        "material": "Inox_316L",
        "length_mm": 229,
        "wall_thickness_mm": 8,
        "tolerance_mm": 0.5,
        "temperature_max_C": 200,
        "standard": "EN558"
    }

    # TEST 1: generate DXF
    print("TEST 1: Generating DXF...")
    dxf_path = generate_dxf_from_specs(sample_specs, "output/test_valve.dxf")
    print(f"  Generated: {dxf_path} ✓")

    # TEST 2: verify file is valid DXF
    print("\nTEST 2: Verifying DXF file...")
    doc = ezdxf.readfile(dxf_path)
    # ezdxf.readfile(): open and parse an existing DXF file
    # if it doesn't raise an error, the file is valid

    msp = doc.modelspace()
    entity_count = len(list(msp))
    # list(msp): get all entities in modelspace as a list
    # len(): count them

    print(f"  File is valid DXF ✓")
    print(f"  Contains {entity_count} drawing entities")

    print("\n  TO VIEW THE DXF FILE:")
    print("  Option 1 (free): Download LibreCAD from https://librecad.org")
    print("  Option 2 (free): Upload to https://sharecad.org/")
    print("  Option 3 (free): Open in FreeCAD from https://www.freecadweb.org/")
    print(f"\n  File location: {os.path.abspath(dxf_path)}")
    # step6_ifc.py
# PURPOSE: Generate an IFC 3D model file with embedded metadata
# TOOL: ifcopenshell
# PIPELINE: specs dict → ifcopenshell creates IFC structure → add 3D geometry + properties → save .ifc

import ifcopenshell
# ifcopenshell: Python library for creating and reading IFC files
# IFC = Industry Foundation Classes
# open standard for sharing building/engineering models with embedded metadata
# install: pip install ifcopenshell

import ifcopenshell.api
# ifcopenshell.api: high-level API module with convenience functions
# makes creating IFC entities much simpler than using the raw API

import ifcopenshell.util.element
# utility functions for working with IFC elements

import os
import json
from datetime import datetime


def create_ifc_project_structure(ifc_file, project_name):
    """
    Create the mandatory IFC hierarchy: Project → Site → Building → Storey.
    Every IFC file needs this structure as a container for elements.
    
    INPUT:  ifc_file (IfcFile) → the IFC file object
            project_name (str) → name for the project
    
    OUTPUT: tuple (project, site, building, storey) → the created hierarchy objects
    """

    project = ifcopenshell.api.run(
        "root.create_entity",
        # command: create a new IFC entity
        ifc_file,
        # which IFC file to add it to

        ifc_class="IfcProject",
        # entity type: IfcProject = top-level container for everything
        # every IFC file has exactly ONE IfcProject

        name=project_name
        # the project's name attribute
    )

    ifcopenshell.api.run(
        "unit.assign_unit",
        # command: assign measurement units to the project
        ifc_file,

        length={"is_metric": True, "raw": "MILLIMETRE"},
        # length unit: millimeters
        # is_metric=True: using metric system
        # raw="MILLIMETRE": the IFC standard unit name

        area={"is_metric": True, "raw": "SQUARE_METRE"},
        # area unit: square meters

        volume={"is_metric": True, "raw": "CUBIC_METRE"}
        # volume unit: cubic meters
    )

    context = ifcopenshell.api.run(
        "context.add_context",
        # command: add a geometry representation context
        # this defines the coordinate system and purpose
        ifc_file,

        context_type="Model"
        # "Model" = 3D geometric model context
        # other options: "Plan" (2D), "Profile"
    )

    site = ifcopenshell.api.run(
        "root.create_entity",
        ifc_file,
        ifc_class="IfcSite",
        # IfcSite: represents a physical site/location
        name="Manufacturing Site"
    )

    building = ifcopenshell.api.run(
        "root.create_entity",
        ifc_file,
        ifc_class="IfcBuilding",
        # IfcBuilding: represents a building or facility
        name="Production Facility"
    )

    storey = ifcopenshell.api.run(
        "root.create_entity",
        ifc_file,
        ifc_class="IfcBuildingStorey",
        # IfcBuildingStorey: a floor/level of the building
        # we use this as the container for mechanical elements
        name="Assembly Floor"
    )

    # --- assemble the hierarchy ---
    ifcopenshell.api.run(
        "aggregate.assign_object",
        # command: assign a child to a parent in the hierarchy
        ifc_file,
        relating_object=project,
        # parent
        related_object=site
        # child
    )

    ifcopenshell.api.run(
        "aggregate.assign_object",
        ifc_file,
        relating_object=site,
        related_object=building
    )

    ifcopenshell.api.run(
        "aggregate.assign_object",
        ifc_file,
        relating_object=building,
        related_object=storey
    )

    return project, site, building, storey, context
    # return all created hierarchy objects for use by other functions


def create_valve_element(ifc_file, specs, storey):
    """
    Create the valve as an IFC mechanical element.
    
    INPUT:  ifc_file → the IFC file
            specs (dict) → engineering specs
            storey → the building storey to place the valve in
    
    OUTPUT: element → the created IFC valve element
    """

    part_name = specs.get("part_name", "Industrial Valve")

    element = ifcopenshell.api.run(
        "root.create_entity",
        ifc_file,
        ifc_class="IfcFlowFitting",
        # IfcFlowFitting: IFC class for pipe fittings and valves
        # more accurate than IfcMechanicalFastener for valves
        # other options:
        # IfcValve: specifically for valves (in IFC4)
        # IfcPipeFitting: for pipe fittings

        name=part_name
        # element name shown in BIM viewers
    )

    ifcopenshell.api.run(
        "spatial.assign_container",
        # command: place the element inside a spatial container
        ifc_file,
        relating_structure=storey,
        # place it in the assembly floor
        related_element=element
        # the valve element
    )

    return element


def add_valve_properties(ifc_file, element, specs):
    """
    Add engineering specifications as IFC property sets.
    Property sets = the metadata attached to IFC elements.
    Anyone opening the IFC file can query these values.
    
    INPUT:  ifc_file → the IFC file
            element → the valve IFC element
            specs (dict) → engineering specifications
    """

    # --- Property Set 1: Technical Specifications ---
    pset_tech = ifcopenshell.api.run(
        "pset.add_pset",
        # command: add a property set to an element
        ifc_file,
        product=element,
        # which element to attach properties to

        name="PSet_ValveTechnicalSpecs"
        # name of the property set
        # "PSet_" prefix is IFC convention
    )

    ifcopenshell.api.run(
        "pset.edit_pset",
        # command: add properties to an existing property set
        ifc_file,
        pset=pset_tech,
        # which property set to edit

        properties={
            # dictionary of property_name: value
            # these become searchable metadata in BIM software

            "NominalDiameter_mm": float(specs.get("diameter_mm", 0)),
            # nominal bore diameter in millimeters
            # float(): ensure numeric type

            "NominalPressure_bar": float(specs.get("pressure_bar", 0)),
            # nominal pressure rating in bar

            "FaceToFaceLength_mm": float(specs.get("length_mm", 0)),
            # face-to-face installation length

            "WallThickness_mm": float(specs.get("wall_thickness_mm", 0) or 0),
            # pipe wall thickness (or 0 if not specified)

            "Tolerance_mm": float(specs.get("tolerance_mm", 0) or 0),
            # dimensional tolerance

            "ValveType": str(specs.get("valve_type", "Unknown")),
            # type of valve: ball, gate, butterfly, etc.

            "ConnectionType": str(specs.get("connection_type", "Unknown"))
            # how it connects to pipes: flanged, threaded, welded
        }
    )

    # --- Property Set 2: Material and Rating ---
    pset_material = ifcopenshell.api.run(
        "pset.add_pset",
        ifc_file,
        product=element,
        name="PSet_ValveMaterialRating"
        # second property set for material-related info
    )

    ifcopenshell.api.run(
        "pset.edit_pset",
        ifc_file,
        pset=pset_material,
        properties={
            "MaterialGrade": str(specs.get("material", "Unknown")),
            # material grade: "Inox_316L", "Carbon_Steel", etc.

            "MaxOperatingTemp_C": float(specs.get("temperature_max_C", 0) or 0),
            # maximum safe operating temperature

            "MinOperatingTemp_C": float(specs.get("temperature_min_C", 0) or 0),
            # minimum operating temperature

            "Weight_kg": float(specs.get("weight_kg", 0) or 0),
            # weight of the valve in kilograms

            "ApplicableStandard": str(specs.get("standard", "N/A")),
            # e.g., "EN558", "ISO 5211"

            "PartNumber": str(specs.get("part_number", "N/A"))
            # manufacturer part number
        }
    )

    # --- Property Set 3: Project Metadata ---
    pset_meta = ifcopenshell.api.run(
        "pset.add_pset",
        ifc_file,
        product=element,
        name="PSet_ProjectMetadata"
    )

    ifcopenshell.api.run(
        "pset.edit_pset",
        ifc_file,
        pset=pset_meta,
        properties={
            "Project": "OpenIndustry Algeria",
            "CreatedBy": "Extraction & CAD Pipeline",
            "CreationDate": datetime.now().isoformat(),
            "PipelineVersion": "1.0"
        }
    )


def generate_ifc_from_specs(specs, output_ifc_path):
    """
    MAIN FUNCTION: Generate complete IFC file from engineering specs.
    
    INPUT:  specs (dict)          → engineering specifications
            output_ifc_path (str) → where to save the .ifc file
    
    OUTPUT: str → output_ifc_path (confirmation)
    """

    os.makedirs(os.path.dirname(output_ifc_path), exist_ok=True)

    # --- create new IFC file ---
    ifc_file = ifcopenshell.file(schema="IFC4")
    # ifcopenshell.file(): create new empty IFC file in memory
    # schema="IFC4": use IFC version 4 (latest stable version)
    # IFC2x3 is older but more compatible with older software

    # --- build project structure ---
    print("  Creating IFC project structure...")
    project, site, building, storey, context = create_ifc_project_structure(
        ifc_file,
        "OpenIndustry Algeria — Valve Project"
    )

    # --- create valve element ---
    print("  Creating valve element...")
    element = create_valve_element(ifc_file, specs, storey)

    # --- add all properties ---
    print("  Adding engineering properties...")
    add_valve_properties(ifc_file, element, specs)

    # --- save the IFC file ---
    ifc_file.write(output_ifc_path)
    # write(): save the IFC file to disk
    # creates a valid IFC STEP file (text format)

    file_size = os.path.getsize(output_ifc_path)
    print(f"  IFC saved: {output_ifc_path} ({file_size:,} bytes)")

    return output_ifc_path


# ============================================================
# HOW TO TEST THIS FILE ALONE:
# ============================================================
if __name__ == "__main__":

    os.makedirs("output", exist_ok=True)

    sample_specs = {
        "part_name": "Vanne à bille DN100 PN40",
        "part_number": "VB-100-40-316L",
        "diameter_mm": 100,
        "pressure_bar": 40,
        "material": "Inox_316L",
        "length_mm": 229,
        "wall_thickness_mm": 8,
        "tolerance_mm": 0.5,
        "temperature_max_C": 200,
        "temperature_min_C": -20,
        "weight_kg": 12.5,
        "standard": "EN558",
        "connection_type": "flanged",
        "valve_type": "ball"
    }

    # TEST 1: generate IFC
    print("TEST 1: Generating IFC...")
    ifc_path = generate_ifc_from_specs(sample_specs, "output/test_valve.ifc")
    print(f"  Generated: {ifc_path} ✓")

    # TEST 2: verify by reading back
    print("\nTEST 2: Verifying IFC file...")
    ifc_check = ifcopenshell.open(ifc_path)
    # ifcopenshell.open(): open and parse an existing IFC file

    elements = ifc_check.by_type("IfcFlowFitting")
    # by_type(): get all entities of a specific IFC class
    # returns a list

    print(f"  Found {len(elements)} valve element(s) ✓")

    psets = ifc_check.by_type("IfcPropertySet")
    print(f"  Found {len(psets)} property sets ✓")

    print("\n  TO VIEW THE IFC FILE:")
    print("  Option 1 (free): BIM Vision → https://bimvision.eu/")
    print("  Option 2 (free): FreeCAD with BIM workbench")
    print("  Option 3 (free): usBIM.viewer+ → https://www.acca.it/")
    print(f"\n  File location: {os.path.abspath(ifc_path)}")
    # step6_ifc.py
# PURPOSE: Generate an IFC 3D model file with embedded metadata
# TOOL: ifcopenshell
# PIPELINE: specs dict → ifcopenshell creates IFC structure → add 3D geometry + properties → save .ifc

import ifcopenshell
# ifcopenshell: Python library for creating and reading IFC files
# IFC = Industry Foundation Classes
# open standard for sharing building/engineering models with embedded metadata
# install: pip install ifcopenshell

import ifcopenshell.api
# ifcopenshell.api: high-level API module with convenience functions
# makes creating IFC entities much simpler than using the raw API

import ifcopenshell.util.element
# utility functions for working with IFC elements

import os
import json
from datetime import datetime


def create_ifc_project_structure(ifc_file, project_name):
    """
    Create the mandatory IFC hierarchy: Project → Site → Building → Storey.
    Every IFC file needs this structure as a container for elements.
    
    INPUT:  ifc_file (IfcFile) → the IFC file object
            project_name (str) → name for the project
    
    OUTPUT: tuple (project, site, building, storey) → the created hierarchy objects
    """

    project = ifcopenshell.api.run(
        "root.create_entity",
        # command: create a new IFC entity
        ifc_file,
        # which IFC file to add it to

        ifc_class="IfcProject",
        # entity type: IfcProject = top-level container for everything
        # every IFC file has exactly ONE IfcProject

        name=project_name
        # the project's name attribute
    )

    ifcopenshell.api.run(
        "unit.assign_unit",
        # command: assign measurement units to the project
        ifc_file,

        length={"is_metric": True, "raw": "MILLIMETRE"},
        # length unit: millimeters
        # is_metric=True: using metric system
        # raw="MILLIMETRE": the IFC standard unit name

        area={"is_metric": True, "raw": "SQUARE_METRE"},
        # area unit: square meters

        volume={"is_metric": True, "raw": "CUBIC_METRE"}
        # volume unit: cubic meters
    )

    context = ifcopenshell.api.run(
        "context.add_context",
        # command: add a geometry representation context
        # this defines the coordinate system and purpose
        ifc_file,

        context_type="Model"
        # "Model" = 3D geometric model context
        # other options: "Plan" (2D), "Profile"
    )

    site = ifcopenshell.api.run(
        "root.create_entity",
        ifc_file,
        ifc_class="IfcSite",
        # IfcSite: represents a physical site/location
        name="Manufacturing Site"
    )

    building = ifcopenshell.api.run(
        "root.create_entity",
        ifc_file,
        ifc_class="IfcBuilding",
        # IfcBuilding: represents a building or facility
        name="Production Facility"
    )

    storey = ifcopenshell.api.run(
        "root.create_entity",
        ifc_file,
        ifc_class="IfcBuildingStorey",
        # IfcBuildingStorey: a floor/level of the building
        # we use this as the container for mechanical elements
        name="Assembly Floor"
    )

    # --- assemble the hierarchy ---
    ifcopenshell.api.run(
        "aggregate.assign_object",
        # command: assign a child to a parent in the hierarchy
        ifc_file,
        relating_object=project,
        # parent
        related_object=site
        # child
    )

    ifcopenshell.api.run(
        "aggregate.assign_object",
        ifc_file,
        relating_object=site,
        related_object=building
    )

    ifcopenshell.api.run(
        "aggregate.assign_object",
        ifc_file,
        relating_object=building,
        related_object=storey
    )

    return project, site, building, storey, context
    # return all created hierarchy objects for use by other functions


def create_valve_element(ifc_file, specs, storey):
    """
    Create the valve as an IFC mechanical element.
    
    INPUT:  ifc_file → the IFC file
            specs (dict) → engineering specs
            storey → the building storey to place the valve in
    
    OUTPUT: element → the created IFC valve element
    """

    part_name = specs.get("part_name", "Industrial Valve")

    element = ifcopenshell.api.run(
        "root.create_entity",
        ifc_file,
        ifc_class="IfcFlowFitting",
        # IfcFlowFitting: IFC class for pipe fittings and valves
        # more accurate than IfcMechanicalFastener for valves
        # other options:
        # IfcValve: specifically for valves (in IFC4)
        # IfcPipeFitting: for pipe fittings

        name=part_name
        # element name shown in BIM viewers
    )

    ifcopenshell.api.run(
        "spatial.assign_container",
        # command: place the element inside a spatial container
        ifc_file,
        relating_structure=storey,
        # place it in the assembly floor
        related_element=element
        # the valve element
    )

    return element


def add_valve_properties(ifc_file, element, specs):
    """
    Add engineering specifications as IFC property sets.
    Property sets = the metadata attached to IFC elements.
    Anyone opening the IFC file can query these values.
    
    INPUT:  ifc_file → the IFC file
            element → the valve IFC element
            specs (dict) → engineering specifications
    """

    # --- Property Set 1: Technical Specifications ---
    pset_tech = ifcopenshell.api.run(
        "pset.add_pset",
        # command: add a property set to an element
        ifc_file,
        product=element,
        # which element to attach properties to

        name="PSet_ValveTechnicalSpecs"
        # name of the property set
        # "PSet_" prefix is IFC convention
    )

    ifcopenshell.api.run(
        "pset.edit_pset",
        # command: add properties to an existing property set
        ifc_file,
        pset=pset_tech,
        # which property set to edit

        properties={
            # dictionary of property_name: value
            # these become searchable metadata in BIM software

            "NominalDiameter_mm": float(specs.get("diameter_mm", 0)),
            # nominal bore diameter in millimeters
            # float(): ensure numeric type

            "NominalPressure_bar": float(specs.get("pressure_bar", 0)),
            # nominal pressure rating in bar

            "FaceToFaceLength_mm": float(specs.get("length_mm", 0)),
            # face-to-face installation length

            "WallThickness_mm": float(specs.get("wall_thickness_mm", 0) or 0),
            # pipe wall thickness (or 0 if not specified)

            "Tolerance_mm": float(specs.get("tolerance_mm", 0) or 0),
            # dimensional tolerance

            "ValveType": str(specs.get("valve_type", "Unknown")),
            # type of valve: ball, gate, butterfly, etc.

            "ConnectionType": str(specs.get("connection_type", "Unknown"))
            # how it connects to pipes: flanged, threaded, welded
        }
    )

    # --- Property Set 2: Material and Rating ---
    pset_material = ifcopenshell.api.run(
        "pset.add_pset",
        ifc_file,
        product=element,
        name="PSet_ValveMaterialRating"
        # second property set for material-related info
    )

    ifcopenshell.api.run(
        "pset.edit_pset",
        ifc_file,
        pset=pset_material,
        properties={
            "MaterialGrade": str(specs.get("material", "Unknown")),
            # material grade: "Inox_316L", "Carbon_Steel", etc.

            "MaxOperatingTemp_C": float(specs.get("temperature_max_C", 0) or 0),
            # maximum safe operating temperature

            "MinOperatingTemp_C": float(specs.get("temperature_min_C", 0) or 0),
            # minimum operating temperature

            "Weight_kg": float(specs.get("weight_kg", 0) or 0),
            # weight of the valve in kilograms

            "ApplicableStandard": str(specs.get("standard", "N/A")),
            # e.g., "EN558", "ISO 5211"

            "PartNumber": str(specs.get("part_number", "N/A"))
            # manufacturer part number
        }
    )

    # --- Property Set 3: Project Metadata ---
    pset_meta = ifcopenshell.api.run(
        "pset.add_pset",
        ifc_file,
        product=element,
        name="PSet_ProjectMetadata"
    )

    ifcopenshell.api.run(
        "pset.edit_pset",
        ifc_file,
        pset=pset_meta,
        properties={
            "Project": "OpenIndustry Algeria",
            "CreatedBy": "Extraction & CAD Pipeline",
            "CreationDate": datetime.now().isoformat(),
            "PipelineVersion": "1.0"
        }
    )


def generate_ifc_from_specs(specs, output_ifc_path):
    """
    MAIN FUNCTION: Generate complete IFC file from engineering specs.
    
    INPUT:  specs (dict)          → engineering specifications
            output_ifc_path (str) → where to save the .ifc file
    
    OUTPUT: str → output_ifc_path (confirmation)
    """

    os.makedirs(os.path.dirname(output_ifc_path), exist_ok=True)

    # --- create new IFC file ---
    ifc_file = ifcopenshell.file(schema="IFC4")
    # ifcopenshell.file(): create new empty IFC file in memory
    # schema="IFC4": use IFC version 4 (latest stable version)
    # IFC2x3 is older but more compatible with older software

    # --- build project structure ---
    print("  Creating IFC project structure...")
    project, site, building, storey, context = create_ifc_project_structure(
        ifc_file,
        "OpenIndustry Algeria — Valve Project"
    )

    # --- create valve element ---
    print("  Creating valve element...")
    element = create_valve_element(ifc_file, specs, storey)

    # --- add all properties ---
    print("  Adding engineering properties...")
    add_valve_properties(ifc_file, element, specs)

    # --- save the IFC file ---
    ifc_file.write(output_ifc_path)
    # write(): save the IFC file to disk
    # creates a valid IFC STEP file (text format)

    file_size = os.path.getsize(output_ifc_path)
    print(f"  IFC saved: {output_ifc_path} ({file_size:,} bytes)")

    return output_ifc_path


# ============================================================
# HOW TO TEST THIS FILE ALONE:
# ============================================================
if __name__ == "__main__":

    os.makedirs("output", exist_ok=True)

    sample_specs = {
        "part_name": "Vanne à bille DN100 PN40",
        "part_number": "VB-100-40-316L",
        "diameter_mm": 100,
        "pressure_bar": 40,
        "material": "Inox_316L",
        "length_mm": 229,
        "wall_thickness_mm": 8,
        "tolerance_mm": 0.5,
        "temperature_max_C": 200,
        "temperature_min_C": -20,
        "weight_kg": 12.5,
        "standard": "EN558",
        "connection_type": "flanged",
        "valve_type": "ball"
    }

    # TEST 1: generate IFC
    print("TEST 1: Generating IFC...")
    ifc_path = generate_ifc_from_specs(sample_specs, "output/test_valve.ifc")
    print(f"  Generated: {ifc_path} ✓")

    # TEST 2: verify by reading back
    print("\nTEST 2: Verifying IFC file...")
    ifc_check = ifcopenshell.open(ifc_path)
    # ifcopenshell.open(): open and parse an existing IFC file

    elements = ifc_check.by_type("IfcFlowFitting")
    # by_type(): get all entities of a specific IFC class
    # returns a list

    print(f"  Found {len(elements)} valve element(s) ✓")

    psets = ifc_check.by_type("IfcPropertySet")
    print(f"  Found {len(psets)} property sets ✓")

    print("\n  TO VIEW THE IFC FILE:")
    print("  Option 1 (free): BIM Vision → https://bimvision.eu/")
    print("  Option 2 (free): FreeCAD with BIM workbench")
    print("  Option 3 (free): usBIM.viewer+ → https://www.acca.it/")
    print(f"\n  File location: {os.path.abspath(ifc_path)}")
    # test_all.py
# PURPOSE: Test every single step of the pipeline automatically
# Run this to verify everything works before running on real data

import os
import sys
import json
import time

print("=" * 60)
print("  EXTRACTION & CAD PIPELINE — FULL TEST SUITE")
print("=" * 60)

passed = 0
# counter for passed tests

failed = 0
# counter for failed tests

errors = []
# list to collect error messages


def test(name, func):
    """
    Run a single test function and track pass/fail.
    
    INPUT:  name (str)    → human-readable test name
            func (callable) → the test function to run (no arguments)
    """

    global passed, failed, errors
    # global: access the module-level variables (not local copies)

    print(f"\n  Testing: {name}...")

    try:
        # try: run the test function
        func()
        # call the function with no arguments

        print(f"  ✓ PASS: {name}")
        passed += 1
        # increment pass counter

    except AssertionError as e:
        # AssertionError: raised by 'assert' statements that fail
        print(f"  ✗ FAIL: {name}")
        print(f"    Reason: {e}")
        failed += 1
        errors.append(f"FAIL - {name}: {e}")

    except Exception as e:
        # Exception: catch any other error
        print(f"  ✗ ERROR: {name}")
        print(f"    Error: {type(e).__name__}: {e}")
        failed += 1
        errors.append(f"ERROR - {name}: {type(e).__name__}: {e}")


# ── SETUP ────────────────────────────────────────────────────
os.makedirs("output", exist_ok=True)
os.makedirs("input", exist_ok=True)
# create necessary folders


# ── TEST GROUP 1: IMPORTS ─────────────────────────────────────
print("\n" + "-" * 40)
print("GROUP 1: LIBRARY IMPORTS")
print("-" * 40)


def test_import_pdfplumber():
    import pdfplumber
    assert pdfplumber is not None, "pdfplumber import failed"


def test_import_fitz():
    import fitz
    assert fitz is not None, "PyMuPDF (fitz) import failed"


def test_import_pytesseract():
    import pytesseract
    assert pytesseract is not None, "pytesseract import failed"


def test_import_ezdxf():
    import ezdxf
    assert ezdxf is not None, "ezdxf import failed"


def test_import_ifcopenshell():
    import ifcopenshell
    assert ifcopenshell is not None, "ifcopenshell import failed"


def test_import_requests():
    import requests
    assert requests is not None, "requests import failed"


def test_import_pillow():
    from PIL import Image
    assert Image is not None, "Pillow (PIL) import failed"


test("Import pdfplumber", test_import_pdfplumber)
test("Import PyMuPDF (fitz)", test_import_fitz)
test("Import pytesseract", test_import_pytesseract)
test("Import ezdxf", test_import_ezdxf)
test("Import ifcopenshell", test_import_ifcopenshell)
test("Import requests", test_import_requests)
test("Import Pillow", test_import_pillow)


# ── TEST GROUP 2: STEP 1 (PDF EXTRACTION) ────────────────────
print("\n" + "-" * 40)
print("GROUP 2: STEP 1 - PDF EXTRACTION")
print("-" * 40)


def test_create_sample_pdf():
    """Create a simple test PDF using reportlab (if available) or fpdf2."""
    try:
        from reportlab.pdfgen import canvas
        # reportlab: library for creating PDFs
        # optional: pip install reportlab

        c = canvas.Canvas("input/test_sample.pdf")
        # create a new PDF canvas

        c.setFont("Helvetica", 12)
        # set font: Helvetica, size 12

        c.drawString(100, 750, "VANNE A BILLE DN100 PN40")
        # drawString(x, y, text): draw text at position (x,y) in points
        # (100, 750) = 100 points from left, 750 from bottom

        c.drawString(100, 730, "Material: Inox 316L")
        c.drawString(100, 710, "Diametre: 100 mm")
        c.drawString(100, 690, "Pression: 40 bar")
        c.drawString(100, 670, "Longueur: 229 mm")
        c.drawString(100, 650, "Tolerance: +/-0.5 mm")
        c.drawString(100, 630, "Temperature max: 200 C")
        c.save()
        # save(): write the PDF to disk

        assert os.path.exists("input/test_sample.pdf"), "PDF not created"
        print("    Used reportlab to create test PDF")

    except ImportError:
        # reportlab not installed: create a minimal text-based PDF manually
        pdf_content = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<</Font<</F1 4 0 R>>>>/Contents 



# test_all.py
# PURPOSE: Test every single step of the pipeline automatically
# Run this to verify everything works before running on real data

import os
import sys
import json
import time

print("=" * 60)
print("  EXTRACTION & CAD PIPELINE — FULL TEST SUITE")
print("=" * 60)

passed = 0
# counter for passed tests

failed = 0
# counter for failed tests

errors = []
# list to collect error messages


def test(name, func):
    """
    Run a single test function and track pass/fail.
    
    INPUT:  name (str)    → human-readable test name
            func (callable) → the test function to run (no arguments)
    """

    global passed, failed, errors
    # global: access the module-level variables (not local copies)

    print(f"\n  Testing: {name}...")

    try:
        # try: run the test function
        func()
        # call the function with no arguments

        print(f"  ✓ PASS: {name}")
        passed += 1
        # increment pass counter

    except AssertionError as e:
        # AssertionError: raised by 'assert' statements that fail
        print(f"  ✗ FAIL: {name}")
        print(f"    Reason: {e}")
        failed += 1
        errors.append(f"FAIL - {name}: {e}")

    except Exception as e:
        # Exception: catch any other error
        print(f"  ✗ ERROR: {name}")
        print(f"    Error: {type(e).__name__}: {e}")
        failed += 1
        errors.append(f"ERROR - {name}: {type(e).__name__}: {e}")


# ── SETUP ────────────────────────────────────────────────────
os.makedirs("output", exist_ok=True)
os.makedirs("input", exist_ok=True)
# create necessary folders


# ── TEST GROUP 1: IMPORTS ─────────────────────────────────────
print("\n" + "-" * 40)
print("GROUP 1: LIBRARY IMPORTS")
print("-" * 40)


def test_import_pdfplumber():
    import pdfplumber
    assert pdfplumber is not None, "pdfplumber import failed"


def test_import_fitz():
    import fitz
    assert fitz is not None, "PyMuPDF (fitz) import failed"


def test_import_pytesseract():
    import pytesseract
    assert pytesseract is not None, "pytesseract import failed"


def test_import_ezdxf():
    import ezdxf
    assert ezdxf is not None, "ezdxf import failed"


def test_import_ifcopenshell():
    import ifcopenshell
    assert ifcopenshell is not None, "ifcopenshell import failed"


def test_import_requests():
    import requests
    assert requests is not None, "requests import failed"


def test_import_pillow():
    from PIL import Image
    assert Image is not None, "Pillow (PIL) import failed"


test("Import pdfplumber", test_import_pdfplumber)
test("Import PyMuPDF (fitz)", test_import_fitz)
test("Import pytesseract", test_import_pytesseract)
test("Import ezdxf", test_import_ezdxf)
test("Import ifcopenshell", test_import_ifcopenshell)
test("Import requests", test_import_requests)
test("Import Pillow", test_import_pillow)


# ── TEST GROUP 2: STEP 1 (PDF EXTRACTION) ────────────────────
print("\n" + "-" * 40)
print("GROUP 2: STEP 1 - PDF EXTRACTION")
print("-" * 40)


def test_create_sample_pdf():
    """Create a simple test PDF using reportlab (if available) or fpdf2."""
    try:
        from reportlab.pdfgen import canvas
        # reportlab: library for creating PDFs
        # optional: pip install reportlab

        c = canvas.Canvas("input/test_sample.pdf")
        # create a new PDF canvas

        c.setFont("Helvetica", 12)
        # set font: Helvetica, size 12

        c.drawString(100, 750, "VANNE A BILLE DN100 PN40")
        # drawString(x, y, text): draw text at position (x,y) in points
        # (100, 750) = 100 points from left, 750 from bottom

        c.drawString(100, 730, "Material: Inox 316L")
        c.drawString(100, 710, "Diametre: 100 mm")
        c.drawString(100, 690, "Pression: 40 bar")
        c.drawString(100, 670, "Longueur: 229 mm")
        c.drawString(100, 650, "Tolerance: +/-0.5 mm")
        c.drawString(100, 630, "Temperature max: 200 C")
        c.save()
        # save(): write the PDF to disk

        assert os.path.exists("input/test_sample.pdf"), "PDF not created"
        print("    Used reportlab to create test PDF")

    except ImportError:
        # reportlab not installed: create a minimal text-based PDF manually
        pdf_content = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<</Font<</F1 4 0 R>>>>/Contents 5 0 R>>endobj
4 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj
5 0 obj<</Length 200>>
stream
BT /F1 12 Tf 100 750 Td (VANNE A BILLE DN100 PN40) Tj
0 -20 Td (Material: Inox 316L) Tj
0 -20 Td (Diametre: 100 mm) Tj
0 -20 Td (Pression: 40 bar) Tj
0 -20 Td (Longueur: 229 mm) Tj
0 -20 Td (Tolerance: +-0.5 mm) Tj ET
endstream
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000266 00000 n 
0000000340 00000 n 
trailer<</Size 6/Root 1 0 R>>
startxref
591
%%EOF"""
        # minimal valid PDF structure written manually
        # BT = begin text, Tf = set font, Td = move position, Tj = show text, ET = end text

        with open("input/test_sample.pdf", 'wb') as f:
            # 'wb' = write binary mode
            f.write(pdf_content)
        print("    Created minimal test PDF manually")

    assert os.path.exists("input/test_sample.pdf")


def test_pdf_extraction():
    from step1_pdf_extraction import extract_text_from_pdf, is_text_sufficient

    text = extract_text_from_pdf("input/test_sample.pdf")
    assert isinstance(text, str), "extract_text_from_pdf should return a string"
    print(f"    Extracted {len(text)} characters")


def test_pdf_sufficiency_check():
    from step1_pdf_extraction import is_text_sufficient

    assert is_text_sufficient("This is enough text " * 5) == True
    # "This is enough text " * 5 = repeats the string 5 times
    # total = 100 characters > 50 minimum

    assert is_text_sufficient("short") == False
    # "short" = 5 characters < 50 minimum


test("Create sample test PDF", test_create_sample_pdf)
test("PDF text extraction (pdfplumber)", test_pdf_extraction)
test("Text sufficiency check", test_pdf_sufficiency_check)


# ── TEST GROUP 3: STEP 2 (OCR) ───────────────────────────────
print("\n" + "-" * 40)
print("GROUP 3: STEP 2 - OCR")
print("-" * 40)


def test_page_rendering():
    import fitz
    from step2_ocr import render_page_as_image

    doc = fitz.open("input/test_sample.pdf")
    page = doc[0]
    # get first page

    image = render_page_as_image(page, scale=1.0)
    # render at 1x scale for speed in testing

    doc.close()

    from PIL import Image
    assert isinstance(image, Image.Image), "Should return PIL Image"
    assert image.width > 0, "Image should have positive width"
    assert image.height > 0, "Image should have positive height"

    image.save("output/test_rendered_page.png")
    print(f"    Rendered: {image.width}x{image.height} pixels")
    print("    Saved preview to: output/test_rendered_page.png")


def test_tesseract_available():
    import pytesseract
    from step2_ocr import set_tesseract_path

    set_tesseract_path()
    # try to configure tesseract path

    try:
        version = pytesseract.get_tesseract_version()
        # get_tesseract_version(): get the installed Tesseract version
        print(f"    Tesseract version: {version}")
        assert version is not None
    except Exception as e:
        raise AssertionError(
            f"Tesseract not found: {e}\n"
            "Install from: https://github.com/UB-Mannheim/tesseract/wiki"
        )


def test_ocr_on_rendered_image():
    import pytesseract
    from PIL import Image
    from step2_ocr import ocr_single_image

    if os.path.exists("output/test_rendered_page.png"):
        image = Image.open("output/test_rendered_page.png")
        # open the rendered image we saved earlier

        text = ocr_single_image(image, languages='eng')
        # run OCR with English language

        assert isinstance(text, str), "OCR should return string"
        print(f"    OCR extracted {len(text)} characters")
        print(f"    Sample: {text[:100].strip()}")
    else:
        print("    Skipped: no rendered image found (run page rendering test first)")


test("Render PDF page as image", test_page_rendering)
test("Tesseract OCR is installed", test_tesseract_available)
test("OCR on rendered image", test_ocr_on_rendered_image)


# ── TEST GROUP 4: STEP 3 (LLM) ──────────────────────────────
print("\n" + "-" * 40)
print("GROUP 4: STEP 3 - LLM (OLLAMA + MISTRAL)")
print("-" * 40)


def test_ollama_running():
    from step3_llm import check_ollama_running
    is_running = check_ollama_running()
    assert is_running, (
        "Ollama is not running!\n"
        "    Start it: ollama serve\n"
        "    Or install from: https://ollama.ai"
    )
    print("    Ollama server is running ✓")


def test_mistral_available():
    from step3_llm import check_model_available
    is_available = check_model_available("mistral")
    assert is_available, (
        "Mistral model not found!\n"
        "    Download it: ollama pull mistral"
    )
    print("    Mistral model is available ✓")


def test_llm_extraction():
    from step3_llm import extract_specs_with_llm

    sample_text = """
    VANNE A BILLE DN100 PN40
    Corps: Inox 316L
    Diametre nominal: 100 mm
    Pression nominale: 40 bar
    Longueur face-a-face: 229 mm
    Tolerance: +-0.5 mm
    Temperature max: 200 degres C
    """

    specs = extract_specs_with_llm(sample_text)
    # run LLM extraction on sample text

    assert isinstance(specs, dict), "LLM should return a dict"
    assert specs.get("diameter_mm") == 100, f"Expected diameter 100, got {specs.get('diameter_mm')}"
    assert specs.get("pressure_bar") == 40, f"Expected pressure 40, got {specs.get('pressure_bar')}"
    assert specs.get("material") is not None, "Material should not be None"

    print(f"    Extracted {len(specs)} fields ✓")
    print(f"    diameter_mm: {specs.get('diameter_mm')}")
    print(f"    pressure_bar: {specs.get('pressure_bar')}")
    print(f"    material: {specs.get('material')}")


test("Ollama server running", test_ollama_running)
test("Mistral model available", test_mistral_available)
test("LLM extraction accuracy", test_llm_extraction)


# ── TEST GROUP 5: STEP 4 (JSON) ──────────────────────────────
print("\n" + "-" * 40)
print("GROUP 5: STEP 4 - JSON SAVE/LOAD")
print("-" * 40)


SAMPLE_SPECS = {
    "part_name": "Vanne à bille DN100 PN40",
    "part_number": "VB-100-40-316L",
    "diameter_mm": 100,
    "outer_diameter_mm": 116,
    "pressure_bar": 40,
    "material": "Inox_316L",
    "length_mm": 229,
    "wall_thickness_mm": 8,
    "tolerance_mm": 0.5,
    "temperature_max_C": 200,
    "temperature_min_C": -20,
    "weight_kg": 12.5,
    "standard": "EN558",
    "connection_type": "flanged",
    "valve_type": "ball"
}
# sample specs used across multiple tests


def test_save_json():
    from step4_json import save_specs_to_json
    path = save_specs_to_json(SAMPLE_SPECS, "output/test_specs.json")
    assert os.path.exists("output/test_specs.json"), "JSON file not created"
    file_size = os.path.getsize("output/test_specs.json")
    assert file_size > 0, "JSON file is empty"
    print(f"    Saved {file_size} bytes")


def test_load_json():
    from step4_json import load_specs_from_json
    loaded = load_specs_from_json("output/test_specs.json")
    assert isinstance(loaded, dict), "Loaded data should be a dict"
    assert loaded["diameter_mm"] == 100, "diameter_mm mismatch"
    assert loaded["material"] == "Inox_316L", "material mismatch"
    assert loaded["pressure_bar"] == 40, "pressure_bar mismatch"
    print(f"    Loaded and verified {len(loaded)} fields ✓")


def test_json_roundtrip():
    """Test that save → load preserves all data exactly."""
    from step4_json import save_specs_to_json, load_specs_from_json

    save_specs_to_json(SAMPLE_SPECS, "output/test_roundtrip.json")
    loaded = load_specs_from_json("output/test_roundtrip.json")

    for key, expected in SAMPLE_SPECS.items():
        actual = loaded.get(key)
        assert actual == expected, f"Roundtrip mismatch for '{key}': expected {expected}, got {actual}"
    print(f"    All {len(SAMPLE_SPECS)} fields preserved exactly ✓")


test("Save specs to JSON", test_save_json)
test("Load specs from JSON", test_load_json)
test("JSON save/load roundtrip", test_json_roundtrip)


# ── TEST GROUP 6: STEP 5 (DXF) ──────────────────────────────
print("\n" + "-" * 40)
print("GROUP 6: STEP 5 - DXF GENERATION")
print("-" * 40)


def test_dxf_generation():
    from step5_dxf import generate_dxf_from_specs
    path = generate_dxf_from_specs(SAMPLE_SPECS, "output/test_valve.dxf")
    assert os.path.exists("output/test_valve.dxf"), "DXF file not created"
    file_size = os.path.getsize("output/test_valve.dxf")
    assert file_size > 0, "DXF file is empty"
    print(f"    Generated {file_size:,} bytes")


def test_dxf_validity():
    """Verify the DXF file can be opened and parsed by ezdxf."""
    import ezdxf
    doc = ezdxf.readfile("output/test_valve.dxf")
    # readfile(): open and parse an existing DXF file
    # raises exception if file is invalid or corrupted

    msp = doc.modelspace()
    entities = list(msp)
    # list(): convert modelspace iterator to list
    # each item is a drawing entity (line, circle, text, etc.)

    assert len(entities) > 0, "DXF should contain drawing entities"
    print(f"    Valid DXF with {len(entities)} entities ✓")

    # count entity types
    circles = [e for e in entities if e.dxftype() == "CIRCLE"]
    lines = [e for e in entities if e.dxftype() == "LINE"]
    texts = [e for e in entities if e.dxftype() == "TEXT"]
    # list comprehensions: filter entities by their DXF type

    print(f"    Circles: {len(circles)}")
    print(f"    Lines: {len(lines)}")
    print(f"    Texts: {len(texts)}")

    assert len(circles) >= 2, "Should have at least 2 circles (bore + outer body)"
    assert len(lines) >= 4, "Should have at least 4 lines"


def test_dxf_layers():
    """Verify all expected layers exist in the DXF."""
    import ezdxf
    doc = ezdxf.readfile("output/test_valve.dxf")

    layer_names = [layer.dxf.name for layer in doc.layers]
    # doc.layers: iterator over all layers
    # layer.dxf.name: the name attribute of each layer

    required_layers = ["GEOMETRY", "CENTERLINE", "DIMENSIONS", "TEXT"]
    for layer in required_layers:
        assert layer in layer_names, f"Layer '{layer}' missing from DXF"
    print(f"    All required layers present: {required_layers} ✓")


test("DXF file generation", test_dxf_generation)
test("DXF file validity", test_dxf_validity)
test("DXF layer structure", test_dxf_layers)


# ── TEST GROUP 7: STEP 6 (IFC) ──────────────────────────────
print("\n" + "-" * 40)
print("GROUP 7: STEP 6 - IFC GENERATION")
print("-" * 40)


def test_ifc_generation():
    from step6_ifc import generate_ifc_from_specs
    path = generate_ifc_from_specs(SAMPLE_SPECS, "output/test_valve.ifc")
    assert os.path.exists("output/test_valve.ifc"), "IFC file not created"
    file_size = os.path.getsize("output/test_valve.ifc")
    assert file_size > 0, "IFC file is empty"
    print(f"    Generated {file_size:,} bytes")


def test_ifc_validity():
    """Verify the IFC file can be opened and contains expected data."""
    ifc = ifcopenshell.open("output/test_valve.ifc")
    # ifcopenshell.open(): open and parse an IFC file

    elements = ifc.by_type("IfcFlowFitting")
    assert len(elements) > 0, "IFC should contain at least one IfcFlowFitting"

    psets = ifc.by_type("IfcPropertySet")
    assert len(psets) >= 3, f"Expected 3+ property sets, got {len(psets)}"

    print(f"    Found {len(elements)} valve elements ✓")
    print(f"    Found {len(psets)} property sets ✓")


def test_ifc_properties():
    """Verify engineering properties are correctly stored in IFC."""
    import ifcopenshell
    ifc = ifcopenshell.open("output/test_valve.ifc")

    psets = ifc.by_type("IfcPropertySet")
    # get all property sets

    all_prop_names = []
    for pset in psets:
        # loop through each property set
        for prop in pset.HasProperties:
            # HasProperties: list of properties in this set
            all_prop_names.append(prop.Name)
            # prop.Name: the property's name

    assert "NominalDiameter_mm" in all_prop_names, "Missing NominalDiameter_mm property"
    assert "MaterialGrade" in all_prop_names, "Missing MaterialGrade property"
    assert "NominalPressure_bar" in all_prop_names, "Missing NominalPressure_bar property"

    print(f"    Found {len(all_prop_names)} total properties ✓")
    print(f"    Key properties verified ✓")


test("IFC file generation", test_ifc_generation)
test("IFC file validity", test_ifc_validity)
test("IFC property content", test_ifc_properties)


# ── FINAL SUMMARY ────────────────────────────────────────────
print("\n" + "=" * 60)
print("  TEST RESULTS SUMMARY")
print("=" * 60)
print(f"  ✓ PASSED: {passed}")
print(f"  ✗ FAILED: {failed}")
print(f"  TOTAL:    {passed + failed}")

if errors:
    print("\n  FAILED TESTS:")
    for err in errors:
        print(f"    • {err}")

if failed == 0:
    print("\n  ALL TESTS PASSED ✓")
    print("  Your pipeline is ready to use!")
    print("\n  NEXT STEP:")
    print("  1. Put your PDF in the input/ folder")
    print("  2. Run: python main.py input/your_file.pdf")
else:
    print(f"\n  {failed} test(s) failed. Fix them before running the pipeline.")

print("=" * 60)