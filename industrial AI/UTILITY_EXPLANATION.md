# UTILITY EXPLANATION: Files 7, 8, 9

## FILE 7: main.py (ORCHESTRATOR)

**Purpose:** The central command-line interface that coordinates all 6 pipeline steps

**What it does:**
- Acts as the "conductor" that calls each step in the correct order
- Handles PDF input from user
- Passes data between steps (text → specs → CAD files)
- Generates final output files (JSON, DXF, IFC)
- Provides progress feedback and error handling

**Key Functions:**

### `run_pipeline(pdf_path, output_prefix)`
Executes the complete workflow:

```
INPUT: your_file.pdf
  ↓
Step 1: extract_text_from_pdf()
  → Extracts: "DN100 PN40 Inox 316L..."
  ↓
Step 2: ocr_pdf_pages() [if needed]
  → Adds: OCR text from scanned pages
  ↓
Step 3: extract_specs_with_llm()
  → Returns: {"diameter_mm": 100, "pressure_bar": 40, ...}
  ↓
Step 4: save_specs_to_json()
  → Writes: result_specs.json
  ↓
Step 5: generate_dxf_from_specs()
  → Writes: result_drawing.dxf (2D CAD)
  ↓
Step 6: generate_ifc_from_specs()
  → Writes: result_model.ifc (3D BIM)
  ↓
OUTPUT: All files ready to use
```

**Usage Examples:**

```bash
# Process a real PDF file
python main.py input/valve_technical_spec.pdf
# Outputs: output/valve_technical_spec_specs.json
#          output/valve_technical_spec_drawing.dxf
#          output/valve_technical_spec_model.ifc

# Test with sample data (no PDF needed)
python main.py test
# Outputs: output/test_specs.json
#          output/test_draw.dxf
#          output/test_model.ifc
```

**Why you need it:**
- Direct, intuitive command-line interface
- No need to manually call 6 separate functions
- Automatic error handling and recovery
- Progress reporting (percentage complete, step names)
- Single entry point for automation/scheduling

**Example output when running:**
```
============================================================
  INDUSTRIAL EXTRACTION & CAD PIPELINE
  PDF → Text → LLM → JSON → DXF & IFC
============================================================

============================================================
STEP 1: PDF TEXT EXTRACTION
============================================================
Extracting text from: input/valve_spec.pdf
✓ Extracted 15234 characters
  First 200 chars: VANNE A BILLE DN100...

============================================================
STEP 3: LLM SPECIFICATION EXTRACTION
============================================================
Sending 15234 chars to Mistral LLM...
  LLM response received in 23.4 seconds
  Successfully extracted 15 specification fields
✓ Extracted 15 specification fields

...

Generated Files:
  • JSON → output/result_specs.json
  • DXF  → output/result_drawing.dxf
  • IFC  → output/result_model.ifc

Viewing Options:
  DXF (2D):  LibreCAD, FreeCAD, AutoCAD
  IFC (3D):  FreeCAD, BIM Vision, Blender
```

---

## FILE 8: test_all.py (TEST SUITE)

**Purpose:** Validates that all modules, libraries, and functions work correctly

**What it does:**
- Tests library availability (pdfplumber, requests, ezdxf, ifcopenshell)
- Tests module imports (can all 6 steps be imported?)
- Tests core functions (JSON save/load, CAD generation)
- Reports pass/fail for each test
- Gives a final summary with error details

**Test Groups:**

### GROUP 1: Library Imports (4 tests)
```python
✓ Can import pdfplumber?
✓ Can import requests?
✓ Can import ezdxf?
✓ Can import ifcopenshell?
```
**Why:** Guarantees all external libraries are installed before running pipeline

### GROUP 2: Module Imports (6 tests)
```python
✓ Can import step1_pdf_extraction module?
✓ Can import step2_ocr module?
✓ Can import step3_llm module?
✓ Can import step4_json module?
✓ Can import step5_dxf module?
✓ Can import step6_ifc module?
```
**Why:** Checks for syntax errors or broken imports in pipeline files

### GROUP 3: Utility Functions (2 tests)
```python
✓ is_text_sufficient() returns correct boolean?
✓ print_specs_table() formats output without crashing?
```
**Why:** Validates helper functions work as expected

### GROUP 4: JSON Operations (1 test)
```python
Test: Create specs dict → save to JSON → load from JSON
Expected: Loaded data matches original
Result: ✓ PASS (or ✗ FAIL with details)
```

### GROUP 5: CAD Generation (2 tests)
```python
✓ Can generate valid DXF file from specs?
  - File created? ✓
  - Has valid entities? ✓
  - Readable by ezdxf? ✓

✓ Can generate valid IFC file from specs?
  - File created? ✓
  - Has valid IFC structure? ✓
  - Contains valve elements? ✓
```

**Usage:**

