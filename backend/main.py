import os
import cv2
import ezdxf
import numpy as np
import trimesh
import traceback
from shapely.geometry import Polygon, MultiPolygon
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import uuid

app = FastAPI(title="Image to 3D Part API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def image_to_stl(image_path: str, stl_output_path: str):
    """
    Enhanced conversion:
    1. Pre-process with Gaussian Blur and Otsu thresholding.
    2. Use morphological closing to bridge gaps.
    3. Extract contours with hierarchy to support holes.
    4. Smooth and simplify contours.
    5. Extrude and repair mesh for watertightness.
    """
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError("Could not read the image.")

    # Pre-processing for cleaner edges
    blurred = cv2.GaussianBlur(img, (5, 5), 0)
    
    # Using Otsu's thresholding for better black/white separation
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # Closing operation: Dilation followed by Erosion to close small gaps in outlines
    kernel = np.ones((5,5), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=1)
    
    # Extract contours with hierarchy (RETR_CCOMP provides 2 levels: external and holes)
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours or hierarchy is None:
         raise ValueError("No distinct shapes found. Ensure the image has high contrast.")

    hierarchy = hierarchy[0]
    height_img = img.shape[0]
    polygons = []

    for i in range(len(contours)):
        # hierarchy[i][3] == -1 means it's an external contour (no parent)
        if hierarchy[i][3] == -1:
            # Simplify contour to remove noise and jitter
            epsilon = 0.0015 * cv2.arcLength(contours[i], True)
            approx = cv2.approxPolyDP(contours[i], epsilon, True)
            
            if len(approx) < 3:
                continue
            
            # External boundary
            shell = [(p[0][0], height_img - p[0][1]) for p in approx]
            
            # Find holes belonging to this contour
            holes = []
            child_idx = hierarchy[i][2]
            while child_idx != -1:
                # Simplify hole contour
                h_epsilon = 0.0015 * cv2.arcLength(contours[child_idx], True)
                h_approx = cv2.approxPolyDP(contours[child_idx], h_epsilon, True)
                
                if len(h_approx) >= 3:
                    hole_shell = [(p[0][0], height_img - p[0][1]) for p in h_approx]
                    holes.append(hole_shell)
                
                # Next sibling hole
                child_idx = hierarchy[child_idx][0]
            
            try:
                poly = Polygon(shell, holes)
                if not poly.is_valid:
                    poly = poly.buffer(0) # Fix self-intersections
                
                if not poly.is_empty:
                    if poly.geom_type == 'MultiPolygon':
                        polygons.extend(poly.geoms)
                    else:
                        polygons.append(poly)
            except Exception:
                continue

    if not polygons:
        raise ValueError("Failed to create valid geometry from image.")

    # Create 3D mesh - extrude everything as a combined geometry
    mesh = trimesh.creation.extrude_polygon(MultiPolygon(polygons), height=10.0)
    
    # CRITICAL: Repair mesh for SOLIDWORKS
    mesh.fix_normals()
    mesh.fill_holes()
    trimesh.repair.fix_inversion(mesh)
    trimesh.repair.fix_winding(mesh)

    # Export to STL
    mesh.export(stl_output_path)


@app.post("/api/convert-to-stl")
async def convert_image_to_stl(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File provided is not an image.")

    temp_dir = tempfile.gettempdir()
    unique_id = str(uuid.uuid4())
    img_path = os.path.join(temp_dir, f"{unique_id}_{file.filename}")
    stl_path = os.path.join(temp_dir, f"{unique_id}_engineering_part.stl")

    try:
        content = await file.read()
        with open(img_path, "wb") as f:
            f.write(content)

        image_to_stl(img_path, stl_path)

        return FileResponse(
            path=stl_path,
            filename="engineering_part.stl",
            media_type="application/vnd.ms-pki.stl"
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
