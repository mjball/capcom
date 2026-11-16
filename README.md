# Capcom

A desk-controlled motorized lens cap for the Canon RF 35 mm F1.8 Macro IS STM, using its 52 mm filter thread.

The active design is the direct-drive OpenSCAD model at [models/direct-drive/Direct_Drive.scad](models/direct-drive/Direct_Drive.scad). Each CAD revision is archived as a separate commit at that path. See [hardware and controls](docs/hardware.md) for the DigiKey parts list.

## Shelved designs and research

The earlier four-bar linkage design is no longer active. Its Python tooling, calculated animations, numerical verification, design notes, and upstream-mesh research are retained in the [shelved linkage archive](archive/shelved-linkage/README.md) for reference. Nothing in that archive should be read as the current fabrication plan.

## Third-party attribution

[Flip Lens Cap](https://www.thingiverse.com/thing:656038) by [cheewee5000](https://www.thingiverse.com/cheewee5000/designs) is licensed under [Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)](https://creativecommons.org/licenses/by-nc/4.0/).

Capcom adapts the original 52 mm base mesh for a servo-driven mechanism. Early revisions include the base as a separate STL. Later revisions embed the mesh in the OpenSCAD model. The upstream mesh and its adaptations are available under CC BY-NC 4.0.