```bash
# Run complete test suite
python test_all.py

# Expected output:
# ============================================================
#   EXTRACTION & CAD PIPELINE — FULL TEST SUITE
# ============================================================
#
# ────────────────────────────────────────────────────
# GROUP 1: LIBRARY IMPORTS
# ────────────────────────────────────────────────────
#   Testing: pdfplumber library...
#   ✓ PASS: pdfplumber library
#   
#   Testing: requests library...
#   ✓ PASS: requests library
#   ...
# 
# ============================================================
# TEST SUMMARY
# ============================================================
# Total tests: 19
# Passed: 19 ✓
# Failed: 0 ✗
#
# ✓✓✓ ALL TESTS PASSED ✓✓✓
```

**When to run test_all.py:**
1. **After first setup** - Verify everything installed correctly
2. **Before processing real data** - Ensure pipeline is ready
3. **After adding new dependencies** - Check for conflicts
4. **Before deploying** - Final validation before production use
5. **After updating code** - Catch regressions

**Example: If a test fails**
```bash
Testing: DXF generation from specs...
✗ ERROR: DXF generation from specs
  Error: ModuleNotFoundError: No module named 'ezdxf'

This tells you: ezdxf library is not installed
Solution: pip install ezdxf
```

---

## FILE 9: agent1.py (ORIGINAL FILE)

**Purpose:** Archive/reference copy of the original monolithic code

**What it contains:**
- All 6 pipeline steps merged into one 2492-line file
- Multiple `if __name__ == "__main__":` test blocks (only first executes)
- Overlapping imports (os imported 3 times, etc.)
- Mixed test code making it hard to debug

**Why keep it:**
1. **Version control** - Shows what the code looked like originally
2. **Reference** - If you need to understand the original structure
3. **Safety backup** - In case refactoring introduced bugs
4. **Documentation** - Shows the "before" state of the code
5. **Regression testing** - Compare old vs new outputs

**DO NOT use agent1.py for:**
- ✗ Running the pipeline (use main.py instead)
- ✗ Importing functions (use individual step files)
- ✗ Development (use individual modular files)
- ✗ Production (monolithic structure causes issues)

---

## WORKFLOW COMPARISON

### ❌ OLD WAY (Using agent1.py)
```
# Problems:
1. Run one test block, other tests unreachable
2. Hard to debug (what failed? all 6 steps mixed)
3. Cannot use individual steps as library
4. Slow to add new features (changes affect everything
5. Hard to maintain (2492 lines of mixed code)

# Usage:
python agent1.py  # Runs only step1 test (others ignored!)
```

### ✅ NEW WAY (Modular + main.py + test_all.py)
```
# Benefits:
1. Each step is independent
2. Easy to debug (errors pinpoint exact step)
3. Can use individual steps as library
4. Fast to add features (modify only needed file)
5. Easy to maintain (6 files × 300 lines each)

# Normal usage:
python main.py input/valve.pdf

# Testing:
python test_all.py

# Advanced: use as library
from step1_pdf_extraction import extract_text_from_pdf
text = extract_text_from_pdf("myfile.pdf")
```

---

## QUICK REFERENCE TABLE

| File | Purpose | When to use | Key functions |
|------|---------|------------|----------------|
| **main.py** | Orchestrator | Day-to-day processing | `run_pipeline()`, `main()` |
| **test_all.py** | Validation | After setup, before deployment | `test()` framework, test groups |
| **agent1.py** | Reference | Documentation, debugging | N/A (for reference only) |

---

## EXAMPLE WORKFLOWS

### Workflow 1: First Time Setup
```bash
1. python test_all.py          # Validate everything works
2. python main.py test         # Test with sample data
3. Check output/test_*.* files # Verify DXF and IFC generated correctly
```

### Workflow 2: Processing Real PDF
```bash
1. Place PDF in input/ folder: input/my_valve.pdf
2. python main.py input/my_valve.pdf
3. Output files created:
   - output/my_valve_specs.json
   - output/my_valve_drawing.dxf
   - output/my_valve_model.ifc
4. Open in CAD: LibreCAD (DXF) or FreeCAD (IFC)
```

### Workflow 3: Debugging a Problem
```bash
1. python test_all.py          # Find which test fails
2. Read error message          # Tells you exact issue
3. Fix the problem
4. Re-run: python test_all.py  # Confirm fixed
5. Resume: python main.py ...
```

### Workflow 4: Development / Adding Features
```bash
1. Edit specific step file (e.g., step5_dxf.py)
2. Test that step: python step5_dxf.py
3. Test all: python test_all.py
4. Integration test: python main.py test
5. Deploy: everything ready
```

---

## SUMMARY

- **main.py** = Use this every day to process PDFs
- **test_all.py** = Use this to validate before & after changes
- **agent1.py** = Reference only, don't run or edit
