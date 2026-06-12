# Hybrid CoreXY (IDEX) — X Bump at Y Direction Change

**Printer:** TwinDragon IDEX, hybrid CoreXY (Markforged / HAQ-XY style, half-CoreXY per toolhead)
**Kinematics class:** Dedicated Y axis (two independent Y motors, Y1/Y2) + one half of a CoreXY loop per toolhead (motors A and B). Comparable to Voron Tridex and RatRig V-Core / hybrid layouts.
**Status:** Diagnosed — mechanical lost motion (backlash), not a firmware/kinematics defect.

---

## 1. Problem Definition

### Symptom
- The **X axis moves cleanly** with no visible issue.
- When the **Y axis reverses direction**, the **X carriage snaps sideways by a small fixed amount first**, and *then* the Y axis begins to move properly.
- The displacement looks like "backlash in Y, but expressed as an X movement."
- Reproducible at very small moves: a **0.1 mm Y reversal shows no visible Y motion at all, yet X still jumps**.
- The motion is **pure X** — never a visible Y twitch, never a diagonal.
- Magnitude is **fixed per reversal**, independent of how far Y subsequently travels.

### Impact
- Rough surfaces and dimensional inaccuracy at features where Y changes direction.
- Worst at perimeters / direction-change-heavy geometry.

