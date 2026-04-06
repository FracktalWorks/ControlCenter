import textwrap
from utils import styles
from utils.logger import get_logger

from PyQt5 import QtCore, QtGui, QtWidgets

# Import resources to ensure Qt resource system is initialized
try:
    import ui.resources.resource_rc
except ImportError:
    # Fallback if resource file is not available
    pass

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s


def format_text_for_dialog(text, max_line_length=50):  # Reduced from 60 to 50
    """
    Format text for better display in dialog boxes by:
    - Wrapping long lines
    - Preserving intentional line breaks
    - Limiting line length for better readability
    """
    if not text:
        return text
    
    # Split by existing line breaks first
    paragraphs = text.split('\n')
    formatted_paragraphs = []
    
    for paragraph in paragraphs:
        if paragraph.strip():  # Non-empty paragraph
            # Wrap the paragraph to max line length with break_long_words to prevent overflow
            wrapped = textwrap.fill(
                paragraph.strip(), 
                width=max_line_length,
                break_long_words=True,
                break_on_hyphens=True
            )
            formatted_paragraphs.append(wrapped)
        else:  # Empty line (preserve spacing)
            formatted_paragraphs.append('')
    
    return '\n'.join(formatted_paragraphs)


def font(size=12, weight=50, bold=False, underline=False, strikeout=False):  # Reduced default from 14 to 12
    """Create and return a standardized QFont used by dialogs.

    Args:
        size: Point size.
        weight: Weight value (50 normal).
        bold: Whether the font is bold.
        underline: Whether the font is underlined.
        strikeout: Whether the font is a strikeout font.

    Returns:
        QtGui.QFont: Configured font instance.
    """
    font = QtGui.QFont()
    # QtGui.QInputMethodEvent
    font.setFamily(_fromUtf8("Gotham"))
    font.setPointSize(size)
    font.setWeight(weight)
    font.setBold(bold)
    font.setUnderline(underline)
    font.setStrikeOut(strikeout)
    return font


class Overlay(QtWidgets.QWidget):
    """A semi-transparent full-screen overlay used to dim the background."""

    def __init__(self, parent):
        """Construct the overlay widget."""
        QtWidgets.QWidget.__init__(self, parent)

        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_NoSystemBackground, True)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)

        palette = QtGui.QPalette(self.palette())
        palette.setColor(palette.Background, QtCore.Qt.transparent)
        self.setPalette(palette)

        screen = QtWidgets.QApplication.desktop().screenNumber(QtWidgets.QApplication.desktop().cursor().pos())
        geom = QtWidgets.QApplication.desktop().screenGeometry(screen)
        self.setGeometry(geom)

    def paintEvent(self, event):
        """Paint a translucent black overlay over the entire widget area."""
        painter = QtGui.QPainter()
        painter.begin(self)
        painter.setOpacity(0.8)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.fillRect(event.rect(), QtGui.QBrush(QtGui.QColor(0, 0, 0, 127)))
        painter.end()


