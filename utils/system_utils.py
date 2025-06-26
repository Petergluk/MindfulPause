# utils/system_utils.py

import os
import sys
import ctypes
from ctypes import wintypes

class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [('cbSize', wintypes.UINT), ('dwTime', wintypes.DWORD)]

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

def get_idle_time_windows() -> float:
    last_input_info = LASTINPUTINFO(); last_input_info.cbSize = ctypes.sizeof(last_input_info)
    if user32.GetLastInputInfo(ctypes.byref(last_input_info)):
        current_time = kernel32.GetTickCount()
        if current_time < last_input_info.dwTime: return 0.0
        return (current_time - last_input_info.dwTime) / 1000.0
    return 0.0

def block_input():
    try: ctypes.windll.user32.BlockInput(True); print("Ввод заблокирован.")
    except Exception as e: print(f"Не удалось заблокировать ввод: {e}")

def unblock_input():
    try: ctypes.windll.user32.BlockInput(False); print("Ввод разблокирован.")
    except Exception as e: print(f"Не удалось разблокировать ввод: {e}")

def create_startup_shortcut():
    if sys.platform != 'win32': return
    try:
        import winshell
        from winshell import startup
        target_path = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(sys.argv[0])
        shortcut_path = os.path.join(startup(), "MindfulPause.lnk")
        with winshell.shortcut(shortcut_path) as shortcut:
            shortcut.path = target_path
            shortcut.working_directory = os.path.dirname(target_path)
            shortcut.description = "MindfulPause - приложение для перерывов"
            icon_path = os.path.join(os.path.dirname(target_path), 'data', 'pict', 'app.ico')
            if os.path.exists(icon_path): shortcut.icon_location = (icon_path, 0)
        print(f"Ярлык автозапуска создан: {shortcut_path}")
    except ImportError: print("Для автозапуска нужна библиотека 'winshell'. Установите ее: pip install winshell")
    except Exception as e: print(f"Ошибка создания ярлыка автозапуска: {e}")

def remove_startup_shortcut():
    if sys.platform != 'win32': return
    try:
        import winshell
        from winshell import startup
        shortcut_path = os.path.join(startup(), "MindfulPause.lnk")
        if os.path.exists(shortcut_path): os.remove(shortcut_path); print(f"Ярлык автозапуска удален: {shortcut_path}")
    except ImportError: print("Для автозапуска нужна библиотека 'winshell'.")
    except Exception as e: print(f"Ошибка удаления ярлыка автозапуска: {e}")