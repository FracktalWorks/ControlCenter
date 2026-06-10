---
name: octoprint-api
description: "Use when interacting with OctoPrint REST API or WebSocket directly: querying printer state, job status, temperatures, sending G-code commands, jogging axes, homing, extruding, setting temperatures, checking connection status, file management, or debugging OctoPrint communication issues. Use from terminal with curl/Invoke-RestMethod or from Python code. Works with any OctoPrint instance given IP and API key."
argument-hint: '[printer-ip] [api-key] [command]'
user-invocable: true
---
# OctoPrint API Interaction Skill

Direct OctoPrint REST API and WebSocket interaction for printer control, monitoring, and debugging.

## When to Use
- Querying live printer state (temps, position, job progress)
- Sending G-code commands directly to the printer
- Jogging axes, homing, extruding filament
- Setting hotend/bed temperatures
- Checking OctoPrint connection health
- Managing print jobs (start, cancel, pause, resume)
- Debugging why ControlCenter can't communicate with the printer
- Testing API endpoints independently from the ControlCenter app

## Prerequisites
- Printer IP address (e.g., `192.168.0.47`)
- OctoPrint API key (find in OctoPrint Settings → API, or in ControlCenter config)
- Default OctoPrint port: `80` (HTTP) or `443` (HTTPS)

---

## API Quick Reference

### Base URL
```
http://<IP>/api/
```

### Common Headers
```
X-Api-Key: <API_KEY>
Content-Type: application/json
```

---

## PowerShell Commands (Windows Terminal)

### 1. Connection & Version Check
```powershell
# Check if OctoPrint is reachable
Invoke-RestMethod -Uri "http://<IP>/api/version" -Headers @{"X-Api-Key"="<KEY>"} | ConvertTo-Json

# Check current connection to printer
Invoke-RestMethod -Uri "http://<IP>/api/connection" -Headers @{"X-Api-Key"="<KEY>"} | ConvertTo-Json -Depth 5
```

### 2. Printer State (full)
```powershell
# Full printer state including temps, position, flags
$state = Invoke-RestMethod -Uri "http://<IP>/api/printer?history=true&limit=5" -Headers @{"X-Api-Key"="<KEY>"}

# Key fields:
$state.state.text              # "Operational", "Printing", "Paused", etc.
$state.temperature.tool0.actual  # Hotend T0 actual temp
$state.temperature.tool0.target  # Hotend T0 target temp
$state.temperature.bed.actual    # Bed actual temp
$state.temperature.bed.target    # Bed target temp
```

### 3. Job Status
```powershell
$job = Invoke-RestMethod -Uri "http://<IP>/api/job" -Headers @{"X-Api-Key"="<KEY>"}

$job.job.file.name           # Current file printing
$job.progress.completion      # % complete
$job.progress.printTime       # Seconds elapsed
$job.progress.printTimeLeft   # Estimated seconds remaining
```

### 4. Send G-Code Commands
```powershell
# Single command
$body = @{command="G28"} | ConvertTo-Json
Invoke-RestMethod -Uri "http://<IP>/api/printer/command" -Method Post -Headers @{"X-Api-Key"="<KEY>"; "Content-Type"="application/json"} -Body $body

# Multiple commands
$body = @{commands=@("G28", "G1 X100 Y100 F6000", "M400")} | ConvertTo-Json
Invoke-RestMethod -Uri "http://<IP>/api/printer/command" -Method Post -Headers @{"X-Api-Key"="<KEY>"; "Content-Type"="application/json"} -Body $body
```

### 5. Jog Axes
```powershell
# Jog X by 10mm
$body = @{command="jog"; x=10; absolute=$false; speed=6000} | ConvertTo-Json
Invoke-RestMethod -Uri "http://<IP>/api/printer/printhead" -Method Post -Headers @{"X-Api-Key"="<KEY>"; "Content-Type"="application/json"} -Body $body

# Home X and Y
$body = @{command="home"; axes=@("x","y")} | ConvertTo-Json
Invoke-RestMethod -Uri "http://<IP>/api/printer/printhead" -Method Post -Headers @{"X-Api-Key"="<KEY>"; "Content-Type"="application/json"} -Body $body
```

### 6. Set Temperatures
```powershell
# Set hotend T0 to 200°C
$body = @{command="target"; targets=@{tool0=200}} | ConvertTo-Json
Invoke-RestMethod -Uri "http://<IP>/api/printer/tool" -Method Post -Headers @{"X-Api-Key"="<KEY>"; "Content-Type"="application/json"} -Body $body

# Set bed to 60°C
$body = @{command="target"; targets=@{bed=60}} | ConvertTo-Json
Invoke-RestMethod -Uri "http://<IP>/api/printer/bed" -Method Post -Headers @{"X-Api-Key"="<KEY>"; "Content-Type"="application/json"} -Body $body

# Set both at once
$body = @{command="target"; targets=@{tool0=200; bed=60}} | ConvertTo-Json
Invoke-RestMethod -Uri "http://<IP>/api/printer/tool" -Method Post -Headers @{"X-Api-Key"="<KEY>"; "Content-Type"="application/json"} -Body $body
```

