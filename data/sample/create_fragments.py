"""
Realistic synthetic pottery fragment generator for pipeline testing.

Simulates a broken pottery vessel by:
  1. Drawing a deformed ellipse (the vessel silhouette) filled with a
     clay-like texture (brown gradient + Perlin-like noise).
  2. Generating irregular fracture lines using biased random walks across
     the silhouette.
  3. Extracting each resulting shard as a separate white-background image.

The fragment images look appreciably more like real sherds than geometric
pie slices, and the matching fracture edges are geometrically complementary,
making them suitable for testing the full reconstruction pipeline.

Run from the project root:
    python data/sample/create_fragments.py
"""

import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
N_FRAGMENTS = 5
IMAGE_SIZE = 500
RANDOM_SEED = 7

# Vessel shape parameters
VESSEL_RX = 165          # base semi-axis x
VESSEL_RY = 140          # base semi-axis y
BOUNDARY_NOISE = 12      # amplitude of deformation on vessel boundary
BOUNDARY_STEPS = 200     # resolution of the boundary polygon

# Texture parameters
CLAY_BASE = (105, 80, 58)   # dark clay brown (R, G, B)
CLAY_LIGHT = (175, 145, 108)
TEXTURE_SCALE = 40           # spatial frequency of the grain noise


def make_noise_field(size: int, scale: int, seed: int) -> np.ndarray:
    """Generate a smooth 2-D noise field via blurred random values."""
    rng = np.random.default_rng(seed)
    small = rng.random((size // scale + 2, size // scale + 2)).astype(np.float32)
    large = np.kron(small, np.ones((scale, scale), dtype=np.float32))
    large = large[:size, :size]
    # Multi-pass Gaussian blur to smooth the noise
    from PIL import Image as _Image, ImageFilter as _IF
    pil = _Image.fromarray((large * 255).astype(np.uint8))
    pil = pil.filter(_IF.GaussianBlur(radius=scale * 0.6))
    return np.array(pil).astype(np.float32) / 255.0


def build_vessel_polygon(
    center: tuple,
    rx: float,
    ry: float,
    n_steps: int,
    noise_amp: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """
    Generate a closed polygon approximating a deformed pottery ellipse.

    Radii are perturbed with smooth noise to produce an organic silhouette
    rather than a perfect ellipse.
    """
    angles = np.linspace(0, 2 * math.pi, n_steps, endpoint=False)
    # Low-frequency perturbation of the radius
    perturbation = rng.uniform(-noise_amp, noise_amp, n_steps)
    # Smooth perturbation with a simple moving average
    window = max(1, n_steps // 20)
    kernel = np.ones(window) / window
    perturbation = np.convolve(perturbation, kernel, mode='same')

    cx, cy = center
    points = []
    for i, angle in enumerate(angles):
        r_x = rx + perturbation[i]
        r_y = ry + perturbation[i] * (ry / rx)
        x = cx + r_x * math.cos(angle)
        y = cy + r_y * math.sin(angle)
        points.append((x, y))
    return np.array(points, dtype=np.float32)


def build_clay_texture(size: int, rng: np.random.Generator) -> np.ndarray:
    """
    Create an RGB array with a clay-like appearance.

    Blends two clay colours using a smooth noise field to simulate
    the uneven surface colour of fired pottery.
    """
    noise = make_noise_field(size, TEXTURE_SCALE, int(rng.integers(0, 9999)))
    base = np.array(CLAY_BASE, dtype=np.float32)
    light = np.array(CLAY_LIGHT, dtype=np.float32)

    noise_3d = noise[:, :, np.newaxis]
    texture = base + noise_3d * (light - base)
    return np.clip(texture, 0, 255).astype(np.uint8)


def random_walk_cut(
    start: np.ndarray,
    end: np.ndarray,
    n_steps: int,
    jitter: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """
    Generate an irregular fracture path from start to end via biased random walk.

    At each step the walker moves predominantly toward end with a random
    lateral deflection, simulating how brittle ceramic fractures propagate.
    """
    path = [start.copy()]
    current = start.astype(float)
    target = end.astype(float)
    direction = target - current
    perp = np.array([-direction[1], direction[0]])
    perp_norm = np.linalg.norm(perp)
    if perp_norm > 0:
        perp /= perp_norm

    for step_idx in range(1, n_steps):
        frac = step_idx / n_steps
        # Lerp toward end + lateral jitter
        lateral = rng.uniform(-jitter, jitter)
        next_pt = start + frac * direction + lateral * perp
        current = next_pt
        path.append(current.copy())

    path.append(end.astype(float))
    return np.array(path, dtype=np.float32)


def polygon_contains(polygon: np.ndarray, point: np.ndarray) -> bool:
    """Test whether a 2-D point lies inside a polygon (ray-casting method)."""
    x, y = float(point[0]), float(point[1])
    inside = False
    n = len(polygon)
    j = n - 1
    for i in range(n):
        xi, yi = float(polygon[i][0]), float(polygon[i][1])
        xj, yj = float(polygon[j][0]), float(polygon[j][1])
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi):
            inside = not inside
        j = i
    return inside


def generate_cut_endpoints(
    vessel: np.ndarray,
    n_cuts: int,
    rng: np.random.Generator,
) -> list:
    """
    Sample n_cuts pairs of boundary points to use as fracture endpoints.

    Each cut connects two roughly opposite points on the vessel boundary,
    dividing it into distinct regions.
    """
    n = len(vessel)
    cuts = []
    for _ in range(n_cuts):
        idx_a = rng.integers(0, n)
        # Opposite point: roughly π apart in index space
        offset = n // 2 + int(rng.integers(-n // 8, n // 8))
        idx_b = (idx_a + offset) % n
        cuts.append((vessel[idx_a], vessel[idx_b]))
    return cuts


def apply_cuts_to_mask(
    mask: np.ndarray,
    cuts: list,
    rng: np.random.Generator,
    line_thickness: int = 2,
) -> np.ndarray:
    """
    Draw fracture cuts onto the binary vessel mask and label connected regions.

    Each cut line is drawn in black, which separates the mask into distinct
    connected components. Returns the labelled component image.
    """
    import cv2
    cut_mask = mask.copy()
    for start, end in cuts:
        path = random_walk_cut(start, end, n_steps=60, jitter=12, rng=rng)
        pts = path.astype(np.int32).reshape(-1, 1, 2)
        cv2.polylines(cut_mask, [pts], isClosed=False, color=0,
                      thickness=line_thickness, lineType=cv2.LINE_AA)

    num_labels, labels = cv2.connectedComponents(cut_mask)
    return labels, num_labels


def render_fragment(
    labels: np.ndarray,
    label_id: int,
    texture: np.ndarray,
    image_size: int,
) -> Image.Image:
    """Extract one connected component and render it on a white background."""
    import cv2
    fragment_mask = (labels == label_id).astype(np.uint8) * 255
    # Small cleanup
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    fragment_mask = cv2.morphologyEx(fragment_mask, cv2.MORPH_OPEN, kernel)

    canvas = np.full((image_size, image_size, 3), 255, dtype=np.uint8)
    mask_3d = fragment_mask[:, :, np.newaxis].astype(np.float32) / 255.0
    canvas = (canvas * (1 - mask_3d) + texture * mask_3d).astype(np.uint8)

    img = Image.fromarray(canvas)
    return img.filter(ImageFilter.GaussianBlur(radius=0.5))


def main() -> None:
    import cv2

    rng = np.random.default_rng(RANDOM_SEED)
    center = (IMAGE_SIZE // 2, IMAGE_SIZE // 2)

    vessel_poly = build_vessel_polygon(
        center, VESSEL_RX, VESSEL_RY,
        BOUNDARY_STEPS, BOUNDARY_NOISE, rng,
    )
    texture = build_clay_texture(IMAGE_SIZE, rng)

    # Draw filled vessel mask
    mask_img = Image.new('L', (IMAGE_SIZE, IMAGE_SIZE), 0)
    draw = ImageDraw.Draw(mask_img)
    poly_coords = [(float(p[0]), float(p[1])) for p in vessel_poly]
    draw.polygon(poly_coords, fill=255)
    vessel_mask = np.array(mask_img)

    # Generate fracture cuts (n_cuts = n_fragments - 1)
    cuts = generate_cut_endpoints(vessel_poly, n_cuts=N_FRAGMENTS - 1, rng=rng)
    labels, num_labels = apply_cuts_to_mask(vessel_mask, cuts, rng)

    # Collect significant components (skip background label 0)
    component_sizes = [
        (lbl, int((labels == lbl).sum()))
        for lbl in range(1, num_labels)
    ]
    component_sizes.sort(key=lambda x: x[1], reverse=True)
    top_components = component_sizes[:N_FRAGMENTS]

    print(f"Generating {len(top_components)} fragment images in: {OUTPUT_DIR}")
    saved = 0
    for rank, (label_id, area) in enumerate(top_components):
        if area < 500:
            continue
        img = render_fragment(labels, label_id, texture, IMAGE_SIZE)
        out_path = os.path.join(OUTPUT_DIR, f'fragment_{saved + 1:02d}.png')
        img.save(out_path)
        print(f"  Saved {os.path.basename(out_path)}  (area={area} px)")
        saved += 1

    print(f"\nDone — {saved} fragments saved.")


if __name__ == '__main__':
    main()
