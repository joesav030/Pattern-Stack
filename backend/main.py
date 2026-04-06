"""
STL Generator API — FastAPI backend
"""

import io
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from generators import search_objects, list_all_objects, generate_stl

app = FastAPI(title="STL Generator API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/objects")
def get_all_objects():
    """Return the full list of supported objects."""
    return list_all_objects()


@app.get("/api/search")
def search(q: str = ""):
    """Search for objects by name or keyword."""
    if not q.strip():
        return list_all_objects()
    return search_objects(q)


@app.get("/api/generate/{object_id}")
def generate(object_id: str):
    """Generate and return an STL file for the given object."""
    stl_bytes = generate_stl(object_id)
    if stl_bytes is None:
        raise HTTPException(status_code=404, detail=f"Object '{object_id}' not found")
    return StreamingResponse(
        io.BytesIO(stl_bytes),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{object_id}.stl"',
            "Content-Length": str(len(stl_bytes)),
        },
    )
