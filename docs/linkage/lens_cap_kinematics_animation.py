#!/usr/bin/env python3
"""Generate and verify the servo-driven lens-cap four-bar animation."""

from __future__ import annotations

import json
import math
import os
import tempfile
from pathlib import Path

import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = SCRIPT_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Keep Matplotlib's runtime cache in a writable temporary location.
MPL_CACHE = Path(tempfile.gettempdir()) / "lens-cap-matplotlib-cache"
MPL_CACHE.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPL_CACHE))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.animation import FuncAnimation, PillowWriter  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Arc, Ellipse, FancyBboxPatch, Patch, Polygon, Rectangle  # noqa: E402


# Dimensionally exact four-bar inputs, in millimetres and degrees.
SERVO_PIVOT = np.array([-31.0, -13.0])
HINGE_PIVOT = np.array([0.0, 0.0])
SERVO_HORN = 15.0
CAP_LEVER = 15.0
CONNECTING_ROD = 35.016
SERVO_TRAVEL_DEG = -155.0  # Clockwise in this side view.
CAP_TRAVEL_DEG = -135.0
CAP_DIAMETER = 52.0

# The existing cap is mounted with its hinge at the lower edge of the lens.
# In the closed position the cap therefore extends upward from the hinge; its
# clockwise opening sweep carries it forward and down, away from the barrel.
CAP_BODY_LOCAL = np.array(
    [
        [0.8, 0.6],
        [4.2, 0.6],
        [4.2, CAP_DIAMETER],
        [0.8, CAP_DIAMETER],
    ]
)
LENS_BARREL_POLYGON = np.array(
    [
        [-66.0, 0.0],
        [0.0, 0.0],
        [0.0, CAP_DIAMETER],
        [-66.0, CAP_DIAMETER],
    ]
)

# Conservative side-view envelope around the SER0049 axis. The linkage/horn
# sits in the parallel plane immediately in front of this stationary body.
SERVO_BODY_WIDTH = 32.5
SERVO_BODY_HEIGHT = 23.0
SERVO_BODY_POLYGON = np.array(
    [
        SERVO_PIVOT + [-SERVO_BODY_WIDTH / 2, -SERVO_BODY_HEIGHT / 2],
        SERVO_PIVOT + [SERVO_BODY_WIDTH / 2, -SERVO_BODY_HEIGHT / 2],
        SERVO_PIVOT + [SERVO_BODY_WIDTH / 2, SERVO_BODY_HEIGHT / 2],
        SERVO_PIVOT + [-SERVO_BODY_WIDTH / 2, SERVO_BODY_HEIGHT / 2],
    ]
)

GIF_PATH = OUTPUT_DIR / "lens_cap_fourbar_with_lens.gif"
REPORT_PATH = OUTPUT_DIR / "lens_cap_fourbar_verification.json"


def rotation(angle_rad: float) -> np.ndarray:
    """Return the 2D rotation matrix for *angle_rad*."""
    c = math.cos(angle_rad)
    s = math.sin(angle_rad)
    return np.array([[c, -s], [s, c]])


def endpoint_constraint(
    servo_angle: float,
    cap_angle: float,
) -> tuple[float, float, float]:
    """Rod-length residual and its two analytic angle derivatives."""
    servo_pin = SERVO_PIVOT + SERVO_HORN * np.array(
        [math.cos(servo_angle), math.sin(servo_angle)]
    )
    cap_pin = HINGE_PIVOT + CAP_LEVER * np.array(
        [math.cos(cap_angle), math.sin(cap_angle)]
    )
    rod = cap_pin - servo_pin
    d_servo_pin = SERVO_HORN * np.array(
        [-math.sin(servo_angle), math.cos(servo_angle)]
    )
    d_cap_pin = CAP_LEVER * np.array(
        [-math.sin(cap_angle), math.cos(cap_angle)]
    )
    residual = float(rod @ rod - CONNECTING_ROD**2)
    d_servo = float(-2.0 * rod @ d_servo_pin)
    d_cap = float(2.0 * rod @ d_cap_pin)
    return residual, d_servo, d_cap


