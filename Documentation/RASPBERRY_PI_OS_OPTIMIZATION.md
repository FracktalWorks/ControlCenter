# Raspberry Pi OS Optimization for Klipper + OctoPrint

## Target System
- **Hardware**: Raspberry Pi Compute Module 4 (BCM2711, 4× Cortex-A72 @ 1.5 GHz)
- **OS**: Debian 13 Trixie 64-bit (kernel 6.12)
- **Purpose**: Real-time 3D printer control — Klipper firmware + OctoPrint + ControlCenter

## Problem Solved
After migrating from Debian 10 Buster (32-bit) to Debian 13 Trixie (64-bit), even simple prints experienced severe **stop-start stuttering** with `print_stall` values of 48-52 and buffer_time sawtoothing between 0.08s and 4.4s every ~6 seconds.

### Root Cause
Multiple power management, scheduling, and kernel regressions introduced in the newer OS caused:
1. WiFi power-save interrupts disrupting CPU scheduling
2. USB autosuspend causing CAN adapter latency
3. No CPU isolation — Klipper competed with system tasks
4. Default SCHED_OTHER priority — Klipper could be preempted
5. High swappiness — kernel swapped during prints
6. GPU memory wasting RAM on a headless system

### Result After Optimization
- **print_stall: 48-52 → 0-2** (96% reduction)
- **buffer_time: 0.08s-4.4s sawtooth → stable 2.0-2.7s**
- **Same G-code file** that previously stalled every ~6s now runs uninterrupted

---

## All Changes by File

### 1. `/boot/firmware/config.txt`

This is the Raspberry Pi firmware configuration. Add/change these lines:

```ini
# === Performance & Thermal ===
arm_boost=1                  # Run at max clock (1.5 GHz)
force_turbo=1                # Never downclock, even under thermal load
temp_limit=75                # Throttle at 75°C (safe margin below 85°C max)

# === Memory ===
gpu_mem=16                   # Minimal GPU RAM (headless system, saves ~60MB)

# === Disable Unused Hardware ===
camera_auto_detect=0         # No CSI ribbon camera (USB cameras use uvcvideo — unaffected)
dtoverlay=disable-bt         # No Bluetooth needed
dtparam=audio=on             # Keep audio for ControlCenter alerts
#dtoverlay=vc4-kms-v3d       # DISABLE GPU DRM driver (headless printer, saves RAM + CPU)

# === Storage ===
dtparam=sd_overclock=100     # Faster SD/eMMC reads for G-code files

# === Display ===
hdmi_ignore_hotplug=1        # Don't poll for HDMI changes (saves power)

# === Reliability ===
dtparam=watchdog=on          # Enable hardware watchdog timer
disable_splash=1             # No boot splash (faster boot)
```

### 2. `/boot/firmware/cmdline.txt`

Kernel boot parameters. Add these to the existing line (space-separated, all on one line):

```
usbcore.autosuspend=-1 isolcpus=3 nohz_full=3 rcu_nocbs=3
```

| Parameter | Effect |
|-----------|--------|
| `usbcore.autosuspend=-1` | Never autosuspend USB devices (CAN adapter stays active) |
| `isolcpus=3` | Isolate CPU core 3 from kernel scheduler |
| `nohz_full=3` | Disable timer tick on CPU 3 (real-time, no jitter) |
| `rcu_nocbs=3` | Offload RCU callbacks from CPU 3 |

Full example cmdline.txt:
```
console=serial0,115200 console=tty1 root=PARTUUID=d5d53d76-02 rootfstype=ext4 fsck.repair=yes rootwait usbcore.autosuspend=-1 isolcpus=3 nohz_full=3 rcu_nocbs=3 quiet splash loglevel=0
```

### 3. `/etc/systemd/system/klipper.service.d/override.conf`

Give Klipper real-time priority and pin it to the isolated CPU:

```bash
sudo mkdir -p /etc/systemd/system/klipper.service.d
sudo tee /etc/systemd/system/klipper.service.d/override.conf << 'EOF'
[Service]
CPUSchedulingPolicy=fifo
CPUSchedulingPriority=99
LimitMEMLOCK=infinity
CPUAffinity=3
EOF
sudo systemctl daemon-reload
```

| Setting | Effect |
|---------|--------|
| `CPUSchedulingPolicy=fifo` | SCHED_FIFO — real-time scheduling, no time-slice expiry |
| `CPUSchedulingPriority=99` | Highest real-time priority |
| `LimitMEMLOCK=infinity` | Allow unlimited mlock (needed for real-time) |
| `CPUAffinity=3` | Pin Klipper to CPU 3 (matches isolcpus) |

### 4. `/etc/sysctl.d/10-klipper-realtime.conf`

Kernel runtime tuning:

