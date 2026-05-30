# QUICK START GUIDE

## 🎯 THE 3 FILES AT A GLANCE

```
┌─────────────────────────────────────────────────────────────┐
│ FILE 7: main.py                                            │
│ ═══════════════════════════════════════════════════════    │
│ WHAT:    Command-line tool that runs the full pipeline     │
│ WHO:     Use this if you want to process PDFs              │
│ WHEN:    Every day - this is your main working tool        │
│ HOW:     python main.py <your_file.pdf>                    │
│ OUTPUT:  • JSON file with extracted specs                  │
│          • 2D DXF drawing (AutoCAD format)                 │
│          • 3D IFC model (BIM format)                       │
│                                                             │
│ Example: python main.py input/valve_technical_spec.pdf     │
│                                                             │
│ Returns: 3 files ready to open in CAD software             │
└─────────────────────────────────────────────────────────────┘
```

```
┌─────────────────────────────────────────────────────────────┐
│ FILE 8: test_all.py                                        │
│ ═══════════════════════════════════════════════════════    │
│ WHAT:    Automated testing suite (19 tests)                │
│ WHO:     Use this to verify everything is working          │
│ WHEN:    • After first setup                               │
│          • Before processing important PDFs                │
│          • After adding new code                           │
│ HOW:     python test_all.py                                │
│ OUTPUT:  • List of all test results                        │
│          • Pass/fail count                                 │
│          • Detailed error messages (if any)                │
│                                                             │
│ Example: python test_all.py                                │
│                                                             │
│ Returns: "✓✓✓ ALL TESTS PASSED" = Ready to go            │
│          "✗✗✗ 3 TEST(S) FAILED" = Fix these first         │
└─────────────────────────────────────────────────────────────┘
```

```
┌─────────────────────────────────────────────────────────────┐
│ FILE 9: agent1.py                                          │
│ ═══════════════════════════════════════════════════════    │
│ WHAT:    Archive of the original monolithic code           │
│ WHO:     Developers & researchers (reference only)         │
│ WHEN:    • Understanding how code was originally written   │
│          • Documenting changes made                        │
│          • Debugging unusual issues                        │
│ HOW:     Don't run it. Just read the code.                 │
│          atom agent1.py  (or any text editor)              │
│ OUTPUT:  None. This is read-only reference.                │
│                                                             │
│ Example: For learning / documentation only                 │
│                                                             │
│ Returns: Understanding of legacy code structure            │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 REAL-WORLD SCENARIOS

### SCENARIO 1: First Time You're Using This Pipeline

**Goal:** Make sure everything is installed and working

**Steps:**
```bash
# Step 1: Run tests
$ python test_all.py

# Output you'll see:
# GROUP 1: LIBRARY IMPORTS
# ✓ PASS: pdfplumber library
# ✓ PASS: requests library
# ✓ PASS: ezdxf library
# ✓ PASS: ifcopenshell library
# 
# GROUP 2: PIPELINE MODULE IMPORTS
# ✓ PASS: step1_pdf_extraction module
# ✓ PASS: step2_ocr module
# ✓ PASS: step3_llm module
# ✓ PASS: step4_json module
# ✓ PASS: step5_dxf module
# ✓ PASS: step6_ifc module
# 
# ...more tests...
#
# TEST SUMMARY
# Total tests: 19
# Passed: 19 ✓
# Failed: 0 ✗
#
# ✓✓✓ ALL TESTS PASSED ✓✓✓

# Step 2: Test with sample data
$ python main.py test

# Output you'll see:
# STEP 4: JSON EXPORT
# ✓ Saved: output/test_specs.json
#
# STEP 5: 2D CAD GENERATION (DXF)
# ✓ Generated: output/test_draw.dxf
#
# STEP 6: 3D BIM MODEL GENERATION (IFC)
# ✓ Generated: output/test_model.ifc
#
# ✓ TEST MODE COMPLETE

# Step 3: Verify output files exist
$ ls output/test_*
# output/test_specs.json    (2.5 KB)
# output/test_draw.dxf      (18.4 KB)
# output/test_model.ifc     (12.1 KB)

