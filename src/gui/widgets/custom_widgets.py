from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QCursor, QFont, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QToolTip, QVBoxLayout, QWidget


class RadialProgressBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.value = 0
        self.maximum = 100
        self.setMinimumSize(120, 120)

    def set_value(self, value):
        self.value = value
        self.update()

    def set_maximum(self, value):
        self.maximum = value
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Geometry
        width = self.width()
        height = self.height()
        size = min(width, height)
        # Center it
        rect = QRectF((width - size) / 2 + 10, (height - size) / 2 + 10, size - 20, size - 20)

        # Design
        # 1. Background Circle (Track)
        pen = QPen(QColor("#1e1e2e"), 12)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.drawArc(rect, 0, 360 * 16)

        # 2. Progress Arc
        if self.maximum > 0:
            angle = (self.value / self.maximum) * 360
        else:
            angle = 0

        # Gradient for progress
        grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
        grad.setColorAt(0.0, QColor("#00f2ff"))  # Cyan
        grad.setColorAt(1.0, QColor("#007acc"))  # Blue

        pen = QPen(QBrush(grad), 12)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        # Standard: Starts at 3 o'clock (0). We want 12 o'clock (90).
        # Positive angle is Counter-Clockwise. Negative is Clockwise.
        painter.drawArc(rect, 90 * 16, -angle * 16)

        # 3. Text
        painter.setPen(QColor("#ffffff"))
        font = QFont("Segoe UI", 16, QFont.Bold)
        painter.setFont(font)

        progress_text = f"{int((self.value / self.maximum) * 100)}%" if self.maximum else "0%"
        painter.drawText(rect, Qt.AlignCenter, progress_text)

        # Small label "Progress"
        font.setPointSize(9)
        font.setBold(False)
        painter.setFont(font)
        painter.setPen(QColor("#a6adc8"))
        # Draw slightly below center? Or stick to simple centered text
        # Let's put it below the %
        rect_sub = rect.adjusted(0, 25, 0, 0)
        painter.drawText(rect_sub, Qt.AlignCenter, "Progress")


class InfoCard(QFrame):
    def __init__(self, title, initial_value, parent=None):
        super().__init__(parent)
        self.setObjectName("InfoCard")
        # Inline style or use styles.py. Using inline for specific widget tweaks if needed.
        self.setStyleSheet(
            """
            QFrame#InfoCard {
                background-color: rgba(30, 30, 46, 0.5); 
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 16px;
            }
        """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)

        self.lbl_title = QLabel(title.upper())
        self.lbl_title.setStyleSheet("color: #a6adc8; font-size: 11px; font-weight: bold; letter-spacing: 1px;")

        self.lbl_value = QLabel(initial_value)
        self.lbl_value.setStyleSheet("color: #ffffff; font-size: 20px; font-weight: bold; margin-top: 5px;")

        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_value)
        layout.addStretch()

    def set_value(self, text):
        self.lbl_value.setText(text)


class HeatmapBar(QWidget):
    def __init__(self, segments=8, parent=None):
        super().__init__(parent)
        self.segments = [0.0] * segments  # List of floats 0.0-1.0
        self.setFixedHeight(50)
        self.setMouseTracking(True)

    def update_segments(self, progress_list):
        """
        progress_list: list of floats from 0.0 to 1.0 representing completeness of each thread.
        """
        self.segments = progress_list
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        count = len(self.segments)
        if count == 0:
            return

        w_total = self.width()
        h = self.height()

        # Spacing
        gap = 4
        bar_w = (w_total - (gap * (count - 1))) / count

        for i, val in enumerate(self.segments):
            x = i * (bar_w + gap)

            # Draw pill shape background
            rect = QRectF(x, 0, bar_w, h)

            # Background (inactive)
            painter.setBrush(QColor("#313244"))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(rect, 4, 4)

            # Foreground (active)
            if val > 0:
                # Fill from bottom up usually for bars, but heatmap often full fill?
                # Image 2 shows vertical bars filling up.
                fill_h = h * val
                fill_rect = QRectF(x, h - fill_h, bar_w, fill_h)

                # Color gradient based on val? Or fixed.
                # Image 2 has green/yellow/red?
                # Let's use Cyan to Green transition
                color = QColor("#00f2ff")
                if val >= 0.99:
                    color = QColor("#a6e3a1")  # Greenish for done

                painter.setBrush(color)
                painter.drawRoundedRect(fill_rect, 4, 4)

    def mouseMoveEvent(self, event):
        x = event.pos().x()
        w_total = self.width()
        count = len(self.segments)
        if count == 0:
            return

        bar_w = (w_total - (4 * (count - 1))) / count
        idx = int(x // (bar_w + 4))

        if 0 <= idx < count:
            val = self.segments[idx]
            # Pass self as 3rd arg to ensure parentage on Wayland
            QToolTip.showText(event.globalPos(), f"Thread {idx + 1}: {int(val * 100)}%", self)
        else:
            QToolTip.hideText()
        count = len(self.segments)
        if count == 0:
            return

        w_total = self.width()
        gap = 4
        bar_w = (w_total - (gap * (count - 1))) / count
        total_slot_w = bar_w + gap

        index = int(x / total_slot_w)

        if 0 <= index < count:
            val = self.segments[index]
            pct = int(val * 100)
            QToolTip.showText(QCursor.pos(), f"Thread #{index + 1}: {pct}%")
        else:
            QToolTip.hideText()

        super().mouseMoveEvent(event)


class ModernButton(QPushButton):
    def __init__(self, text, primary=False, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(34)
        if primary:
            self.setStyleSheet(
                """
                QPushButton {
                    background-color: #00f2ff;
                    color: #11111b;
                    border: none;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #89dcff; }
            """
            )


class MiniGraph(QWidget):
    def __init__(self, color="#00f2ff", parent=None):
        super().__init__(parent)
        self.points = [0] * 30
        self.line_color = QColor(color)
        self.setFixedHeight(50)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)  # Let clicks pass through if needed

    def add_value(self, value):
        self.points.pop(0)
        self.points.append(value)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        max_val = max(self.points) or 1
        step_x = w / (len(self.points) - 1)

        path = QPainterPath()
        # Start bottom left
        path.moveTo(0, h)

        for i, val in enumerate(self.points):
            x = i * step_x
            y = h - ((val / max_val) * (h * 0.8)) - 2  # Keep some headroom
            if i == 0:
                path.moveTo(x, y)
            else:
                # Smooth curve?
                # content_path.cubicTo(...)
                # For now straight lines are faster and look "techy"
                path.lineTo(x, y)

        # Fill
        fill_path = QPainterPath(path)
        fill_path.lineTo(w, h)
        fill_path.lineTo(0, h)

        grad = QLinearGradient(0, 0, 0, h)
        c_top = QColor(self.line_color)
        c_top.setAlpha(80)
        c_bottom = QColor(self.line_color)
        c_bottom.setAlpha(0)
        grad.setColorAt(0, c_top)
        grad.setColorAt(1, c_bottom)

        painter.fillPath(fill_path, grad)

        pen = QPen(self.line_color, 2)
        painter.setPen(pen)
        painter.drawPath(path)
