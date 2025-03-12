from PyQt5.QtCore import QObject, pyqtSignal
from utils.helpers import run_async
import time

class ProcessAutomationController(QObject):
    progress_update_signal = pyqtSignal(int)

    def __init__(self, main_window):
        super(ProcessAutomationController, self).__init__()
        self.main_window = main_window
        self.process_running = False

    @run_async
    def initialLevellingRecoat(self):
        """Perform the initial levelling recoat."""
        self.main_window.home_screen.playPauseButton.setChecked(True)
        self.main_window.home_screen.playPauseButton.setText("Pause")
        self.set_motion_control_buttons_enabled(False)
        
        layerHeight = self.main_window.printer_status.layerHeight
        initialLevellingHeight = self.main_window.printer_status.initialLevellingHeight
        recoatCount = int(initialLevellingHeight / layerHeight)
        sequence = self.main_window.printer_status.initialLevellingRecoatingSequence

        for i in range(recoatCount):
            if not self.process_running:
                break

            # Pause handling
            while not self.main_window.home_screen.playPauseButton.isChecked():
                if not self.process_running:
                    break
                time.sleep(1)  # Sleep for a short duration to avoid busy waiting

            if not self.process_running:
                break

            # Perform recoat operation
            sequence_replaced = replace_placeholders(sequence, self.main_window.printer_status)
            for line in sequence_replaced.split('\n'):
                self.run_async_send_gcode(line)

        self.set_motion_control_buttons_enabled(True)
        self.main_window.home_screen.playPauseButton.setChecked(False)
        self.main_window.home_screen.playPauseButton.setText("Play")

    @run_async
    def heatedBufferRecoat(self):
        """Perform the heated buffer recoat."""
        self.main_window.home_screen.playPauseButton.setChecked(True)
        self.main_window.home_screen.playPauseButton.setText("Pause")
        self.set_motion_control_buttons_enabled(False)
        
        layerHeight = self.main_window.printer_status.layerHeight
        heatedBufferHeight = self.main_window.printer_status.heatedBufferHeight
        recoatCount = int(heatedBufferHeight / layerHeight)
        sequence = self.main_window.printer_status.heatedBufferRecoatingSequence

        for i in range(recoatCount):
            if not self.process_running:
                break

            # Pause handling
            while not self.main_window.home_screen.playPauseButton.isChecked():
                if not self.process_running:
                    break
                time.sleep(1)  # Sleep for a short duration to avoid busy waiting

            if not self.process_running:
                break

            # Perform recoat operation
            sequence_replaced = replace_placeholders(sequence, self.main_window.printer_status)
            for line in sequence_replaced.split('\n'):
                self.run_async_send_gcode(line)

        self.set_motion_control_buttons_enabled(True)
        self.main_window.home_screen.playPauseButton.setChecked(False)
        self.main_window.home_screen.playPauseButton.setText("Play")

    @run_async
    def dose_recoat_layer(self):
        """Perform a single recoat using the layer height from the parameters screen."""
        self.set_motion_control_buttons_enabled(False)  # Disable motion control buttons
        sequence = self.main_window.printer_status.printingRecoatingSequence
        sequence_replaced = replace_placeholders(sequence, self.main_window.printer_status)
        for line in sequence_replaced.split('\n'):
            self.main_window.moonraker_api.send_gcode(line)
        self.progress_update_signal.emit(100)
        self.set_motion_control_buttons_enabled(True)  # Re-enable motion control buttons

    @run_async
    def prepare_powder_loading(self):
        """Prepare for powder loading."""
        self.set_motion_control_buttons_enabled(False)
        sequence = self.main_window.printer_status.powderLoadingSequence
        sequence_replaced = replace_placeholders(sequence, self.main_window.printer_status)
        for line in sequence_replaced.split('\n'):
            self.main_window.moonraker_api.send_gcode(line)
        self.set_motion_control_buttons_enabled(True)

    @run_async
    def move_to_starting_sequence(self):
        """Execute the move to starting sequence."""
        self.set_motion_control_buttons_enabled(False)
        sequence = self.main_window.printer_status.moveToStartingSequence
        sequence_replaced = replace_placeholders(sequence, self.main_window.printer_status)
        for line in sequence_replaced.split('\n'):
            self.main_window.moonraker_api.send_gcode(line)
        self.set_motion_control_buttons_enabled(True)

    @run_async
    def prepare_for_part_removal_sequence(self):
        """Execute the prepare for part removal sequence."""
        self.set_motion_control_buttons_enabled(False)
        sequence = self.main_window.printer_status.prepareForPartRemovalSequence
        sequence_replaced = replace_placeholders(sequence, self.main_window.printer_status)
        for line in sequence_replaced.split('\n'):
            self.main_window.moonraker_api.send_gcode(line)
        self.set_motion_control_buttons_enabled(True)

    @run_async
    def start_printing_sequence(self):
        """Start the main printing sequence."""
        self.set_motion_control_buttons_enabled(False)
        self.main_window.home_screen.printProgressBar.setValue(0)

        # Step 1: Initial Levelling Recoat
        self.initialLevellingRecoat()
        self.main_window.home_screen.printProgressBar.setValue(10)

        # Step 2: Heated Buffer Recoat
        self.heatedBufferRecoat()
        self.main_window.home_screen.printProgressBar.setValue(20)

        # Step 3 and 4: Mark laser and dose recoat layer until partHeight is achieved
        layerHeight = self.main_window.printer_status.layerHeight
        partHeight = self.main_window.printer_status.partHeight
        recoatCount = int(partHeight / layerHeight)

        for i in range(recoatCount):
            if not self.process_running:
                self.main_window.home_screen.printProgressBar.setValue(0)
                break

            # Pause handling
            while not self.main_window.home_screen.playPauseButton.isChecked():
                if not self.process_running:
                    self.main_window.home_screen.printProgressBar.setValue(0)
                    break
                time.sleep(1)  # Sleep for a short duration to avoid busy waiting

            if not self.process_running:
                self.main_window.home_screen.printProgressBar.setValue(0)
                break

            # Mark laser until scancard status is "Already working"
            while self.main_window.printer_status.scancard_status != "Already working":
                if not self.process_running:
                    self.main_window.home_screen.printProgressBar.setValue(0)
                    break
                self.main_window.start_scancard_mark()
                time.sleep(1)  # Sleep for a short duration to avoid busy waiting

            if not self.process_running:
                self.main_window.home_screen.printProgressBar.setValue(0)
                break

            # Dose recoat layer
            self.dose_recoat_layer()
            progress = int((i + 1) / recoatCount * 60) + 20
            self.main_window.home_screen.printProgressBar.setValue(progress)

        # Step 5: Final Heated Buffer Recoat
        self.heatedBufferRecoat()
        self.main_window.home_screen.printProgressBar.setValue(100)

        self.set_motion_control_buttons_enabled(True)

    @run_async
    def run_async_send_gcode(self, gcode):
        self.main_window.moonraker_api.send_gcode(gcode)

    def stop_process(self):
        """Stop the recoat process."""
        self.process_running = False
        self.main_window.home_screen.playPauseButton.setChecked(False)
        self.main_window.home_screen.playPauseButton.setText("Play")
        self.main_window.home_screen.printProgressBar.setValue(0)

    def set_motion_control_buttons_enabled(self, enabled):
        """Enable or disable motion control buttons."""
        for button in self.main_window.control_screen.motion_control_buttons:
            button.setEnabled(enabled)

def replace_placeholders(sequence: str, printer_status) -> str:
    """Replace placeholders in the sequence with actual values from the printer_status model."""
    placeholders = {
        "{layerHeight}": printer_status.layerHeight,
        "{initialLevellingHeight}": printer_status.initialLevellingHeight,
        "{heatedBufferHeight}": printer_status.heatedBufferHeight,
        "{powderLoadingExtraHeightGap}": printer_status.powderLoadingExtraHeightGap,
        "{bedTemperature}": printer_status.bedTemperature,
        "{volumeTemperature}": printer_status.volumeTemperature,
        "{chamberTemperature}": printer_status.chamberTemperature,
        "{p}": printer_status.p,
        "{i}": printer_status.i,
        "{d}": printer_status.d,
        "{powderLoadingHeight}": printer_status.initialLevellingHeight + 2 * printer_status.heatedBufferHeight + printer_status.partHeight,
        "{dosingHeight}": printer_status.dosingHeight  # Add dosingHeight
    }
    for placeholder, value in placeholders.items():
        sequence = sequence.replace(placeholder, str(value))
    return sequence