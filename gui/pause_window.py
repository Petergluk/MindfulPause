# gui/pause_window.py

import os
import random
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QDialog, QDialogButtonBox, QApplication,
                             QTextEdit, QFrame)
from PySide6.QtCore import Qt, QTimer, Signal, QRect
from PySide6.QtGui import QPainter, QColor, QPixmap, QFont, QPainterPath
from utils.system_utils import block_input, unblock_input

class PauseWindow(QWidget):
    pause_finished = Signal(bool)
    FONT_FAMILY = "Arial"; MIN_FONT_SIZE = 12; MAX_FONT_SIZE = 32; TIMER_FONT_SIZE = 24
    FS_V_PADDING = 80; FS_H_PADDING = 150; WIN_PADDING = 50
    IMAGE_V_RATIO = 0.45; TEXT_TOP_MARGIN = 20; TEXT_BOTTOM_MARGIN = 20; TIMER_AREA_HEIGHT = 60

    def __init__(self, app, practice_text, duration, is_big_break=False, strict_mode=False, darken_screen=True):
        super().__init__()
        self.app, self.practice_text, self.duration, self.is_big_break, self.strict_mode, self.darken_screen = \
            app, practice_text, duration, is_big_break, strict_mode, darken_screen
        self.remaining_time = duration
        self.image_path = self.get_random_image()
        self.image_area, self.text_area, self.timer_area = QRect(), QRect(), QRect()
        self.init_ui()
        self.start_timer()
        if self.strict_mode and self.is_big_break: block_input()
            
    def init_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.text_widget = QTextEdit(self)
        self.text_widget.setReadOnly(True); self.text_widget.setFrameStyle(QFrame.NoFrame)
        self.text_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff); self.text_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text_widget.setStyleSheet("QTextEdit { background: transparent; color: #FFFDE7; border: none; }")
        self.text_widget.setText(self.practice_text)
        if self.is_big_break or (not self.is_big_break and self.darken_screen): self.showFullScreen()
        else: self.setFixedSize(600, 400); self.center_on_screen()
        self.recalculate_geometry(); self.apply_geometry_and_font()

    def resizeEvent(self, event): super().resizeEvent(event); self.recalculate_geometry(); self.apply_geometry_and_font()

    def recalculate_geometry(self):
        is_fullscreen = self.isFullScreen()
        v_pad = self.FS_V_PADDING if is_fullscreen else self.WIN_PADDING
        h_pad = self.FS_H_PADDING if is_fullscreen else self.WIN_PADDING
        content_rect = self.rect().adjusted(h_pad, v_pad, -h_pad, -v_pad)
        timer_height = self.TIMER_AREA_HEIGHT if self.is_big_break else 0
        self.timer_area = QRect(content_rect.x(), content_rect.bottom() - timer_height, content_rect.width(), timer_height)
        img_height = content_rect.height() * self.IMAGE_V_RATIO
        self.image_area = QRect(content_rect.x(), content_rect.y(), content_rect.width(), int(img_height))
        text_y_start = self.image_area.bottom() + self.TEXT_TOP_MARGIN
        text_y_end = self.timer_area.top() - (self.TEXT_BOTTOM_MARGIN if self.is_big_break else 0)
        self.text_area = QRect(content_rect.x(), text_y_start, content_rect.width(), text_y_end - text_y_start)

    def apply_geometry_and_font(self):
        self.text_widget.setGeometry(self.text_area)
        is_scrollable = self.text_widget.verticalScrollBar().maximum() > 0
        font_size = self.MIN_FONT_SIZE if is_scrollable else self._get_optimal_font_size_for_widget(self.practice_text, self.text_area.size())
        font = QFont(self.FONT_FAMILY, font_size)
        self.text_widget.setFont(font)
        self.text_widget.setAlignment(Qt.AlignCenter if not is_scrollable else Qt.AlignTop | Qt.AlignHCenter)

    def _get_optimal_font_size_for_widget(self, text, size):
        temp_doc = self.text_widget.document().clone()
        font_size = self.MAX_FONT_SIZE
        while font_size >= self.MIN_FONT_SIZE:
            font = QFont(self.FONT_FAMILY, font_size); temp_doc.setDefaultFont(font); temp_doc.setTextWidth(size.width())
            if temp_doc.size().height() <= size.height(): return font_size
            font_size -= 1
        return self.MIN_FONT_SIZE

    def paintEvent(self, event):
        painter = QPainter(self); painter.setRenderHint(QPainter.Antialiasing)
        if self.isFullScreen(): painter.fillRect(self.rect(), QColor(0, 0, 0, 230))
        else: path = QPainterPath(); path.addRoundedRect(self.rect(), 15, 15); painter.fillPath(path, QColor(16, 16, 32, 242))
        if self.image_path and os.path.exists(self.image_path):
            pixmap = QPixmap(self.image_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(self.image_area.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                img_draw_rect = QRect(0, 0, scaled_pixmap.width(), scaled_pixmap.height()); img_draw_rect.moveCenter(self.image_area.center())
                painter.drawPixmap(img_draw_rect, scaled_pixmap)
        if self.is_big_break:
            painter.setPen(QColor("#FFFDE7")); painter.setFont(QFont(self.FONT_FAMILY, self.TIMER_FONT_SIZE, QFont.Bold))
            painter.drawText(self.timer_area, Qt.AlignCenter, self.format_time(self.remaining_time))
            
    def get_random_image(self):
        images_dir = os.path.join(self.app.BASE_DIR, 'data', 'pict')
        if not os.path.exists(images_dir): return None
        formats = ('.png', '.jpg', '.jpeg', '.bmp'); images = [f for f in os.listdir(images_dir) if f.lower().endswith(formats) and 'app.ico' not in f.lower()]
        if images: return os.path.join(images_dir, random.choice(images))
        return None
        
    def format_time(self, seconds): m, s = divmod(seconds, 60); return f"{int(m):02d}:{int(s):02d}"
    def center_on_screen(self): screen = QApplication.primaryScreen().geometry(); self.move((screen.width() - self.width()) // 2, (screen.height() - self.height()) // 2)
    def start_timer(self): self.timer = QTimer(self); self.timer.timeout.connect(self.update_timer); self.timer.start(1000)
    def update_timer(self): self.remaining_time -= 1; self.update(); self.check_finish()
    def check_finish(self):
        if self.remaining_time < 0: self.finish_pause(manually_interrupted=False)

    def finish_pause(self, manually_interrupted):
        self.timer.stop()
        if self.strict_mode and self.is_big_break: unblock_input()
        self.pause_finished.emit(manually_interrupted); self.close()
        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            if self.is_big_break and self.strict_mode: return
            elif self.is_big_break and not self.strict_mode: self.show_exit_dialog()
            else: self.finish_pause(manually_interrupted=True)
                
    def show_exit_dialog(self):
        self.timer.stop()
        dialog = QDialog(self); dialog.setWindowTitle("Подтверждение"); dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowStaysOnTopHint)
        dialog.setStyleSheet("background-color: #F3E5F5; color: black; font-size: 14px;")
        layout = QVBoxLayout(dialog); layout.addWidget(QLabel("Вы уверены, что хотите прервать перерыв?"))
        buttons = QDialogButtonBox(QDialogButtonBox.Yes | QDialogButtonBox.No)
        buttons.button(QDialogButtonBox.Yes).setText("Да"); buttons.button(QDialogButtonBox.No).setText("Нет")
        buttons.accepted.connect(dialog.accept); buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec() == QDialog.Accepted: self.finish_pause(manually_interrupted=True)
        else: self.timer.start(1000)

class BreakWarningWindow(QWidget):
    postpone_clicked = Signal(); start_now_clicked = Signal()
    def __init__(self, duration=30):
        super().__init__(); self.remaining_time = duration; self.drag_position = None; self.init_ui(); self.start_countdown()
    def init_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool); self.setAttribute(Qt.WA_TranslucentBackground); self.setFixedSize(320, 150)
        self.main_label = QLabel("Большой перерыв"); self.main_label.setAlignment(Qt.AlignCenter); self.main_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        self.timer_label = QLabel(); self.timer_label.setAlignment(Qt.AlignCenter); self.timer_label.setStyleSheet("color: white; font-size: 14px;")
        postpone_btn = QPushButton("Отложить"); postpone_btn.clicked.connect(self.on_postpone)
        start_btn = QPushButton("Начать сейчас"); start_btn.clicked.connect(self.on_start_now)
        style = "QPushButton { background-color: white; color: #9C27B0; border: none; padding: 6px 12px; border-radius: 4px; font-weight: bold; } QPushButton:hover { background-color: #F3E5F5; }"
        postpone_btn.setStyleSheet(style); start_btn.setStyleSheet(style)
        layout = QVBoxLayout(); layout.addWidget(self.main_label); layout.addWidget(self.timer_label)
        buttons_layout = QHBoxLayout(); buttons_layout.addWidget(postpone_btn); buttons_layout.addWidget(start_btn)
        layout.addLayout(buttons_layout); self.setLayout(layout); self.update_countdown_label(); self.move_to_corner()
    def paintEvent(self, event): painter = QPainter(self); painter.setRenderHint(QPainter.Antialiasing); path = QPainterPath(); path.addRoundedRect(self.rect(), 10, 10); painter.fillPath(path, QColor("#9C27B0"))
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton: self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft(); event.accept()
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_position: self.move(event.globalPosition().toPoint() - self.drag_position); event.accept()
    def mouseReleaseEvent(self, event): self.drag_position = None; event.accept()
    def move_to_corner(self): screen = QApplication.primaryScreen().geometry(); self.move(screen.width()-self.width()-20, screen.height()-self.height()-60)
    def start_countdown(self): self.timer = QTimer(self); self.timer.timeout.connect(self.countdown_tick); self.timer.start(1000)
    def countdown_tick(self):
        self.remaining_time -= 1; self.update_countdown_label()
        if self.remaining_time <= 0: self.on_start_now()
    def update_countdown_label(self): self.timer_label.setText(f"Пауза через: {self.remaining_time} сек")
    def on_postpone(self): self.timer.stop(); self.postpone_clicked.emit(); self.close()
    def on_start_now(self): self.timer.stop(); self.start_now_clicked.emit(); self.close()
    def closeEvent(self, event): self.timer.stop(); super().closeEvent(event)