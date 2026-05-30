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
