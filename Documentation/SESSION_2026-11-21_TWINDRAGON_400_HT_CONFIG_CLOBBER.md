# Live Debugging Session — 2026-11-21

## Printer: TwinDragon 400 HT @ 172.29.228.66

### Session Summary
The printer was found halted with `Unknown pin chip name 'toolhead1'`. The live
`printer.cfg` had been overwritten with **another machine's MCU block** (wrong
`canbus_uuid` values, `[mcu toolhead1]` commented out) and that machine's
`SAVE_CONFIG` calibration. The correct config was restored from the unit's own
backup, and ControlCenter's config deployment/restore paths were hardened so a
bad `printer.cfg` can never be written again.

---

## Machine Identity

| Item | Value |
|------|-------|
| IP | `172.29.228.66` (changed from `10.143.225.66` on 21 Nov 11:55 via touch UI) |
| Board | Raspberry Pi CM4, Debian 13 (trixie), kernel `6.18.50+rpt-rpi-v8` |
| OctoPrint | **1.11.8.post5** (upgraded since the 19 Nov session, which ran 1.7.48) |
| Plugins | ControlCenter 1.1.8, OctoKlipper 0.4.2, TwinDragon Print Restore 1.0.6 |
| Klipper | `bd6a517e`, `Production` branch of `FracktalWorks/klipper_IDEX` |
| Config root | `/home/pi/printer_data/config` (`/home/pi/*.cfg` are symlinks into it) |
| Touch UI | `fw-touchui` → `.xinitrc` → `/home/pi/OctoPrint/venv` package |

---

## Symptom

```
Send: STATUS
Recv: // Unknown pin chip name 'toolhead1'
Recv: // Printer is halted
Recv: // Klipper state: Not ready
```

`/api/printer` reported `Operational` but all temperatures were `null` — OctoPrint
was talking to a klippy host that had never loaded a config.

## Root cause

The live `printer.cfg` held a foreign MCU block:

```ini
[mcu]
canbus_uuid: d9d3f257e82c        # board on this printer: 0a58f8645369

[mcu toolhead0]
canbus_uuid: 2e49f7a5e543        # board on this printer: ecda989b639d

#[mcu toolhead1]                 # section commented out entirely
#canbus_uuid: 3ec1b8773dd7       # board on this printer: 27006611a2db
```

`PRINTER_TWINDRAGON_400_HT.cfg` includes `TOOLHEADS_TD-01_TOOLHEAD1.cfg`, which
uses `toolhead1:` pins in 15 places. Klipper creates every `[mcu …]` object before
any other section (`mcu.add_printer_objects` runs first in `klippy.py`), so this
is not an include-order problem: the section simply did not exist, and pin lookup
aborted the config load.

The `SAVE_CONFIG` block in the same file carried a 600 mm-class bed mesh
(`mesh_min` 50/50 → `mesh_max` 570/550) and `z_offset = -0.850`, i.e. calibration
from a different unit, on a 430 × 400 mm machine.

### How it got there

ControlCenter's touch UI deploys `firmware/*` templates over the live config
(`copy_firmware_files` → `update_printer_cfg`) and can restore `printer-*.cfg`
backups (`restore_backup_config`). Both paths accepted any content:

* `update_printer_cfg()` preserved the MCU block by matching the
  `# MCU Config` header, but fell back to the template when the marker was absent —
  and the template shipped with **real-looking UUIDs from another printer** in the
  unused `/home/pi/oprint` installation.
* `is_config_valid()` only checked "has sections, no NUL bytes", so
  `restore_backup_config()` happily restored foreign configs (hundreds of
  `printer-2026111*.cfg` backups in the config dir contain those UUIDs).
* `KLIPPER_CONFIG_PATH` was `/home/pi/`, while Klipper reads
  `/home/pi/printer_data/config`; `/home/pi/PRINTER_TWINDRAGON_400_HT.cfg` and
  `CHAMBER_HEATER.cfg` are plain files, not symlinks, so those deploys silently
  went nowhere while `printer.cfg` (a symlink) was modified.

Timeline: the error first appeared 18 Nov 13:33, was cleared during the 19 Nov
session, and returned at the 19 Nov 21:29 reboot after a printer re-selection →
`RESTART` → "Restore factory defaults" sequence in the touch UI.

---

## Fix applied on the printer

1. Restored the unit's own known-good config, keeping includes and calibration:
   `printer-20261119_213242.cfg` → `printer.cfg` (backup of the broken file kept as
   `printer.cfg.bak.20261121_121932`).
2. Restarted `klipper`; all three MCUs load and the host reaches `ready`:

