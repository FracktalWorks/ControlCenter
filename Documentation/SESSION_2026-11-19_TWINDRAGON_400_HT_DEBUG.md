# Live Debugging Session — 2026-11-19

## Printer: TwinDragon 400 HT @ 10.143.225.66

### Session Summary
Connected over SSH and diagnosed why the printer would not start. All three MCUs were
brought back online, the input-shaper config was repaired, the chamber heater was made
visible in OctoPrint and the touch UI, and the webcam stream was restored. Changes were
made in the repo (committed locally) and, where needed to make the unit work, on the
printer itself.

---

## Machine Identity

| Item | Value |
|------|-------|
| Hostname | `pi` |
| Board | Raspberry Pi Compute Module 4 Rev 1.1 |
| OS | Debian 13 (trixie), kernel `6.18.50+rpt-rpi-v8`, aarch64 |
| Python | 3.13.5 |
| OctoPrint | 1.7.48, serial on `/tmp/printer` @ 250000 |
| ControlCenter | 1.1.8 (installed in `/home/pi/OctoPrint/venv`) |
| Klipper | `bd6a517e`, branch `Production`, `/home/pi/klipper_IDEX` |
| Config root | `/home/pi/printer_data/config` (`printer.cfg` and `variables.cfg` are symlinks) |
| CAN | `can0` @ 1 Mbit via gs_usb STM32H723 bridge |

> The previous session target was `10.188.136.9` ("raspberrypi", Dragon 400, Debian 10).
> This machine is a different printer and had moved to `10.143.225.66` after the subnet changed.

---

## 1. Printer would not start — toolhead MCUs stuck in CanBoot

### Symptom
`Klipper state: Not ready`, `mcu 'toolhead0': Timeout on connect`, bed temperature `None`.

### Diagnosis
`canbus_query.py` reported both toolhead boards in the bootloader, not running Klipper:

```
Found canbus_uuid=ecda989b639d, Application: CanBoot   (toolhead0)
Found canbus_uuid=27006611a2db, Application: CanBoot   (toolhead1)
```

A CAN capture showed `SET_NODEID ecda989b639d → 5` being sent and requests on `0x10A`
with **no replies on `0x10B`** — the board had no application to answer with. Nodes still
reported `CanBoot` after `CMD_RESET` + 18 s, so no valid image was present. Klipper itself
was healthy: the mainboard (`0a58f8645369`) connected normally.

Also fixed along the way: `can0` was in a bad state (`Got error -1 in can read: (100)
Network is down`), which was masking the mainboard connection. After an interface reset the
mainboard connected again.

### Fix
Flashed both toolhead boards with the matching RP2040 build using **Katapult** (the tool
was renamed from CanBoot, so `~/CanBoot/scripts/flash_can.py` does not exist):

```bash
/home/pi/klippy-env/bin/python /home/pi/katapult/scripts/flash_can.py \
  -i can0 -f /home/pi/klipper_IDEX/out/klipper.bin -u ecda989b639d   # toolhead0
/home/pi/klippy-env/bin/python /home/pi/katapult/scripts/flash_can.py \
  -i can0 -f /home/pi/klipper_IDEX/out/klipper.bin -u 27006611a2db   # toolhead1
```

Verified before writing: `Detected Klipper binary version bd6a517e, MCU: rp2040`, and after
writing: `Verification Complete: SHA = 5BDF01640A3D35236C9E20FD1951E4DD847995F5`.

Result — all three MCUs online:

```
Loaded MCU 'mcu'       137 commands (bd6a517e)
Loaded MCU 'toolhead0' 136 commands (bd6a517e)
Loaded MCU 'toolhead1' 136 commands (bd6a517e)
```

---

## 2. `[input_shaper]` not allowed with `dual_carriage`

### Symptom
Once the MCUs connected, Klipper stopped with:

```
configparser.Error: Input shaper parameters cannot be configured via [input_shaper]
section with dual_carriage(s) enabled.
```