# SUCCESS: System is ready!
```

---

### SCENARIO 2: Process Your First Real PDF

**Goal:** Extract specs from an actual technical document

**Your PDF:** `input/pump_specifications.pdf`

**Steps:**
```bash
# Step 1: Put the PDF in the input folder
$ cp ~/Downloads/pump_specifications.pdf input/

# Step 2: Run the pipeline
$ python main.py input/pump_specifications.pdf

# Output you'll see:
# ============================================================
#   INDUSTRIAL EXTRACTION & CAD PIPELINE
#   PDF → Text → LLM → JSON → DXF & IFC
# ============================================================
#
# ============================================================
# STEP 1: PDF TEXT EXTRACTION
# ============================================================
# Extracting text from: input/pump_specifications.pdf
# ✓ Extracted 8234 characters
#   First 200 chars: POMPE CENTRIFUGE IRRIGATION...
#
# ============================================================
# STEP 2: OCR PROCESSING
# ============================================================
# PDF is fully digital (no OCR needed)
#
# ============================================================
# STEP 3: LLM SPECIFICATION EXTRACTION
# ============================================================
# Building prompt for mistral...
# Prompt length: 8847 characters
# Sending to mistral via Ollama...
# LLM response received in 18.3 seconds
# Parsing LLM response...
# Successfully extracted 15 specification fields
#
# ============================================================
# STEP 4: JSON EXPORT
# ============================================================
# Saving specifications to JSON...
#   JSON saved: output/pump_specifications_specs.json (2341 bytes)
#
# Extracted Specifications:
# ==================================================
#   EXTRACTED ENGINEERING SPECIFICATIONS
# ==================================================
#   part_name                  Pompe centrifuge DN80
#   part_number                PC-80-30-316L
#   diameter_mm                80
#   pressure_bar               30
#   material                   Inox_316L
#   length_mm                  180
#   wall_thickness_mm          6
#   tolerance_mm               0.3
#   temperature_max_C          120
#   weight_kg                  8.7
#   standard                   EN733
#   valve_type                 centrifuge
# ==================================================
#
# ============================================================
# STEP 5: 2D CAD GENERATION (DXF)
# ============================================================
# Generating 2D engineering drawing...
#   Drawing front view...
#   Drawing side view...
#   Adding dimension annotations...
#   Adding title block...
#   DXF saved: output/pump_specifications_drawing.dxf (24,521 bytes)
#
# ============================================================
# STEP 6: 3D BIM MODEL GENERATION (IFC)
# ============================================================
# Generating 3D parametric model...
#   Creating IFC project structure...
#   Creating valve element...
#   Adding engineering properties...
#   IFC saved: output/pump_specifications_model.ifc (15,342 bytes)
#
# ============================================================
# PIPELINE COMPLETE
# ============================================================
# All steps executed successfully!
#
# Generated Files:
#   • JSON → output/pump_specifications_specs.json
#   • DXF  → output/pump_specifications_drawing.dxf
#   • IFC  → output/pump_specifications_model.ifc
#
# Viewing Options:
#   DXF (2D):  LibreCAD, FreeCAD, AutoCAD, or upload to sharecad.org
#   IFC (3D):  FreeCAD, BIM Vision, Blender, BIM Track online
#
# Results saved to: output/pump_specifications_results.json

# Step 3: Open the generated files
$ # Open with FreeCAD
$ freecad output/pump_specifications_drawing.dxf
$ freecad output/pump_specifications_model.ifc

# SUCCESS: You now have 2D drawing + 3D model!
```

---

### SCENARIO 3: Something's Not Working

**Goal:** Debug what went wrong

**Steps:**
```bash
# Step 1: Run the test suite to find the problem
$ python test_all.py

# Output shows:
# GROUP 5: CAD FILE GENERATION
# ✗ ERROR: DXF generation from specs
#   Error: ModuleNotFoundError: No module named 'ezdxf'

# DIAGNOSIS: ezdxf is not installed

# Step 2: Fix the problem
$ pip install ezdxf

# Step 3: Verify fix
$ python test_all.py

# Output shows:
# GROUP 5: CAD FILE GENERATION
# ✓ PASS: DXF generation from specs
# 
# ✓✓✓ ALL TESTS PASSED ✓✓✓

# SUCCESS: Problem solved!

