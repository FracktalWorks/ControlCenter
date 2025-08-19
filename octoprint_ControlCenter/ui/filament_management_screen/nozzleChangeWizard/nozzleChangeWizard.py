"""
Nozzle Change Wizard
====================

Initial scaffold for the nozzle change flow driven by the UI file
`nozzleChangeWizard.ui`.

What’s implemented now
----------------------
- Load the .ui and wire up core widgets.
- Basic Next/Cancel navigation across 6 steps.
- Step label updates ("Step X/6").
- Simulated "Checking Nozzle Connection" on step 5 with a progress bar
  and automatic transition to step 6 when complete.

What we will add next (placeholders exist)
-----------------------------------------
- Motion, heating, and safety checks.
- Loading of step GIFs from resources.
- Hooks to printer model signals, as needed.
"""

import os
import time
from PyQt5 import uic, QtCore, QtGui
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget, QLabel, QProgressBar, QComboBox

from utils.helpers import check_ui_elements, run_async
from utils.logger import get_logger
from utils import dialog
# Use machineBuildSize from the printer model instead of importing config here


class NozzleChangeWizard(QWidget):
	"""Wizard widget to guide the user through nozzle replacement.

	Responsibilities (current):
	- Load and bind UI elements.
	- Provide basic navigation and step labeling.
	- Simulate the connection check on step 5 using a timer-driven progress bar.

	Later:
	- Integrate motion/heating commands and real connection checks.
	- Load instructional GIFs.
	"""

	# Step indices (0-based) for clarity
	STEP_INTRO = 0
	STEP_DISCONNECT = 1
	STEP_REMOVE_NOZZLE = 2
	STEP_SELECT_NOZZLE = 3
	STEP_CHECK_CONNECTION = 4
	STEP_DONE = 5
	TOTAL_STEPS = 6

	def __init__(self, main_window):
		super().__init__()
		self.main_window = main_window
		# These are commonly present throughout the app; guard if missing.
		self.model = main_window.printer_model
		self.octoprint_client = getattr(main_window, "octoprint_client", None)
		self.active_tool = "tool0"  # default; updated in setup()
		self._did_initial_move = False  # run movement once per open

		self.logger = get_logger(self.__class__.__name__)
		self.logger.info("Initializing NozzleChangeWizard")

		# Load UI
		try:
			ui_file_path = os.path.join(os.path.dirname(__file__), "nozzleChangeWizard.ui")
			uic.loadUi(ui_file_path, self)
			self.logger.debug("nozzleChangeWizard UI loaded")
		except Exception as e:
			self.logger.error(f"Failed to load nozzleChangeWizard UI: {e}", exc_info=True)
			dialog.WarningOk(self, f"Failed to load Nozzle Change Wizard UI: {e}", overlay=True)
			return

		# Bind UI elements
		self.stackedWidget: QStackedWidget = self.findChild(QStackedWidget, "stackedWidget")
		self.stepLabel: QLabel = self.findChild(QLabel, "stepLabel")

		# Step pages (optional to hold references explicitly)
		self.step1Page: QWidget = self.findChild(QWidget, "step1Page")
		self.step2Page: QWidget = self.findChild(QWidget, "step2Page")
		self.step3Page: QWidget = self.findChild(QWidget, "step3Page")
		self.step4Page: QWidget = self.findChild(QWidget, "step4Page")
		self.step5Page: QWidget = self.findChild(QWidget, "step5Page")
		self.step6Page: QWidget = self.findChild(QWidget, "step6Page")

		# Media labels for GIFs (optional loading later)
		self.step2Gif: QLabel = self.findChild(QLabel, "step2Gif")
		self.step3Gif: QLabel = self.findChild(QLabel, "step3Gif")
		self.step4Gif: QLabel = self.findChild(QLabel, "step4Gif")
		self.step6Gif: QLabel = self.findChild(QLabel, "step6Gif")

		# Step 5 specifics
		self.step5Label: QLabel = self.findChild(QLabel, "step5Label")
		self.nozzleCheckProgressBar: QProgressBar = self.findChild(QProgressBar, "nozzleCheckProgressBar")

		# Step 4 specifics (nozzle selection)
		self.changeNozzleComboBox: QComboBox = self.findChild(QComboBox, "changeNozzleComboBox")

		# Buttons
		self.nextButton: QPushButton = self.findChild(QPushButton, "step1NextButton")
		self.cancelButton: QPushButton = self.findChild(QPushButton, "step1CancelButton")

		# Validate required elements
		required = [
			self.stackedWidget,
			self.stepLabel,
			self.step1Page, self.step2Page, self.step3Page, self.step4Page, self.step5Page, self.step6Page,
			self.nozzleCheckProgressBar,
			self.changeNozzleComboBox,
			self.nextButton, self.cancelButton,
		]
		check_ui_elements(self, required, "NozzleChangeWizard")

		# State
		self._current_step = 0
		self._progress_timer = QtCore.QTimer(self)
		self._progress_timer.setInterval(50)  # ms
		self._progress_timer.timeout.connect(self._advance_nozzle_check_progress)

		# Connection handling flags (disconnect REST during step 2; keep WS running)
		self._rest_was_disconnected = False
		self._rest_reconnected = False
		self._awaiting_reconnect_validation = False
		self._reconnect_timeout_timer = QtCore.QTimer(self)
		self._reconnect_timeout_timer.setSingleShot(True)
		# Temp checking state for step 5
		self._temp_check_timer = QtCore.QTimer(self)
		self._temp_check_timer.setInterval(500)
		self._temp_check_timer.timeout.connect(self._temp_check_tick)
		self._temp_check_attempts = 0
		self._temp_check_valid = 0

		# Step 1 guard: disable Next for at least 10 seconds on intro
		self._step1_guard_timer = QtCore.QTimer(self)
		self._step1_guard_timer.setSingleShot(True)
		# Inline handler: when guard elapses and we're still on Step 1, enable Next
		self._step1_guard_timer.timeout.connect(lambda: self._enable_next(True) if self._current_step == self.STEP_INTRO else None)

		# Wire signals
		self.nextButton.clicked.connect(self.on_next_clicked)
		self.cancelButton.clicked.connect(self.on_cancel_clicked)
		# Listen to Klipper state via the printer model (controller wires websocket -> model)
		self._klipper_ready = False
		self.model.klipper_state_changed.connect(self._on_klipper_state)
		try:
			ks = getattr(self.model, 'klipper_state', None)
			self._on_klipper_state(ks)
		except Exception:
			pass

		# Start at step 1
		self.goto_step(self.STEP_INTRO)

		# Preload GIFs from resources and hook page-change playback
		self._resource_dir = os.path.join(os.path.dirname(__file__), "resources")
		# (page_index, target_label, file_name)
		self._gif_specs = [
			(1, self.step2Gif, "1_Cover Removal .gif"),
			(2, self.step3Gif, "2_Nozzle Removal.gif"),
			(3, self.step4Gif, "3_Nozzle Install.gif"),
			(5, self.step6Gif, "4_Cover Install.gif"),
		]
		self._gif_movies = {}  # page_index -> QMovie
		self._load_step_gifs_safe()
		if self.stackedWidget:
			self.stackedWidget.currentChanged.connect(self._on_page_changed)
			# Initialize playback for current page
			self._on_page_changed(self.stackedWidget.currentIndex())

	# ----- Qt events -----------------------------------------------------
	def showEvent(self, event):  # noqa: N802 (Qt naming)
		super().showEvent(event)
		# Match ChangeFilamentWizard: keep showEvent light and only reset the UI
		try:
			self.goto_step(self.STEP_INTRO)
			self.logger.debug("Reset stacked widget to step 1 on show")
		except Exception as e:
			self.logger.warning(f"Error resetting wizard on show: {e}")

	def changeNozzle(self):
		"""Initialize and prepare the nozzle change flow (called from setup)."""
		self.logger.info("NozzleChange.changeNozzle() started")
		# Reset movement gate so each entry can perform the initial move if safe
		self._did_initial_move = False
		try:
			self.goto_step(self.STEP_INTRO)
			tool_str = self.active_tool or "tool0"
			# Preflight: filament unloaded and tool cool
			if not self._check_filament_unloaded(tool_str):
				return
			if not self._check_tool_cool(tool_str):
				return
			# Motion: if safe and idle, home and move
			self._perform_initial_move_if_safe()
		except Exception as e:
			self.logger.error(f"Error initializing nozzle change: {e}")

	# ----- Navigation -----------------------------------------------------
	def goto_step(self, index: int):
		"""Switch to the given step index (0-based)."""
		index = max(0, min(index, self.TOTAL_STEPS - 1))
		self._current_step = index
		if self.stackedWidget:
			self.stackedWidget.setCurrentIndex(index)
		self._update_step_label()

		# Step-specific connection handling
		# Step 2 (index 1): disconnect printer via REST while keeping websocket running
		if index == self.STEP_DISCONNECT:
			self._disconnect_printer_soft()
		# Step 5 handled in _begin_reconnect_validation

		# Enter/leave step-specific hooks
		if index == self.STEP_CHECK_CONNECTION:  # Step 5 page (0-based index)
			self._begin_reconnect_validation()
		else:
			self._teardown_step5_connections()
			self._stop_nozzle_check()

		# Step 4 setup/teardown
		if index == self.STEP_SELECT_NOZZLE:
			self._prepare_step4()
		else:
			self._teardown_step4()

		# Step 1 guard handling: start when entering intro; stop when leaving
		if index == self.STEP_INTRO:
			try:
				if self._step1_guard_timer.isActive():
					self._step1_guard_timer.stop()
				# Always enforce a fresh 10s guard when showing step 1
				self._enable_next(False)
				self._step1_guard_timer.start(10000)
			except Exception:
				pass
		else:
			try:
				if self._step1_guard_timer.isActive():
					self._step1_guard_timer.stop()
			except Exception:
				pass


		# Enable/disable Next based on step and update label
		if self.nextButton:
			if index == self.STEP_CHECK_CONNECTION:
				self._enable_next(False)
			elif index == self.STEP_SELECT_NOZZLE:
				self._enable_next(bool(self.changeNozzleComboBox and self.changeNozzleComboBox.currentIndex() > 0))
			elif index == self.STEP_INTRO:
				# Keep disabled during the intro guard; will be enabled on timer elapsed
				self._enable_next(False)
			else:
				self._enable_next(True)
			self.nextButton.setText("Done" if index == self.STEP_DONE else "Next")

	def on_next_clicked(self):
		try:
			# If we are on the last step, treat Next as Done
			if self._current_step >= self.STEP_DONE:
				self.on_finish_clicked()
				return
			# Enforce selection and persist nozzle (step 4)
			if self._current_step == self.STEP_SELECT_NOZZLE:
				if not self.changeNozzleComboBox or self.changeNozzleComboBox.currentIndex() <= 0:
					dialog.WarningOk(self, "Please select a nozzle size to continue.", overlay=True)
					return
				nozzle = self.changeNozzleComboBox.currentText()
				try:
					self.model.update_tool_bay_state(self.active_tool, nozzle=nozzle, persist=True)
					self.logger.info(f"Persisted nozzle '{nozzle}' for {self.active_tool}")
				except Exception as e:
					self.logger.warning(f"Unable to persist nozzle selection: {e}")
			# If we are on step 5, Next is disabled until progress completes.
			self.goto_step(self._current_step + 1)
		except Exception as e:
			self.logger.error(f"Error advancing to next step: {e}")

	def on_cancel_clicked(self):
		try:
			self._stop_nozzle_check()
			# If we previously disconnected in step 2 and haven't reconnected, reconnect now
			if self._rest_was_disconnected and not self._rest_reconnected:
				self._connect_printer_soft()
			# Return to the filament management screen if available
			fms = getattr(self.main_window, "filament_management_screen", None)
			if fms and hasattr(fms, "show_material_nozzle_screen"):
				fms.show_material_nozzle_screen()
			# Reset to step 1 for the next open
			self.goto_step(0)
		except Exception as e:
			self.logger.error(f"Error cancelling nozzle change wizard: {e}")
			dialog.WarningOk(self, f"Error cancelling Nozzle Change Wizard: {e}", overlay=True)

	def _update_step_label(self):
		try:
			if self.stepLabel:
				self.stepLabel.setText(f"Step {self._current_step + 1}/{self.TOTAL_STEPS}")
		except Exception:
			pass



	# ----- Step 5: Nozzle connection check (simulated) -------------------
	def _start_nozzle_check(self):
		try:
			self._set_step5_status("Checking Nozzle Connection ...", 0)
			self._progress_timer.start()
			self._enable_next(False)
		except Exception as e:
			self.logger.warning(f"Failed to start nozzle check simulation: {e}")

	def _advance_nozzle_check_progress(self):
		try:
			if not self.nozzleCheckProgressBar:
				return
			value = self.nozzleCheckProgressBar.value() + 2
			if value >= 100:
				value = 100
				self._stop_nozzle_check()
				if self.step5Label:
					self.step5Label.setText("Nozzle connection OK")
				# Auto-advance to step 6 after short delay
				QtCore.QTimer.singleShot(300, lambda: self.goto_step(5))
				return
			self.nozzleCheckProgressBar.setValue(value)
		except Exception:
			# Keep UI responsive even if something goes wrong
			pass

	def _stop_nozzle_check(self):
		try:
			if self._progress_timer.isActive():
				self._progress_timer.stop()
			# Re-enable Next outside of step 5
			if self._current_step != self.STEP_CHECK_CONNECTION:
				self._enable_next(True)
		except Exception:
			pass

	def on_finish_clicked(self):
		"""Finish the wizard and return to the main Material/Nozzle page."""
		try:
			self._stop_nozzle_check()
			# Ensure we reconnect if we had disconnected earlier
			if self._rest_was_disconnected and not self._rest_reconnected:
				self._connect_printer_soft()
			fms = getattr(self.main_window, "filament_management_screen", None)
			if fms and hasattr(fms, "show_material_nozzle_screen"):
				fms.show_material_nozzle_screen()
			# Reset to step 1 ready for next open
			self.goto_step(0)
		except Exception as e:
			self.logger.error(f"Error finishing nozzle change wizard: {e}")

	# (preflight and motion handled via changeNozzle() called from setup)

	# ----- Media helpers --------------------------------------------------
	def _load_step_gifs_safe(self):
		"""Create QMovies for each step GIF and attach to their labels."""
		try:
			self._gif_movies.clear()
			for page_idx, label, fname in self._gif_specs:
				if not label or not fname:
					continue
				path = os.path.join(self._resource_dir, fname)
				movie = QtGui.QMovie(path)
				if not movie.isValid():
					self.logger.debug(f"GIF not valid or missing: {path}")
					continue
				movie.setCacheMode(QtGui.QMovie.CacheAll)
				label.setMovie(movie)
				self._gif_movies[page_idx] = movie
		except Exception as e:
			self.logger.debug(f"GIFs not loaded: {e}")

	def _stop_all_gifs(self):
		"""Stop all loaded GIF movies."""
		for movie in list(self._gif_movies.values()):
			try:
				movie.stop()
			except Exception:
				pass

	def _play_gif_for_page(self, page_idx: int, restart: bool = True):
		"""Start the GIF for a given page index; optionally restart from frame 0."""
		movie = self._gif_movies.get(page_idx)
		if not movie:
			return
		try:
			if restart:
				movie.stop()
			movie.start()
		except Exception:
			pass

	def _on_page_changed(self, idx: int):
		"""Keep only the current page's GIF playing for clarity and performance."""
		try:
			self._stop_all_gifs()
			self._play_gif_for_page(idx, restart=True)
		except Exception:
			pass

	def _on_klipper_state(self, state: str):
		self._klipper_ready = (str(state).strip().lower() == 'ready')

	# ----- Step 5: reconnect and validate temperature ---------------------
	def _begin_reconnect_validation(self):
		"""On step 5, reconnect to printer, wait for Operational, reselect tool, validate temp, then advance or go back."""
		try:
			# Update UI for connection phase
			self._set_step5_status("Connecting to printer ...", 10)
			# Guard against multiple connections
			self._awaiting_reconnect_validation = True
			self._temp_check_attempts = 0
			self._temp_check_valid = 0
			# Fire the (soft) reconnect sequence
			self._connect_printer_soft()
			# Start async waiter for Operational + Klipper ready before any printer ops
			self._wait_for_ready_async()
		except Exception as e:
			self.logger.warning(f"Failed to begin reconnect validation: {e}")

	def _teardown_step5_connections(self):
		try:
			if self._reconnect_timeout_timer.isActive():
				self._reconnect_timeout_timer.stop()
			if self._temp_check_timer.isActive():
				self._temp_check_timer.stop()
			self._awaiting_reconnect_validation = False
		except Exception:
			pass

	@run_async
	def _wait_for_ready_async(self):
		"""Background wait until printer is Operational and Klipper is ready, or timeout."""
		deadline = time.time() + 60.0
		ready = False
		while time.time() < deadline and self._awaiting_reconnect_validation:
			try:
				status = str(getattr(self.model, 'printer_status', '')).strip().lower()
				if status == 'operational' and self._klipper_ready:
					ready = True
					break
			except Exception:
				pass
			time.sleep(1)
		if not self._awaiting_reconnect_validation:
			return
		if not ready:
			QtCore.QTimer.singleShot(0, lambda: self._handle_reconnect_failure("Unable to reconnect to the printer. Please check connections and try again."))
			return
		# Ready: proceed on main thread
		QtCore.QTimer.singleShot(0, self._on_ready_then_check)

	def _on_ready_then_check(self):
		if not self._awaiting_reconnect_validation:
			return
		# Update UI and progress
		self._set_step5_status("Connected. Checking nozzle temperature ...", 70)
		# Select the correct tool now that Klipper is ready
		try:
			tool_idx = int((self.active_tool or "tool0").replace("tool", "") or 0)
			self.octoprint_client.selectTool(tool_idx)
		except Exception:
			pass
		# Start temperature validation shortly
		QtCore.QTimer.singleShot(500, self._validate_reconnect_temperature)

	def _handle_reconnect_failure(self, message: str):
		self._awaiting_reconnect_validation = False
		try:
			dialog.WarningOk(self, message, overlay=True)
			QtCore.QTimer.singleShot(0, lambda: self.goto_step(3))
		except Exception:
			pass

	def _validate_reconnect_temperature(self):
		"""Start periodic temperature sampling to avoid junk readings and reflect progress."""
		if not self._awaiting_reconnect_validation:
			return
		try:
			# Initialize sampling counters
			self._temp_check_attempts = 0
			self._temp_check_valid = 0
			self._set_step5_status(None, 75)
			self._temp_check_timer.start()
		except Exception as e:
			self.logger.warning(f"Failed to start temperature sampling: {e}")

	def _temp_check_tick(self):
		if not self._awaiting_reconnect_validation:
			self._temp_check_timer.stop()
			return
		try:
			self._temp_check_attempts += 1
			tool_idx = int((self.active_tool or "tool0").replace("tool", "") or 0)
			temps = getattr(self.model, 'temperatures', {}) or {}
			actual = temps.get(f'tool{tool_idx}Actual')
			try:
				actual_val = float(actual) if actual is not None else None
			except Exception:
				actual_val = None
			if actual_val is not None and 15 <= actual_val <= 50:
				self._temp_check_valid += 1
				# Increase progress for valid samples towards 100
				if self.nozzleCheckProgressBar:
					base = 75
					inc = min(self._temp_check_valid, 3) * 8  # 75 -> 99 over 3 valid samples
					self.nozzleCheckProgressBar.setValue(min(base + inc, 99))
			# Decide outcome
			if self._temp_check_valid >= 3:
				self._temp_check_timer.stop()
				self._set_step5_status("Nozzle connection OK", 100)
				self._awaiting_reconnect_validation = False
				QtCore.QTimer.singleShot(200, lambda: self.goto_step(5))
				return
			# Allow up to 50 attempts total before failing
			if self._temp_check_attempts >= 50 and self._temp_check_valid < 3:
				self._temp_check_timer.stop()
				try:
					dialog.WarningOk(self, "There was a connection issue. Please recheck the connections.", overlay=True)
					QtCore.QTimer.singleShot(0, lambda: self.goto_step(3))
				finally:
					self._awaiting_reconnect_validation = False
		except Exception as e:
			self._temp_check_timer.stop()
			self._awaiting_reconnect_validation = False
			self.logger.warning(f"Temperature sampling failed: {e}")

	def _on_reconnect_timeout(self):
		# Could not reach Operational in time
		self._reconnect_timeout_timer.stop()
		if not self._awaiting_reconnect_validation:
			return
		try:
			dialog.WarningOk(self, "Unable to reconnect to the printer. Please check connections and try again.", overlay=True)
			QtCore.QTimer.singleShot(0, lambda: self.goto_step(3))
		finally:
			self._awaiting_reconnect_validation = False

	# ----- Connection helpers --------------------------------------------
	def _disconnect_printer_soft(self):
		"""Disconnect the printer via REST, keeping our websocket client running."""
		if not self.octoprint_client:
			return
		try:
			self.octoprint_client.disconnect()
			self._rest_was_disconnected = True
			self._rest_reconnected = False
			self.logger.info("OctoPrint REST: disconnect command sent (websocket remains connected)")
		except Exception as e:
			self.logger.warning(f"Failed to disconnect printer (soft): {e}")

	def _connect_printer_soft(self):
		"""Reconnect the printer via REST using saved settings."""
		if not self.octoprint_client:
			return
		try:
			# Connect to Klipper's virtual serial at the expected port and baudrate
			self.octoprint_client.connectPrinter(port="/tmp/printer", baudrate=115200)
			self.nozzleCheckProgressBar.setValue(30)
			# Issue Klipper restarts after a short delay to allow the serial link to be ready
			self.step5Label.setText("Restarting Klipper ...")
			self.nozzleCheckProgressBar.setValue(50)
			self._rest_reconnected = True
			self.logger.info("OctoPrint REST: connect command sent")
		except Exception as e:
			self.logger.warning(f"Failed to reconnect printer (soft): {e}")


	# ----- Step 4: Nozzle selection ---------------------------------------
	def _prepare_step4(self):
		"""Populate nozzle options and enforce selection before proceeding."""
		try:
			try:
				self.changeNozzleComboBox.currentIndexChanged.disconnect(self._on_nozzle_choice_changed)
			except Exception:
				pass

			self.changeNozzleComboBox.clear()
			self.changeNozzleComboBox.addItem("Select nozzle size")
			options = []
			if self.model is not None and hasattr(self.model, 'nozzle_options'):
				options = list(getattr(self.model, 'nozzle_options') or [])
			if not options:
				options = ["0.25", "0.4", "0.6", "0.8", "1.0"]
			for opt in options:
				self.changeNozzleComboBox.addItem(str(opt))

			# Preselect current nozzle if available in model state
			current_nozzle = None
			try:
				if self.model and hasattr(self.model, 'get_bay_state') and self.active_tool:
					state = self.model.get_bay_state(self.active_tool)
					current_nozzle = state.get('nozzle') if isinstance(state, dict) else None
			except Exception:
				current_nozzle = None

			if current_nozzle:
				idx = self.changeNozzleComboBox.findText(str(current_nozzle))
				if idx > 0:
					self.changeNozzleComboBox.setCurrentIndex(idx)

			# Next enabled only when a real selection is made
			if self.nextButton:
				self.nextButton.setEnabled(self.changeNozzleComboBox.currentIndex() > 0)

			self.changeNozzleComboBox.currentIndexChanged.connect(self._on_nozzle_choice_changed)
		except Exception as e:
			self.logger.warning(f"Failed to prepare step 4: {e}")

	def _teardown_step4(self):
		try:
			if self.changeNozzleComboBox:
				try:
					self.changeNozzleComboBox.currentIndexChanged.disconnect(self._on_nozzle_choice_changed)
				except Exception:
					pass
		except Exception:
			pass

	def _on_nozzle_choice_changed(self, idx: int):
		try:
			if self.nextButton:
				self.nextButton.setEnabled(idx > 0)
		except Exception:
			pass


	# ----- Public API for parent screen -----------------------------------
	def setup(self, params=None):
		"""Prepare wizard with optional parameters.

		Params may be a dict like {"tool": "tool0"} or a str "tool0".
		"""
		try:
			tool = None
			if isinstance(params, dict):
				tool = params.get("tool")
			elif isinstance(params, str):
				tool = params
			if tool in ("tool0", "tool1"):
				self.active_tool = tool
			self.logger.info(f"NozzleChangeWizard.setup: active_tool={self.active_tool}")
			# Kick off the nozzle change flow like ChangeFilamentWizard.changeFilament()
			self.changeNozzle()
		except Exception as e:
			self.logger.error(f"Error in NozzleChangeWizard.setup: {e}")

	# ----- Helpers: readability and reuse ---------------------------------
	def _enable_next(self, enabled: bool):
		try:
			if self.nextButton:
				self.nextButton.setEnabled(bool(enabled))
		except Exception:
			pass

	def _set_step5_status(self, text: str = None, progress: int = None):
		if text is not None and self.step5Label:
			self.step5Label.setText(text)
		if progress is not None and self.nozzleCheckProgressBar:
			self.nozzleCheckProgressBar.setValue(int(progress))

	def _show_material_nozzle_screen_and_return(self):
		fms = getattr(self.main_window, "filament_management_screen", None)
		if fms and hasattr(fms, "show_material_nozzle_screen"):
			QtCore.QTimer.singleShot(0, lambda: fms.show_material_nozzle_screen())
		return False

	def _get_tool_index(self, tool: str) -> int:
		try:
			return int((tool or "tool0").replace('tool', '') or 0)
		except Exception:
			return 0

	def _is_printer_idle(self) -> bool:
		status = (str(getattr(self.model, 'printer_status', '')) or '').lower()
		return status not in ('printing', 'paused')

	def _check_filament_unloaded(self, tool: str) -> bool:
		try:
			state = self.model.get_bay_state(tool) or {}
			if str(state.get('status')) == 'Loaded':
				dialog.WarningOk(self, "Filament is loaded. Please unload filament before changing the nozzle.", overlay=True)
				return self._show_material_nozzle_screen_and_return()
			return True
		except Exception:
			return True

	def _check_tool_cool(self, tool: str) -> bool:
		try:
			temps = self.model.temperatures or {}
			tool_idx = self._get_tool_index(tool)
			t = temps.get(f'tool{tool_idx}') or temps.get(f'tool{tool_idx}Actual')
			if t is not None and float(t) > 50:
				dialog.WarningOk(self, "Tool temperature is too high to touch (> 50°C). Please initiate cooling and wait for it to be cool enough to touch", overlay=True)
				return self._show_material_nozzle_screen_and_return()
			return True
		except Exception:
			return True

	def _perform_initial_move_if_safe(self):
		try:
			if self._did_initial_move or not self._is_printer_idle():
				return
			size = self.model.machineBuildSize
			x = int((size.get('X') or 0) / 2)
			y = 0.0
			if self.octoprint_client:
				self.octoprint_client.gcode("G90")
				self.octoprint_client.gcode("G28")
				try:
					tool_idx = self._get_tool_index(self.active_tool)
					self.octoprint_client.selectTool(tool_idx)
				except Exception:
					pass
				self.octoprint_client.jog(z=-10, absolute=False, speed=1800)
				self.octoprint_client.jog(x=x, y=y, absolute=True, speed=6000)
			self._did_initial_move = True
		except Exception as move_err:
			self.logger.warning(f"Initial move skipped: {move_err}")

