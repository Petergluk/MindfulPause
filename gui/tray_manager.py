# gui/tray_manager.py

# -*- coding: utf-8 -*-

import sys
import os
from PySide6.QtWidgets import QMenu, QSystemTrayIcon, QStyle # <--- ИСПРАВЛЕНИЕ: Добавлен импорт QStyle
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import QObject

class TrayManager(QObject):
    """Менеджер системного трея"""
    
    def __init__(self, app):
        super().__init__()
        self.app = app
        # ИСПРАВЛЕНО: Используем базовую директорию из главного класса
        self.base_dir = app.BASE_DIR
        self.create_tray_icon()
        
    def create_tray_icon(self):
        """Создание иконки в системном трее"""
        # ИСПРАВЛЕНО: Построение абсолютного пути к иконке
        icon_path = os.path.join(self.base_dir, 'data', 'pict', 'app.ico')
        
        if os.path.exists(icon_path):
            self.icon = QIcon(icon_path)
        else:
            # Запасной вариант, если иконка не найдена
            self.icon = self.app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon) # Используем QStyle.StandardPixmap
            
        self.tray_icon = QSystemTrayIcon(self.icon, self.app)
        self.tray_icon.setToolTip("MindfulPause")
        
        self.create_menu()
        
        self.tray_icon.activated.connect(self.on_tray_activated)
        
    def create_menu(self):
        """Создание контекстного меню"""
        self.menu = QMenu()
        
        settings_action = QAction("Открыть настройки", self.menu)
        settings_action.triggered.connect(self.app.show_settings)
        self.menu.addAction(settings_action)
        
        disable_menu = QMenu("Отключить на время", self.menu)
        disable_1h = QAction("На 1 час", disable_menu)
        disable_1h.triggered.connect(lambda: self.app.disable_temporarily(1))
        disable_menu.addAction(disable_1h)
        disable_2h = QAction("На 2 часа", disable_menu)
        disable_2h.triggered.connect(lambda: self.app.disable_temporarily(2))
        disable_menu.addAction(disable_2h)
        disable_3h = QAction("На 3 часа", disable_menu)
        disable_3h.triggered.connect(lambda: self.app.disable_temporarily(3))
        disable_menu.addAction(disable_3h)
        self.menu.addMenu(disable_menu)
        
        break_now_action = QAction("Сделать большой перерыв сейчас", self.menu)
        break_now_action.triggered.connect(self.app.start_big_break)
        self.menu.addAction(break_now_action)
        
        self.menu.addSeparator()
        
        quit_action = QAction("Выход", self.menu)
        quit_action.triggered.connect(self.app.quit_app)
        self.menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(self.menu)
        
    def on_tray_activated(self, reason):
        """Обработка клика по иконке в трее"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger: # Использовал полное имя для ясности
            # Левый клик показывает настройки
            self.app.show_settings()
            
    def show(self):
        self.tray_icon.show()
        
    def hide(self):
        self.tray_icon.hide()
        
    def update_status_disabled(self, hours):
        self.tray_icon.setToolTip(f"MindfulPause - Отключено на {hours} час(а)")
        
    def update_status_enabled(self):
        self.tray_icon.setToolTip("MindfulPause")