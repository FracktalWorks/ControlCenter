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
		self.model = getattr(main_window, "printer_model", None)
		self.octoprint_client = getattr(main_window, "octoprint_client", None)
		self.active_tool = "tool0"  # default; updated in setup()

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

		# Optional: preload GIFs if/when resources are available
		self._load_step_gifs_safe()

	# ----- Qt events -----------------------------------------------------
	def showEvent(self, event):  # noqa: N802 (Qt naming)
		super().showEvent(event)
		try:
			# Preflight: block wizard if filament is loaded or tool is hot
			model = getattr(self.main_window, 'printer_model', self.model)
			tool_str = self.active_tool if isinstance(self.active_tool, str) else f"tool{int(self.active_tool) or 0}"
			# Check filament status
			is_loaded = False
			try:
				if model and hasattr(model, 'get_bay_state'):
					state = model.get_bay_state(tool_str) or {}
					is_loaded = str(state.get('status')) == 'Loaded'
			except Exception:
				is_loaded = False
			if is_loaded:
				try:
					dialog.WarningOk(self, "Filament is loaded. Please unload filament before changing the nozzle.", overlay=True)
				except Exception:
					pass
				fms = getattr(self.main_window, "filament_management_screen", None)
				if fms and hasattr(fms, "show_material_nozzle_screen"):
					QtCore.QTimer.singleShot(0, lambda: fms.show_material_nozzle_screen())
				return
			# Check temperature > 50C
			too_hot = False
			try:
				temps = getattr(model, 'temperatures', {}) or {}
				tool_idx = 0
				try:
					tool_idx = int(tool_str.replace('tool', ''))
				except Exception:
					tool_idx = 0
				t = temps.get(f'tool{tool_idx}')
				if t is None:
					t = temps.get(f'tool{tool_idx}Actual')
				too_hot = (t is not None and float(t) > 50)
			except Exception:
				too_hot = False
			if too_hot:
				try:
					dialog.WarningOk(self, "Tool temperature is too high to touch (> 50°C). Please initiate cooling and wait for it to be cool enough to touch", overlay=True)
				except Exception:
					pass
				fms = getattr(self.main_window, "filament_management_screen", None)
				if fms and hasattr(fms, "show_material_nozzle_screen"):
					QtCore.QTimer.singleShot(0, lambda: fms.show_material_nozzle_screen())
				return
			self.goto_step(0)
		except Exception as e:
			self.logger.warning(f"Error resetting wizard on show: {e}")

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

	# (simplified: preflight checks are inlined in showEvent for readability)

	# ----- Media helpers --------------------------------------------------
	def _load_step_gifs_safe(self):
		"""Attempt to load GIFs for steps 2/3/4/6 from resources.

		The actual resource paths are TBD. This is a safe no-op if resources
		are absent to avoid raising during early development.
		"""
		try:
			# Example placeholders; replace with actual resource paths later.
			# self._assign_movie(self.step2Gif, ":/media/nozzle_step2.gif")
			# self._assign_movie(self.step3Gif, ":/media/nozzle_step3.gif")
			# self._assign_movie(self.step4Gif, ":/media/nozzle_step4.gif")
			# self._assign_movie(self.step6Gif, ":/media/nozzle_step6.gif")
			pass
		except Exception as e:
			self.logger.debug(f"GIFs not loaded (expected during scaffold): {e}")

	def _assign_movie(self, label: QLabel, resource_path: str):
		if not label:
			return
		try:
			movie = QtGui.QMovie(resource_path)
			if movie.isValid():
				label.setMovie(movie)
				movie.start()
		except Exception:
			# Ignore if resource isn't present yet
			pass

	# ----- Step 4: Nozzle selection ---------------------------------------
	def _prepare_step4(self):
		"""Populate nozzle options and enforce selection before proceeding."""
		try:
			if not self.changeNozzleComboBox:
				return
			# Avoid signal duplication
			try:
				self.changeNozzleComboBox.currentIndexChanged.disconnect(self._on_nozzle_choice_changed)
			except Exception:
				pass

			self.changeNozzleComboBox.clear()
			self.changeNozzleComboBox.addItem("(Select nozzle size)")
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

	def _persist_nozzle_selection(self):
		"""Persist selected nozzle in the printer model, similar to filament persistence."""
		try:
			if not self.changeNozzleComboBox or self.changeNozzleComboBox.currentIndex() <= 0:
				return
			nozzle = self.changeNozzleComboBox.currentText()
			if self.model and hasattr(self.model, 'update_tool_bay_state') and self.active_tool:
				self.model.update_tool_bay_state(self.active_tool, nozzle=nozzle, persist=True)
				self.logger.info(f"Persisted nozzle '{nozzle}' for {self.active_tool}")
		except Exception as e:
			self.logger.error(f"Failed to persist nozzle selection: {e}")

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
			# Reset UI state on open
			self.goto_step(0)
		except Exception as e:
			self.logger.error(f"Error in NozzleChangeWizard.setup: {e}")

