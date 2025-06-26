# utils/xml_manager.py

import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
import random

class XMLManager:
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir
        self.settings_path = os.path.join(self.data_dir, 'settings_ru.xml')
        self.practice_path = os.path.join(self.data_dir, 'practice_ru.xml')
        self.micropractice_path = os.path.join(self.data_dir, 'micropractice_ru.xml')
        self.ensure_data_files_exist()

    def _pretty_print(self, root):
        xml_str = ET.tostring(root, 'utf-8')
        reparsed = minidom.parseString(xml_str)
        return reparsed.toprettyxml(indent="  ")

    def ensure_data_files_exist(self):
        os.makedirs(self.data_dir, exist_ok=True)
        if not os.path.exists(self.settings_path):
            root = ET.Element('settings')
            config = ET.SubElement(root, 'config')
            defaults = {
                'big_break_enabled': 'True', 'big_break_interval': '60', 'big_break_duration': '5',
                'short_pause_enabled': 'True', 'short_pause_interval': '20', 'short_pause_duration': '20',
                'warning_enabled': 'True', 'warning_time': '30', 'strict_mode': 'False',
                'sound_enabled': 'True', 'sound_start_enabled': 'True', 'darken_short_pause': 'False',
                'autostart': 'False', 'track_activity': 'True'
            }
            for k, v in defaults.items(): ET.SubElement(config, k).text = v
            with open(self.settings_path, 'w', encoding='utf-8') as f: f.write(self._pretty_print(root))
        
        if not os.path.exists(self.practice_path):
            root = ET.Element('practices')
            defaults = ['Пройдитесь по комнате, осознавая каждый шаг.', 'Гимнастика для глаз. Посмотрите вверх-вниз, влево-вправо.']
            # Используем тег <practice> при создании
            for p in defaults: ET.SubElement(root, 'practice').text = p
            with open(self.practice_path, 'w', encoding='utf-8') as f: f.write(self._pretty_print(root))

        if not os.path.exists(self.micropractice_path):
            root = ET.Element('practices')
            defaults = ['Один осознанный вдох-выдох.', 'Почувствуйте стопы.']
            # Используем тег <practice> при создании
            for p in defaults: ET.SubElement(root, 'practice').text = p
            with open(self.micropractice_path, 'w', encoding='utf-8') as f: f.write(self._pretty_print(root))

    def load_settings(self):
        try:
            tree = ET.parse(self.settings_path)
            root = tree.getroot()
            settings = {}
            config_element = root.find('config')
            if config_element is not None:
                for elem in config_element:
                    val = elem.text
                    if val is not None and val.lower() in ['true', 'false']:
                        settings[elem.tag] = (val.lower() == 'true')
                    elif val is not None:
                        settings[elem.tag] = int(val)
            return settings
        except (FileNotFoundError, ET.ParseError):
            print(f"Warning: Could not load settings from {self.settings_path}. Using defaults.")
            self.ensure_data_files_exist()
            return self.load_settings()

    def save_settings(self, settings):
        tree = ET.parse(self.settings_path); root = tree.getroot()
        config = root.find('config')
        for key, value in settings.items():
            elem = config.find(key)
            if elem is not None: elem.text = str(value)
        with open(self.settings_path, 'w', encoding='utf-8') as f: f.write(self._pretty_print(root))
    
    def _get_practices_from_file(self, file_path):
        if not os.path.exists(file_path): return []
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            # <<< ИЗМЕНЕНИЕ: Ищем тег 'practice', а не 'string' >>>
            return [elem.text for elem in root.findall('practice') if elem.text]
        except ET.ParseError as e:
            print(f"Error parsing XML file {file_path}: {e}")
            return []

    def get_all_practices(self): return self._get_practices_from_file(self.practice_path)
    def get_all_micropractices(self): return self._get_practices_from_file(self.micropractice_path)
    
    def get_random_practice(self): 
        practices = self.get_all_practices()
        return random.choice(practices or ["Время отдохнуть!"])
        
    def get_random_micropractice(self): 
        micropractices = self.get_all_micropractices()
        return random.choice(micropractices or ["Минутка для себя."])

    def _add_practice_to_file(self, text, file_path):
        tree = ET.parse(file_path); root = tree.getroot()
        # <<< ИЗМЕНЕНИЕ: Создаем тег 'practice', а не 'string' >>>
        ET.SubElement(root, 'practice').text = text
        with open(file_path, 'w', encoding='utf-8') as f: f.write(self._pretty_print(root))

    def add_practice(self, text): self._add_practice_to_file(text, self.practice_path)
    def add_micropractice(self, text): self._add_practice_to_file(text, self.micropractice_path)

    def _delete_practices_from_file(self, practices_to_delete, file_path):
        tree = ET.parse(file_path); root = tree.getroot()
        # <<< ИЗМЕНЕНИЕ: Ищем тег 'practice', а не 'string' >>>
        for p_text in practices_to_delete:
            for elem in root.findall('practice'):
                if elem.text == p_text: root.remove(elem)
        with open(file_path, 'w', encoding='utf-8') as f: f.write(self._pretty_print(root))

    def delete_practices(self, practices): self._delete_practices_from_file(practices, self.practice_path)
    def delete_micropractices(self, practices): self._delete_practices_from_file(practices, self.micropractice_path)
    
    def reload_practices(self): pass
    def get_ui_texts(self): return {}