# Step 4: Try again
$ python main.py input/pump_specifications.pdf
# (now works!)
```

---

### SCENARIO 4: You Want to Understand the Code

**Goal:** Learn how the system works

**Steps:**
```bash
# Step 1: Read the architecture overview
$ cat ARCHITECTURE.md

# Step 2: Read the utility explanation
$ cat UTILITY_EXPLANATION.md

# Step 3: Look at the old monolithic code (for reference)
$ less agent1.py
# (shows all 6 steps merged - understand why we refactored)

# Step 4: Read individual step files
$ cat step1_pdf_extraction.py     # Simple text extraction
$ cat step3_llm.py                # More complex LLM interaction
$ cat step5_dxf.py                # CAD drawing code

# Step 5: Understand the orchestrator
$ cat main.py                     # Shows how it all connects

# SUCCESS: You understand the entire system!
```

---

### SCENARIO 5: You Want to Modify the Code

**Goal:** Change how the PDF extraction works

**Steps:**
```bash
# Step 1: Edit only the file you need to change
$ vim step1_pdf_extraction.py
# (make your changes)

# Step 2: Test just that step
$ python step1_pdf_extraction.py
# (runs the built-in test for step 1)

# Step 3: Run full test suite
$ python test_all.py
# (verifies nothing else broke)

# Step 4: Test with real PDF
$ python main.py input/pump_specifications.pdf
# (verify everything still works end-to-end)

# SUCCESS: Your changes work!
```

---

## ✅ DECISION FLOWCHART

```
I need to...

    ├─ Process a PDF?
    │  └─ → python main.py input/file.pdf
    │
    ├─ Verify everything works?
    │  └─ → python test_all.py
    │
    ├─ Test with sample data?
    │  └─ → python main.py test
    │
    ├─ Debug a problem?
    │  ├─ Run: python test_all.py
    │  └─ Read the error message
    │
    ├─ Understand how it works?
    │  ├─ Read: ARCHITECTURE.md
    │  ├─ Read: UTILITY_EXPLANATION.md
    │  └─ Read: agent1.py (reference)
    │
    ├─ Modify one step?
    │  ├─ Edit: step1,2,3,4,5, or 6 .py file
    │  ├─ Test: python <that_file>.py
    │  ├─ Validate: python test_all.py
    │  └─ Integration: python main.py test
    │
    ├─ Add a new feature?
    │  ├─ Create: new_step_X.py
    │  ├─ Import in: main.py
    │  ├─ Add test in: test_all.py
    │  └─ Verify: python test_all.py
    │
    └─ Something else?
       └─ Check the documentation files
```

---

## 📊 COMPARISON TABLE

| Task | Use This | Time | Difficulty |
|------|----------|------|------------|
| Process PDF | main.py | 5 min* | ⭐ Easy |
| Test system | test_all.py | 30 sec | ⭐ Easy |
| Understand code | ARCHITECTURE.md + agent1.py | 20 min | ⭐⭐ Medium |
| Debug error | test_all.py + read error | 10 min | ⭐⭐ Medium |
| Modify code | Edit step file + test_all.py | 30 min | ⭐⭐⭐ Hard |
| Add feature | Create new file + integrate | 1+ hour | ⭐⭐⭐ Hard |

*Excluding LLM response time (typically 15-30 seconds spent waiting for Ollama)

---

## 🎓 LEARNING PATH

```
Beginner
├─ Just want to process PDFs?
│  └─ → Learn: main.py only
│  └─ → Learn: How to use command-line
│
Intermediate
├─ Want to understand the system?
│  ├─ → Learn: ARCHITECTURE.md
│  ├─ → Learn: UTILITY_EXPLANATION.md
│  ├─ → Learn: How test_all.py works
│  └─ → Study: main.py
│
Advanced
├─ Want to modify/extend the system?
│  ├─ → Study: All 6 step files
│  ├─ → Study: agent1.py (original design)
│  ├─ → Understand: Dependency graph
│  └─ → Learn: How to write test cases
│
Expert
└─ Want to redesign the entire system?
   ├─ → Understand: All files
   ├─ → Optimize: Performance bottlenecks
   ├─ → Refactor: For modularity
   └─ → Document: Your changes
```