```
Loaded MCU 'mcu'       137 commands (bd6a517e)
Loaded MCU 'toolhead0' 136 commands (bd6a517e)
Loaded MCU 'toolhead1' 136 commands (bd6a517e)
```

3. Reconnected OctoPrint to `/tmp/printer`. Live temperatures confirm all three
   MCUs: bed 29.8 °C, chamber 29.7 °C, tool0 37.3 °C, tool1 34.6 °C.
4. Replaced the stale `firmware/printer.cfg` template in the unused
   `/home/pi/oprint` installation (foreign UUIDs → `XXXXXXXXXXX` placeholders).
5. Synced the deployed `firmware/PRINTER_TWINDRAGON_400_HT.cfg` template with the
   live file (Z `position_endstop`/`position_max` 415 → 418) so a deploy no longer
   regresses the tuned build height.
6. Installed the hardened `utils/printer_config_manager.py` into both site-packages
   copies and restarted `fw-touchui`.

Every modified file on the printer has a `.pre-fix-20261121` backup.

---

## Prevention (repo change)

`utils/printer_config_manager.py`:

| Change | Purpose |
|--------|---------|
| `validate_mcu_configuration()` | Rejects a composed config when `[mcu]` is missing, a `canbus_uuid` is not 12 hex chars (placeholders included), a section has neither `canbus_uuid` nor `serial`, or the include chain uses `chip:pin` for an MCU with no `[mcu chip]` section |
| `is_config_valid()` now runs the MCU check | `restore_backup_config()` / `get_valid_backup_files()` / the startup self-check skip foreign or broken backups instead of restoring them |
| `update_printer_cfg()` | Refuses to write when the MCU block could not be preserved from the existing file, and refuses any composed config that fails `validate_mcu_configuration()` — the live file is left untouched |
| `resolve_klipper_config_path()` | Deploys and validates against `/home/pi/printer_data/config` when it holds the live `printer.cfg`, falling back to `/home/pi` on legacy images |

Because `_ensure_valid_printer_config()` runs before the UI loads, a clobbered
config now triggers an automatic restore from the newest *valid* backup instead of
starting a UI on a halted printer.

Regression tests: `test_printer_config_validation.py` (6 cases, run on the unit
against the installed module — all pass).

---

## Verification

```
live valid       : True
foreign backup   : False   (pins reference undefined MCU(s): toolhead1)
known-good backup: True
```

```
klipper    : active      fw-touchui : active
Klipper state parsed from payload: ready
ControlScreen: Klipper state changed to: 'ready', is_ready: True
```

Temporary remote-admin command used during the session was removed from
OctoPrint `system.actions`; uploaded helper files were deleted.

---

## Webcam feed and IP changes

The webcam is served by `fw-webcam` directly on `:8080`; there is no reverse
proxy, so OctoPrint's webcam URL must be absolute (`http://<LAN-IP>:8080/...`).
Two problems were fixed:

* The 19 Nov deploy ran while WiFi was being reconfigured. `_get_lan_ip()` failed
  and `_apply_webcam_endpoints()` **wrote `127.0.0.1`**, which is only reachable
  from the Pi itself — remote browsers saw no feed. It now keeps the previously
  configured endpoints when the IP cannot be determined.
* A DHCP change left the old IP in OctoPrint until someone redeployed. Writing
  `config.yaml` externally does not update a running OctoPrint (settings are held
  in memory), so `refresh_webcam_endpoints()` now POSTs to
  `http://127.0.0.1:5000/api/settings`, which updates memory *and* the file.

`refresh_webcam_endpoints()` runs:

| Trigger | Location |
|---------|----------|
| Every application start (after Klipper is operational) | `MainController.onStartupCompleted` |
| WiFi change | `NetworkSettings.wifiReconnectResult` → `refreshWebcamEndpoints()` |
| Static IP change (eth0/wlan0) | `NetworkSettings.staticIPReconnectResult` → `refreshWebcamEndpoints()` |

Verified on the unit: setting the URL to a bogus `10.99.99.99` and running the
refresh restored `http://172.29.228.66:8080/?action=stream`, and a restart of
`fw-touchui` logged `OctoPrint webcam endpoints updated for IP 172.29.228.66`.
OctoPrint mirrors the value into `webcam.webcams[0]` and the legacy
`webcam.streamUrl`, so the UI, snapshot and stream all use the same URL.

---

## Emergency stop recovery (M112)

**Symptom:** after an emergency stop the touch UI ended up with the printer offline,
and the unit could come back configured as a different machine model.

**Two defects were found and fixed:**

1. OctoPrint force-sends `M112` and **drops the serial connection**
   (`Changing monitoring state from "Operational" to "Offline after error"`).
   `refresh_klipper_status()` then sent `FIRMWARE_RESTART` five times into a closed
   port. Nothing reconnected OctoPrint, so the printer stayed offline until someone
   reconnected by hand or re-selected the model.
