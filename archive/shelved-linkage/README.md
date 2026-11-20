# Shelved four-bar linkage design

> **Status: historical and shelved.** Capcom now uses the versioned direct-drive design in `models/direct-drive/Lens_Cap_Direct_Drive_V42.scad`. The material here preserves an earlier linkage-based approach and its research; it is not the current fabrication plan.

This archive consolidates work recovered from the ChatGPT conversations **DIY Servo Stand Off** and **Linkage Design Software**, the DIY working directory, and surviving temporary preview files. Existing artifacts are retained byte-for-byte wherever possible.

## Recovered artifacts

- `lens_cap_kinematics_animation.py` — the final Python generator and numerical verifier for the calculated four-bar animation.
- `outputs/lens_cap_fourbar_with_lens.gif` — the refined animation with the lens barrel, rigid 52 mm cap, servo envelope, and clearance context.
- `outputs/lens_cap_fourbar_verification.json` — frame-by-frame numerical checks produced with the refined animation.
- `outputs/lens_cap_15mm_physical_kinematics.gif` — an earlier, simpler calculated animation recovered from a temporary preview directory. Its original generator script was not found as a standalone file.
- `research/upstream-mesh/` — the STL inspection script, original upstream STL parts, mesh report, and rendered inspection views used while understanding the lens cap geometry.

The refined generator writes its GIF and JSON report to `outputs/`, so its original relative layout remains runnable:

```sh
python3 lens_cap_kinematics_animation.py
```

It requires Python 3, NumPy, Matplotlib, and Pillow.

The upstream mesh research can be regenerated from its own directory:

```sh
cd research/upstream-mesh
python3 inspect_lens_cap_stl.py
```

That script requires Python 3, NumPy, and Matplotlib. The preserved `mesh_report.json` contains the absolute output paths from its original run; regenerating it will record paths for the new checkout.

## Last linkage geometry

The final calculated proposal used these side-view values:

| Parameter | Value |
| --- | ---: |
| Fixed-axis horizontal separation | 31 mm |
| Fixed-axis vertical separation | 13 mm |
| Fixed-axis distance | 33.62 mm |
| Servo horn | 15.000 mm |
| Cap-side lever | 15.000 mm |
| Connecting rod | 35.016 mm |
| Servo travel | 155 degrees |
| Cap travel | 135 degrees |
| Closed cap-pin location from hinge | 14.97 mm forward, 0.87 mm down |
| Reported minimum transmission angle | approximately 29.7 degrees |

The retained verification report checks 120 calculated frames. It reports fixed pivots, rigid link lengths to floating-point precision, monotonic opening motion, exact commanded travel, and no collision in the modeled side-view envelopes.

These results validate the mathematical model, not the physical assembly. The 31 mm by 13 mm pivot measurement was approximate; out-of-plane alignment, the bent music-wire shape, bracket thickness, VHB thickness, and real three-dimensional clearances were not fully validated.

## Design evolution retained in the conversations

Before the final 15/15 mm proposal, the linkage research considered several geometries:

| Variant | Cap lever | Rod projection | Servo travel | Cap travel | Notes |
| --- | ---: | ---: | ---: | ---: | --- |
| Unequal-lever proposal | 11 mm | 37 mm | 92.6 degrees | 135 degrees | Bracket hole approximately 10.8 mm forward and 1.9 mm above the hinge. |
| Existing-bracket check | 13.88 mm forward | 37 mm | 133 degrees | 135 degrees | Minimum horn-to-link angle was only about 12.7 degrees. |
| Shortened-rod check | Existing bracket | approximately 34 mm | approximately 119 degrees | 135 degrees | Estimated minimum horn-to-link angle improved to about 31 degrees. |
| Parallelogram proposal | 15 mm | 33.62 mm | 135 degrees | 135 degrees | One-to-one rotation with parallel 15 mm levers. |
| Final optimized proposal | 15 mm | 35.016 mm | 155 degrees | 135 degrees | The geometry represented by the retained calculated animations. |

The conversations referenced additional generated files named `lens_cap_v2_calculated_motion.gif`, `lens_cap_v2_31x13_to_scale.png`, `lens_cap_v2_31x13_to_scale.svg`, `lens_cap_v2_bracket_detail.png`, `lens_cap_v2_135deg_motion.gif`, `lens_cap_v2_135deg_to_scale.png`, `lens_cap_v2_135deg_to_scale.svg`, and `servo_sweep_marked.png`. A search of the user workspace and temporary directories did not find surviving copies, so they are documented here but not represented as recovered artifacts.

## Upstream attribution

The files `research/upstream-mesh/52mm_Lens_Cap-Base.STL` and `research/upstream-mesh/52mm_Lens_Cap-Cap.STL` are from [Flip Lens Cap](https://www.thingiverse.com/thing:656038) by [cheewee5000](https://www.thingiverse.com/cheewee5000/designs), licensed under [Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)](https://creativecommons.org/licenses/by-nc/4.0/). The inspection renders and Capcom adaptations remain subject to that attribution and license.
