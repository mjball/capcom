#!/usr/bin/env python3
"""Inspect and render the two binary STL parts of the 52 mm flip lens cap."""

from __future__ import annotations

import json
import os
import struct
import tempfile
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "outputs" / "thingiverse_656038"
OUTPUT.mkdir(parents=True, exist_ok=True)

MPL_CACHE = Path(tempfile.gettempdir()) / "lens-cap-stl-matplotlib-cache"
MPL_CACHE.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPL_CACHE))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.collections import PolyCollection  # noqa: E402
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # noqa: E402


def read_binary_stl(path: Path) -> tuple[np.ndarray, np.ndarray, str]:
    with path.open("rb") as handle:
        header = handle.read(80).decode("ascii", errors="replace").strip()
        count = struct.unpack("<I", handle.read(4))[0]
        record_dtype = np.dtype(
            [
                ("normal", "<f4", (3,)),
                ("vertices", "<f4", (3, 3)),
                ("attribute", "<u2"),
            ]
        )
        records = np.fromfile(handle, dtype=record_dtype, count=count)
    if len(records) != count:
        raise RuntimeError(f"Expected {count} triangles in {path}, read {len(records)}")
    return (
        records["vertices"].astype(float),
        records["normal"].astype(float),
        header,
    )


def mesh_summary(path: Path, triangles: np.ndarray) -> dict[str, object]:
    vertices = triangles.reshape(-1, 3)
    unique_vertices = np.unique(np.round(vertices, decimals=5), axis=0)
    lower = vertices.min(axis=0)
    upper = vertices.max(axis=0)
    return {
        "file": path.name,
        "triangle_count": int(len(triangles)),
        "unique_vertex_count": int(len(unique_vertices)),
        "bounds_min_mm": lower.tolist(),
        "bounds_max_mm": upper.tolist(),
        "size_xyz_mm": (upper - lower).tolist(),
        "centroid_of_vertices_mm": vertices.mean(axis=0).tolist(),
    }


def equalize_axes(ax, lower: np.ndarray, upper: np.ndarray) -> None:
    center = (lower + upper) / 2.0
    radius = float(np.max(upper - lower)) / 2.0 * 1.04
    ax.set_xlim(center[0] - radius, center[0] + radius)
    ax.set_ylim(center[1] - radius, center[1] + radius)
    ax.set_zlim(center[2] - radius, center[2] + radius)
    ax.set_box_aspect((1, 1, 1))


def render_part(path: Path, triangles: np.ndarray, normals: np.ndarray) -> Path:
    vertices = triangles.reshape(-1, 3)
    lower = vertices.min(axis=0)
    upper = vertices.max(axis=0)
    views = [
        ("Isometric", 24, -58),
        ("Opposite isometric", 24, 122),
        ("Top (XY)", 90, -90),
        ("Bottom (XY)", -90, -90),
        ("Front (XZ)", 0, -90),
        ("Side (YZ)", 0, 0),
    ]

    light = np.array([0.25, -0.45, 0.86])
    light /= np.linalg.norm(light)
    unit_normals = normals / np.maximum(np.linalg.norm(normals, axis=1, keepdims=True), 1e-12)
    intensity = np.clip(0.58 + 0.34 * (unit_normals @ light), 0.22, 0.95)
    base_color = np.array([0.22, 0.55, 0.82])
    face_colors = np.column_stack((intensity[:, None] * base_color, np.ones(len(triangles))))

    fig = plt.figure(figsize=(15, 10), constrained_layout=True)
    fig.suptitle(path.name, fontsize=16, fontweight="bold")
    for index, (title, elev, azim) in enumerate(views, start=1):
        ax = fig.add_subplot(2, 3, index, projection="3d")
        collection = Poly3DCollection(
            triangles,
            facecolors=face_colors,
            edgecolors="none",
            linewidths=0,
            zsort="average",
        )
        ax.add_collection3d(collection)
        equalize_axes(ax, lower, upper)
        ax.view_init(elev=elev, azim=azim)
        ax.set_title(title)
        ax.set_xlabel("X mm")
        ax.set_ylabel("Y mm")
        ax.set_zlabel("Z mm")
        ax.grid(False)
    destination = OUTPUT / f"{path.stem}_views.png"
    fig.savefig(destination, dpi=180)
    plt.close(fig)
    return destination


def render_annotated_parts(meshes: dict[str, np.ndarray]) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(13, 6), constrained_layout=True)
    settings = {
        "Base": {
            "title": "Stationary Base",
            "color": "#52677a",
            "labels": [
                ("52 mm threaded ring", (39, 54.5), (19, 62)),
                ("fixed hinge ears / yoke", (70.5, 28), (52, 8)),
                ("latch eye", (7, 28), (10, 8)),
            ],
        },
        "Cap": {
            "title": "Moving Cap",
            "color": "#2f7fba",
            "labels": [
                ("moving flap", (39, 42), (20, 62)),
                ("central hinge knuckle", (70.5, 28), (48, 8)),
                ("latch tongue", (4, 28), (11, 8)),
            ],
        },
    }
    for ax, (name, triangles) in zip(axes, meshes.items()):
        projected = triangles[:, :, [0, 2]]
        collection = PolyCollection(
            projected,
            facecolors=settings[name]["color"],
            edgecolors="none",
            alpha=0.93,
        )
        ax.add_collection(collection)
        vertices = projected.reshape(-1, 2)
        lower = vertices.min(axis=0)
        upper = vertices.max(axis=0)
        ax.set_xlim(lower[0] - 8, upper[0] + 8)
        ax.set_ylim(lower[1] - 10, upper[1] + 10)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title(settings[name]["title"], fontsize=18, fontweight="bold")
        for text, target, label in settings[name]["labels"]:
            ax.annotate(
                text,
                xy=target,
                xytext=label,
                fontsize=11,
                ha="center",
                va="center",
                arrowprops={"arrowstyle": "->", "lw": 1.4, "color": "#20252a"},
                bbox={"boxstyle": "round,pad=0.25", "fc": "white", "ec": "#aab2b9", "alpha": 0.94},
            )
    fig.suptitle("Thingiverse 656038 — exact 52 mm STL parts", fontsize=16)
    fig.text(
        0.5,
        0.015,
        "Front view. In the installed project orientation, rotate the assembly so the hinge is at the bottom.",
        ha="center",
        fontsize=11,
        color="#3f4750",
    )
    destination = OUTPUT / "52mm_parts_annotated.png"
    fig.savefig(destination, dpi=180, facecolor="white")
    plt.close(fig)
    return destination


def main() -> None:
    paths = [
        ROOT / "52mm_Lens_Cap-Base.STL",
        ROOT / "52mm_Lens_Cap-Cap.STL",
    ]
    report: dict[str, object] = {
        "source": "https://www.thingiverse.com/thing:656038",
        "parts": [],
    }
    renders = []
    meshes: dict[str, np.ndarray] = {}
    for path in paths:
        triangles, normals, header = read_binary_stl(path)
        meshes["Base" if "Base" in path.stem else "Cap"] = triangles
        summary = mesh_summary(path, triangles)
        summary["stl_header"] = header
        report["parts"].append(summary)
        renders.append(str(render_part(path, triangles, normals)))
    renders.append(str(render_annotated_parts(meshes)))
    report["renders"] = renders
    destination = OUTPUT / "mesh_report.json"
    destination.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
