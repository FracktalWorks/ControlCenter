import textwrap
from utils import styles

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
            # Check if text is long enough to require scrolling
            text_length = len(objLabel.text())
            needs_scrolling = text_length > 500 or objLabel.text().count('\n') > 8
            
            if needs_scrolling:
                # Create scroll area for long text
                self._create_scrollable_content(objLabel)
            else:
                # Standard label setup for shorter text
                objLabel.setStyleSheet(styles.msgbox_label)
                objLabel.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
                objLabel.setMinimumSize(350, 120)
                objLabel.setMaximumSize(650, 400)  # Reasonable max height
                objLabel.setWordWrap(True)
                objLabel.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
                objLabel.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
                objLabel.setScaledContents(False)
                
        # Set size policy for the message box itself to allow proper resizing
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        
        # Ensure the dialog doesn't exceed screen bounds
        self.setMaximumSize(500, 500)

    def _create_scrollable_content(self, objLabel):
        """
        Replace the standard message box label with a scrollable text area.
        Creates a scroll area with large scroll buttons for touch-friendly interaction.
        
        Args:
            objLabel: The original QLabel to be replaced with scrollable content
        """
        # Store the original text and parent
        text = objLabel.text()
        label_parent = objLabel.parent()
        
        # Create scroll area
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)  # We'll use custom buttons
        scroll_area.setMinimumSize(400, 200)
        scroll_area.setMaximumSize(450, 350)
        
        # Create content widget with text
        content_widget = QtWidgets.QWidget()
        content_layout = QtWidgets.QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create text label for scrollable content
        text_label = QtWidgets.QLabel(text)
        text_label.setStyleSheet(styles.msgbox_label)
        text_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        text_label.setWordWrap(True)
        text_label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        text_label.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.MinimumExpanding)
        
        content_layout.addWidget(text_label)
        content_layout.addStretch()  # Push content to top
        scroll_area.setWidget(content_widget)
        
        # Create container widget for scroll area and buttons
        container_widget = QtWidgets.QWidget()
        container_layout = QtWidgets.QVBoxLayout(container_widget)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(5)
        
        # Create scroll up button with large touch target
        scroll_up_button = QtWidgets.QPushButton("▲")
        scroll_up_button.setMinimumHeight(44)  # Touch-friendly size
        scroll_up_button.setMaximumHeight(44)
        scroll_up_button.setStyleSheet("""
            QPushButton {
                border: 1px solid rgb(87, 87, 87);
                background-color: rgb(200, 200, 200);
                border-radius: 5px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgb(220, 220, 220);
            }
            QPushButton:pressed {
                background-color: rgb(180, 180, 180);
            }
        """)
        
        # Create scroll down button
        scroll_down_button = QtWidgets.QPushButton("▼")
        scroll_down_button.setMinimumHeight(44)
        scroll_down_button.setMaximumHeight(44)
        scroll_down_button.setStyleSheet(scroll_up_button.styleSheet())
        
        # Connect scroll buttons
        scroll_up_button.clicked.connect(lambda: self._scroll_content(scroll_area, -50))
        scroll_down_button.clicked.connect(lambda: self._scroll_content(scroll_area, 50))
        
        # Add components to container
        container_layout.addWidget(scroll_up_button)
        container_layout.addWidget(scroll_area)
        container_layout.addWidget(scroll_down_button)
        
        # Replace the original label with our scrollable container
        # Find the label's layout and replace it
        if label_parent and hasattr(label_parent, 'layout') and label_parent.layout():
            parent_layout = label_parent.layout()
            
            # Find and remove the original label
            for i in range(parent_layout.count()):
                item = parent_layout.itemAt(i)
                if item and item.widget() == objLabel:
                    parent_layout.removeItem(item)
                    objLabel.setParent(None)
                    # Insert our container at the same position
                    parent_layout.insertWidget(i, container_widget)
                    break
        else:
            # Fallback: try to find messagebox layout directly
            for widget in self.findChildren(QtWidgets.QWidget):
                if hasattr(widget, 'layout') and widget.layout():
                    layout = widget.layout()
                    for i in range(layout.count()):
                        item = layout.itemAt(i)
                        if item and item.widget() == objLabel:
                            layout.removeItem(item)
                            objLabel.setParent(None)
                            layout.insertWidget(i, container_widget)
                            return
        
        # Store references for potential future use
        self._scroll_area = scroll_area
        self._scroll_up_button = scroll_up_button
        self._scroll_down_button = scroll_down_button
        
    def _scroll_content(self, scroll_area, delta_y):
        """
        Scroll the content in the scroll area by the specified amount.
        
        Args:
            scroll_area: The QScrollArea to scroll
            delta_y: Amount to scroll (positive = down, negative = up)
        """
        scrollbar = scroll_area.verticalScrollBar()
        current_value = scrollbar.value()
        scrollbar.setValue(current_value + delta_y)
        
        # Update button states based on scroll position
        if hasattr(self, '_scroll_up_button') and hasattr(self, '_scroll_down_button'):
            # Enable/disable buttons based on scroll position
            at_top = scrollbar.value() <= scrollbar.minimum()
            at_bottom = scrollbar.value() >= scrollbar.maximum()
            
            self._scroll_up_button.setEnabled(not at_top)
            self._scroll_down_button.setEnabled(not at_bottom)

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
        if objLabel and not hasattr(self, '_scroll_area'):  # Only if we haven't created scroll area yet
            # Check if text is long enough to require scrolling
            text_length = len(objLabel.text())
            needs_scrolling = text_length > 500 or objLabel.text().count('\n') > 8
            
            if needs_scrolling:
                # Create scroll area for long text
                self._create_scrollable_content(objLabel)
            else:
                # Standard label setup for shorter text
                objLabel.setStyleSheet(styles.msgbox_label)
                objLabel.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
                objLabel.setMinimumSize(250, 120)
                objLabel.setMaximumSize(600, 400)  # Consistent with __init__
                objLabel.setWordWrap(True)
                objLabel.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
                objLabel.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
                objLabel.setScaledContents(False)
        
        # Update scroll button states if scroll area exists
        if hasattr(self, '_scroll_area'):
            # Initialize scroll button states
            scrollbar = self._scroll_area.verticalScrollBar()
            at_top = scrollbar.value() <= scrollbar.minimum()
            at_bottom = scrollbar.value() >= scrollbar.maximum()
            
            if hasattr(self, '_scroll_up_button'):
                self._scroll_up_button.setEnabled(not at_top)
            if hasattr(self, '_scroll_down_button'):
                self._scroll_down_button.setEnabled(not at_bottom)
        
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
