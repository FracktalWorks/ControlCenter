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
from PyQt5 import uic, QtCore, QtGui
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget, QLabel, QProgressBar, QComboBox

from utils.helpers import check_ui_elements
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

		# Wire signals
		self.nextButton.clicked.connect(self.on_next_clicked)
		self.cancelButton.clicked.connect(self.on_cancel_clicked)

		# Start at step 1
		self.goto_step(0)

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
			self.goto_step(0)
			self.logger.debug("Reset stacked widget to step 1 on show")
		except Exception as e:
			self.logger.warning(f"Error resetting wizard on show: {e}")

	def changeNozzle(self):
		"""Initialize and prepare the nozzle change flow (called from setup)."""
		self.logger.info("NozzleChange.changeNozzle() started")
		# Reset movement gate so each entry can perform the initial move if safe
		self._did_initial_move = False
		try:
			self.goto_step(0)
			model = self.model
			tool_str = self.active_tool or "tool0"
			# Preflight: filament must be unloaded
			try:
				state = model.get_bay_state(tool_str) or {}
				if str(state.get('status')) == 'Loaded':
					dialog.WarningOk(self, "Filament is loaded. Please unload filament before changing the nozzle.", overlay=True)
					fms = getattr(self.main_window, "filament_management_screen", None)
					if fms and hasattr(fms, "show_material_nozzle_screen"):
						QtCore.QTimer.singleShot(0, lambda: fms.show_material_nozzle_screen())
					return
			except Exception:
				pass
			# Preflight: tool should be cool to touch
			try:
				temps = model.temperatures or {}
				tool_idx = int(tool_str.replace('tool', '') or 0)
				t = temps.get(f'tool{tool_idx}') or temps.get(f'tool{tool_idx}Actual')
				if t is not None and float(t) > 50:
					dialog.WarningOk(self, "Tool temperature is too high to touch (> 50°C). Please initiate cooling and wait for it to be cool enough to touch", overlay=True)
					fms = getattr(self.main_window, "filament_management_screen", None)
					if fms and hasattr(fms, "show_material_nozzle_screen"):
						QtCore.QTimer.singleShot(0, lambda: fms.show_material_nozzle_screen())
					return
			except Exception:
				pass
			# Motion: if safe and idle, home and move to front-center (X/2, Y=0) and lower Z slightly
			try:
				status = (str(getattr(model, 'printer_status', '')) or '').lower()
				if not self._did_initial_move and status not in ('printing', 'paused'):
					size = model.machineBuildSize
					x = int((size.get('X') or 0) / 2)
					y = 0.0
					if self.octoprint_client:
						self.octoprint_client.gcode("G90")
						self.octoprint_client.gcode("G28")
						try:
							tool_idx = int((self.active_tool or "tool0").replace("tool", "") or 0)
							self.octoprint_client.selectTool(tool_idx)
						except Exception:
							pass
						self.octoprint_client.jog(z=-10, absolute=False, speed=1800)
						self.octoprint_client.jog(x=x, y=y, absolute=True, speed=6000)
					self._did_initial_move = True
			except Exception as move_err:
				self.logger.warning(f"Initial move skipped: {move_err}")
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

		# Enter-step hooks
		if index == 4:  # Step 5 page (0-based index)
			self._start_nozzle_check()
		else:
			self._stop_nozzle_check()

		# Step 4 setup/teardown
		if index == 3:
			self._prepare_step4()
		else:
			self._teardown_step4()


		# Enable/disable Next based on step and update label
		if self.nextButton:
			if index == 4:
				self.nextButton.setEnabled(False)
			elif index == 3:
				enabled = bool(self.changeNozzleComboBox and self.changeNozzleComboBox.currentIndex() > 0)
				self.nextButton.setEnabled(enabled)
			else:
				self.nextButton.setEnabled(True)
			self.nextButton.setText("Done" if index == self.TOTAL_STEPS - 1 else "Next")

	def on_next_clicked(self):
		try:
			# If we are on the last step, treat Next as Done
			if self._current_step >= self.TOTAL_STEPS - 1:
				self.on_finish_clicked()
				return
			# Enforce selection and persist nozzle (step 4)
			if self._current_step == 3:
				if not self.changeNozzleComboBox or self.changeNozzleComboBox.currentIndex() <= 0:
					try:
						dialog.WarningOk(self, "Please select a nozzle size to continue.", overlay=True)
					except Exception:
						pass
					return
				nozzle = self.changeNozzleComboBox.currentText()
				try:
					model = getattr(self.main_window, 'printer_model', self.model)
					if model and hasattr(model, 'update_tool_bay_state'):
						model.update_tool_bay_state(self.active_tool, nozzle=nozzle, persist=True)
						self.logger.info(f"Persisted nozzle '{nozzle}' for {self.active_tool}")
				except Exception as e:
					self.logger.warning(f"Unable to persist nozzle selection: {e}")
			# If we are on step 5 (index 4), Next is disabled until progress completes.
			self.goto_step(self._current_step + 1)
		except Exception as e:
			self.logger.error(f"Error advancing to next step: {e}")

	def on_cancel_clicked(self):
		try:
			self._stop_nozzle_check()
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
			if self.step5Label:
				self.step5Label.setText("Checking Nozzle Connection ...")
			if self.nozzleCheckProgressBar:
				self.nozzleCheckProgressBar.setValue(0)
			self._progress_timer.start()
			if self.nextButton:
				self.nextButton.setEnabled(False)
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
			if self.nextButton and self._current_step != 4:
				# Re-enable Next outside of step 5
				self.nextButton.setEnabled(True)
		except Exception:
			pass

	def on_finish_clicked(self):
		"""Finish the wizard and return to the main Material/Nozzle page."""
		try:
			self._stop_nozzle_check()
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