2. A `shutdown` arriving inside the 60 s startup grace period was ignored completely
   (`Ignoring unhealthy Klipper state during startup grace period`), so an e-stop
   shortly after boot was never handled at all.

**Fixes:**

| Change | Effect |
|--------|--------|
| `_ensure_serial_connection()` in `MainController` | Re-opens the serial port (saved `port`/`baudrate` preferences, default `/tmp/printer` @ 250000) before each recovery attempt |
| `shutdown` / `error` treated as terminal states | Bypass the startup grace period and the mid-print guard — a terminated Klipper cannot finish a print anyway |
| Factory restore guard | No more hard-coded `"DRAGON_400"` fallback; the restore aborts when the active model cannot be determined |
| `restore_backup_config()` model check | A backup whose `[include PRINTER_*.cfg]` differs from the active model is skipped |

**Verified on the unit:** `M112` sent 7 s after application start →

```
Reconnecting to printer on /tmp/printer @ 250000
Printer connection restored (state: Operational)
Attempt 1/5: Sending FIRMWARE_RESTART command
Klipper state recovered to 'ready' after 1 attempt(s)
```

Recovery took 14 s. `printer.cfg` kept `[include PRINTER_TWINDRAGON_400_HT.cfg]` and
all three `canbus_uuid` values, and the OctoPrint profile stayed "Twin Dragon 400 HT".

Regression test: `test_printer_config_validation.BackupModelGuardTest` (7 tests total,
all passing on the unit).

---

## Timelapse recording

**Symptom:** the Timelapse tab showed *"Take note that timelapse configuration is
disabled while your printer is printing"* and nothing was ever recorded.

**Root cause:** the live `webcam.timelapse` config was `type: off`, and ControlCenter's
`config/config.yaml` template had **no timelapse block at all** — so every deploy
(`update_octoprint_config`) rewrote `config.yaml` and erased the timelapse configuration.
OctoPrint 1.11 also does not persist `webcam.timelapse` when it is set through the
generic settings API, so only `POST /api/timelapse` (or the config file itself) keeps it.

**Fixes:**

| Change | Where |
|--------|-------|
| Template ships `timelapseEnabled: true` and `type: zchange` (fps 25, render after success) | [config/config.yaml](../octoprint_ControlCenter/config/config.yaml) |
| `update_octoprint_config()` preserves the live `webcam.timelapse` / `timelapseEnabled` instead of resetting them to template defaults | [utils/printer_config_manager.py](../octoprint_ControlCenter/utils/printer_config_manager.py) |
| Unit configured via `POST /api/timelapse` and persisted to `~/.octoprint/config.yaml` | printer |
| Removed the misleading banner from the Timelapse tab | printer `octoprint/templates/tabs/timelapse.jinja2` (backup `.pre-fix-20261121`) |

The timelapse *form fields* stay read-only during a print (OctoPrint design — changing
the mode mid-print discards the running capture). Recording itself now starts with every
print: one frame per layer change, rendered to MP4 after a successful print.

**Verified:** after an OctoPrint restart `GET /api/timelapse` still reports
`type: zchange`; the web UI renders the Timelapse tab without the banner; ffmpeg captures
from the snapshot URL on the printer (`SNAPSHOT OK`, 67 KB JPEG); 12 tests pass on the
unit (including two new ones proving a config deploy keeps the timelapse settings).

> The banner removal edits an OctoPrint core template; a future OctoPrint upgrade will
> restore the original file. The recording configuration itself lives in `config.yaml`
> and is re-applied by the ControlCenter template.

---

## Follow-up

1. The two 19 Nov commits plus these are still local-only; a release is needed
   to ship the guard to other units (they run 1.1.8 without it).
2. Network Settings screen raises `Image.__init__() got an unexpected keyword
   argument 'qrcode_modules'` (QR widget vs. installed `qrcode` API).
3. `/home/pi/oprint` still contains an obsolete copy of ControlCenter; it is not
   used by `fw-touchui` (which runs from the OctoPrint venv) but should be removed
   to avoid future confusion.
4. OctoPrint 1.11 deprecates the global API key (removed in 1.13); ControlCenter
   falls back to it on this unit.

---

## Rollback

Printer: copy the `.pre-fix-20261121` files back, or
`cp /home/pi/printer_data/config/printer.cfg.bak.20261121_121932 printer.cfg`
(warning: that file is the broken one), then
`sudo systemctl restart klipper` and `sudo systemctl restart fw-touchui`.

Repo: `git revert <commit>`.