### Cause
The `SAVE_CONFIG` block in `printer.cfg` still held global shaper values
(`shaper_type_x/freq_x/type_y/freq_y`). The `klipper_IDEX` fork rejects those whenever
`[dual_carriage]` is present.

### Fix
Removed the `[input_shaper]` block from the `SAVE_CONFIG` section, and migrated the
calibrated values into `variables.cfg` where `[delayed_gcode STARTUP]` picks them up:

```
shaper_t0_x_type = 'mzv'    shaper_t0_x_freq = 56.4
shaper_y_type    = 'zv'     shaper_y_freq    = 49.2
```

`STARTUP` then applies them per carriage via `SET_INPUT_SHAPER`.

---

## 3. Jinja `UndefinedError` in `STARTUP`

### Symptom
`gcode.CommandError: Error evaluating 'delayed_gcode STARTUP:gcode':
jinja2.exceptions.UndefinedError: 'dict object' has no attribute 'shaper_t1_x_freq'`

### Cause
The macro passed `svv.shaper_t1_x_freq|float` with no default. Jinja's `float` filter only
catches `TypeError`/`ValueError`, so an undefined attribute raises outright whenever
toolhead1 has never been calibrated.

### Fix
`shaper_t1_x_freq|float` → `shaper_t1_x_freq|default(0)|float`, matching the pattern already
used for the Y axis.

---

## 4. `Unknown command: "SET_INPUT_SHAPER"`

### Cause
Deleting the `[input_shaper]` section entirely also unloads the module, so the command it
registers disappeared.

### Fix
Re-added `[input_shaper]` as an **empty section**. It loads the module and registers
`SET_INPUT_SHAPER`, while no shaper is enabled so the `dual_carriage` check passes.

---

## 5. Chamber heater not visible in OctoPrint or the touch UI

### Symptom
Home-screen chamber tile and control-screen bed/chamber toggle showed nothing;
`/api/printer` returned only `bed`, `tool0`, `tool1`.

### Diagnosis
| Piece | State |
|-------|-------|
| `CHAMBER_HEATER.cfg` included by `PRINTER_TWINDRAGON_400_HT.cfg` | present |
| `[heater_generic Chamber]` in Klipper | working, reads ~29.5 °C |
| `has_chamber_heater()` on device | `True` |
| OctoPrint profile `heatedChamber` | **`false`** |

OctoPrint discards the `C:` field from `M105` unless the printer profile declares a heated
chamber, so no `chamber` key ever reached the model or the UI.

### Fix
`heatedChamber: true` in `TWINDRAGON_400_HT.profile`, deployed to the device profile.

Verified with a safe command (target below ambient, so the heater must stay off):

```
M141 S25 → chamber target 25.0,  Chamber: target=25 temp=29.5 pwm=0.000
M141 S0  → chamber target 0.0
```

---

## 6. Chamber temperature disappeared again (regression)

### Symptom
After a reboot the chamber was gone from OctoPrint once more.

### Cause
ControlCenter re-deploys the OctoPrint printer profile on boot and on
Settings → printer re-selection:

```
14:59:06 - SettingsScreen - INFO - Printer configuration changed to: TWINDRAGON_400_HT
14:59:06 - utils.printer_config_manager - INFO - Updated OctoPrint printer profile
```

`update_octoprint_printer_profile()` copied `heatedChamber: false` from the **installed
plugin template**, overwriting the corrected value. The same path also restored the broken
webcam URL.

### Fix
Two layers:

1. **On the device** — replaced the installed templates so a deploy writes correct values:
   - `config/TWINDRAGON_400_HT.profile` → `heatedChamber: true`
   - `config/config.yaml` → absolute webcam URLs
   - `utils/printer_config_manager.py` → LAN-IP injection for webcam
2. **In the repo** — the profile flag is no longer trusted from the template at all.
   `printer_config_manager.printer_has_chamber_heater()` walks the active `printer.cfg`
   `[include]` chain looking for `[heater_generic Chamber]`, and
   `update_octoprint_printer_profile()` writes that result into the deployed profile.
   `printer_ui_config.has_chamber_heater()` falls back to the same detection.

