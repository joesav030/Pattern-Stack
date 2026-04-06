"""
STL generators for common 3D-printable objects.
All dimensions are in millimeters.
"""

import numpy as np
import trimesh
import trimesh.creation
from shapely.geometry import Polygon


# ── helpers ──────────────────────────────────────────────────────────────────

def _to_stl_bytes(mesh: trimesh.Trimesh) -> bytes:
    mesh.fix_normals()
    return mesh.export(file_type="stl")


def _star_polygon(points: int = 5, outer_r: float = 20, inner_r: float = 9) -> Polygon:
    angles = np.linspace(0, 2 * np.pi, points * 2, endpoint=False) - np.pi / 2
    radii = np.tile([outer_r, inner_r], points)
    xy = np.column_stack([radii * np.cos(angles), radii * np.sin(angles)])
    return Polygon(xy)


def _gear_polygon(teeth: int = 12, pitch_r: float = 18, tooth_h: float = 4,
                  root_r: float = 14, hub_r: float = 5) -> Polygon:
    outer_r = pitch_r + tooth_h
    angles = np.linspace(0, 2 * np.pi, teeth * 4, endpoint=False)
    pts = []
    for i, a in enumerate(angles):
        q = i % 4
        r = outer_r if q in (1, 2) else root_r
        pts.append((r * np.cos(a), r * np.sin(a)))
    return Polygon(pts)


def _heart_polygon(scale: float = 1.0) -> Polygon:
    t = np.linspace(0, 2 * np.pi, 200)
    x = scale * 16 * np.sin(t) ** 3
    y = scale * (13 * np.cos(t) - 5 * np.cos(2 * t) - 2 * np.cos(3 * t) - np.cos(4 * t))
    return Polygon(np.column_stack([x, y]))


def _arrow_polygon(length: float = 50, shaft_w: float = 10,
                   head_w: float = 24, head_l: float = 22) -> Polygon:
    shaft_l = length - head_l
    hw = shaft_w / 2
    hw2 = head_w / 2
    pts = [
        (0, -hw), (shaft_l, -hw),
        (shaft_l, -hw2), (length, 0),
        (shaft_l, hw2), (shaft_l, hw),
        (0, hw),
    ]
    return Polygon(pts)


def _extrude(polygon: Polygon, height: float) -> trimesh.Trimesh:
    return trimesh.creation.extrude_polygon(polygon, height)


# ── object generators ─────────────────────────────────────────────────────────

def gen_cube() -> bytes:
    return _to_stl_bytes(trimesh.creation.box(extents=[40, 40, 40]))


def gen_box() -> bytes:
    return _to_stl_bytes(trimesh.creation.box(extents=[70, 45, 35]))


def gen_sphere() -> bytes:
    return _to_stl_bytes(trimesh.creation.icosphere(subdivisions=4, radius=25))


def gen_cylinder() -> bytes:
    return _to_stl_bytes(trimesh.creation.cylinder(radius=20, height=50, sections=64))


def gen_cone() -> bytes:
    return _to_stl_bytes(trimesh.creation.cone(radius=22, height=50, sections=64))


def gen_pyramid() -> bytes:
    h, b = 50, 30
    hb = b / 2
    verts = np.array([
        [0,  0,  h],    # apex
        [-hb, -hb, 0],
        [ hb, -hb, 0],
        [ hb,  hb, 0],
        [-hb,  hb, 0],
    ], dtype=float)
    faces = np.array([
        [0, 2, 1], [0, 3, 2], [0, 4, 3], [0, 1, 4],
        [1, 2, 3], [1, 3, 4],
    ])
    return _to_stl_bytes(trimesh.Trimesh(vertices=verts, faces=faces))


def gen_torus() -> bytes:
    return _to_stl_bytes(trimesh.creation.torus(major_radius=25, minor_radius=8))


def gen_ring() -> bytes:
    return _to_stl_bytes(trimesh.creation.torus(major_radius=10, minor_radius=2.5))


