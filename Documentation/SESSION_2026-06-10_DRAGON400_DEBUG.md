# Live Debugging Session — 2026-06-10

## Printer: Dragon 400 @ 192.168.0.47

### Session Summary
Connected via SSH and OctoPrint API to diagnose a paused print with filament sensor issues.

---

## Actions Taken

### 1. Network Configuration
- **Port 80 redirect**: Set up nftables NAT rule redirecting port 80 → 5000 so OctoPrint is accessible at `http://192.168.0.47/` without specifying a port.
  - Rules: `table inet nat { chain prerouting/output { tcp dport 80 redirect to :5000 } }`
  - Persisted to `/etc/nftables.conf`, service enabled at boot.
- **OctoPrint port**: 5000 (default OctoPrint port)
- **API Key**: `B508534ED20348F090B4D0AD637D3660`

### 2. Service Cleanup
- **Removed Moonraker**: Stopped, disabled, masked the service. Removed all associated files:
  - `/home/pi/moonraker/` (source, 8.9 MB)
  - `/home/pi/moonraker-env/` (Python venv, 99 MB)
  - `/home/pi/printer_data/config/moonraker.conf`
  - `/home/pi/printer_data/logs/moonraker.log*` (3 files)
  - `/home/pi/printer_data/database/moonraker-sql.db`
  - `/home/pi/printer_data/systemd/moonraker.env`
  - `/home/pi/kiauh/kiauh/components/moonraker/`
  - `/etc/systemd/system/moonraker.service`
  - `/usr/share/polkit-1/rules.d/moonraker.rules`
- **Rationale**: ControlCenter exclusively uses OctoPrint REST API + WebSocket. Moonraker was idle (zero active connections). Updates can be handled via OctoPrint plugins or SSH.
- **Total freed**: ~108 MB

### 3. Print Diagnostics

#### Current Print State (via OctoPrint API)
| Field | Value |
|-------|-------|
| State | **Paused** |
| File | `TD400_Pooja assoc 11hours 386g.gcode` |
| Progress | 1.64% |
| Elapsed | 44 min |
| Hotend | 204.8°C / 205°C |
| Bed | 59.9°C / 60°C |

#### Klipper Log Analysis (from `/home/pi/printer_data/logs/klippy.log`)
| Metric | Value | Assessment |
|--------|-------|------------|
| `print_stall` | 23 | 🔴 Critical — OctoPrint can't feed gcode fast enough |
| `buffer_time` | 0.4–3.8s | 🔴 Warning — frequently below 2s minimum |
| `sysload` | 0.05–0.09 | ✅ Good |
| `memavail` | ~1.1 GB | ✅ Good |
| CAN `tx_retries` | 11,000–11,200 | 🟡 Watch — ~4 retries/sec, no errors |
| Filament sensor events | ~every 6 sec | 🔴 Critical — false triggering |

#### Root Cause Hypothesis
The print paused because `[filament_switch_sensor T0_RUNOUT]` is firing repeated runout events every ~6 seconds. The `[filament_motion_sensor encoder_sensor_T0]` (jam sensor) is disabled at startup via `SET_T0_FILAMENT_JAM_SENSOR_STARTUP`, so the culprit is the **runout switch sensor**, not the jam/encoder sensor.

---

## Files Modified on Printer

| File | Change |
|------|--------|
| `/etc/nftables.conf` | Added port 80 → 5000 redirect rules |
| `/etc/systemd/system/moonraker.service` | Removed |
| `/home/pi/printer_data/config/moonraker.conf` | Removed |

---

## Agent Skills Created/Updated

| File | Action |
|------|--------|
| `.github/skills/klipper-ssh-debug/SKILL.md` | Created + updated with ControlCenter error patterns |
| `.github/skills/octoprint-api/SKILL.md` | Created with PowerShell + Bash API recipes |

---

## Phase 2: Stop-Start / Bandwidth Starvation Debugging

### Problem
Even simple models (benchy) stutter. Old 32-bit Buster system worked fine with same G-code. New Debian 13 Trixie 64-bit has periodic buffer starvation.