class SelfCenteringMessageBox(QtWidgets.QMessageBox):
    """Customized frameless message box that centers on screen and can show an overlay."""

    def __init__(self, timeout=3, parent=None, overlay=False):
        """Initialize the message box and optional overlay.

        Args:
            timeout: Unused placeholder for potential auto-close in future.
            parent: Parent widget.
            overlay: Whether to show the dimming overlay while visible.
        """
        self._showOverlay = overlay
        self.overlay = Overlay(None)

        super(SelfCenteringMessageBox, self).__init__(None)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)

        objIcon = self.findChild(QtWidgets.QLabel, 'qt_msgboxex_icon_label') 
        if objIcon:
            objIcon.setStyleSheet(styles.msgbox_icon)
            # objIcon.setMinimumSize(60, 60)
            # objIcon.setGeometry(QtCore.QRect(0, 0, 60, 60))
            # height = objIcon.height()

        objLabel = self.findChild(QtWidgets.QLabel, 'qt_msgbox_label')
        if objLabel:
            objLabel.setStyleSheet(styles.msgbox_label)
            objLabel.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
            objLabel.setMinimumSize(350, 120)
            objLabel.setMaximumSize(450, 500)  # Reduced width from 500 to 450
            objLabel.setWordWrap(True)  # Enable word wrapping
            objLabel.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
            
            # Set text eliding and additional properties to ensure proper wrapping
            objLabel.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
            objLabel.setScaledContents(False)
            
            # If text is very long, add scroll area
            text_length = len(objLabel.text())
            if text_length > 500:  # Threshold for very long text
                objLabel.setMaximumSize(450, 500)  # Reduce height for scroll and use consistent width
                
        # Set size policy for the message box itself to allow proper resizing
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        
        # Ensure the dialog doesn't exceed screen bounds
        self.setMaximumSize(500, 500)

    def setLocalIcon(self, icon=None):
        """Set an icon using a Qt resource path.

        Args:
            icon: Resource path to the icon (e.g., ':/Icons/img/icons/success.png').
        """
        if icon:
            # Use Qt resource system for icons
            pixmap = QtGui.QPixmap(_fromUtf8(icon))
            if not pixmap.isNull():
                self.setIconPixmap(pixmap.scaled(40, 40))
            else:
                pass

    def show(self):
        """Show the dialog centered on the active screen and apply styles."""
        # Apply label settings just before showing, in case the label wasn't found during init
        objLabel = self.findChild(QtWidgets.QLabel, 'qt_msgbox_label')
        if objLabel:
            objLabel.setStyleSheet(styles.msgbox_label)
            objLabel.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
            objLabel.setMinimumSize(350, 120)
            objLabel.setMaximumSize(450, 300)  # Consistent with __init__
            objLabel.setWordWrap(True)
            objLabel.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
            objLabel.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
            objLabel.setScaledContents(False)
        
        if self._showOverlay:
            self.overlay.show()
        super(SelfCenteringMessageBox, self).show()

        frameGm = self.frameGeometry()
        screen = QtWidgets.QApplication.desktop().screenNumber(QtWidgets.QApplication.desktop().cursor().pos())
        centerPoint = QtWidgets.QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())

    def hide(self):
        """Hide the dialog and its overlay."""
        super(SelfCenteringMessageBox, self).hide()
        self.overlay.hide()
    
    def close(self):
        """Close the dialog and ensure overlay is hidden."""
        self.overlay.hide()
        self.overlay.close()
        return super(SelfCenteringMessageBox, self).close()
    
    def done(self, result):
        """Override done to ensure overlay is cleaned up when dialog is dismissed."""
        self.overlay.hide()
        self.overlay.close()
        super(SelfCenteringMessageBox, self).done(result)

    def showOverlay(self, overlay):
        """Enable or disable the overlay when the dialog is shown.

        Args:
            overlay: True to enable overlay, False to disable.
        """
        self._showOverlay = overlay


def dialog(parent, text, **kwargs):
    """Create and show a styled, optionally overlayed message box.

    Args:
        parent: Parent widget.
        text: Message text (optionally wrapped for readability).
        **kwargs: Optional parameters:
            - fontSize (int): Font point size.
            - icon (str): Qt resource path to an icon.
            - buttons (QMessageBox.StandardButtons): Buttons to show.
            - geometry (QRect): Optional geometry for the dialog.
            - overlay (bool): Whether to show background overlay.
            - format_text (bool): Whether to auto-wrap text.

    Returns:
        SelfCenteringMessageBox: The shown dialog instance.
    """
    fontSize = kwargs.get('fontSize', 12)  # Reduced default font size from 14 to 12
    icon = kwargs.get('icon', None)
    buttons = kwargs.get('buttons', QtWidgets.QMessageBox.Ok)
    geometry = kwargs.get('geometry', None)
    overlay = kwargs.get('overlay', False)
    format_text = kwargs.get('format_text', True)  # Option to enable/disable text formatting

    # Format the text for better display if enabled
    if format_text:
        text = format_text_for_dialog(text)

    choice = SelfCenteringMessageBox(parent)  # QtWidgets.QMessageBox()
    choice.setFont(font(fontSize))
    choice.setText(text)
    choice.setStandardButtons(buttons)
    choice.showOverlay(overlay)

    if icon:
        choice.setLocalIcon(icon)
        # choice.setIcon(QtWidgets.QMessageBox.Information)

    if geometry:
        choice.setGeometry(geometry)

    choice.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
    choice.setStyleSheet(styles.msgbox)
    choice.show()
    return choice