def gen_vase() -> bytes:
    # Outer profile revolved around Z axis (r, z)
    profile = np.array([
        [12,  0],
        [16,  6],
        [20, 14],
        [19, 24],
        [13, 38],
        [ 9, 52],
        [11, 60],
        [14, 65],
        [12, 70],
    ], dtype=float)
    mesh = trimesh.creation.revolve(profile, sections=64)
    return _to_stl_bytes(mesh)


def gen_bowl() -> bytes:
    profile = np.array([
        [35,  0],
        [33,  6],
        [28, 14],
        [19, 22],
        [ 8, 28],
        [ 2, 30],
    ], dtype=float)
    mesh = trimesh.creation.revolve(profile, sections=64)
    return _to_stl_bytes(mesh)


def gen_cup() -> bytes:
    # Outer wall profile
    outer = np.array([
        [20,  0],
        [22,  5],
        [23, 30],
        [24, 60],
    ], dtype=float)
    # Inner wall (hollow) – revolve outer, then inner, boolean subtract
    # Simpler: revolve an annular cross-section using annulus helper
    mesh = trimesh.creation.annulus(r_min=20, r_max=24, height=60, sections=64)
    # Add bottom disk
    bottom = trimesh.creation.cylinder(radius=20, height=2, sections=64)
    bottom.apply_translation([0, 0, 1])
    cup = trimesh.util.concatenate([mesh, bottom])
    return _to_stl_bytes(cup)


def gen_pen_holder() -> bytes:
    walls = trimesh.creation.annulus(r_min=22, r_max=26, height=90, sections=64)
    bottom = trimesh.creation.cylinder(radius=22, height=3, sections=64)
    bottom.apply_translation([0, 0, 1.5])
    holder = trimesh.util.concatenate([walls, bottom])
    return _to_stl_bytes(holder)


def gen_phone_stand() -> bytes:
    # Wedge: tall back, short front, tilted platform
    # Base slab
    base = trimesh.creation.box([80, 12, 4])
    base.apply_translation([0, 0, 2])

    # Back support
    back = trimesh.creation.box([80, 4, 60])
    back.apply_translation([0, -4, 30])

    # Angled arm (approximated as a rotated box)
    arm = trimesh.creation.box([80, 38, 4])
    angle = np.radians(30)
    rot = trimesh.transformations.rotation_matrix(angle, [1, 0, 0])
    arm.apply_transform(rot)
    arm.apply_translation([0, 2, 22])

    # Phone slot lip
    lip = trimesh.creation.box([80, 4, 8])
    lip.apply_transform(rot)
    lip.apply_translation([0, 2 + 14, 22 + 7])

    stand = trimesh.util.concatenate([base, back, arm, lip])
    return _to_stl_bytes(stand)


def gen_coaster() -> bytes:
    disk = trimesh.creation.cylinder(radius=45, height=4, sections=128)
    rim = trimesh.creation.annulus(r_min=42, r_max=45, height=8, sections=128)
    coaster = trimesh.util.concatenate([disk, rim])
    return _to_stl_bytes(coaster)


def gen_gear() -> bytes:
    poly = _gear_polygon(teeth=16, pitch_r=22, tooth_h=5, root_r=18, hub_r=6)
    mesh = _extrude(poly, height=8)
    # Center hole
    hole = trimesh.creation.cylinder(radius=6, height=10, sections=32)
    hole.apply_translation([0, 0, -1])
    result = trimesh.boolean.difference([mesh, hole], engine="blender") if False else mesh
    return _to_stl_bytes(mesh)


def gen_hex_nut() -> bytes:
    # Hexagonal prism
    angles = np.linspace(0, 2 * np.pi, 6, endpoint=False) + np.pi / 6
    hex_pts = np.column_stack([20 * np.cos(angles), 20 * np.sin(angles)])
    hex_poly = Polygon(hex_pts)
    mesh = _extrude(hex_poly, height=12)
    return _to_stl_bytes(mesh)


def gen_star() -> bytes:
    poly = _star_polygon(points=5, outer_r=28, inner_r=12)
    return _to_stl_bytes(_extrude(poly, height=8))


