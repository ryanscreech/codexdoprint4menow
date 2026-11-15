# Model / resume / handover procedure

1. Establish authority: part number, datasheet revision, original CAD assembly, specimen dimensions and desired function. Hash inputs; record units (typically mm), coordinate axes, reference surfaces and fit-critical datums.
2. Make a schedule with source citation per dimension. Keep nominal, manufacturer tolerance, manual measurement with uncertainty, provisional proxy, and printer allowance in **different fields**. Never measure labeled dimensions from screen pixels.
3. Ask only blocking measurements early. If dimensions remain unavailable, document provisional envelopes and avoid claiming guaranteed physical fit.
4. Reuse proven CadQuery/FreeCAD/OpenSCAD/OCCT infrastructure **if suitable**. Prefer parameterised editable geometry, fixed/moving parts separated, and full continuous actuator/tool access sweeps rather than endpoint checks alone.
5. For enclosure modifications, preserve mating/screw/PCB mounting interfaces; distinguish insertion/assembly path from static occupancy. Do not globally scale original geometry to gain clearance.
6. Export appropriate STEP and 3MF. Re-import delivered outputs and check units, bounding boxes, datums, occupancy, topology, fit-critical dimensions, motion sweep, collision/keep-out and registration to originals. Expected values must come from independent authority, not the output model itself.
7. On failure, preserve initial fail evidence, correct cause and rerun; do not silently relax baseline.
8. Version results in fresh folders and maintain a concise README, reproducible commands actually run, checks, SHA-256, explicit limitations, next session first action and minimal transcript references.
9. Never report physical printing, device fit or mechanical actuation as verified without actual tests. Reserve separate gates: CAD geometry → slicing → printed coupon → assembly → function.