### Reference case
Matches the Duet forum thread *"Issues with Haq XY/Markforged kinematics"* (topic 23325), **first symptom only** — the discrete X bump at gantry direction change. (The thread's second, separate symptom — continuous X drift over a long Y move caused by non-parallel belt paths — is **not** part of this report.)

---

## 2. Root Cause

### 2.1 The kinematic coupling
In this hybrid layout the X carriage position depends on **both** the A/B (X) motor **and** the gantry (Y) position:

```
x_carriage = a - c * Y_gantry
```

- `a` = A/B motor belt feed
- `Y_gantry` = actual physical gantry position
- `c` = coupling constant for the belt routing (≈ 1)

This coupling is **by design**. It is exactly what keeps X stationary during a normal Y move: when the gantry moves, the firmware **actively rotates the A/B motor** to feed/retract belt and cancel the geometric pull. X staying still during a Y move is an *active* compensation, not a passive accident.

### 2.2 Why the bump appears (the decisive mechanism)
The bump is caused by **Y-drivetrain backlash decoupling the commanded gantry position from the actual gantry position** at the moment of reversal:

1. On a Y reversal, the **Y motors turn**, but the gantry is briefly stuck inside its drivetrain backlash → `Y_gantry` does **not** change yet. (This is why a 0.1 mm Y reversal shows **no visible Y motion**.)
2. The firmware **still rotates the A/B motor** by `c · Y_commanded`, because as far as it knows the gantry *is* moving and X must be compensated. The A/B drivetrain transmits this (its slack is small / already engaged), so belt actually feeds.
3. With the gantry not yet moving, the compensation has nothing to cancel against:

```
Δx = c * Y_commanded  -  c * (Y_gantry - Y_gantry0)
   = c * Y_commanded  -  c * 0
   = c * Y_commanded        →  appears entirely as X motion
```

4. As Y continues and the gantry finally chews through its backlash, `Y_gantry` catches up, the `c · Y_gantry` term grows, and X recovers back toward zero. This is the **"X first, then Y"** timing — the gantry lags the motor's compensation by exactly one backlash width.

### 2.3 Why the errors do not cancel
Two distinct effects happen at a reversal:

| Effect | Nature | Result |
|--------|--------|--------|
| Geometric belt length redistribution (`+Δy` one side, `−Δy` other) | **Signed** | Cancels — this is the intended behavior |
| Commanded compensation `c · Y_commanded` when the gantry has not moved | **Uncancelled** | Lands entirely on X |
| Loop clearance / lost motion (bearings, grub screws, tooth seating) | **Unsigned (series)** | Adds up (`G_total = Σ|gᵢ|`), rectified into a discrete jump at reversal |

The signed geometric term cancels (as expected). The **commanded compensation** and the **unsigned clearance** do not — they are the bump.

### 2.4 Why it is pure X and never diagonal
The toolhead carriage rides on the **X linear guide mounted to the gantry**. Relative to the gantry, its only degree of freedom is **translation along X**. The released belt motion therefore has exactly one place to go — along X. A diagonal would require carriage-vs-gantry motion in Y, which the rail mechanically forbids.

### 2.5 Why Y backlash itself is "invisible"
The Y backlash is real and flips at reversal, but it acts **along Y — the axis that was commanded to move**. It shows up as a tiny start-of-move lag in the commanded direction (e.g. moved 4.97 instead of 5.00 mm), which the eye/indicator cannot distinguish from a clean move. The same lost motion dumped onto the **stationary** X axis is glaringly visible. Rule of thumb: *backlash in the commanded direction = invisible lag; backlash dumped on a perpendicular axis = visible bump.*

### 2.6 Is the kinematics fundamentally flawed?
**No.** The coupling is a property shared (more strongly) by every standard CoreXY, which tune to excellent accuracy. Coupling **redistributes** error to a perpendicular axis; it does **not** raise the error floor. As `B_Y → 0`, the coupled term `c · B_Y → 0` and the cross-talk vanishes. The trade accepted with this architecture is **lower moving mass + IDEX dual printing** in exchange for **less tolerance of mechanical slop**. The achievable accuracy ceiling equals a Cartesian's; the path to it is less forgiving.

---

## 3. Diagnostic Tests

### Test A — Localize: X loop vs Y racking
1. Mount a dial indicator on the carriage measuring **X**.
2. Run repeated `G1 Y+5` / `G1 Y-5`; record the X deviation at each reversal (baseline).
3. **Rigidly clamp the gantry to the frame** and repeat the Y command (motors will stall — acceptable).
   - Bump **disappears** when clamped → lost motion is in the **gantry / Y drivetrain**.
   - Bump **persists** → lost motion is in the **A/B belt / pulley / carriage** path.

### Test B — Quantify loop lost motion by hand
1. Energise steppers (idle hold on).
2. Indicator on carriage in X; push/pull the carriage by hand.
3. Movement > ~0.02 mm = confirmed lost motion. Compare **both** carriages: only one bad → that carriage's belt/idlers; both equal → systemic (gantry idlers / Y racking).

### Test C — Scaling sweep (mechanism + measure B_Y)
1. Indicator on carriage in **X**.
2. Command Y reversals **too small to move the gantry**: `0.02, 0.05, 0.10, 0.20 mm`.
3. Observe:
   - X bump **scales linearly with the Y command while the gantry stays dead-still** → confirms the kinematic-compensation mechanism (Section 2.2). Slope `Δx / Y_commanded` = coupling constant `c` (expect ≈ 1).
   - X bump magnitude at saturation ≈ **Y-drivetrain backlash `B_Y`** (the target to eliminate).

### Test D — Acceleration dependence (clearance vs compliance)
- Repeat the bump measurement at low vs high acceleration / `square_corner_velocity`.
  - Bump **constant** with acceleration → **clearance-dominated** (grub screws, bearing play, tooth seating). Wider belt will **not** help.
  - Bump **scales** with acceleration → **compliance-dominated** (belt stretch). Wider/stiffer belt **will** help.

### Test E — Gantry racking (dual-Y sync)
- Indicators on **both** ends of the gantry; jog Y back and forth.
- One side lagging at reversal = **Y tension/backlash mismatch** racking the gantry → contributes to the X bump.

---

## 4. Mitigations (ordered: cheapest / highest-yield first)

Re-measure the bump (Test A baseline) **after each step** so you know what actually helped.

### Step 1 — Match and firm up both Y belt tensions (highest yield)
- Tension **both** Y belts firmly and **equally** (frequency-match left vs right with a phone tuner app — equal pitch = equal tension).
- Unequal Y tension racks the gantry at reversal and is the #1 cause on independent-Y machines.

### Step 2 — Eliminate mechanical slop in the Y path
- **Grub screws** on Y1/Y2 motor pinions and Y idler pulleys — on the shaft flat, both screws, threadlocker if needed.
- **Idler bearings** in the Y path — replace any with axial/radial play; ensure shouldered with no end-float.
- **Toothed engagement** — avoid running a belt's toothed side on a smooth/bearing idler; use tooth-on-tooth or a smooth idler on the flat back only.

### Step 3 — Square the gantry + per-side homing
- Mechanically square the gantry to the frame (push both sides to a hard reference, then lock pulleys).
- In Klipper, run the two Y motors as `[stepper_y]` + `[stepper_y1]` (dual-carriage or independent endstops) on **separate drivers** so the gantry re-squares at every home.

### Step 4 — Reduce A/B (X) drivetrain backlash (second-order)
- Tension A and B belts firmly; tighten A/B pinion grub screws; check carriage-end idlers for play.
- Does not cause the bump but sets how cleanly the compensation transmits.

### Step 5 — Hardware upgrades (only if justified by tests)
- **Larger / more-teeth pulleys (e.g. 16T → 20T):** more teeth in mesh → less tooth backlash + less polygon effect. Sound, modest upgrade. Cost: ~20% coarser resolution / lower belt torque per step — do not oversize past ~20–24T.
- **Wider belt (6 → 9 mm):** ~50% stiffer axially, reduces belt-stretch **compliance**. Only worthwhile if **Test D** shows the bump is **acceleration-dependent**. Does little for clearance-dominated backlash.

### Step 6 — Firmware masking (last resort, not a substitute)
- `[input_shaper]` (run `SHAPER_CALIBRATE` with an ADXL): reduces the ringing the bump excites, shrinking the surface artifact — does not remove backlash.
- True backlash compensation is a band-aid; prefer mechanical removal.

---

## 5. Target / Definition of Done
- X bump reduced from baseline toward **≤ 0.02–0.03 mm**, where it no longer affects surface finish.
- Reference: the cited Duet case went from **0.2 mm → 0.01 mm** purely by fixing Y-side mechanics (same lever).

---

## 6. Summary

| Item | Conclusion |
|------|-----------|
| Root cause | Y-drivetrain backlash decouples actual gantry position from commanded position; the A/B motor's kinematic compensation then leaks onto the stationary X axis at reversal |
| Not the cause | Firmware kinematics matrix, coupling math, belt-path parallelism (that is a separate, continuous-drift symptom) |
| Dominant fix | Eliminate Y backlash + match Y-side tension + square gantry (`B_Y → 0` ⇒ bump → 0) |
| Hardware | Modest pulley upgrade helps; wider belt only if bump is acceleration-dependent |
| Architecture | Not flawed — coupling redistributes error, does not raise the accuracy floor; same ceiling as Cartesian, less forgiving of slop |
| Key measurements | Test A (localize), Test C (confirm mechanism, measure `B_Y` and `c`), Test D (clearance vs compliance) |