def Ok(parent, text, **kwargs):
    """Show an OK dialog."""
    return dialog(parent, text, **kwargs).exec_() == QtWidgets.QMessageBox.Ok


def Cancel(parent, text, **kwargs):
    """Show a Cancel dialog with a single Cancel button."""
    return dialog(parent, text, buttons=QtWidgets.QMessageBox.Cancel, **kwargs).exec_() == QtWidgets.QMessageBox.Cancel


def OkCancel(parent, text, **kwargs):
    """Show a dialog with Ok and Cancel buttons."""
    return dialog(parent, text, buttons=QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel, **kwargs).exec_() == QtWidgets.QMessageBox.Cancel


def Yes(parent, text, **kwargs):
    """Show a Yes-only dialog."""
    return dialog(parent, text, buttons=QtWidgets.QMessageBox.Yes, **kwargs).exec_() == QtWidgets.QMessageBox.Yes


def YesNo(parent, text, **kwargs):
    """Show a dialog with Yes and No buttons."""
    return dialog(parent, text, buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, **kwargs).exec_() == QtWidgets.QMessageBox.Yes


def WarningOk(parent, text, **kwargs):
    """Show a warning dialog with OK button."""
    return Ok(parent, text, icon=":/Icons/img/icons/exclamation-mark.png", **kwargs)


def WarningCancel(parent, text, **kwargs):
    """Show a warning dialog with Cancel button."""
    return Cancel(parent, text, icon=":/Icons/img/icons/exclamation-mark.png", **kwargs)


def WarningOkCancel(parent, text, **kwargs):
    """Show a warning dialog with Ok and Cancel buttons."""
    return OkCancel(parent, text, icon=":/Icons/img/icons/exclamation-mark.png", **kwargs)


def WarningYes(parent, text, **kwargs):
    """Show a warning dialog with Yes button."""
    return Yes(parent, text, icon=":/Icons/img/icons/exclamation-mark.png", **kwargs)


def WarningYesNo(parent, text, **kwargs):
    """Show a warning dialog with Yes and No buttons."""
    return YesNo(parent, text, icon=":/Icons/img/icons/exclamation-mark.png", **kwargs)


def SuccessOk(parent, text, **kwargs):
    """Show a success dialog with OK button."""
    return Ok(parent, text, icon=":/Icons/img/icons/success.png", **kwargs)


def SuccessYesNo(parent, text, **kwargs):
    """Show a success dialog with Yes and No buttons."""
    return YesNo(parent, text, icon=":/Icons/img/icons/success.png", **kwargs)


def ErrorOk(parent, text, **kwargs):
    """Show an error dialog with OK button."""
    return Ok(parent, text, icon=":/Icons/img/icons/error.png", **kwargs)


def ErrorOkCancel(parent, text, **kwargs):
    """Show an error dialog with Ok and Cancel buttons."""
    return OkCancel(parent, text, icon=":/Icons/img/icons/error.png", **kwargs)


def InfoOk(parent, text, **kwargs):
    """Show an info dialog with OK button."""
    return Ok(parent, text, icon=":/Icons/img/icons/information.png", **kwargs)


def InfoYesNo(parent, text, **kwargs):
    """Show an info dialog with Yes and No buttons."""
    return YesNo(parent, text, icon=":/Icons/img/icons/information.png", **kwargs)


