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