Regression test (stale template forced to `false`, active config loading `CHAMBER_HEATER.cfg`):

```
template heatedChamber : False   (stale on purpose)
deploy returned        : True
deployed heatedChamber : True
PASS - stale template overridden by Klipper config
```

Detection per printer: `TWINDRAGON_400_HT` → True; `DRAGON_400`, `TWINDRAGON_600_V1` → False.

---

## 7. Webcam feed blank in OctoPrint

### Symptom
No camera image; OctoPrint log showed `404 GET /webcam/?action=stream`.

### Diagnosis
The camera stack was healthy the whole time:

```
fw-webcam.service   active   OV5647 CSI, 1296x972 @ 15 fps on :8080
GET :8080/?action=stream    → 200 multipart/x-mixed-replace
GET :8080/?action=snapshot  → 200 image/jpeg
```

The fault was the URL. `plugins.classicwebcam.stream` was `/webcam/?action=stream`, an
**OctoPi-only** relative path that depends on its haproxy. These images have no proxy
(`nginx` not installed), so it resolved to `http://<printer>:5000/webcam/...` and 404'd.

`/home/pi/fw-deploy/webcam/install-webcam.sh` documents the correct behaviour:

> `OctoPrint classicwebcam stream/snapshot URLs -> http://<LAN IP>:8080/?action=stream|snapshot`
> `("/webcam/?action=stream" only works behind OctoPi's haproxy, which these printers do not have)`

### Fix
`update_octoprint_config()` now writes absolute endpoints at deploy time, via a new
`_apply_webcam_endpoints()` helper and a `_get_lan_ip()` UDP route probe (no packets sent):

```
webcam.stream                    = http://10.143.225.66:8080/?action=stream
webcam.snapshot                  = http://127.0.0.1:8080/?action=snapshot
plugins.classicwebcam.*          = same values
```

Both the legacy `webcam:` section and `plugins.classicwebcam` are written, because the
one-time migration from `webcam:` has already run on existing installs.

Verified from a different machine on the LAN:

```
snapshot  HTTP 200  image/jpeg  71,694 bytes
stream    HTTP 200  multipart/x-mixed-replace
```

---

## 8. Z endstop / build height updated

`[stepper_z]` in `PRINTER_TWINDRAGON_400_HT.cfg` was updated from the reference unit:

```diff
-position_endstop: 415 #410 #417.000
-position_max: 415 #410 #417.000
+position_endstop: 419 #410 #417.000
+position_max: 419 #410 #417.000
```

The repo file is now byte-identical to the printer's deployed copy.

---

## Repo Changes (local commits, not pushed)

```
c6da4e8  Derive chamber heater support from the Klipper config, not the profile template
ad045ee  TwinDragon 400 HT: fix chamber heater, input shaper, webcam and Z endstop
```

### `ad045ee` — 6 files

| File | Change |
|------|--------|
| [config/TWINDRAGON_400_HT.profile](../octoprint_ControlCenter/config/TWINDRAGON_400_HT.profile) | `heatedChamber: true` |
| [config/config.yaml](../octoprint_ControlCenter/config/config.yaml) | webcam `stream` → absolute URL |
| [firmware/BASE_TWINDRAGON.cfg](../octoprint_ControlCenter/firmware/BASE_TWINDRAGON.cfg) | empty `[input_shaper]`; `shaper_t1_x_freq\|default(0)` |
| [firmware/CHAMBER_HEATER.cfg](../octoprint_ControlCenter/firmware/CHAMBER_HEATER.cfg) | placeholders removed, pins documented as verified |
| [firmware/PRINTER_TWINDRAGON_400_HT.cfg](../octoprint_ControlCenter/firmware/PRINTER_TWINDRAGON_400_HT.cfg) | `[stepper_z]` 415 → 419 |
| [utils/printer_config_manager.py](../octoprint_ControlCenter/utils/printer_config_manager.py) | `_get_lan_ip()`, `_apply_webcam_endpoints()` |

### `c6da4e8` — 2 files

