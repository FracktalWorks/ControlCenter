---
name: klipper-log-analyzer
description: "Use when analyzing Klipper klippy.log Stats lines for print quality issues: bandwidth usage, buffer starvation (print_stall), host buffer time sawtooth patterns, MCU task load, CAN bus retries, system load, and identifying the root cause of stop-start/stuttering behavior. This skill contains the source code of the OctoKlipper KlipperLogAnalyzer module and explains how to interpret its output."
argument-hint: '[klippy.log path or printer IP]'
user-invocable: true
---
# Klipper Log Analyzer Skill

Analyzes Klipper `klippy.log` Stats lines to diagnose print quality issues — especially bandwidth starvation, buffer underruns, and stop-start behavior.

Based on the OctoKlipper plugin's `KlipperLogAnalyzer` (v0.3.9.5, AGPLv3).

## When to Use
- Printer stuttering / stop-start during prints
- High "bandwidth usage" or "host buffer usage" reported by OctoKlipper's Analyse Print Log
- Investigating `print_stall` values > 0
- Seeing buffer_time sawtooth patterns in logs
- Diagnosing whether the bottleneck is OctoPrint, Klipper, USB, or CAN bus

## Key Metrics in Stats Lines

Each Stats line in klippy.log looks like:
```
Stats 7544.4: gcodein=479413 mcu: mcu_awake=0.014 mcu_task_avg=0.000001 bytes_write=5964273 bytes_read=2933478 bytes_retransmit=0 ... toolhead0: ... print_time=7554.987 buffer_time=2.408 print_stall=25 ... sysload=0.43 memavail=1137160
```

### Critical Metrics

| Metric | What It Means | Healthy Range |
|--------|---------------|---------------|
| `print_stall` | Times the motion queue was starved (cumulative, never decreases) | **0** — any value > 0 is a problem |
| `buffer_time` | Seconds of G-code buffered ahead of the toolhead (sawtooths when starving) | > 1.0s, stable |
| `gcodein` | Total G-code commands received by Klipper (stalls = OctoPrint not sending) | Should increment every Stats line |
| `mcu: bytes_retransmit` | USB retransmissions to main MCU | **0** |
| `mcu: tx_retries` | USB transmit retries to main MCU | **0** |
| `toolhead0: tx_retries` | CAN bus retries to toolhead | < 1000 over a print |
| `mcu_task_avg` | Average time MCU spends processing each command | < 0.001 (0.1%) |
| `sysload` | Linux system load average | < 1.0 |
| `memavail` | Available RAM in bytes | > 100MB |

### Sawtooth Pattern Detection (from KlipperLogAnalyzer source)

The OctoKlipper plugin's `find_print_restarts()` method detects buffer runoff events:

```python
# A "runoff" event occurs when buffer_time drops below 1.0 second
# If the print_stall counter resets (decreases), it indicates a Klipper restart
# between prints — those runoffs are NOT print defects.
# Runoffs without a print_stall reset ARE print defects (actual starvation).
```

## Diagnostic Flowchart

```
1. Check mcu: bytes_retransmit & tx_retries
   ├─ > 0 → USB cable/noise/power issue (hardware)
   └─ = 0 → USB is clean, continue

2. Check gcodein across consecutive Stats lines
   ├─ Constantly incrementing → OctoPrint is feeding fine
   └─ Stalls (same value 3+ seconds) → OctoPrint bottleneck

3. Check buffer_time pattern
   ├─ Stable > 1.0 → healthy
   ├─ Sawtooth (high→low→high) + gcodein stalls → OctoPrint starvation
   └─ Always low (< 0.5) → G-code too dense for serial speed

4. Check toolhead0: tx_retries (CAN bus)
   ├─ Climbing rapidly (> 10/sec) → CAN wiring/noise issue
   └─ Slow climb (< 5/sec) → normal for CAN, not the root cause

5. Check sysload & memavail
   ├─ sysload > 2.0 → Pi CPU bottleneck
   └─ memavail < 50MB → Pi memory pressure
```

## Root Cause → Fix Mapping

