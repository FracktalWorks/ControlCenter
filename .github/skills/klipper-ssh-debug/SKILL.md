---
name: klipper-ssh-debug
description: "Use when connecting to a 3D printer via SSH for live debugging: reading klipper logs (klippy.log), running Klipper diagnostic commands (DUMP_TMC, QUERY_ENDSTOPS, QUERY_FILAMENT_SENSOR, GET_POSITION), checking service status, parsing Stats lines for print_stall/buffer_time/tx_retries, diagnosing MCU shutdowns, TMC driver errors, filament sensor events, or CAN bus issues. Also use when the user gives a printer IP, username, and password and wants to investigate printer problems live."
argument-hint: '[printer-ip] [username] [password]'
user-invocable: true
---
# Klipper SSH Debugging Skill

Live SSH-based troubleshooting of Klipper 3D printers. Connects to Raspberry Pi printers, reads logs, runs diagnostics, and interprets results.

## When to Use
- User provides printer IP + credentials and wants live debugging
- Investigating print quality issues from klipper logs
- Diagnosing MCU shutdowns, TMC driver errors, thermal issues
- Checking print stalls, buffer underruns, CAN bus retries
- Filament sensor false triggers or misconfiguration
- Verifying Klipper/OctoPrint/Moonraker service health
- Running DUMP_TMC, QUERY_ENDSTOPS, or other diagnostic commands

## Prerequisites
- Printer IP address, SSH username, and password from the user
- Printer must be reachable on port 22 from the local machine

---

## Procedure

### Step 1: Verify Connectivity
```powershell
Test-NetConnection -ComputerName <IP> -Port 22
```
If port 22 is unreachable, the printer is offline or firewalled. Inform the user.

### Step 2: Establish SSH Session (async + password)

**CRITICAL**: On Windows, `sshpass` is NOT available. Use the two-step async pattern:

```powershell
# Start SSH in async mode (will prompt for password)
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 <user>@<IP>
```
Wait for password prompt, then send password via `send_to_terminal`. The session stays alive for subsequent commands.

**Alternative**: If the user has an SSH key already set up, use:
```powershell
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 <user>@<IP>
```

### Step 3: Gather System Overview
Run these commands chained together for efficiency:
```bash
echo "=== SYSTEM ===" && uname -a && \
echo "=== KLIPPER ===" && sudo systemctl is-active klipper && \
echo "=== OCTOPRINT ===" && sudo systemctl is-active octoprint && \
echo "=== MOONRAKER ===" && sudo systemctl is-active moonraker 2>/dev/null || echo "moonraker not installed" && \
echo "=== DISK ===" && df -h / && \
echo "=== MEMORY ===" && free -h && \
echo "=== PRINTER CONFIG ===" && grep -E '^\s*\[include' /home/pi/printer.cfg 2>/dev/null
```
**Note**: `sudo` may prompt for password — use the same password as SSH login on Raspberry Pi defaults.

### Step 4: Locate and Read Klipper Log

**Log locations** (check in order):
| Path | When used |
|------|-----------|
| `/home/pi/printer_data/logs/klippy.log` | Moonraker-based installs (most common) |
| `/tmp/klippy.log` | Legacy/older installs |
| `/home/pi/klipper.log` | Very old installs |

Find it:
```bash
find /home/pi -name "klippy.log" -o -name "klipper.log" 2>/dev/null
```

Read recent entries:
```bash
tail -80 /home/pi/printer_data/logs/klippy.log
```

### Step 5: Parse Key Log Patterns

