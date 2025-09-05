---
mode: 'agent'
tools: ['codebase']
description: 'Fix issues and debug problems in the ControlCenter project'
---

# Debug and Fix Issues

Your goal is to debug and fix issues in the ControlCenter 3D printer interface.

## Requirements

Ask for the specific issue description, error messages, or problem symptoms if not provided.

Common issue types:
* UI loading failures or missing elements
* OctoPrint communication problems
* Temperature or position monitoring issues
* Wizard navigation or state problems
* Signal/slot connection issues

## Debugging Approach

### Error Analysis
* Review error logs and stack traces
* Check UI element initialization and validation
* Verify signal/slot connections
* Validate file paths and imports

### Common Issues
* Missing UI elements - check Qt Designer names and `findChild()` calls
* Configuration not loading - verify Klipper file paths and permissions
* WebSocket connection issues - check OctoPrint connectivity and API
* Signal disconnection errors - ensure proper cleanup in destructors

## Diagnostic Steps
1. Check logging output for error details
2. Verify UI component initialization with `check_ui_elements()`
3. Test OctoPrint client connection and API responses
4. Validate configuration file access and parsing
5. Review signal/slot connection patterns

## Fix Patterns
Follow debugging patterns from `.github/instructions.md`:
* Add comprehensive error handling with try-catch blocks
* Use proper logging for diagnostic information
* Implement fallback behaviors for failed operations
* Validate all external dependencies and connections

## Testing
* Test fixes on both single and dual nozzle configurations
* Verify UI responsiveness on 800x480 touchscreen
* Test with connected and disconnected printer states
* Validate error handling with various failure scenarios

Provide detailed analysis of the root cause and implement robust fixes that prevent similar issues.