def gen_heart() -> bytes:
    poly = _heart_polygon(scale=1.4)
    return _to_stl_bytes(_extrude(poly, height=8))


def gen_arrow() -> bytes:
    poly = _arrow_polygon(length=60, shaft_w=12, head_w=28, head_l=24)
    return _to_stl_bytes(_extrude(poly, height=8))


def gen_pipe() -> bytes:
    return _to_stl_bytes(
        trimesh.creation.annulus(r_min=15, r_max=20, height=80, sections=64)
    )


def gen_hook() -> bytes:
    # Half-torus for the curve
    half_torus = trimesh.creation.torus(major_radius=18, minor_radius=4)
    # Slice to half
    plane_origin = [0, 0, 0]
    plane_normal = [1, 0, 0]
    half = trimesh.intersections.slice_mesh_plane(
        half_torus, plane_normal, plane_origin, cap=True
    )
    # Vertical shaft
    shaft = trimesh.creation.cylinder(radius=4, height=35, sections=32)
    shaft.apply_translation([18, 0, -17.5])
    hook = trimesh.util.concatenate([half, shaft])
    return _to_stl_bytes(hook)


def gen_keychain() -> bytes:
    ring = trimesh.creation.torus(major_radius=14, minor_radius=2.5)
    tag = trimesh.creation.box([30, 20, 4])
    tag.apply_translation([30, 0, 0])
    keychain = trimesh.util.concatenate([ring, tag])
    return _to_stl_bytes(keychain)


def gen_dice() -> bytes:
    return _to_stl_bytes(trimesh.creation.box([35, 35, 35]))


def gen_planter() -> bytes:
    walls = trimesh.creation.annulus(r_min=28, r_max=32, height=50, sections=64)
    bottom = trimesh.creation.cylinder(radius=28, height=3, sections=64)
    bottom.apply_translation([0, 0, 1.5])
    planter = trimesh.util.concatenate([walls, bottom])
    return _to_stl_bytes(planter)


# ── registry ──────────────────────────────────────────────────────────────────