def RetrySkipCancel(parent, text, **kwargs):
    """Show a dialog with Retry, Skip, and Cancel buttons."""
    msgbox = dialog(parent, text, buttons=QtWidgets.QMessageBox.NoButton, **kwargs)
    retry_button = msgbox.addButton("Retry", QtWidgets.QMessageBox.ActionRole)
    skip_button = msgbox.addButton("Skip", QtWidgets.QMessageBox.ActionRole)
    cancel_button = msgbox.addButton("Cancel", QtWidgets.QMessageBox.RejectRole)
    
    result = msgbox.exec_()
    clicked_button = msgbox.clickedButton()
    
    if clicked_button == retry_button:
        return "retry"
    elif clicked_button == skip_button:
        return "skip"
    else:
        return "cancel"


def RetryCancel(parent, text, **kwargs):
    """Show a dialog with Retry and Cancel buttons."""
    msgbox = dialog(parent, text, buttons=QtWidgets.QMessageBox.NoButton, **kwargs)
    retry_button = msgbox.addButton("Retry", QtWidgets.QMessageBox.ActionRole)
    cancel_button = msgbox.addButton("Cancel", QtWidgets.QMessageBox.RejectRole)
    
    result = msgbox.exec_()
    clicked_button = msgbox.clickedButton()
    
    if clicked_button == retry_button:
        return "retry"
    else:
        return "cancel"


def LoadingDialog(parent, text, **kwargs):
    """Show a buttonless loading dialog that must be manually closed.
    
    Args:
        parent: Parent widget.
        text: Message text to display.
        **kwargs: Optional parameters (fontSize, icon, overlay, etc.)
    
    Returns:
        SelfCenteringMessageBox: The dialog instance (call .hide() or .close() to dismiss).
    """
    # Remove any buttons and create a non-modal dialog
    # CRITICAL: Set overlay to False to avoid UI blocking issues
    kwargs['buttons'] = QtWidgets.QMessageBox.NoButton
    kwargs['overlay'] = False  # Don't use overlay for loading dialog
    
    msgbox = dialog(parent, text, **kwargs)
    
    # Make it non-blocking so code can continue
    msgbox.setModal(False)
    
    return msgbox