### 7. Extrude / Retract
```powershell
# Extrude 10mm at 300mm/min
$body = @{command="extrude"; amount=10; speed=300} | ConvertTo-Json
Invoke-RestMethod -Uri "http://<IP>/api/printer/tool" -Method Post -Headers @{"X-Api-Key"="<KEY>"; "Content-Type"="application/json"} -Body $body

# Retract 5mm
$body = @{command="extrude"; amount=-5; speed=500} | ConvertTo-Json
Invoke-RestMethod -Uri "http://<IP>/api/printer/tool" -Method Post -Headers @{"X-Api-Key"="<KEY>"; "Content-Type"="application/json"} -Body $body
```

### 8. File Management
```powershell
# List files
Invoke-RestMethod -Uri "http://<IP>/api/files" -Headers @{"X-Api-Key"="<KEY>"} | ConvertTo-Json -Depth 5

# Select and start a print
$body = @{command="select"; print=$true} | ConvertTo-Json
Invoke-RestMethod -Uri "http://<IP>/api/files/local/<filename.gcode>" -Method Post -Headers @{"X-Api-Key"="<KEY>"; "Content-Type"="application/json"} -Body $body
```

### 9. Job Control
```powershell
# Pause
$body = @{command="pause"; action="pause"} | ConvertTo-Json
Invoke-RestMethod -Uri "http://<IP>/api/job" -Method Post -Headers @{"X-Api-Key"="<KEY>"; "Content-Type"="application/json"} -Body $body

# Resume
$body = @{command="pause"; action="resume"} | ConvertTo-Json
Invoke-RestMethod -Uri "http://<IP>/api/job" -Method Post -Headers @{"X-Api-Key"="<KEY>"; "Content-Type"="application/json"} -Body $body

# Cancel
$body = @{command="cancel"} | ConvertTo-Json
Invoke-RestMethod -Uri "http://<IP>/api/job" -Method Post -Headers @{"X-Api-Key"="<KEY>"; "Content-Type"="application/json"} -Body $body
```

---

## Bash Commands (from SSH on the Pi itself)

When already SSH'd into the printer, use `curl` to hit localhost:

```bash
# Quick status check
curl -s -H "X-Api-Key: <KEY>" "http://localhost/api/printer?history=false" | python3 -m json.tool

# Send G-code
curl -s -H "X-Api-Key: <KEY>" -H "Content-Type: application/json" \
  -d '{"command":"G28"}' "http://localhost/api/printer/command"

# Home all axes
curl -s -H "X-Api-Key: <KEY>" -H "Content-Type: application/json" \
  -d '{"command":"home","axes":["x","y","z"]}' "http://localhost/api/printer/printhead"

# Set temps
curl -s -H "X-Api-Key: <KEY>" -H "Content-Type: application/json" \
  -d '{"command":"target","targets":{"tool0":200,"bed":60}}' "http://localhost/api/printer/tool"
```

---

## WebSocket (Real-Time Updates)

ControlCenter uses WebSocket for live updates. To test/debug WebSocket connectivity:

```python
import websocket
import json

def on_message(ws, message):
    data = json.loads(message)
    if 'current' in data:
        temps = data['current'].get('temps', [])
        for t in temps:
            print(f"{t.get('name')}: {t.get('actual')}°C / {t.get('target')}°C")

ws = websocket.WebSocketApp(
    "ws://<IP>/sockjs/websocket",
    on_message=on_message
)
ws.run_forever()
```

Key WebSocket message types to watch:
- `current` → temperature updates (`data.current.temps[]`)
- `history` → position updates (`data.current.logs[]`)
- `event` → printer events (print started, paused, error)

---

## Diagnostic Checklist

When debugging OctoPrint communication issues:

1. **Can you reach the API at all?**
   ```powershell
   Invoke-RestMethod -Uri "http://<IP>/api/version" -Headers @{"X-Api-Key"="<KEY>"}
   ```
   - No response → OctoPrint not running or wrong port/IP
   - 403 Forbidden → wrong API key
   - 200 OK with version → API is working

2. **Is OctoPrint connected to Klipper?**
   ```powershell
   $conn = Invoke-RestMethod -Uri "http://<IP>/api/connection" -Headers @{"X-Api-Key"="<KEY>"}
   $conn.current.state   # Should be "Operational" or "Printing"
   ```
   - "Closed" or "Error" → Klipper may have crashed or serial port issue

3. **Are temperature updates flowing?**
   ```powershell
   $state = Invoke-RestMethod -Uri "http://<IP>/api/printer" -Headers @{"X-Api-Key"="<KEY>"}
   $state.temperature   # Check if tool0, bed temps are present and updating
   ```

4. **Check OctoPrint logs on the Pi:**
   ```bash
   tail -50 /home/pi/.octoprint/logs/octoprint.log
   ```

---

## API Key Discovery

If the user doesn't know the API key:
1. Check ControlCenter config: `octoprint_ControlCenter/config/config.yaml`
2. Check on the Pi: `cat /home/pi/.octoprint/config.yaml | grep -i key`
3. Look in OctoPrint web UI: Settings → API → API Key
