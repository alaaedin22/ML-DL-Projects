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

        print(f"  [PASS] {name}")
        passed += 1
        # increment pass counter

    except AssertionError as e:
        # AssertionError: raised by 'assert' statements that fail
        print(f"  [FAIL] {name}")
        print(f"    Reason: {e}")
        failed += 1
        errors.append(f"FAIL - {name}: {e}")

    except Exception as e:
        # Exception: catch any other error
        print(f"  [ERROR] {name}")
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

def test_pdfplumber():
    import pdfplumber
    assert pdfplumber is not None

def test_requests():
    import requests
    assert requests is not None

def test_ezdxf():
    import ezdxf
    assert ezdxf is not None

def test_ifcopenshell():
    import ifcopenshell
    assert ifcopenshell is not None

test("pdfplumber library", test_pdfplumber)
test("requests library", test_requests)
test("ezdxf library", test_ezdxf)
test("ifcopenshell library", test_ifcopenshell)


# ── TEST GROUP 2: MODULE IMPORTS ──────────────────────────────
print("\n" + "-" * 40)
print("GROUP 2: PIPELINE MODULE IMPORTS")
print("-" * 40)

def test_step1_import():
    from step1_pdf_extraction import extract_text_from_pdf, is_text_sufficient
    assert callable(extract_text_from_pdf)
    assert callable(is_text_sufficient)

def test_step2_import():
    from step2_ocr import ocr_pdf_pages, render_page_as_image
    assert callable(ocr_pdf_pages)
    assert callable(render_page_as_image)

def test_step3_import():
    from step3_llm import extract_specs_with_llm, query_llm
    assert callable(extract_specs_with_llm)
    assert callable(query_llm)

def test_step4_import():
    from step4_json import save_specs_to_json, load_specs_from_json
    assert callable(save_specs_to_json)
    assert callable(load_specs_from_json)

def test_step5_import():
    from step5_dxf import generate_dxf_from_specs
    assert callable(generate_dxf_from_specs)

def test_step6_import():
    from step6_ifc import generate_ifc_from_specs
    assert callable(generate_ifc_from_specs)

test("step1_pdf_extraction module", test_step1_import)
test("step2_ocr module", test_step2_import)
test("step3_llm module", test_step3_import)
test("step4_json module", test_step4_import)
test("step5_dxf module", test_step5_import)
test("step6_ifc module", test_step6_import)


# ── TEST GROUP 3: UTILITY FUNCTIONS ───────────────────────────
print("\n" + "-" * 40)
print("GROUP 3: UTILITY FUNCTIONS")
print("-" * 40)

def test_is_text_sufficient():
    from step1_pdf_extraction import is_text_sufficient
    assert is_text_sufficient("This is a sufficiently long test string with more than fifty characters to pass the test.") == True
    assert is_text_sufficient("Hi") == False
    assert is_text_sufficient("") == False

def test_print_specs_table():
    from step4_json import print_specs_table
    sample = {"diameter_mm": 100, "pressure_bar": 40}
    print_specs_table(sample)
    # just verify it doesn't crash

test("is_text_sufficient() function", test_is_text_sufficient)
test("print_specs_table() function", test_print_specs_table)


# ── TEST GROUP 4: JSON OPERATIONS ─────────────────────────────
print("\n" + "-" * 40)
print("GROUP 4: JSON SAVE/LOAD")
print("-" * 40)

def test_json_save_load():
    from step4_json import save_specs_to_json, load_specs_from_json
    
    test_specs = {
        "part_name": "Test Valve",
        "diameter_mm": 100,
        "pressure_bar": 40,
    }
    
    path = "output/test_json.json"
    save_specs_to_json(test_specs, path)
    assert os.path.exists(path), "JSON file not created"
    
    loaded = load_specs_from_json(path)
    assert loaded["diameter_mm"] == 100
    assert loaded["pressure_bar"] == 40
    
    os.remove(path)

test("JSON save and load", test_json_save_load)


# ── TEST GROUP 5: CAD GENERATION ──────────────────────────────
print("\n" + "-" * 40)
print("GROUP 5: CAD FILE GENERATION")
print("-" * 40)

def test_dxf_generation():
    from step5_dxf import generate_dxf_from_specs
    import ezdxf
    
    spec_data = {
        "part_name": "Test Valve DN50",
        "diameter_mm": 50,
        "pressure_bar": 16,
        "material": "Inox_316L",
        "length_mm": 150,
        "wall_thickness_mm": 6,
        "tolerance_mm": 0.3,
        "standard": "EN558"
    }
    
    dxf_file = "output/test_gen.dxf"
    result = generate_dxf_from_specs(spec_data, dxf_file)
    
    assert os.path.exists(dxf_file), "DXF file not created"
    assert os.path.getsize(dxf_file) > 0, "DXF file is empty"
    
    # verify it's a valid DXF
    doc = ezdxf.readfile(dxf_file)
    msp = doc.modelspace()
    entity_count = len(list(msp))
    assert entity_count > 0, f"DXF has no entities"
    
    os.remove(dxf_file)

def test_ifc_generation():
    from step6_ifc import generate_ifc_from_specs
    import ifcopenshell
    
    spec_data = {
        "part_name": "Test Valve DN50",
        "part_number": "TV-50-16",
        "diameter_mm": 50,
        "pressure_bar": 16,
        "material": "Inox_316L",
        "length_mm": 150,
        "wall_thickness_mm": 6,
        "tolerance_mm": 0.3,
        "temperature_max_C": 180,
        "temperature_min_C": -10,
        "weight_kg": 5.2,
        "standard": "EN558",
        "connection_type": "flanged",
        "valve_type": "ball"
    }
    
    ifc_file = "output/test_gen.ifc"
    result = generate_ifc_from_specs(spec_data, ifc_file)
    
    assert os.path.exists(ifc_file), "IFC file not created"
    assert os.path.getsize(ifc_file) > 0, "IFC file is empty"
    
    # verify it's valid IFC
    ifc_doc = ifcopenshell.open(ifc_file)
    elements = ifc_doc.by_type("IfcFlowFitting")
    assert len(elements) > 0, "No valve elements in IFC"
    
    os.remove(ifc_file)

test("DXF generation from specs", test_dxf_generation)
test("IFC generation from specs", test_ifc_generation)


# ── SUMMARY ───────────────────────────────────────────────────
print("\n" + "=" * 60)
print("TEST SUMMARY")
print("=" * 60)

total = passed + failed
print(f"\nTotal tests: {total}")
print(f"Passed: {passed} [OK]")
print(f"Failed: {failed} [FAIL]")

if errors:
    print(f"\nErrors encountered:")
    for error in errors:
        print(f"  • {error}")

if failed == 0:
    print("\n*** ALL TESTS PASSED ***")
    sys.exit(0)
else:
    print(f"\n*** {failed} TEST(S) FAILED ***")
    sys.exit(1)