class InputShaperProgressDialog(QtWidgets.QDialog):
    """Live-scrolling dialog that displays input shaper calibration progress.

    Connects to ``printer_model.terminal_message_received`` and shows
    relevant Klipper output in a scrollable text area.
    """

    # Keywords that indicate an input-shaper related terminal message
    _RELEVANT_KEYWORDS = [
        'testing frequency', 'shaper', 'calibrat', 'recommended',
        'save_config', 'input shaper', 'smoothing', 'vibration',
        'fitted', 'axis', 'accelerometer', 'resonance', 'writing raw',
        'echo:',
    ]

    def __init__(self, parent=None, is_idex=False):
        # Use None as parent so the dialog is a top-level window (same pattern as SelfCenteringMessageBox)
        super().__init__(None)
        self._logger = get_logger('InputShaperProgressDialog')
        self._logger.info(f"__init__: is_idex={is_idex}, parent={parent}")
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint
        )
        self.setFixedSize(520, 420)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self._is_idex = is_idex
        # IDEX: 3 axes (T0 X, T1 X, shared Y); Single: 2 axes (X, Y)
        self._expected_axes = 3 if is_idex else 2
        self._completed_axes = 0
        self._overlay = Overlay(None)

        # --- layout ---
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        self._title_label = QtWidgets.QLabel("Input Shaper Calibration")
        self._title_label.setFont(font(14, bold=True))
        self._title_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self._title_label)

        self._status_label = QtWidgets.QLabel("Initializing…")
        self._status_label.setFont(font(10))
        self._status_label.setWordWrap(True)
        layout.addWidget(self._status_label)

        self._log_text = QtWidgets.QTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setFont(QtGui.QFont("Courier", 9))
        self._log_text.setStyleSheet(
            "QTextEdit { background-color: #1e1e1e; color: #d4d4d4; "
            "border: 1px solid #555; border-radius: 4px; padding: 4px; }"
        )
        layout.addWidget(self._log_text, stretch=1)

        self._close_button = QtWidgets.QPushButton("Close")
        self._close_button.setEnabled(False)
        self._close_button.setStyleSheet(
            "QPushButton { border: 1px solid rgb(87,87,87); "
            "background-color: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0.188, "
            "stop:0 rgba(180,180,180,255), stop:1 rgba(255,255,255,255)); "
            "height: 50px; width: 120px; border-radius: 5px; font: 12pt 'Gotham'; } "
            "QPushButton:pressed { background-color: qlineargradient(x1:0,y1:0,x2:0,y2:1, "
            "stop:0 #dadbde, stop:1 #f6f7fa); } "
            "QPushButton:disabled { color: #999; }"
        )
        self._close_button.clicked.connect(self.accept)
        layout.addWidget(self._close_button, alignment=QtCore.Qt.AlignCenter)

        self.setStyleSheet(
            "InputShaperProgressDialog { background-color: rgb(240,240,240); "
            "border: 2px solid rgb(87,87,87); border-radius: 10px; }"
        )
        self._logger.info("__init__ complete: dialog built successfully")

    # --- public helpers ---

    def set_status(self, text):
        self._status_label.setText(text)

    def append_message(self, text):
        self._log_text.append(text)
        # auto-scroll
        sb = self._log_text.verticalScrollBar()
        sb.setValue(sb.maximum())

    def mark_complete(self, success=True):
        if success:
            self._status_label.setText("Calibration complete. Printer will restart to apply settings.")
        else:
            self._status_label.setText("Calibration encountered an issue. Check the log above.")
        self._close_button.setEnabled(True)

    # --- terminal message handler ---

    def on_terminal_message(self, message):
        """Filter and display relevant input-shaper messages."""
        msg_lower = message.lower()
        if any(kw in msg_lower for kw in self._RELEVANT_KEYWORDS):
            self.append_message(message.strip())
            self._logger.debug(f"Relevant message: {message.strip()[:100]}")

        # Each SHAPER_CALIBRATE_BASE prints this after finishing one axis.
        # Only mark complete once ALL expected axes are done (before SAVE_CONFIG restarts Klipper).
        if 'the save_config command will update' in msg_lower:
            self._completed_axes += 1
            remaining = self._expected_axes - self._completed_axes
            self._logger.info(f"Axis completed: {self._completed_axes}/{self._expected_axes}")
            if remaining > 0:
                self.set_status(
                    f"Axis {self._completed_axes}/{self._expected_axes} done. "
                    f"Calibrating next axis…"
                )
            else:
                self.set_status("All axes calibrated! Saving configuration & restarting printer…")
                self.mark_complete(success=True)

    # --- overrides ---

    def _center_on_screen(self):
        """Center the dialog on the active screen."""
        screen = QtWidgets.QApplication.desktop().screenNumber(
            QtWidgets.QApplication.desktop().cursor().pos()
        )
        center = QtWidgets.QApplication.desktop().screenGeometry(screen).center()
        fg = self.frameGeometry()
        fg.moveCenter(center)
        self.move(fg.topLeft())
        self._logger.debug(f"Centered on screen {screen} at {fg.topLeft()}")

    def show(self):
        self._logger.info("show() called")
        self._overlay.show()
        super().show()
        self._center_on_screen()
        self.raise_()
        self.activateWindow()
        self._logger.info(f"show() complete: visible={self.isVisible()}, geometry={self.geometry()}")

    def exec_(self):
        """Show overlay, center, and run the modal event loop."""
        self._logger.info("exec_() called")
        self._overlay.show()
        self._center_on_screen()
        self.raise_()
        self.activateWindow()
        self._logger.info(f"exec_() entering event loop: visible={self.isVisible()}, geometry={self.geometry()}")
        return super().exec_()

    def done(self, result):
        self._logger.info(f"done() called with result={result}")
        self._overlay.hide()
        self._overlay.close()
        super().done(result)

    def closeEvent(self, event):
        self._logger.info("closeEvent() called")
        self._overlay.hide()
        self._overlay.close()
        super().closeEvent(event)