OBJECTS = {
    "cube": {
        "label": "Cube",
        "description": "Perfect 40 mm cube",
        "tags": ["box", "square", "basic", "simple"],
        "generator": gen_cube,
    },
    "box": {
        "label": "Rectangular Box",
        "description": "70 × 45 × 35 mm storage box",
        "tags": ["container", "storage", "rectangular", "case"],
        "generator": gen_box,
    },
    "sphere": {
        "label": "Sphere",
        "description": "Smooth 25 mm radius ball",
        "tags": ["ball", "round", "globe", "orb"],
        "generator": gen_sphere,
    },
    "cylinder": {
        "label": "Cylinder",
        "description": "Round cylinder (r=20 mm, h=50 mm)",
        "tags": ["tube", "round", "pillar", "column"],
        "generator": gen_cylinder,
    },
    "cone": {
        "label": "Cone",
        "description": "Cone (r=22 mm, h=50 mm)",
        "tags": ["triangle", "pointy", "funnel"],
        "generator": gen_cone,
    },
    "pyramid": {
        "label": "Pyramid",
        "description": "Square-base pyramid (30 × 30 × 50 mm)",
        "tags": ["triangle", "pointy", "egypt", "tetrahedron"],
        "generator": gen_pyramid,
    },
    "torus": {
        "label": "Torus",
        "description": "Donut shape (major r=25, minor r=8 mm)",
        "tags": ["donut", "ring", "loop", "circle"],
        "generator": gen_torus,
    },
    "ring": {
        "label": "Ring",
        "description": "Slim jewelry-style ring (r=10 mm)",
        "tags": ["jewelry", "band", "circle", "loop"],
        "generator": gen_ring,
    },
    "vase": {
        "label": "Vase",
        "description": "Decorative curved vase (h=70 mm)",
        "tags": ["flower", "pot", "jar", "decorative"],
        "generator": gen_vase,
    },
    "bowl": {
        "label": "Bowl",
        "description": "Hemispherical bowl (r=35 mm)",
        "tags": ["dish", "cup", "container", "food"],
        "generator": gen_bowl,
    },
    "cup": {
        "label": "Cup",
        "description": "Simple open cup (r=24 mm, h=60 mm)",
        "tags": ["mug", "drink", "container", "glass"],
        "generator": gen_cup,
    },
    "pen_holder": {
        "label": "Pen Holder",
        "description": "Desktop pen/pencil holder (h=90 mm)",
        "tags": ["pencil", "desk", "organizer", "stationery"],
        "generator": gen_pen_holder,
    },
    "phone_stand": {
        "label": "Phone Stand",
        "description": "Angled phone / tablet stand",
        "tags": ["phone", "mobile", "tablet", "desk", "holder"],
        "generator": gen_phone_stand,
    },
    "coaster": {
        "label": "Coaster",
        "description": "Round coaster with rim (r=45 mm)",
        "tags": ["drink", "table", "flat", "disk"],
        "generator": gen_coaster,
    },
    "gear": {
        "label": "Gear",
        "description": "16-tooth spur gear",
        "tags": ["cog", "machine", "mechanical", "teeth"],
        "generator": gen_gear,
    },
    "hex_nut": {
        "label": "Hex Nut",
        "description": "Hexagonal nut (across-flats=40 mm)",
        "tags": ["bolt", "hardware", "hex", "fastener", "nut"],
        "generator": gen_hex_nut,
    },
    "star": {
        "label": "Star",
        "description": "5-pointed star (h=8 mm)",
        "tags": ["shape", "decoration", "five", "point"],
        "generator": gen_star,
    },
    "heart": {
        "label": "Heart",
        "description": "Heart shape (h=8 mm)",
        "tags": ["love", "valentine", "decoration", "romantic"],
        "generator": gen_heart,
    },
    "arrow": {
        "label": "Arrow",
        "description": "Directional arrow (60 × 28 × 8 mm)",
        "tags": ["direction", "pointer", "sign"],
        "generator": gen_arrow,
    },
    "pipe": {
        "label": "Pipe",
        "description": "Hollow pipe / tube (h=80 mm)",
        "tags": ["tube", "hollow", "channel", "cylinder"],
        "generator": gen_pipe,
    },
    "hook": {
        "label": "Hook",
        "description": "Wall hook for hanging items",
        "tags": ["hanger", "hang", "wall", "coat", "key"],
        "generator": gen_hook,
    },
    "keychain": {
        "label": "Keychain",
        "description": "Keychain ring with flat tag",
        "tags": ["key", "ring", "tag", "accessory"],
        "generator": gen_keychain,
    },
    "dice": {
        "label": "Dice",
        "description": "Six-sided die (35 mm)",
        "tags": ["game", "d6", "cube", "random"],
        "generator": gen_dice,
    },
    "planter": {
        "label": "Mini Planter",
        "description": "Small plant pot (r=32 mm, h=50 mm)",
        "tags": ["plant", "pot", "flower", "succulent", "garden"],
        "generator": gen_planter,
    },
}


def search_objects(query: str) -> list[dict]:
    q = query.lower().strip()
    results = []
    for key, obj in OBJECTS.items():
        score = 0
        if q in key:
            score += 3
        if q in obj["label"].lower():
            score += 3
        if q in obj["description"].lower():
            score += 1
        for tag in obj["tags"]:
            if q in tag:
                score += 2
        if score > 0:
            results.append({
                "id": key,
                "label": obj["label"],
                "description": obj["description"],
                "score": score,
            })
    results.sort(key=lambda x: -x["score"])
    return results


def list_all_objects() -> list[dict]:
    return [
        {"id": key, "label": obj["label"], "description": obj["description"]}
        for key, obj in OBJECTS.items()
    ]


def generate_stl(object_id: str) -> bytes | None:
    obj = OBJECTS.get(object_id)
    if obj is None:
        return None
    return obj["generator"]()