def solve_start_angles() -> tuple[float, float]:
    """Solve both exact endpoint constraints for the two start angles."""
    servo_delta = math.radians(SERVO_TRAVEL_DEG)
    cap_delta = math.radians(CAP_TRAVEL_DEG)

    # Initial values come from the previously synthesized, rounded design.
    angles = np.radians(np.array([-13.18, -3.31], dtype=float))
    for _ in range(20):
        f0, a0, b0 = endpoint_constraint(angles[0], angles[1])
        f1, a1, b1 = endpoint_constraint(
            angles[0] + servo_delta,
            angles[1] + cap_delta,
        )
        jacobian = np.array([[a0, b0], [a1, b1]])
        step = np.linalg.solve(jacobian, -np.array([f0, f1]))
        angles += step
        if float(np.linalg.norm(step)) < 1e-14:
            break

    residuals = np.array(
        [
            endpoint_constraint(angles[0], angles[1])[0],
            endpoint_constraint(
                angles[0] + servo_delta,
                angles[1] + cap_delta,
            )[0],
        ]
    )
    if float(np.max(np.abs(residuals))) > 1e-9:
        raise RuntimeError(f"Endpoint synthesis did not converge: {residuals}")
    return float(angles[0]), float(angles[1])


def circle_intersections(
    center0: np.ndarray,
    radius0: float,
    center1: np.ndarray,
    radius1: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Return the two intersections of two non-degenerate circles."""
    offset = center1 - center0
    distance = float(np.linalg.norm(offset))
    if distance <= 0.0:
        raise RuntimeError("Coincident circle centres")
    if distance > radius0 + radius1 + 1e-10:
        raise RuntimeError("Linkage circles do not reach")
    if distance < abs(radius0 - radius1) - 1e-10:
        raise RuntimeError("One linkage circle contains the other")

    direction = offset / distance
    along = (radius0**2 - radius1**2 + distance**2) / (2.0 * distance)
    height_sq = max(radius0**2 - along**2, 0.0)
    height = math.sqrt(height_sq)
    midpoint = center0 + along * direction
    perpendicular = np.array([-direction[1], direction[0]])
    return midpoint + height * perpendicular, midpoint - height * perpendicular


def solve_motion(progress: np.ndarray) -> dict[str, np.ndarray | float]:
    """Solve the exact assembly branch at each commanded servo position."""
    servo_start, cap_start = solve_start_angles()
    servo_delta = math.radians(SERVO_TRAVEL_DEG)
    servo_angles = servo_start + progress * servo_delta
    servo_pins = SERVO_PIVOT + SERVO_HORN * np.column_stack(
        (np.cos(servo_angles), np.sin(servo_angles))
    )

    expected_start = HINGE_PIVOT + CAP_LEVER * np.array(
        [math.cos(cap_start), math.sin(cap_start)]
    )
    cap_pins: list[np.ndarray] = []
    previous = expected_start
    for servo_pin in servo_pins:
        candidates = circle_intersections(
            HINGE_PIVOT,
            CAP_LEVER,
            servo_pin,
            CONNECTING_ROD,
        )
        selected = min(candidates, key=lambda point: float(np.linalg.norm(point - previous)))
        cap_pins.append(selected)
        previous = selected

    cap_pins_array = np.array(cap_pins)
    raw_cap_angles = np.arctan2(
        cap_pins_array[:, 1] - HINGE_PIVOT[1],
        cap_pins_array[:, 0] - HINGE_PIVOT[0],
    )
    cap_angles = np.unwrap(raw_cap_angles)

    return {
        "servo_start": servo_start,
        "cap_start": cap_start,
        "servo_angles": servo_angles,
        "cap_angles": cap_angles,
        "servo_pins": servo_pins,
        "cap_pins": cap_pins_array,
    }


def make_frame_schedule() -> tuple[np.ndarray, list[str]]:
    """Build an eased open/close loop with short endpoint dwells."""
    steps = 48
    u = np.linspace(0.0, 1.0, steps + 1)
    eased = 0.5 - 0.5 * np.cos(np.pi * u)

    progress = np.concatenate(
        (
            np.zeros(8),
            eased[1:],
            np.ones(8),
            eased[-2::-1],
            np.zeros(8),
        )
    )
    states = (
        ["CLOSED"] * 8
        + ["OPENING"] * steps
        + ["OPEN"] * 8
        + ["CLOSING"] * steps
        + ["CLOSED"] * 8
    )
    return progress, states


def transform_points(points: np.ndarray, angle: float) -> np.ndarray:
    """Rotate points rigidly around the cap hinge."""
    return HINGE_PIVOT + points @ rotation(angle).T


def convex_polygons_overlap(first: np.ndarray, second: np.ndarray) -> bool:
    """Return True only when two convex polygons have positive-area overlap."""
    for polygon in (first, second):
        edges = np.roll(polygon, -1, axis=0) - polygon
        axes = np.column_stack((-edges[:, 1], edges[:, 0]))
        for axis in axes:
            length = float(np.linalg.norm(axis))
            if length <= 1e-14:
                continue
            unit = axis / length
            first_projection = first @ unit
            second_projection = second @ unit
            if (
                float(np.max(first_projection)) <= float(np.min(second_projection)) + 1e-10
                or float(np.max(second_projection)) <= float(np.min(first_projection)) + 1e-10
            ):
                return False
    return True


def validate_motion(
    motion: dict[str, np.ndarray | float],
    progress: np.ndarray,
) -> dict[str, float | int | bool | list[float]]:
    """Numerically verify every rigid link, pivot, and cap attachment."""
    servo_pins = np.asarray(motion["servo_pins"])
    cap_pins = np.asarray(motion["cap_pins"])
    servo_angles = np.asarray(motion["servo_angles"])
    cap_angles = np.asarray(motion["cap_angles"])
    cap_start = float(motion["cap_start"])

    horn_lengths = np.linalg.norm(servo_pins - SERVO_PIVOT, axis=1)
    cap_lever_lengths = np.linalg.norm(cap_pins - HINGE_PIVOT, axis=1)
    rod_lengths = np.linalg.norm(cap_pins - servo_pins, axis=1)

    initial_cap_pin = HINGE_PIVOT + CAP_LEVER * np.array(
        [math.cos(cap_start), math.sin(cap_start)]
    )
    cap_attachment_from_rigid_rotation = np.array(
        [
            HINGE_PIVOT
            + rotation(angle - cap_start) @ (initial_cap_pin - HINGE_PIVOT)
            for angle in cap_angles
        ]
    )
    attachment_error = np.linalg.norm(
        cap_pins - cap_attachment_from_rigid_rotation,
        axis=1,
    )

    cap_rotations = cap_angles - cap_start
    cap_polygons = np.array(
        [transform_points(CAP_BODY_LOCAL, angle) for angle in cap_rotations]
    )
    initial_cap_edges = np.linalg.norm(
        np.roll(cap_polygons[0], -1, axis=0) - cap_polygons[0],
        axis=1,
    )
    cap_edge_errors = np.array(
        [
            np.max(
                np.abs(
                    np.linalg.norm(np.roll(polygon, -1, axis=0) - polygon, axis=1)
                    - initial_cap_edges
                )
            )
            for polygon in cap_polygons
        ]
    )

    bracket_local = np.array(
        [
            [1.1, 3.5],
            [1.1, 13.0],
            cap_pins[0],
        ]
    )
    bracket_polygons = np.array(
        [transform_points(bracket_local, angle) for angle in cap_rotations]
    )

    cap_lens_collisions = sum(
        convex_polygons_overlap(polygon, LENS_BARREL_POLYGON)
        for polygon in cap_polygons
    )
    cap_servo_collisions = sum(
        convex_polygons_overlap(polygon, SERVO_BODY_POLYGON)
        for polygon in cap_polygons
    )
    bracket_lens_collisions = sum(
        convex_polygons_overlap(polygon, LENS_BARREL_POLYGON)
        for polygon in bracket_polygons
    )
    bracket_servo_collisions = sum(
        convex_polygons_overlap(polygon, SERVO_BODY_POLYGON)
        for polygon in bracket_polygons
    )

    opening_mask = np.isclose(progress, np.maximum.accumulate(progress))
    unique_opening_angles = cap_angles[opening_mask]
    monotonic_opening = bool(np.all(np.diff(unique_opening_angles) <= 1e-10))

    servo_travel = math.degrees(float(servo_angles[np.argmax(progress)] - servo_angles[0]))
    cap_travel = math.degrees(float(cap_angles[np.argmax(progress)] - cap_angles[0]))

    report: dict[str, float | int | bool | list[float]] = {
        "frame_count": int(len(progress)),
        "fixed_servo_pivot_mm": SERVO_PIVOT.tolist(),
        "fixed_cap_hinge_mm": HINGE_PIVOT.tolist(),
        "servo_start_angle_deg": math.degrees(float(motion["servo_start"])),
        "cap_lever_start_angle_deg": math.degrees(cap_start),
        "servo_travel_deg": servo_travel,
        "cap_travel_deg": cap_travel,
        "maximum_servo_horn_length_error_mm": float(
            np.max(np.abs(horn_lengths - SERVO_HORN))
        ),
        "maximum_cap_lever_length_error_mm": float(
            np.max(np.abs(cap_lever_lengths - CAP_LEVER))
        ),
        "maximum_connecting_rod_length_error_mm": float(
            np.max(np.abs(rod_lengths - CONNECTING_ROD))
        ),
        "maximum_cap_attachment_rigidity_error_mm": float(np.max(attachment_error)),
        "maximum_cap_body_edge_length_error_mm": float(np.max(cap_edge_errors)),
        "cap_body_lens_collision_frames": int(cap_lens_collisions),
        "cap_body_servo_collision_frames": int(cap_servo_collisions),
        "cap_bracket_lens_collision_frames": int(bracket_lens_collisions),
        "cap_bracket_servo_collision_frames": int(bracket_servo_collisions),
        "opening_motion_is_monotonic": monotonic_opening,
    }

    tolerances_ok = (
        abs(servo_travel - SERVO_TRAVEL_DEG) < 1e-9
        and abs(cap_travel - CAP_TRAVEL_DEG) < 1e-9
        and report["maximum_servo_horn_length_error_mm"] < 1e-10
        and report["maximum_cap_lever_length_error_mm"] < 1e-10
        and report["maximum_connecting_rod_length_error_mm"] < 1e-10
        and report["maximum_cap_attachment_rigidity_error_mm"] < 1e-10
        and report["maximum_cap_body_edge_length_error_mm"] < 1e-10
        and report["cap_body_lens_collision_frames"] == 0
        and report["cap_body_servo_collision_frames"] == 0
        and report["cap_bracket_lens_collision_frames"] == 0
        and report["cap_bracket_servo_collision_frames"] == 0
        and monotonic_opening
    )
    report["all_checks_passed"] = bool(tolerances_ok)
    if not tolerances_ok:
        raise RuntimeError(f"Kinematic validation failed: {json.dumps(report, indent=2)}")
    return report


def build_animation(
    motion: dict[str, np.ndarray | float],
    progress: np.ndarray,
    states: list[str],
) -> FuncAnimation:
    """Create the engineering-style Matplotlib animation."""
    servo_pins = np.asarray(motion["servo_pins"])
    cap_pins = np.asarray(motion["cap_pins"])
    servo_angles = np.asarray(motion["servo_angles"])
    cap_angles = np.asarray(motion["cap_angles"])
    servo_start = float(motion["servo_start"])
    cap_start = float(motion["cap_start"])

    fig, ax = plt.subplots(figsize=(12.4, 10.2), dpi=100)
    fig.patch.set_facecolor("#f8fafc")
    ax.set_facecolor("#ffffff")

    ax.set_xlim(-72.0, 55.0)
    ax.set_ylim(-43.0, 60.0)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("horizontal position (mm)  ·  lens front is to the right", color="#334155")
    ax.set_ylabel("vertical position (mm)", color="#334155")
    ax.set_xticks(np.arange(-70.0, 51.0, 10.0))
    ax.set_yticks(np.arange(-40.0, 51.0, 10.0))
    ax.grid(which="major", color="#cbd5e1", linewidth=0.8, alpha=0.65)
    ax.tick_params(colors="#475569", labelsize=9)
    for spine in ax.spines.values():
        spine.set_color("#94a3b8")

    fig.suptitle(
        "Servo-driven flip-open lens cap · exact four-bar kinematics",
        x=0.5,
        y=0.975,
        fontsize=16,
        fontweight="semibold",
        color="#0f172a",
    )
    ax.set_title(
        "15.000 mm horn  ·  35.016 mm connecting rod  ·  15.000 mm cap lever  ·  fixed axes Δx = 31 mm, Δy = 13 mm",
        fontsize=10.5,
        color="#475569",
        pad=12,
    )
    ax.text(
        0.018,
        0.975,
        "SIDE VIEW  ·  lower hinge  ·  solids included in clearance check",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=8.5,
        fontweight="semibold",
        color="#475569",
        zorder=8.0,
    )

    # Stationary lens/barrel context. Its 52 mm front diameter comes from the
    # existing flip-open cap; barrel length is intentionally schematic.
    barrel = FancyBboxPatch(
        (-66.0, 0.0),
        66.0,
        52.0,
        boxstyle="round,pad=0,rounding_size=4",
        facecolor="#e2e8f0",
        edgecolor="#64748b",
        linewidth=1.6,
        alpha=0.72,
        zorder=0.4,
    )
    ax.add_patch(barrel)
    ax.add_patch(
        Rectangle(
            (-7.0, 0.0),
            7.0,
            52.0,
            facecolor="#cbd5e1",
            edgecolor="#64748b",
            linewidth=1.2,
            alpha=0.82,
            zorder=0.6,
        )
    )
    ax.add_patch(
        Ellipse(
            (-1.5, 26.0),
            width=5.0,
            height=44.0,
            facecolor="#bae6fd",
            edgecolor="#0284c7",
            linewidth=1.2,
            alpha=0.72,
            zorder=0.8,
        )
    )
    ax.axhline(26.0, color="#0ea5e9", linewidth=0.9, linestyle=(0, (5, 4)), alpha=0.55, zorder=0.9)
    ax.text(
        -63.0,
        4.0,
        "lens barrel (side-view context)",
        color="#475569",
        fontsize=9.5,
        va="bottom",
        zorder=1.0,
    )
    ax.text(
        -10.5,
        24.2,
        "front\nelement",
        color="#0369a1",
        fontsize=8.5,
        ha="center",
        va="bottom",
        zorder=1.0,
    )

    servo_body = Polygon(
        SERVO_BODY_POLYGON,
        closed=True,
        facecolor="#94a3b8",
        edgecolor="#475569",
        linewidth=1.5,
        alpha=0.58,
        zorder=1.3,
    )
    ax.add_patch(servo_body)
    ax.text(
        SERVO_PIVOT[0],
        SERVO_PIVOT[1] + 7.0,
        "SER0049 servo body\n(projected envelope)",
        color="#334155",
        fontsize=8.2,
        ha="center",
        va="center",
        zorder=1.4,
    )

    # Fixed-pivot offsets and swept paths.
    ax.plot(
        [SERVO_PIVOT[0], HINGE_PIVOT[0]],
        [SERVO_PIVOT[1], SERVO_PIVOT[1]],
        color="#64748b",
        linestyle=(0, (2, 3)),
        linewidth=1.1,
        zorder=1.1,
    )
    ax.plot(
        [HINGE_PIVOT[0], HINGE_PIVOT[0]],
        [SERVO_PIVOT[1], HINGE_PIVOT[1]],
        color="#64748b",
        linestyle=(0, (2, 3)),
        linewidth=1.1,
        zorder=1.1,
    )
    ax.text(-15.5, -15.2, "31 mm", color="#475569", fontsize=8.5, ha="center", va="top")
    ax.text(1.4, -6.5, "13 mm", color="#475569", fontsize=8.5, ha="left", va="center", rotation=90)

    ax.add_patch(
        Arc(
            SERVO_PIVOT,
            2 * SERVO_HORN,
            2 * SERVO_HORN,
            theta1=math.degrees(servo_start + math.radians(SERVO_TRAVEL_DEG)),
            theta2=math.degrees(servo_start),
            color="#2563eb",
            linewidth=1.0,
            linestyle=(0, (3, 4)),
            alpha=0.42,
            zorder=1.2,
        )
    )
    ax.add_patch(
        Arc(
            HINGE_PIVOT,
            2 * CAP_LEVER,
            2 * CAP_LEVER,
            theta1=math.degrees(cap_start + math.radians(CAP_TRAVEL_DEG)),
            theta2=math.degrees(cap_start),
            color="#f59e0b",
            linewidth=1.0,
            linestyle=(0, (3, 4)),
            alpha=0.48,
            zorder=1.2,
        )
    )

    # Closed-position shapes in the cap's own rigid coordinate system. The
    # lower hinge puts the cap above the axis when closed, so clockwise motion
    # carries the solid cap forward, never through the lens or servo.
    initial_cap_pin = cap_pins[0]
    bracket_local = np.array(
        [
            [1.1, 3.5],
            [1.1, 13.0],
            initial_cap_pin,
        ]
    )
    cap_patch = Polygon(
        CAP_BODY_LOCAL,
        closed=True,
        facecolor="#155e75",
        edgecolor="#083344",
        linewidth=2.0,
        alpha=0.90,
        zorder=3.0,
    )
    bracket_patch = Polygon(
        bracket_local,
        closed=True,
        facecolor="#fbbf24",
        edgecolor="#b45309",
        linewidth=1.4,
        alpha=0.62,
        zorder=4.1,
    )
    ax.add_patch(cap_patch)
    ax.add_patch(bracket_patch)

    servo_horn_line, = ax.plot(
        [],
        [],
        color="#2563eb",
        linewidth=5.0,
        solid_capstyle="round",
        zorder=5.0,
    )
    connecting_rod_line, = ax.plot(
        [],
        [],
        color="#374151",
        linewidth=4.2,
        solid_capstyle="round",
        zorder=5.2,
    )
    cap_lever_line, = ax.plot(
        [],
        [],
        color="#f59e0b",
        linewidth=5.0,
        solid_capstyle="round",
        zorder=5.4,
    )
    joint_markers, = ax.plot(
        [],
        [],
        linestyle="none",
        marker="o",
        markersize=6.5,
        markerfacecolor="#ffffff",
        markeredgecolor="#111827",
        markeredgewidth=1.5,
        zorder=6.0,
    )
    fixed_markers, = ax.plot(
        [SERVO_PIVOT[0], HINGE_PIVOT[0]],
        [SERVO_PIVOT[1], HINGE_PIVOT[1]],
        linestyle="none",
        marker="o",
        markersize=8.0,
        markerfacecolor="#111827",
        markeredgecolor="#ffffff",
        markeredgewidth=1.2,
        zorder=6.2,
    )

    ax.annotate(
        "fixed servo axis",
        xy=SERVO_PIVOT,
        xytext=(-51.5, 5.5),
        fontsize=9,
        color="#1e3a8a",
        arrowprops=dict(arrowstyle="->", color="#64748b", linewidth=1.0),
        zorder=7.0,
    )
    ax.annotate(
        "cap hinge",
        xy=HINGE_PIVOT,
        xytext=(10.0, 7.0),
        fontsize=9,
        color="#92400e",
        arrowprops=dict(arrowstyle="->", color="#64748b", linewidth=1.0),
        zorder=7.0,
    )

    status_text = ax.text(
        0.975,
        0.965,
        "",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=12,
        fontweight="semibold",
        color="#0f172a",
        bbox=dict(boxstyle="round,pad=0.45", facecolor="#ffffff", edgecolor="#cbd5e1", alpha=0.94),
        zorder=8.0,
    )
    angle_text = ax.text(
        0.975,
        0.900,
        "",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=9.5,
        color="#334155",
        linespacing=1.4,
        zorder=8.1,
    )

    legend_handles = [
        Line2D([0], [0], color="#2563eb", lw=5, label="15 mm servo horn"),
        Line2D([0], [0], color="#374151", lw=4.2, label="35.016 mm rod"),
        Line2D([0], [0], color="#f59e0b", lw=5, label="15 mm cap-side lever"),
        Patch(facecolor="#155e75", edgecolor="#083344", label="52 mm rigid lens cap (edge-on)"),
        Patch(facecolor="#94a3b8", edgecolor="#475569", label="stationary servo envelope"),
    ]
    legend = ax.legend(
        handles=legend_handles,
        loc="lower left",
        frameon=True,
        framealpha=0.94,
        facecolor="#ffffff",
        edgecolor="#cbd5e1",
        fontsize=8.7,
        borderpad=0.8,
    )
    legend.set_zorder(9.0)

    fig.text(
        0.5,
        0.018,
        "Lower-hinge physical model. Every frame is checked for cap/bracket collision with the lens barrel and servo envelope.",
        ha="center",
        va="bottom",
        fontsize=8.5,
        color="#64748b",
    )
    fig.subplots_adjust(left=0.10, right=0.96, top=0.91, bottom=0.09)

    def update(frame_index: int):
        servo_pin = servo_pins[frame_index]
        cap_pin = cap_pins[frame_index]
        cap_rotation = cap_angles[frame_index] - cap_start

        servo_horn_line.set_data(
            [SERVO_PIVOT[0], servo_pin[0]],
            [SERVO_PIVOT[1], servo_pin[1]],
        )
        connecting_rod_line.set_data(
            [servo_pin[0], cap_pin[0]],
            [servo_pin[1], cap_pin[1]],
        )
        cap_lever_line.set_data(
            [HINGE_PIVOT[0], cap_pin[0]],
            [HINGE_PIVOT[1], cap_pin[1]],
        )
        joint_markers.set_data(
            [servo_pin[0], cap_pin[0]],
            [servo_pin[1], cap_pin[1]],
        )
        cap_patch.set_xy(transform_points(CAP_BODY_LOCAL, cap_rotation))
        bracket_patch.set_xy(transform_points(bracket_local, cap_rotation))

        servo_moved = abs(math.degrees(servo_angles[frame_index] - servo_start))
        cap_moved = abs(math.degrees(cap_angles[frame_index] - cap_start))
        status_text.set_text(states[frame_index])
        angle_text.set_text(
            f"servo travel   {servo_moved:6.1f}° / 155.0°\n"
            f"cap rotation  {cap_moved:6.1f}° / 135.0°"
        )
        return (
            servo_horn_line,
            connecting_rod_line,
            cap_lever_line,
            joint_markers,
            fixed_markers,
            cap_patch,
            bracket_patch,
            status_text,
            angle_text,
        )

    return FuncAnimation(
        fig,
        update,
        frames=len(progress),
        interval=1000 / 24,
        blit=False,
        repeat=True,
    )


def main() -> None:
    progress, states = make_frame_schedule()
    motion = solve_motion(progress)
    report = validate_motion(motion, progress)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    animation = build_animation(motion, progress, states)
    animation.save(
        GIF_PATH,
        writer=PillowWriter(fps=24),
        dpi=100,
        savefig_kwargs={"facecolor": "#f8fafc"},
    )
    plt.close("all")

    print(json.dumps(report, indent=2))
    print(f"GIF: {GIF_PATH}")
    print(f"Verification: {REPORT_PATH}")


if __name__ == "__main__":
    main()