| Root Cause | Symptoms | Fix |
|-----------|----------|-----|
| **OctoPrint serial plugin throttling** | gcodein stalls, USB clean, low CPU | Increase baudrate, disable `sendChecksumWithUnknownCommands`, increase `maxConsecutiveResends` |
| **G-code too dense** | buffer_time always < 0.5s even when streaming, high bytes_write rate | Re-slice with larger minimum segment length, use ArcWelder plugin |
| **OctoPrint I/O bottleneck** | gcodein stalls, Pi disk I/O high | Move gcodes to faster storage, enable virtual_sdcard direct print |
| **Pi CPU bottleneck** | sysload > 2.0, gcodein stalls | Reduce OctoPrint plugins, disable camera streaming during print |
| **USB noise** | mcu: bytes_retransmit > 0 | Replace USB cable, add ferrite bead, USB isolator |
| **CAN bus noise** | toolhead0: tx_retries climbing fast | Check CAN wiring, termination resistors (120Ω) |
| **virtual_sdcard missing** | Not using Klipper's native file handling | Add `[virtual_sdcard]` to printer.cfg, print via SD card upload |

## OctoKlipper KlipperLogAnalyzer Reference

### API Endpoint
The `getStats` command is called via OctoPrint's plugin API:
```
POST /api/plugin/octoklipper
Body: {"command": "getStats", "logFile": "/path/to/klippy.log"}
```

### Analysis Algorithm (from source)

```python
MAXBANDWIDTH = 25000.0    # 25,000 bytes/sec = 100% on graph
MAXBUFFER = 2.0           # 2 seconds = 100% buffer on graph
STATS_INTERVAL = 5.0      # Stats collection interval
TASK_MAX = 0.0025          # Max acceptable MCU task time
```

**Bandwidth %**: `(bytes_write_delta / (MAXBANDWIDTH * time_delta)) * 100`
- Above 50% consistently → G-code is very dense
- Spikes above 100% → bursts that may cause stalls

**Host Buffer %**: `((MAXBUFFER - buffer_time) / MAXBUFFER) * 100`
- Near 100% (buffer near 0) → printer about to stall
- The "risk zone" is when this approaches 100%

**Load %**: `((mcu_task_avg + 3*mcu_task_stddev) / TASK_MAX) * 100`
- Above 50% → MCU is working hard
- Above 100% → MCU overloaded

**Awake %**: `(mcu_awake / STATS_INTERVAL) * 100`
- Indicates how much time the MCU spends awake vs sleeping
- High values → MCU is saturated

### Print Restart Detection
The `find_print_restarts()` method identifies when `print_stall` decreases (indicating a Klipper restart between prints), so it doesn't flag buffer runoffs from a previous print session as current print defects.

## Quick SSH Diagnostic Commands

```bash
# Get latest Stats lines (last 2 minutes of printing)
tail -200 /home/pi/printer_data/logs/klippy.log | grep "Stats" | tail -30

# Count total stalls
grep "Stats" /home/pi/printer_data/logs/klippy.log | tail -1 | grep -oP 'print_stall=\K\d+'

# Check for USB errors (should be 0)
grep "Stats" /home/pi/printer_data/logs/klippy.log | tail -100 | grep -oP 'mcu:.*?bytes_retransmit=\K\d+' | sort -u

# Check buffer_time range (min and max)
grep "Stats" /home/pi/printer_data/logs/klippy.log | tail -100 | grep -oP 'buffer_time=\K[\d.]+' | sort -n | head -1
grep "Stats" /home/pi/printer_data/logs/klippy.log | tail -100 | grep -oP 'buffer_time=\K[\d.]+' | sort -n | tail -1

# Check for gcodein stalls (same value repeating)
grep "Stats" /home/pi/printer_data/logs/klippy.log | tail -100 | grep -oP 'gcodein=\K\d+' | uniq -c | sort -rn | head -5
```

## OctoPrint Serial Settings to Check

```bash
# Check current connection settings
curl -s -H "X-Api-Key: <KEY>" http://<IP>:5000/api/connection

# Key settings that affect streaming performance:
# - baudrate: should be 250000 for virtual serial (not 115200)
# - port: /tmp/printer (Klipper virtual serial)
# - sendChecksumWithUnknownCommands: should be false for Klipper
# - maxConsecutiveResends: increase if getting resend requests
```