| File | Change |
|------|--------|
| [utils/printer_config_manager.py](../octoprint_ControlCenter/utils/printer_config_manager.py) | `_config_includes_chamber_heater()`, `printer_has_chamber_heater()`, profile override |
| [utils/printer_ui_config.py](../octoprint_ControlCenter/utils/printer_ui_config.py) | `has_chamber_heater()` falls back to config detection |

Validation: `py_compile` clean; Python 3.7-compatible (no f-strings in new code, no new dependencies).

---

## Changes Made On The Printer

### Config files (`/home/pi/printer_data/config`)

| File | Change | Backup |
|------|--------|--------|
| `printer.cfg` | removed `[input_shaper]` from `SAVE_CONFIG` | `printer.cfg.bak.20261119_125600` |
| `BASE_TWINDRAGON.cfg` | empty `[input_shaper]`; `shaper_t1_x_freq\|default(0)` | `BASE_TWINDRAGON.cfg.bak.20261119_125759` |
| `variables.cfg` | added `shaper_t0_x_type/freq`, `shaper_y_type/freq` | — |
| MCU flash | toolhead0 + toolhead1 → `bd6a517e` (RP2040) | — |

### Installed plugin (`/home/pi/OctoPrint/venv/lib/python3.13/site-packages/octoprint_ControlCenter`)

Replaced 3 files with the corrected repo versions (backups suffixed `.pre-fix-20261119-151141`):

| File | Reason |
|------|--------|
| `config/TWINDRAGON_400_HT.profile` | `heatedChamber: true` |
| `config/config.yaml` | absolute webcam URLs |
| `utils/printer_config_manager.py` | LAN-IP webcam injection |

Also backed up: `/home/pi/.octoprint/config.yaml` and
`/home/pi/.octoprint/printerProfiles/_default.profile` (`.pre-fix-20261119-151141`).

> Note: patching site-packages is not tracked by pip. A release from commit `c6da4e8` is the
> clean way to ship this permanently.

### Services restarted
`klipper`, `octoprint`, `fw-touchui` (and `fw-touchui` again to clear the documented
WebSocket reconnect give-up after each OctoPrint restart).

---

## Current Verified State

| Service | Status |
|---------|--------|
| `klipper` | active — all 3 MCUs loaded, state `ready` |
| `octoprint` | active — `Operational`, serial connected |
| `fw-webcam` | active — MJPEG on :8080 |
| `fw-touchui` | active — WebSocket connected |

Live temperatures (chamber now present):

```json
{"bed": 30.6, "chamber": {"actual": 29.3, "target": 0.0},
 "tool0": 31.0, "tool1": 31.1}
```

---

## Outstanding / Follow-up

1. **GitHub push pending** — two commits are local only (`ahead 2`). `git push origin
   production` needs credentials in an interactive shell.
2. **toolhead1 X input shaping is at 0 Hz** — no calibration data for T1 was available and no
   value was invented. Run `SHAPER_CALIBRATE TOOL=1`.
3. **`webcamd.service` is still enabled** (legacy ustreamer for USB cameras). It is inactive
   but would grab `/dev/video0` if started and break the CSI stream — the webcam installer
   normally disables it.
4. **USB pendrive** — the SanDisk 3.2 Gen1 intermittently fails to enumerate
   (`USB disconnect` 0.28 s after detection, then a stalled handshake). It later enumerated
   correctly as `sda`. The mount path is `/media/usb0` via `fw-usb-mount@.service`; if it
   recurs, try another hub port, a USB 2.0 stick, or check the drive on a PC.
5. **Dragon 400 @ 10.188.136.9** (earlier machine, diagnosis only): all six TMC5160 drivers
   fail with `Unable to write tmc spi ... register GLOBALSCALER` and SPI readback is
   `0x00` — a shared SPI bus / driver-supply fault, not config. No changes were made there.

---

## Rollback

Repo: `git reset --hard ad045ee^` (both commits) or `git revert c6da4e8 ad045ee`.

Printer: restore the `.bak.*` / `.pre-fix-*` files listed above, then
`sudo systemctl restart klipper octoprint` and `sudo systemctl restart fw-touchui`.
