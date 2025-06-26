# MindfulPause.py

import sys
import os
import ctypes
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QStyle
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import QTimer

# Импортируем все необходимые модули
from utils.xml_manager import XMLManager
from utils.sound_manager import SoundManager
from utils.activity_tracker import ActivityTracker
from utils.system_utils import create_startup_shortcut, remove_startup_shortcut
from utils.timer_manager import TimerManager
from gui.settings_window import SettingsWindow
from gui.pause_window import PauseWindow, BreakWarningWindow

class MindfulPauseApp(QApplication):
    def __init__(self, sys_argv):
        super().__init__(sys_argv)
        self.setQuitOnLastWindowClosed(False)

        # Универсальный способ определения базовой директории
        if getattr(sys, 'frozen', False):
            self.BASE_DIR = os.path.dirname(sys.executable)
        else:
            self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))

        myappid = 'mycompany.myproduct.subproduct.version'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

        # --- Инициализация менеджеров ---
        self.xml_manager = XMLManager(data_dir=os.path.join(self.BASE_DIR, 'data'))
        self.settings = self.xml_manager.load_settings()
        
        self.sound_manager = SoundManager(base_dir=self.BASE_DIR)
        self.timer_manager = TimerManager()
        
        self.activity_tracker = ActivityTracker(
            timeout_minutes=30,
            is_enabled=self.settings.get('track_activity', True)
        )

        # --- Инициализация GUI ---
        self.warning_window = None
        self.active_pause_window = None
        self.settings_window = None

        # --- Состояние приложения ---
        self.is_paused_by_user = False
        self.is_temporarily_disabled = False
        self.disable_timer = QTimer(self)
        self.disable_timer.setSingleShot(True)
        self.disable_timer.timeout.connect(self.enable_app)

        # Создаем иконку трея здесь, чтобы она была частью основного класса
        self.create_tray_icon()
        self.tray_icon.show()

        # --- Подключение сигналов к слотам ---
        self.connect_signals()

        # --- Первоначальная настройка и запуск ---
        self.apply_settings()
        self.check_autostart()

    def create_tray_icon(self):
        """Создает иконку и меню в системном трее."""
        self.tray_icon = QSystemTrayIcon(self)
        
        active_icon_path = os.path.join(self.BASE_DIR, 'data', 'pict', 'app.ico')
        paused_icon_path = os.path.join(self.BASE_DIR, 'data', 'pict', 'app_paused.ico')

        self.active_icon = QIcon(active_icon_path)
        # Проверяем наличие иконки паузы, если нет - используем активную
        if os.path.exists(paused_icon_path):
            self.paused_icon = QIcon(paused_icon_path)
        else:
            print(f"Warning: Paused icon not found at {paused_icon_path}. Using active icon as a fallback.")
            self.paused_icon = self.active_icon
        
        self.tray_icon.setIcon(self.active_icon)
        self.tray_icon.setToolTip("MindfulPause")
        
        menu = QMenu()
        
        # Действие "Начать большой перерыв сейчас"
        break_now_action = QAction("Сделать большой перерыв сейчас", self)
        break_now_action.triggered.connect(self.test_big_break)
        menu.addAction(break_now_action)

        # Действие "Приостановить/Возобновить"
        self.pause_action = QAction("Приостановить таймеры", self)
        self.pause_action.triggered.connect(self.toggle_pause)
        menu.addAction(self.pause_action)

        # Меню "Отключить на время"
        disable_menu = QMenu("Отключить на время", menu)
        for hours in [1, 2, 3, 8]:
            # Используем lambda с параметром, чтобы передать значение
            action = QAction(f"На {hours} час(а)", disable_menu)
            action.triggered.connect(lambda checked, h=hours: self.disable_temporarily(h))
            disable_menu.addAction(action)
        menu.addMenu(disable_menu)

        menu.addSeparator()

        # Действие "Настройки"
        settings_action = QAction("Настройки", self)
        settings_action.triggered.connect(self.show_settings)
        menu.addAction(settings_action)
        
        menu.addSeparator()
        
        # Действие "Выход"
        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.quit)
        menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)

    def connect_signals(self):
        """Централизованное подключение всех сигналов к слотам."""
        self.timer_manager.big_break_signal.connect(self.show_warning_or_break)
        self.timer_manager.short_pause_signal.connect(self.show_short_pause)
        self.timer_manager.warning_signal.connect(self.show_warning_window)
        
        self.activity_tracker.user_inactive.connect(self.on_user_inactive)
        self.activity_tracker.user_active.connect(self.on_user_active)

    def apply_settings(self):
        """Применяет загруженные настройки ко всем компонентам приложения."""
        if self.is_temporarily_disabled or self.is_paused_by_user:
            return

        self.timer_manager.stop_all_timers()
        
        if self.settings.get('big_break_enabled', True):
            self.timer_manager.set_warning_time(self.settings.get('warning_time', 30))
            self.timer_manager.start_big_break_timer(self.settings.get('big_break_interval', 60))
        
        if self.settings.get('short_pause_enabled', True):
            self.timer_manager.start_short_pause_timer(self.settings.get('short_pause_interval', 20))

        self.activity_tracker.set_enabled(self.settings.get('track_activity', True))
        print("Таймеры и настройки обновлены.")

    def check_autostart(self):
        """Проверяет и устанавливает/удаляет ярлык автозапуска."""
        if self.settings.get('autostart', False):
            create_startup_shortcut()
        else:
            remove_startup_shortcut()

    def show_settings(self):
        """Показывает окно настроек."""
        if self.settings_window is None or not self.settings_window.isVisible():
            self.settings_window = SettingsWindow(self, self.xml_manager)
            self.settings_window.settings_saved.connect(self.on_settings_saved)
            self.settings_window.show()
            self.settings_window.activateWindow()
            self.settings_window.raise_()
        else:
            self.settings_window.activateWindow()
            self.settings_window.raise_()

    def on_settings_saved(self):
        """Вызывается при сохранении настроек."""
        self.settings = self.xml_manager.load_settings()
        self.check_autostart()
        if not self.is_paused_by_user and not self.is_temporarily_disabled:
            self.apply_settings()
        print("Настройки сохранены и применены.")

    def toggle_pause(self):
        """Переключает состояние паузы, инициированное пользователем."""
        self.is_paused_by_user = not self.is_paused_by_user
        
        if self.is_paused_by_user:
            self.timer_manager.stop_all_timers()
            self.activity_tracker.stop()
            self.pause_action.setText("Возобновить таймеры")
            self.tray_icon.setIcon(self.paused_icon)
            self.tray_icon.setToolTip("MindfulPause (на паузе)")
            print("Таймеры приостановлены пользователем.")
        else:
            self.pause_action.setText("Приостановить таймеры")
            self.tray_icon.setIcon(self.active_icon)
            self.tray_icon.setToolTip("MindfulPause")
            if not self.is_temporarily_disabled:
                self.apply_settings()
                print("Таймеры возобновлены пользователем.")

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_settings()

    def show_short_pause(self):
        if self.active_pause_window: return
        self.timer_manager.pause_all_timers()
        text = self.xml_manager.get_random_micropractice()
        duration = self.settings.get('short_pause_duration', 20)
        darken = self.settings.get('darken_short_pause', False)
        self.active_pause_window = PauseWindow(self, text, duration, is_big_break=False, darken_screen=darken)
        self.active_pause_window.pause_finished.connect(self.on_pause_finished)
        if self.settings.get('sound_start_enabled', True):
            self.sound_manager.play_start_sound()
        self.active_pause_window.show()

    def show_warning_or_break(self):
        if self.warning_window or self.active_pause_window: return
        if self.settings.get('warning_enabled', True):
            self.show_warning_window()
        else:
            self.start_big_break()

    def show_warning_window(self):
        if self.warning_window or self.active_pause_window: return
        self.warning_window = BreakWarningWindow(self.settings.get('warning_time', 30))
        self.warning_window.start_now_clicked.connect(self.start_big_break)
        self.warning_window.postpone_clicked.connect(self.on_warning_postponed)
        self.warning_window.show()

    def on_warning_postponed(self):
        if self.warning_window:
            self.warning_window.close()
            self.warning_window = None
        self.timer_manager.postpone_big_break(5)

    def start_big_break(self):
        if self.active_pause_window: return
        if self.warning_window:
            self.warning_window.close()
            self.warning_window = None
        self.timer_manager.stop_all_timers()
        text = self.xml_manager.get_random_practice()
        duration = self.settings.get('big_break_duration', 5) * 60
        strict = self.settings.get('strict_mode', False)
        self.active_pause_window = PauseWindow(self, text, duration, is_big_break=True, strict_mode=strict)
        self.active_pause_window.pause_finished.connect(self.on_pause_finished)
        self.active_pause_window.show()

    def on_pause_finished(self, manually_interrupted):
        if not self.active_pause_window: return
        was_big_break = self.active_pause_window.is_big_break
        was_strict = self.active_pause_window.strict_mode
        self.active_pause_window = None
        if was_big_break and was_strict and manually_interrupted:
            self.start_big_break()
            return
        if was_big_break and not manually_interrupted and self.settings.get('sound_enabled', True):
            self.sound_manager.play_end_sound()
        self.apply_settings()

    def on_user_inactive(self):
        if self.is_paused_by_user or self.is_temporarily_disabled: return
        print("Пользователь неактивен, таймеры на паузе.")
        self.timer_manager.pause_all_timers()

    def on_user_active(self):
        if self.is_paused_by_user or self.is_temporarily_disabled: return
        print("Пользователь снова активен, перезапускаем таймеры.")
        self.timer_manager.resume_all_timers()

    def test_big_break(self):
        if self.active_pause_window: self.active_pause_window.close()
        self.start_big_break()

    def test_short_pause(self):
        if self.active_pause_window: self.active_pause_window.close()
        self.show_short_pause()

    def disable_temporarily(self, hours):
        self.is_temporarily_disabled = True
        self.timer_manager.stop_all_timers()
        self.activity_tracker.stop()
        self.tray_icon.setIcon(self.paused_icon)
        self.tray_icon.setToolTip(f"MindfulPause - Отключено на {hours} час(а)")
        self.disable_timer.start(hours * 3600 * 1000)
        print(f"Приложение отключено на {hours} час(а).")

    def enable_app(self):
        self.is_temporarily_disabled = False
        self.tray_icon.setIcon(self.active_icon)
        self.tray_icon.setToolTip("MindfulPause")
        if not self.is_paused_by_user:
            self.apply_settings()
        print("Приложение снова активно.")

if __name__ == '__main__':
    app = MindfulPauseApp(sys.argv)
    sys.exit(app.exec())