#### Print State (from Stats lines)
```
Stats 5430.0: ... print_time=5443.064 buffer_time=3.784 print_stall=23 ...
```
| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| `print_stall` | 0 | 1-5 | >10 (host can't feed gcode fast enough) |
| `buffer_time` | >5.0s | 2.0-5.0s | <2.0s (risk of starvation) |
| `sysload` | <1.0 | 1.0-2.0 | >2.0 (CPU overloaded) |
| `memavail` | >500MB | 200-500MB | <200MB |

#### CAN Bus Health (from canstat_toolhead lines)
```
canstat_toolhead0: ... rx_error=0 tx_error=0 tx_retries=11200 ...
```
- `rx_error > 0` or `tx_error > 0`: Critical — physical CAN bus fault (wiring, termination)
- `tx_retries` climbing rapidly (>10/sec): Noise or interference on CAN bus
- `bus_state=active`: Normal. `bus_state=passive` or `off`: Severe CAN errors

#### Filament Sensor Events
```
Filament Sensor switch_sensor_T0: runout event detected, Time 5432.91
```
If events fire every ~6 seconds repeatedly: sensor is flaky/false-triggering.
- Check sensor wiring and connector seating
- Check `[filament_switch_sensor]` config for correct `switch_pin` and pull-up (`^`)
- Add debounce: increase `pause_on_runout: False` if custom macros handle it

#### MCU Errors
Look for patterns like:
```
MCU 'mcu' shutdown: Timer too close
MCU 'mcu' shutdown: ADC out of range
```
- "Timer too close" → USB instability, high accel, or power supply noise
- "ADC out of range" → Thermistor wiring fault or wrong `sensor_type`

### Step 6: Run Diagnostic G-Code Commands

**TMC Driver Status**:
```bash
# Via OctoPrint API (preferred — see octoprint-api skill)
# Or inject directly if Klipper API is available:
echo "DUMP_TMC STEPPER=stepper_x" >> /tmp/printer
```

**Endstop Status**:
```bash
echo "QUERY_ENDSTOPS" >> /tmp/printer
```

**Filament Sensor Status**:
```bash
echo "QUERY_FILAMENT_SENSOR SENSOR=T0_RUNOUT" >> /tmp/printer
```

**Position**:
```bash
echo "GET_POSITION" >> /tmp/printer
```

### Step 7: Check Configuration Files
```bash
# List all active config includes
grep -E '^\s*\[include' /home/pi/printer.cfg

# View PRINTER_VARIABLES
grep -A 30 '\[gcode_macro PRINTER_VARIABLES\]' /home/pi/printer.cfg

# Check save_variables (runtime state)
cat /home/pi/variables.cfg 2>/dev/null
```

---

## Diagnostic Quick-Reference

| Symptom in Log | Likely Cause | Action |
|---------------|-------------|--------|
| `print_stall` > 0 | OctoPrint/network can't keep up | Check WiFi signal, SD card speed, OctoPrint plugins |
| `tx_retries` climbing | CAN bus noise | Check CAN wiring, termination, cable routing |
| `Filament Sensor ... runout event detected` repeating | Flaky sensor | Check wiring, connector, debounce settings |
| `Heater not heating at expected rate` | Wiring, PID, thermistor | Run `PID_CALIBRATE`, check thermistor type |
| `TMC ...: Driver error` | Overcurrent/overtemp | Run `DUMP_TMC`, reduce `run_current` |
| `Move out of range` | Homing failed, bad offset | Re-home, check `position_min/max` |
| `Timer too close` | USB noise/power | USB isolator, check PSU, reduce `max_accel` |
| `gcodein` not incrementing | Print paused/stalled | Check OctoPrint job state, filament sensor |

---

## ControlCenter-Specific Error Patterns

> From `Documentation/ERROR_HANDLING_IMPROVEMENTS.md`

### The Cascading Error Chain (Critical to Recognize)
When debugging mid-print failures where the UI shows "Printer is not ready, Cancelling Print":

1. Transient Klipper state change fires `onKlipperStateChanged()`
2. That triggers `FIRMWARE_RESTART` recovery
3. Restart causes transient "Printer is not ready" + MCU reset errors
4. `showPrinterError()` sees "Printer is not ready" as critical → cancels print + M112
5. M112 causes "Shutdown due to M112" → re-enters handler → cascade

**Fix pattern**: add re-entrancy guard (`_handling_critical_error` flag) + mid-print guard (skip FIRMWARE_RESTART when Printing/Paused). See `main_controller.py` for implementation.

### CRITICAL_PRINTER_ERRORS Pitfalls
- Substring matching is used — be specific to avoid false positives
- `"probe"` matched innocent messages like `"probe accuracy results:"` — replaced with `"Probe triggered prior to movement"`
- `"Error loading template"` and `"Must home axis first"` are Klipper `CommandError`s, NOT shutdowns — do NOT treat as critical

### Klipper Restart Grace Period
When restarting Klipper intentionally (after SAVE_CONFIG):
1. Set `_klipper_restart_in_progress = True` before sending RESTART
2. Use a grace timer (timeout + 10s) to suppress transient MCU errors
3. Wait async for Klipper state → 'ready' before continuing
4. Use `restart_klipper_and_wait()` utility in `main_controller.py`

---

## WebSocket Debugging Notes

> From `Documentation/WEBSOCKET_UI_UPDATE_FIXES.md`

### Common WebSocket Failure Modes
1. **`@run_async` on `process()`** — NEVER decorate the WebSocket message processor with @run_async. It spawns ephemeral threads that cause silent signal drops and race conditions. The QThread's event loop already handles cross-thread delivery.
2. **Direct `self.printer_model` access from WebSocket** — ALWAYS route through Qt signals. The WebSocket runs on its own QThread; direct model access causes AttributeError (silently swallowed) or thread-safety issues.
3. **Permanent reconnect give-up** — After 5 failed reconnect attempts, the WebSocket permanently stops. Fix: back off 30s, reset counter, retry indefinitely.

### Correct Data Flow
```
WebSocket (QThread) → pyqtSignal → PrinterModel (QObject) → pyqtSignal → UI Screens
```

---

## Post-Diagnosis
- Summarize findings in a table (service status, key metrics, anomalies)
- Propose minimal config changes with exact file paths
- Provide test procedure to verify each fix
- Always check both single-nozzle and dual-nozzle code paths when suggesting ControlCenter app changes
- **Document significant findings** in `Documentation/` folder for future reference