### Architecture Discovery
- **Raspberry Pi Compute Module 4** (BCM2711, 4× Cortex-A72, 1.5 GHz)
- **Klipper → MCU**: CAN bus via USB CAN adapter (`gs_usb` driver, OpenMoko CAN adapter)
- **MCU**: STM32H723 in CAN bus bridge mode (USB → CAN bridge)
- **Toolhead**: RP2040 on CAN bus
- **OctoPrint → Klipper**: Virtual serial via PTY (`/dev/pts/0`, symlinked as `/tmp/printer`)

### Root Cause
Multiple system-level regressions from Debian 10 Buster (32-bit) → Debian 13 Trixie (64-bit) + kernel 6.12:

| Category | Old (Buster 32-bit) | New (Trixie 64-bit) | Impact |
|----------|---------------------|---------------------|--------|
| WiFi Power Save | Probably disabled | **ON** (default) | Periodic CPU interruptions every ~100ms beacon |
| USB Autosuspend | Probably disabled | **2s default** | CAN adapter could suspend mid-print |
| CPU Isolation | N/A | No isolation | All 4 cores shared with system tasks |
| GPU Memory | Minimal | 76 MB | Wasted RAM on headless system |
| vc4-kms-v3d | Probably disabled | Active | Unnecessary DRM/KMS overhead |
| SD Card Clock | Default | Default | G-code read latency |
| Klipper Priority | SCHED_OTHER | SCHED_OTHER | Can be preempted by any process |
| Swappiness | Maybe tuned | 60 (default) | Kernel could swap during prints |
| PTY Baudrate | Unknown | 115200 | Kernel tty layer may throttle |

### Fixes Applied

#### Live (immediate effect, no restart)
| Fix | Before | After |
|-----|--------|-------|
| WiFi Power Save | ON | OFF (`iw set power_save off`) |
| USB Autosuspend | 2s | Disabled (`-1`) |
| PTY Baudrate | 115200 | 921600 (`stty -F /dev/pts/0`) |
| Swappiness | 60 | 1 |
| vfs_cache_pressure | 100 | 50 |
| RT Runtime Limit | 950000/default | -1 (unlimited) |

#### Persistent (survives reboot)
| File | Change |
|------|--------|
| `/boot/firmware/config.txt` | `gpu_mem=16`, `force_turbo=1`, `dtparam=sd_overclock=100`, `#dtoverlay=vc4-kms-v3d` |
| `/boot/firmware/cmdline.txt` | Added `usbcore.autosuspend=-1 isolcpus=3 nohz_full=3 rcu_nocbs=3` |
| `/etc/rc.local` | WiFi power save OFF + PTY baudrate 921600 |
| `/etc/sysctl.d/10-klipper-realtime.conf` | swappiness=1, vfs_cache_pressure=50, sched_rt_runtime_us=-1 |
| `/etc/systemd/system/klipper.service.d/override.conf` | SCHED_FIFO 99, CPUAffinity=3, LimitMEMLOCK=infinity |
| `/home/pi/.octoprint/config.yaml` | `baudrate: 250000`, `serial.log: true` |

#### Needs Restart to Activate
- Klipper: SCHED_FIFO + CPU isolation (CPU3)
- OctoPrint: 250000 baudrate + serial logging
- Reboot needed for: config.txt, cmdline.txt changes

### Current Print Status
- `print_stall=40` (was 25 at start of session, accumulated)
- Print still running at ~3% (auto-resumed from pause)
- Buffer starvation pattern persists (min buffer_time 0.24s, was 0.08s — slight improvement)

## Next Steps (Pending)

1. **Stop print & reboot** — Apply all persistent changes (config.txt, cmdline.txt, service overrides)
2. **Run test print** — Verify if stop-start is resolved
3. **Check serial.log** — If still stuttering, OctoPrint serial log will reveal exact bottleneck
4. **Investigate filament runout sensor** — `T0_FILAMENT_RUNOUT_SENSOR.cfg` false-triggering
5. **Investigate print_stall** — check if print_stall still increments after fixes
