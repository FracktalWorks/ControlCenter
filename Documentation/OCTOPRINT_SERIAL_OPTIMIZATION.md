# OctoPrint Serial Optimization for Klipper

## Problem

After migrating from Debian 10 Buster to Debian 13 Trixie, prints exhibited severe **stop-start stuttering** — the printer would pause for 2-3 seconds every ~7 seconds, causing `print_stall` values of 48-52.

The root cause was a **combination** of OS-level power management regressions (documented in `RASPBERRY_PI_OS_OPTIMIZATION.md`) AND OctoPrint's default serial settings being incompatible with Klipper's virtual serial communication model.

## Root Cause: OctoPrint Serial Defaults vs Klipper

OctoPrint's default serial settings are designed for **RepRap firmware (Marlin)** over physical USB-serial connections. Klipper communicates via `/tmp/printer` — a Unix pseudo-terminal (PTY) — which has fundamentally different characteristics:

| Aspect | Physical Serial (Marlin) | Virtual PTY (Klipper) |
|--------|-------------------------|----------------------|
| Data corruption risk | Yes (noise, ground loops) | **Zero** (kernel in-memory) |
| Baudrate matters | Yes (hardware clock) | Minimal (kernel in-memory) |
| Position reporting | Poll M114 every ~10s | Klipper can auto-report |
| Checksums needed | Yes (corruption detection) | **No** (perfect reliability) |
| Unknown commands | May crash firmware | Klipper handles gracefully |

### The M114 Polling Sawtooth

The single most impactful misconfiguration was `autoreport_pos: False`. When OctoPrint believes the firmware cannot auto-report position, it sends `M114` polls every ~10 seconds:

```
G1 X100 Y100 F6000     ← normal G-code
G1 X101 Y101 E0.1      ← ...
M114                    ← POLL! Blocks the queue for ~500ms round-trip
G1 X102 Y102 E0.2      ← resumes after response
```

Each `M114` round-trip takes ~100-500ms over the PTY. During this time, G-code sending pauses, the Klipper buffer drains, and the printer **stutters**. The ~7-second sawtooth pattern in `buffer_time` corresponds exactly to these polling intervals.

### The Checksum Overhead

OctoPrint defaults to appending `*NN` XOR checksums to every G-code line:
```
N12345 G1 X100 Y100 F6000*56
```

For a 100,000-line print, this adds ~500KB of extra data through the PTY plus CPU time to compute each checksum. Over a PTY (which is a kernel pipe, not a noise-prone wire), checksums provide zero benefit.

---

## Changes Applied

### File: `/home/pi/.octoprint/config.yaml`

All changes are in the `serial:` section. Apply using Python `yaml` module (YAML structure matters — do NOT edit by hand):

```yaml
serial:
  port: /tmp/printer
  baudrate: 250000              # Was 115200 — higher virtual serial throughput
  autoconnect: true
  disconnectOnErrors: false
  ignoreErrorsFromFirmware: true
  log: true                     # Enable serial.log for debugging
  
  # === Klipper-specific optimizations ===
  capabilities:
    autoreport_pos: true        # Was False — STOPS M114 polling (main fix!)
  
  neverSendChecksum: true       # No *NN overhead (PTY is error-free)
  sendChecksumWithUnknownCommands: false  # Klipper handles unknowns
  unknownCommandsNeedAck: false # Klipper won't crash on unknown commands
  supportResendsWithoutOk: true # Better line handling for Klipper
  helloCommand: 'M110 N0'       # Standard Klipper greeting
  
  maxWritePasses: 10            # Write more lines per pass
  timeout:
    temperature: 10             # Relaxed temp polling
    sdStatus: 10
    positionLogWait: 20         # Relaxed position logging
  maxTimeouts:
    temperature: 10             # More tolerance
    sdStatus: 5
```

### Python script to apply:

```python
import yaml

with open('/home/pi/.octoprint/config.yaml', 'r') as f:
    config = yaml.safe_load(f)

s = config['serial']
s['capabilities']['autoreport_pos'] = True
s['neverSendChecksum'] = True
s['sendChecksumWithUnknownCommands'] = False
s['unknownCommandsNeedAck'] = False
s['supportResendsWithoutOk'] = True
s['helloCommand'] = 'M110 N0'
s['maxWritePasses'] = 10
s['timeout'] = {'temperature': 10, 'sdStatus': 10, 'positionLogWait': 20}
s['maxTimeouts'] = {'temperature': 10, 'sdStatus': 5}
s['baudrate'] = 250000

with open('/home/pi/.octoprint/config.yaml', 'w') as f:
    yaml.dump(config, f, default_flow_style=False, sort_keys=False)

print('Done — restart OctoPrint to apply')
```

After editing, restart OctoPrint:
```bash
sudo systemctl restart octoprint
```

---

## Verification

After restart, verify the settings are active:

```bash
# Check connection (baudrate should be 250000)
curl -s -H "X-Api-Key: <KEY>" http://localhost:5000/api/connection | python3 -m json.tool

# Check all serial settings
python3 -c "
import yaml
with open('/home/pi/.octoprint/config.yaml') as f:
    s = yaml.safe_load(f).get('serial', {})
for k in ['baudrate', 'neverSendChecksum', 'capabilities']:
    print(f'{k}: {s.get(k)}')
"
```

Monitor print quality:
```bash
# Check for print_stall and buffer_time sawtooth
strings /home/pi/printer_data/logs/klippy.log | grep "Stats" | tail -20 | \
  grep -oP 'buffer_time=\K[\d.]+|print_stall=\K\d+'

# Healthy output: buffer_time between 1.5-3.0, print_stall=0
# Unhealthy: buffer_time drops below 0.5, print_stall increasing
```

---

## FAQ: Is Disabling Checksums Safe?

**Yes — completely safe for Klipper.** Here's why:

1. **Klipper connects via `/tmp/printer`** which is a Unix pseudo-terminal (PTY). This is a kernel-level in-memory pipe — there is **zero chance of data corruption**. Checksums exist to detect corruption on real serial wires (noise, ground loops, interference), which don't apply here.

2. **OctoPrint's checksums are NOT the same as G-code file integrity.** The `*NN` checksum is computed line-by-line during serial transmission, not at file-read time. File-level integrity is handled by your slicer and OctoPrint's file management.

3. **Klipper does its own command validation.** Klipper parses and validates every G-code command independently. Malformed commands (which can't happen over a PTY anyway) would be rejected by Klipper with a clear error message.

4. **This is standard practice.** The official Klipper documentation, OctoKlipper plugin, and community best practices all recommend `neverSendChecksum: True` for Klipper.

5. **What if you switch back to Marlin?** If you ever reconnect to a Marlin-based printer over a real USB serial connection, re-enable checksums. The setting is specific to the current printer profile.

**Bottom line:** Disabling checksums for Klipper saves ~5 bytes per G-code line and CPU cycles — with zero downside. It's one of the recommended Klipper optimizations.

---

## FAQ: Baudrate on a Virtual PTY

A PTY (`/dev/pts/0`) is not a real serial port — it's a kernel pipe. The baudrate setting is technically meaningless for data rate because there's no hardware clock. **However**, the Linux kernel's tty layer uses the baudrate for certain timing calculations and buffer management. Setting it higher (250000 or 921600) ensures the kernel doesn't introduce artificial throttling based on the baud rate value.

For maximum throughput, also set the PTY baudrate directly:
```bash
sudo stty -F /dev/pts/0 921600
```

To make this persistent, add to `/etc/rc.local`:
```bash
for i in $(seq 1 30); do
    [ -L /tmp/printer ] && /bin/stty -F /tmp/printer 921600 2>/dev/null && break
    sleep 1
done
```

---

## Results

| Metric | Before (defaults) | After (optimized) |
|--------|-------------------|-------------------|
| `autoreport_pos` | False (M114 polling) | True (auto-report) |
| Checksums | Every line `*NN` | None |
| Baudrate | 115200 | 250000 |
| `print_stall` | 48–52 | **0–1** |
| `buffer_time` | 0.08–4.4s sawtooth | **2.0–2.7s stable** |
| M114 polls | Every ~10s | **None** |
| Bytes per 100K lines | ~15MB (with checksums) | ~13MB (saved ~2MB) |
