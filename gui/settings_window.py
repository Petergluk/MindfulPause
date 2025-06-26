# gui/settings_window.py

import os
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTabWidget, QPushButton, QCheckBox, QSpinBox,
                             QLabel, QTextEdit, QGroupBox, QGridLayout,
                             QTextBrowser, QScrollArea)
from PySide6.QtCore import Signal, Qt, QTimer
from PySide6.QtGui import QIcon

class SettingsWindow(QMainWindow):
    settings_saved = Signal()
    
    def __init__(self, app, xml_manager):
        super().__init__()
        self.app = app
        self.xml_manager = xml_manager
        # self.xml_manager.reload_practices() # <-- Удаляем это отсюда
        self.settings = xml_manager.load_settings()
        self.ui_texts = xml_manager.get_ui_texts()
        self.base_dir = getattr(app, 'BASE_DIR', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.practice_checkboxes = []
        self.micropractice_checkboxes = []
        self.init_ui()
        self.load_settings()
        
    def init_ui(self):
        self.setWindowTitle('Настройки MindfulPause')
        self.setFixedSize(600, 580)
        icon_path = os.path.join(self.base_dir, 'data', 'pict', 'app.ico')
        if os.path.exists(icon_path): self.setWindowIcon(QIcon(icon_path))
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        self.create_settings_tab()
        self.create_practices_tab()
        self.create_info_tab()
        save_button = QPushButton('Сохранить и выйти')
        save_button.clicked.connect(self.save_and_close)
        save_button.setStyleSheet("QPushButton { background-color: #9C27B0; color: white; padding: 8px; border-radius: 4px; font-weight: bold; } QPushButton:hover { background-color: #7B1FA2; }")
        main_layout.addWidget(save_button)
        self.setStyleSheet("QMainWindow { background-color: #F3E5F5; } QTabWidget::pane { border: 1px solid #E1BEE7; background-color: white; } QTabBar::tab { background-color: #E1BEE7; padding: 8px 16px; margin-right: 2px; } QTabBar::tab:selected { background-color: #9C27B0; color: white; } QScrollArea { border: none; }")

    # --- НОВЫЙ МЕТОД ---
    def showEvent(self, event):
        """Этот метод вызывается каждый раз, когда окно становится видимым."""
        super().showEvent(event)
        self.update_practices_list() # Обновляем список практик при каждом открытии окна
        
    def create_settings_tab(self):
        settings_widget = QWidget()
        layout = QVBoxLayout(settings_widget)
        big_break_group = QGroupBox('Большой перерыв')
        big_break_layout = QGridLayout(big_break_group)
        self.big_break_checkbox = QCheckBox('Делать большой перерыв')
        self.big_break_interval = QSpinBox(); self.big_break_interval.setRange(1, 480); self.big_break_interval.setSuffix(' мин')
        self.big_break_duration = QSpinBox(); self.big_break_duration.setRange(1, 20); self.big_break_duration.setSuffix(' мин')
        big_break_layout.addWidget(self.big_break_checkbox, 0, 0, 1, 3)
        big_break_layout.addWidget(QLabel('Каждые:'), 1, 0); big_break_layout.addWidget(self.big_break_interval, 1, 1)
        big_break_layout.addWidget(QLabel('Длительность:'), 2, 0); big_break_layout.addWidget(self.big_break_duration, 2, 1)
        short_pause_group = QGroupBox('Короткая пауза')
        short_pause_layout = QGridLayout(short_pause_group)
        self.short_pause_checkbox = QCheckBox('Делать короткую паузу')
        self.short_pause_interval = QSpinBox(); self.short_pause_interval.setRange(5, 60); self.short_pause_interval.setSuffix(' мин')
        self.short_pause_duration = QSpinBox(); self.short_pause_duration.setRange(5, 60); self.short_pause_duration.setSuffix(' сек')
        short_pause_layout.addWidget(self.short_pause_checkbox, 0, 0, 1, 3)
        short_pause_layout.addWidget(QLabel('Каждые:'), 1, 0); short_pause_layout.addWidget(self.short_pause_interval, 1, 1)
        short_pause_layout.addWidget(QLabel('Длительность:'), 2, 0); short_pause_layout.addWidget(self.short_pause_duration, 2, 1)
        self.warning_checkbox = QCheckBox('Предупреждать о большом перерыве')
        self.warning_time = QSpinBox(); self.warning_time.setRange(15, 90); self.warning_time.setSuffix(' сек')
        warning_layout = QHBoxLayout(); warning_layout.addWidget(self.warning_checkbox); warning_layout.addWidget(self.warning_time); warning_layout.addStretch()
        self.strict_mode_checkbox = QCheckBox('Строгий режим')
        self.sound_checkbox = QCheckBox('Звук окончания большого перерыва')
        self.start_sound_checkbox = QCheckBox('Звук начала короткой паузы')
        self.darken_checkbox = QCheckBox('Полноэкранный режим короткой паузы')
        self.autostart_checkbox = QCheckBox('Автозапуск')
        self.tracking_checkbox = QCheckBox('Отслеживать активность')
        self.set_tooltips()
        test_layout = QHBoxLayout()
        test_big_button = QPushButton('Попробовать большой перерыв'); test_short_button = QPushButton('Попробовать короткую паузу')
        test_big_button.clicked.connect(self.test_big_break); test_short_button.clicked.connect(self.test_short_pause)
        test_layout.addWidget(test_big_button); test_layout.addWidget(test_short_button)
        layout.addWidget(big_break_group); layout.addWidget(short_pause_group); layout.addLayout(warning_layout)
        layout.addWidget(self.strict_mode_checkbox); layout.addWidget(self.sound_checkbox); layout.addWidget(self.start_sound_checkbox)
        layout.addWidget(self.darken_checkbox); layout.addWidget(self.autostart_checkbox); layout.addWidget(self.tracking_checkbox)
        layout.addLayout(test_layout); layout.addStretch()
        self.tab_widget.addTab(settings_widget, 'Настройки')
        
    def create_practices_tab(self):
        practices_widget = QWidget()
        layout = QVBoxLayout(practices_widget)
        add_group = QGroupBox("Новая практика")
        add_layout = QVBoxLayout(add_group)
        self.practice_text = QTextEdit(); self.practice_text.setPlaceholderText('Введите текст новой практики здесь...'); self.practice_text.setMaximumHeight(80)
        self.add_micropractice_checkbox = QCheckBox('Микропрактика (для коротких пауз)')
        add_button = QPushButton('Добавить'); add_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 6px; border-radius: 4px;"); add_button.clicked.connect(self.add_practice)
        add_layout.addWidget(self.practice_text); add_layout.addWidget(self.add_micropractice_checkbox); add_layout.addWidget(add_button)
        list_group = QGroupBox("Существующие практики")
        list_layout = QVBoxLayout(list_group)
        scroll_area = QScrollArea(); scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.practices_layout = QVBoxLayout(self.scroll_content); self.practices_layout.setSpacing(5); self.practices_layout.setAlignment(Qt.AlignTop)
        scroll_area.setWidget(self.scroll_content)
        delete_button = QPushButton("Удалить выбранные"); delete_button.setStyleSheet("background-color: #f44336; color: white; padding: 6px; border-radius: 4px;"); delete_button.clicked.connect(self.delete_selected_practices)
        list_layout.addWidget(scroll_area); list_layout.addWidget(delete_button)
        layout.addWidget(add_group); layout.addWidget(list_group)
        # self.update_practices_list() # <-- Удаляем вызов отсюда, он теперь в showEvent
        self.tab_widget.addTab(practices_widget, 'Практики')

    def create_info_tab(self):
        info_widget = QWidget()
        layout = QVBoxLayout(info_widget)
        info_text = QTextBrowser(); info_text.setReadOnly(True); info_text.setOpenExternalLinks(True)
        info_text.setHtml("""
            <h1>MindfulPause</h1><p><b>Версия:</b> 1.1</p>
            <p>Приложение для регулярных перерывов и практик осознанности.<br>
            Делайте перерывы, снижайте стресс, повышайте концентрацию!</p><br>
            <p><b>Сайт проекта:</b> <a href="https://www.danzasemantica.ru/MindfulPause/">Danzasemantica.ru</a></p>
            <p><b>Обратная связь (Telegram):</b> <a href="https://t.me/danzasemantica/1077">Обсуждение проекта</a></p>
            <p><b>Поддержать проект:</b></p>
            <ul><li>Для РФ: <a href="https://pay.cloudtips.ru/p/012f0b15">CloudTips</a></li><li>Для остального мира: <a href="https://t.me/danzasemantica/570">Telegram</a></li></ul>
        """)
        layout.addWidget(info_text)
        self.tab_widget.addTab(info_widget, 'Информация')
        
    def set_tooltips(self):
        self.strict_mode_checkbox.setToolTip('В строгом режиме большой перерыв нельзя прервать или свернуть.\nВ обычном режиме его можно завершить: сначала кликните по окну, затем нажмите Esc.')
        self.warning_checkbox.setToolTip('Показывает небольшое окно с обратным отсчетом\nза указанное время до начала большого перерыва.')
        self.sound_checkbox.setToolTip('Проигрывает звуковой сигнал по завершении большого перерыва.')
        self.start_sound_checkbox.setToolTip('Проигрывает звуковой сигнал в момент начала короткой паузы.')
        self.darken_checkbox.setToolTip('Короткая пауза будет отображаться на весь экран с темным фоном.\nЕсли опция выключена, пауза появится в небольшом окне по центру экрана.')
        self.autostart_checkbox.setToolTip('Приложение будет автоматически запускаться вместе с Windows.')
        self.tracking_checkbox.setToolTip('Приостанавливает таймер большого перерыва, если вы не пользуетесь компьютером,\nи возобновляет его, когда вы возвращаетесь.')
        
    def load_settings(self):
        self.big_break_checkbox.setChecked(self.settings.get('big_break_enabled', True))
        self.big_break_interval.setValue(self.settings.get('big_break_interval', 60))
        self.big_break_duration.setValue(self.settings.get('big_break_duration', 5))
        self.short_pause_checkbox.setChecked(self.settings.get('short_pause_enabled', True))
        self.short_pause_interval.setValue(self.settings.get('short_pause_interval', 20))
        self.short_pause_duration.setValue(self.settings.get('short_pause_duration', 20))
        self.warning_checkbox.setChecked(self.settings.get('warning_enabled', True))
        self.warning_time.setValue(self.settings.get('warning_time', 30))
        self.strict_mode_checkbox.setChecked(self.settings.get('strict_mode', False))
        self.sound_checkbox.setChecked(self.settings.get('sound_enabled', True))
        self.start_sound_checkbox.setChecked(self.settings.get('sound_start_enabled', True))
        self.darken_checkbox.setChecked(self.settings.get('darken_short_pause', False))
        self.autostart_checkbox.setChecked(self.settings.get('autostart', False))
        self.tracking_checkbox.setChecked(self.settings.get('track_activity', True))
        
    def apply_ui_to_settings(self):
        self.settings['big_break_enabled'] = self.big_break_checkbox.isChecked(); self.settings['big_break_interval'] = self.big_break_interval.value()
        self.settings['big_break_duration'] = self.big_break_duration.value(); self.settings['short_pause_enabled'] = self.short_pause_checkbox.isChecked()
        self.settings['short_pause_interval'] = self.short_pause_interval.value(); self.settings['short_pause_duration'] = self.short_pause_duration.value()
        self.settings['warning_enabled'] = self.warning_checkbox.isChecked(); self.settings['warning_time'] = self.warning_time.value()
        self.settings['strict_mode'] = self.strict_mode_checkbox.isChecked(); self.settings['sound_enabled'] = self.sound_checkbox.isChecked()
        self.settings['sound_start_enabled'] = self.start_sound_checkbox.isChecked(); self.settings['darken_short_pause'] = self.darken_checkbox.isChecked()
        self.settings['autostart'] = self.autostart_checkbox.isChecked(); self.settings['track_activity'] = self.tracking_checkbox.isChecked()
        
    def save_settings(self): self.apply_ui_to_settings(); self.xml_manager.save_settings(self.settings)
    def save_and_close(self): self.save_settings(); self.settings_saved.emit(); self.close()
        
    def add_practice(self):
        text = self.practice_text.toPlainText().strip()
        if text:
            if self.add_micropractice_checkbox.isChecked(): self.xml_manager.add_micropractice(text)
            else: self.xml_manager.add_practice(text)
            self.practice_text.clear(); self.update_practices_list()
            
    def update_practices_list(self):
        # Очищаем старый список виджетов
        for i in reversed(range(self.practices_layout.count())): 
            widget = self.practices_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        self.practice_checkboxes.clear(); self.micropractice_checkboxes.clear()
        
        self.practices_layout.addWidget(QLabel("<b>Практики для больших перерывов:</b>"))
        practices = self.xml_manager.get_all_practices()
        if practices:
            for p_text in practices: 
                cb = QCheckBox(p_text)
                self.practice_checkboxes.append(cb)
                self.practices_layout.addWidget(cb)
        else: 
            self.practices_layout.addWidget(QLabel("<i>(пусто)</i>"))
            
        self.practices_layout.addWidget(QLabel("<br><b>Микропрактики для коротких пауз:</b>"))
        micropractices = self.xml_manager.get_all_micropractices()
        if micropractices:
            for p_text in micropractices: 
                cb = QCheckBox(p_text)
                self.micropractice_checkboxes.append(cb)
                self.practices_layout.addWidget(cb)
        else: 
            self.practices_layout.addWidget(QLabel("<i>(пусто)</i>"))

    def delete_selected_practices(self):
        p_del = [cb.text() for cb in self.practice_checkboxes if cb.isChecked()]
        m_del = [cb.text() for cb in self.micropractice_checkboxes if cb.isChecked()]
        if p_del: self.xml_manager.delete_practices(p_del)
        if m_del: self.xml_manager.delete_micropractices(m_del)
        self.update_practices_list()

    def run_test(self, test_function):
        if self.app and hasattr(self.app, test_function.__name__):
            self.save_settings(); self.settings_saved.emit()
            self.hide(); QTimer.singleShot(200, test_function); QTimer.singleShot(1000, self.show)

    def test_big_break(self): self.run_test(self.app.test_big_break)
    def test_short_pause(self): self.run_test(self.app.test_short_pause)
    def closeEvent(self, event): self.save_settings(); self.settings_saved.emit(); event.accept()