```bash
sudo tee /etc/sysctl.d/10-klipper-realtime.conf << 'EOF'
# Minimize swapping during prints
vm.swappiness=1
# Reduce tendency to drop caches
vm.vfs_cache_pressure=50
# Unlimited real-time CPU time (SCHED_FIFO can run indefinitely)
kernel.sched_rt_runtime_us=-1
# Disable IPv6 (reduces network stack overhead on printer-only network)
net.ipv6.conf.all.disable_ipv6=1
net.ipv6.conf.default.disable_ipv6=1
net.ipv6.conf.lo.disable_ipv6=1
# TCP optimizations
net.core.rmem_default=65536
net.core.wmem_default=65536
net.ipv4.tcp_slow_start_after_idle=0
EOF
sudo sysctl -p /etc/sysctl.d/10-klipper-realtime.conf
```

### 5. `/etc/rc.local`

Runtime commands executed at boot:

```bash
sudo tee /etc/rc.local << 'EOF'
#!/bin/sh
# Disable WiFi power management (prevents periodic CPU interrupts)
/usr/sbin/iw dev wlan0 set power_save off

# Set pseudo-terminal baudrate high (kernel tty layer may throttle on 115200)
/bin/stty -F /dev/pts/0 921600 2>/dev/null || /bin/true

# Pin USB interrupt (CAN adapter) to Klipper's CPU core
# IRQ 30 = xhci-hcd:usb1 (check with: cat /proc/interrupts | grep usb)
# 8 = CPU 3 affinity mask
/bin/echo 8 > /proc/irq/30/smp_affinity 2>/dev/null || /bin/true

exit 0
EOF
sudo chmod +x /etc/rc.local
```

> **Note**: The IRQ number (30) may differ on other Pi models. Find it with:
> ```bash
> cat /proc/interrupts | grep -i "usb\|xhci"
> ```

### 6. `/etc/fstab`

Reduce filesystem write pressure:

```
PARTUUID=xxxxx  /  ext4  defaults,noatime,commit=60  0  1
```

| Option | Effect |
|--------|--------|
| `noatime` | Don't update file access timestamps (reduces writes) |
| `commit=60` | Flush journal every 60s instead of 5s (fewer writes, slight risk on power loss) |

### 7. `/home/pi/.octoprint/config.yaml`

OctoPrint serial settings (edit with `python3 -c "import yaml..."` — YAML structure matters):

```yaml
serial:
  port: /tmp/printer
  baudrate: 250000          # Was 115200 — higher virtual serial speed
  autoconnect: true
  disconnectOnErrors: false
  ignoreErrorsFromFirmware: true
  log: true                 # Enable serial.log for debugging
```

### 8. Services to Disable

```bash
# Disable Bluetooth
sudo systemctl disable --now bluetooth
sudo systemctl mask bluetooth

# Disable Avahi/mDNS (Bonjour service discovery — not needed)
sudo systemctl disable --now avahi-daemon
```

### 9. Log Rotation

Prevent logs from filling the SD card:

```bash
# Klipper log rotation (daily, max 100MB, keep 7 days)
sudo tee /etc/logrotate.d/klipper << 'EOF'
/home/pi/printer_data/logs/klippy.log {
    daily
    rotate 7
    maxsize 100M
    missingok
    notifempty
    copytruncate
    compress
    delaycompress
}
EOF

# OctoPrint log rotation (weekly, max 50MB, keep 4 weeks)
sudo tee /etc/logrotate.d/octoprint << 'EOF'
/home/pi/.octoprint/logs/*.log {
    weekly
    rotate 4
    maxsize 50M
    missingok
    notifempty
    copytruncate
    compress
    delaycompress
}
EOF
```

### 10. Thermal Monitoring

```bash
# Create thermal monitor script
sudo tee /usr/local/bin/thermal-monitor.sh << 'EOF'
#!/bin/bash
LOG=/home/pi/printer_data/logs/thermal.log
TEMP_RAW=$(vcgencmd measure_temp | grep -oP '\d+\.\d+')
TEMP_INT=${TEMP_RAW%.*}
THROTTLE=$(vcgencmd get_throttled | grep -oP '0x\d+')
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "$TIMESTAMP temp=${TEMP_RAW}°C throttled=${THROTTLE}" >> $LOG

if [ "$TEMP_INT" -gt 70 ]; then
    echo "$TIMESTAMP WARNING: High temp ${TEMP_RAW}°C" >> $LOG
fi
if [ "$TEMP_INT" -gt 73 ]; then
    logger -t thermal "CRITICAL: Pi at ${TEMP_RAW}°C — consider cooling"
fi
if [ -f "$LOG" ] && [ "$(stat -c%s "$LOG" 2>/dev/null)" -gt 1048576 ]; then
    mv "$LOG" "${LOG}.old"
fi
EOF
sudo chmod +x /usr/local/bin/thermal-monitor.sh

# Run every 5 minutes via cron
(crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/thermal-monitor.sh") | crontab -
```

### 11. Hardware Watchdog

