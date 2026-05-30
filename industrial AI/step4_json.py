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
