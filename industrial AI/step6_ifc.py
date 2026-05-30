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
    
    OUTPUT: tuple (project, site, building, storey, context) → the created hierarchy objects
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
        products=[site],
        # child objects as a list
        relating_object=project
        # parent
    )

    ifcopenshell.api.run(
        "aggregate.assign_object",
        ifc_file,
        products=[building],
        relating_object=site
    )

    ifcopenshell.api.run(
        "aggregate.assign_object",
        ifc_file,
        products=[storey],
        relating_object=building
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
        products=[element],
        # the valve element as a list
        relating_structure=storey
        # place it in the assembly floor
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
    print("TEST 1: Generating IFC model...")
    ifc_path = generate_ifc_from_specs(sample_specs, "output/test_valve.ifc")
    print(f"  Generated: {ifc_path} ✓")

    # TEST 2: verify file was created
    print("\nTEST 2: Verifying IFC file...")
    if os.path.exists(ifc_path):
        file_size = os.path.getsize(ifc_path)
        print(f"  File exists ✓ ({file_size:,} bytes)")
    else:
        print("  File NOT created ✗")
        exit(1)

    # TEST 3: try to read it back
    print("\nTEST 3: Reading IFC file...")
    try:
        ifc = ifcopenshell.open(ifc_path)
        print(f"  File is valid IFC ✓")
        print(f"  Schema version: {ifc.schema}")
    except Exception as e:
        print(f"  ERROR reading file: {e}")
        exit(1)

    print("\n  TO VIEW THE IFC FILE:")
    print("  Option 1 (free): FreeCAD from https://www.freecadweb.org/")
    print("  Option 2 (free): Blender from https://www.blender.org/")
    print("  Option 3 (online): BIM Track at https://www.bimtrack.co/")
    print(f"\n  File location: {os.path.abspath(ifc_path)}")