```bash
# Install watchdog daemon
sudo apt-get install -y watchdog

# Configure
sudo tee /etc/watchdog.conf << 'EOF'
watchdog-device = /dev/watchdog
watchdog-timeout = 15
realtime = yes
priority = 1
interval = 10
pidfile = /home/pi/printer_data/comms/klippy.pid
max-load-1 = 24
min-memory = 1
EOF

sudo systemctl enable watchdog
```

---

## Verification Checklist

After applying all changes and rebooting, verify each one:

```bash
# 1. CPU governor
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor  # Should be: performance

# 2. CPU isolation
cat /proc/cmdline | grep -o "isolcpus=\S*"    # Should be: isolcpus=3

# 3. GPU memory
vcgencmd get_mem gpu                            # Should be: gpu=16M

# 4. USB autosuspend
cat /sys/module/usbcore/parameters/autosuspend  # Should be: -1

# 5. WiFi power save
iw dev wlan0 get power_save                     # Should be: Power save: off

# 6. Swappiness
cat /proc/sys/vm/swappiness                     # Should be: 1

# 7. Klipper scheduling
systemctl show klipper -p CPUSchedulingPolicy -p CPUSchedulingPriority -p CPUAffinity
# Should be: CPUSchedulingPolicy=1 CPUSchedulingPriority=99 CPUAffinity=3

# 8. Klipper CPU affinity
taskset -cp $(pgrep -f klippy.py)               # Should show: affinity list: 3

# 9. USB IRQ affinity
cat /proc/irq/30/smp_affinity                   # Should be: 8 (CPU 3)

# 10. IPv6 disabled
cat /proc/sys/net/ipv6/conf/all/disable_ipv6    # Should be: 1

# 11. Services
systemctl is-active klipper octoprint            # Both should be: active
systemctl is-active bluetooth avahi-daemon       # Both should be: inactive

# 12. No throttling history
vcgencmd get_throttled                           # Should be: throttled=0x0

# 13. Temperature
vcgencmd measure_temp                            # Should be < 50°C at idle

# 14. PTY baudrate
stty -a -F /dev/pts/0 2>/dev/null | head -1     # Should show: speed 921600 baud

# 15. OctoPrint baudrate
curl -s -H "X-Api-Key: <KEY>" http://localhost:5000/api/connection | python3 -c "import sys,json; print(json.load(sys.stdin)['current']['baudrate'])"
# Should be: 250000
```

---

## Files Summary

| File | Purpose |
|------|---------|
| `/boot/firmware/config.txt` | Pi firmware: clocks, memory, thermal, overlays |
| `/boot/firmware/cmdline.txt` | Kernel: USB, CPU isolation, RCU |
| `/etc/systemd/system/klipper.service.d/override.conf` | Klipper: real-time priority + CPU pinning |
| `/etc/sysctl.d/10-klipper-realtime.conf` | Kernel: swappiness, IPv6, TCP, RT runtime |
| `/etc/rc.local` | Boot-time: WiFi PS off, PTY speed, IRQ affinity |
| `/etc/fstab` | Filesystem: noatime + commit=60 |
| `/home/pi/.octoprint/config.yaml` | OctoPrint: baudrate 250000, serial logging |
| `/etc/logrotate.d/klipper` | Klipper log rotation |
| `/etc/logrotate.d/octoprint` | OctoPrint log rotation |
| `/usr/local/bin/thermal-monitor.sh` | Temperature logging (cron every 5 min) |
| `/etc/watchdog.conf` | Hardware watchdog configuration |

---

## Notes for Replication on Other Printer Setups

1. **IRQ number** — The USB IRQ (30 on CM4) may differ. Find yours via:
   ```bash
   cat /proc/interrupts | grep -i "usb\|xhci"
   ```

2. **CPU count** — `isolcpus=3` assumes 4 cores (0-3). On Pi 5 (4 cores), use the same. On Pi Zero 2W (4 cores), same. On older Pi 2/3 (4 cores), same.

3. **Network type** — If using Ethernet instead of WiFi, you can skip `iw set power_save off`. The WiFi power-save fix is only needed for WiFi-connected printers.

4. **32-bit vs 64-bit** — All settings work on both architectures. The 64-bit migration was the trigger for these issues, but the fixes are architecture-independent.

5. **GPU driver** — Only disable `vc4-kms-v3d` if the Pi is truly headless (no graphical desktop, no ControlCenter touchscreen). ControlCenter uses Xorg on the framebuffer — vc4-kms-v3d can stay enabled for display-heavy setups.

6. **Audio** — Keep `dtparam=audio=on` if ControlCenter uses audio alerts. Disable it (`dtparam=audio=off`) only on fully headless, audio-free setups.

7. **USB cameras** — The `camera_auto_detect=0` only affects CSI ribbon cameras. USB UVC cameras (used by ControlCenter) are completely unaffected.

8. **Reboot required** — Most config.txt and cmdline.txt changes require a full reboot. The sysctl, service, and rc.local changes take effect immediately or on service restart.
