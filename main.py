# main.py
# PURPOSE: Full end-to-end pipeline orchestrator
# Runs all 6 steps: PDF extraction → OCR → LLM → JSON → DXF → IFC
# USAGE: python main.py <pdf_file_path>

import os
import sys
import json
from datetime import datetime

# Import all pipeline modules
from step1_pdf_extraction import extract_text_from_pdf, is_text_sufficient
from step2_ocr import ocr_pdf_pages
from step3_llm import extract_specs_with_llm
from step4_json import save_specs_to_json, load_specs_from_json, print_specs_table
from step5_dxf import generate_dxf_from_specs
from step6_ifc import generate_ifc_from_specs


def ensure_directories():
    """Create necessary directories for pipeline."""
    os.makedirs("input", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    os.makedirs("output/logs", exist_ok=True)


def log_step(step_num, step_name, message):
    """Print formatted step information."""
    print(f"\n{'='*60}")
    print(f"STEP {step_num}: {step_name}")
    print(f"{'='*60}")
    print(message)


def run_pipeline(pdf_path, output_prefix="output/result"):
    """
    MAIN PIPELINE: Execute all 6 steps on a PDF document.
    
    INPUT:  pdf_path (str)        → path to the PDF file to process
            output_prefix (str)   → output file prefix (without extension)
    
    OUTPUT: dict → final results with paths to all generated files
    """

    results = {
        "timestamp": datetime.now().isoformat(),
        "pdf_input": pdf_path,
        "files_generated": {}
    }

    try:
        # ── STEP 1: PDF TEXT EXTRACTION ──────────────────────────────
        log_step(1, "PDF TEXT EXTRACTION", 
                 f"Extracting text from: {pdf_path}")
        
        text_extracted = extract_text_from_pdf(pdf_path)
        char_count = len(text_extracted)
        
        print(f"✓ Extracted {char_count} characters")
        print(f"  First 200 chars: {text_extracted[:200]}...")
        
        results["step1_chars_extracted"] = char_count
        

        # ── STEP 2: OCR FOR SCANNED PAGES ────────────────────────────
        if not is_text_sufficient(text_extracted):
            log_step(2, "OCR PROCESSING", 
                     "PDF contains scanned pages, running OCR...")
            
            ocr_text = ocr_pdf_pages(pdf_path)
            ocr_char_count = len(ocr_text)
            print(f"✓ OCR extracted {ocr_char_count} characters")
            
            # Combine digital and scanned text
            text_extracted = text_extracted + "\n\n[OCR RESULTS]\n" + ocr_text
            results["step2_ocr_chars"] = ocr_char_count
        else:
            log_step(2, "OCR PROCESSING", 
                     "PDF is fully digital (no OCR needed)")
            results["step2_ocr_needed"] = False
        

        # ── STEP 3: LLM SPECIFICATION EXTRACTION ─────────────────────
        log_step(3, "LLM SPECIFICATION EXTRACTION", 
                 f"Sending {len(text_extracted)} chars to Mistral LLM...")
        
        specs = extract_specs_with_llm(text_extracted)
        print(f"✓ Extracted {len(specs)} specification fields")
        
        results["step3_specs_count"] = len(specs)
        results["step3_specs"] = specs
        

        # ── STEP 4: SAVE SPECIFICATIONS AS JSON ──────────────────────
        log_step(4, "JSON EXPORT", 
                 f"Saving specifications to JSON...")
        
        json_path = f"{output_prefix}_specs.json"
        save_specs_to_json(specs, json_path)
        print(f"✓ Saved: {json_path}")
        
        results["files_generated"]["json"] = json_path
        

        # Display extracted specs
        print("\nExtracted Specifications:")
        print_specs_table(specs)
        

        # ── STEP 5: GENERATE 2D CAD DRAWING (DXF) ───────────────────
        log_step(5, "2D CAD GENERATION (DXF)", 
                 "Generating 2D engineering drawing...")
        
        dxf_path = f"{output_prefix}_drawing.dxf"
        generate_dxf_from_specs(specs, dxf_path)
        print(f"✓ Generated: {dxf_path}")
        
        file_size = os.path.getsize(dxf_path)
        print(f"  File size: {file_size:,} bytes")
        
        results["files_generated"]["dxf"] = dxf_path
        

        # ── STEP 6: GENERATE 3D BIM MODEL (IFC) ─────────────────────
        log_step(6, "3D BIM MODEL GENERATION (IFC)", 
                 "Generating 3D parametric model...")
        
        ifc_path = f"{output_prefix}_model.ifc"
        generate_ifc_from_specs(specs, ifc_path)
        print(f"✓ Generated: {ifc_path}")
        
        file_size = os.path.getsize(ifc_path)
        print(f"  File size: {file_size:,} bytes")
        
        results["files_generated"]["ifc"] = ifc_path
        

        # ── FINAL SUMMARY ────────────────────────────────────────────
        log_step(0, "PIPELINE COMPLETE", "All steps executed successfully!")
        
        print("\nGenerated Files:")
        for file_type, file_path in results["files_generated"].items():
            print(f"  • {file_type.upper():4s} → {file_path}")
        
        print("\nViewing Options:")
        print("  DXF (2D):  LibreCAD, FreeCAD, AutoCAD, or upload to sharecad.org")
        print("  IFC (3D):  FreeCAD, BIM Vision, Blender, BIM Track online")
        
        return results

    except Exception as e:
        print(f"\n✗ ERROR: {type(e).__name__}: {e}")
        results["error"] = str(e)
        return results


def main():
    """
    Command-line interface for the pipeline.
    
    USAGE:
        python main.py <pdf_file>              # Process a PDF
        python main.py test                    # Run with sample data
    """

    print("\n" + "="*60)
    print("  INDUSTRIAL EXTRACTION & CAD PIPELINE")
    print("  PDF → Text → LLM → JSON → DXF & IFC")
    print("="*60)
    
    ensure_directories()
    
    # Parse command-line arguments
    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  python main.py <pdf_file>   - Process a PDF file")
        print("  python main.py test          - Run with sample data")
        sys.exit(1)
    
    argument = sys.argv[1]
    
    # Handle "test" mode with sample data
    if argument.lower() == "test":
        print("\nRunning in TEST MODE with sample data...\n")
        
        # Create sample PDF input for testing
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
        - Connexion: Brides PN40 (EN1092-1)
        - Norme applicable: EN558 / ISO 5211
        """
        
        # For test mode, manually create specs (skip PDF/OCR/LLM)
        test_specs = {
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
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "mode": "test",
            "step3_specs": test_specs,
            "files_generated": {}
        }
        
        log_step(4, "JSON EXPORT", "Saving test specifications...")
        json_path = "output/test_specs.json"
        save_specs_to_json(test_specs, json_path)
        print(f"✓ Saved: {json_path}")
        results["files_generated"]["json"] = json_path
        
        log_step(5, "2D CAD GENERATION", "Generating test DXF...")
        dxf_path = "output/test_draw.dxf"
        generate_dxf_from_specs(test_specs, dxf_path)
        print(f"✓ Generated: {dxf_path}")
        results["files_generated"]["dxf"] = dxf_path
        
        log_step(6, "3D BIM GENERATION", "Generating test IFC...")
        ifc_path = "output/test_model.ifc"
        generate_ifc_from_specs(test_specs, ifc_path)
        print(f"✓ Generated: {ifc_path}")
        results["files_generated"]["ifc"] = ifc_path
        
        print("\n✓ TEST MODE COMPLETE")
        print("\nGenerated Files:")
        for file_type, file_path in results["files_generated"].items():
            print(f"  • {file_type.upper():4s} → {file_path}")
        
        return
    
    # Handle normal PDF processing
    pdf_file = argument
    
    if not os.path.exists(pdf_file):
        print(f"\n✗ ERROR: File not found: {pdf_file}")
        sys.exit(1)
    
    if not pdf_file.lower().endswith('.pdf'):
        print(f"\n✗ ERROR: File is not a PDF: {pdf_file}")
        sys.exit(1)
    
    # Run the full pipeline
    output_prefix = os.path.splitext(os.path.basename(pdf_file))[0]
    output_prefix = f"output/{output_prefix}"
    
    results = run_pipeline(pdf_file, output_prefix)
    
    # Save results summary
    results_file = f"{output_prefix}_results.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to: {results_file}")


if __name__ == "__main__":
    main()
