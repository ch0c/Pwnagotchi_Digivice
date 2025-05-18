import logging
import os
import json
import random
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

import pwnagotchi
import pwnagotchi.plugins as plugins
import pwnagotchi.ui.fonts as fonts
from pwnagotchi.ui.components import LabeledValue, Text, Rect, FilledRect, Line, Bitmap
from pwnagotchi.ui.view import BLACK
from pwnagotchi.utils import save_config

FACE_FOLDERS = {
    # Rookie
    "agumon": "/custom-faces/agumon/",
    "betamon": "/custom-faces/betamon/",
    "gabumon": "/custom-faces/gabumon/",
    # Champion
    "greymon": "/custom-faces/greymon/",
    "tyrannomon": "/custom-faces/tyrannomon/",
    "devimon": "/custom-faces/devimon/",
    "meramon": "/custom-faces/meramon/",
    "airdramon": "/custom-faces/airdramon/",
    "seadramon": "/custom-faces/seadramon/",
    "numemon": "/custom-faces/numemon/",
    "garurumon": "/custom-faces/garurumon/",
    "kabuterimon": "/custom-faces/kabuterimon/",
    # Ultimate
    "metal greymon": "/custom-faces/metalgreymon/",
    "metal garurumon": "/custom-faces/metalgarurumon/",
    "skull greymon": "/custom-faces/skullgreymon/",
    "mamemon": "/custom-faces/mamemon/",
    "monzaemon": "/custom-faces/monzaemon/",
}

# Experience point values
DEAUTH_XP = 1.2
HANDSHAKE_XP = 1.5
ASSOCIATION_XP = 0.8
ROOKIE_EVOLVE_XP = 1500
CHAMPION_EVOLVE_XP = 3000

# File paths
DATA_FILE = "/etc/pwnagotchi/digivice_data.json"
AGE_ICON_PATH = "/custom-faces/age.png"
EVOLVE_ICON_PATH = "/custom-faces/evolve.png"

FACE_TYPES = [
    "look_r", "look_l", "look_r_happy", "look_l_happy",
    "sleep", "sleep2", "awake", "bored", "intense", "cool",
    "happy", "excited", "grateful", "motivated", "demotivated",
    "smart", "lonely", "sad", "angry", "friend", "broken",
    "debug", "upload", "upload1", "upload2"
]


class Digivice(plugins.Plugin):
    __author__ = 'choc'
    __version__ = '2.1.0'
    __license__ = 'GPL3'
    __description__ = 'Digivice Plugin'

    def __init__(self):
        self.exp = 0
        self.age_days = 0
        self.current_form = None
        self.start_time = None
        self.assoc_count = 0
        self.deauth_count = 0
        self.handshake_count = 0
        self.starter = "random"
        self.agent = None
        self.exp_bar_rect = None
        self.exp_bar_fill = None
        
        # Evolution pathways
        self.evolution_conditions = {
            "rookie": {
                "agumon": [
                    {'form': 'greymon',    'deauths': 40,  'handshakes': 80},
                    {'form': 'tyrannomon', 'handshakes': 70},
                    {'form': 'devimon',    'deauths': 50},
                    {'form': 'meramon',    'associations': 800},
                    {'form': 'numemon'}
                ],
                "betamon": [
                    {'form': 'devimon',    'deauths': 40,  'handshakes': 80},
                    {'form': 'meramon',    'handshakes': 70},
                    {'form': 'airdramon',  'deauths': 50},
                    {'form': 'seadramon',  'associations': 800},
                    {'form': 'numemon'}                
                ],
                "gabumon": [
                    {'form': 'garurumon',  'deauths': 40, 'handshakes': 80},
                    {'form': 'kabuterimon','handshakes': 90},
                    {'form': 'numemon'}
                ]
            },
            "champion": {
                "greymon":      {'form': 'metal greymon',   'deauths': 60,  'handshakes': 120},
                "garurumon":    {'form': 'metal garurumon', 'associations': 1200, 'handshakes': 120},
                "kabuterimon":  {'form': 'skull greymon',   'handshakes': 110},
                "tyrannomon":   {'form': 'mamemon',         'handshakes': 110},
                "meramon":      {'form': 'mamemon',         'associations': 1300},
                "seadramon":    {'form': 'mamemon',         'associations': 1300},
                "devimon":      {'form': 'metal greymon',   'deauths': 60,  'handshakes': 120},
                "airdramon":    {'form': 'metal greymon',   'deauths': 60,  'handshakes': 120},
                "numemon":      {'form': 'monzaemon',       'associations': 1300, 'deauths': 60}
            }
        }

    def on_loaded(self):
        self.starter = self.options.get("starter", "random").lower()
        if self.starter not in ["agumon", "betamon", "gabumon", "random"]:
            self.starter = "random"
            
        logging.info(f"[Digivice] Plugin loaded. Starter: {self.starter.title()}")
        self.load_data()

    def load_data(self):
        try:
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, "r") as f:
                    data = json.load(f)
                    self.exp = data.get("exp", 0)
                    self.current_form = data.get("current_form", self.select_starting_digimon())
                    self.assoc_count = data.get("assoc_count", 0)
                    self.deauth_count = data.get("deauth_count", 0)
                    self.handshake_count = data.get("handshake_count", 0)
                    start_time_str = data.get("start_time")
                    self.start_time = (datetime.datetime.fromisoformat(start_time_str) 
                                      if start_time_str else datetime.datetime.now())
            else:
                self.initialize_new_data()
        except Exception as e:
            logging.error(f"[Digivice] Load error: {e}, resetting data")
            self.initialize_new_data()

    def initialize_new_data(self):
        self.current_form = self.select_starting_digimon()
        self.start_time = datetime.datetime.now()
        self.exp = 0
        self.assoc_count = 0
        self.deauth_count = 0
        self.handshake_count = 0
        self.save_data()
        self.modify_config()

    def select_starting_digimon(self) -> str:
        if self.starter == "random":
            return random.choice(["agumon", "betamon", "gabumon"])
        return self.starter

    def save_data(self):
        try:
            os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
            
            data = {
                "exp": self.exp,
                "current_form": self.current_form,
                "start_time": self.start_time.isoformat(),
                "assoc_count": self.assoc_count,
                "deauth_count": self.deauth_count,
                "handshake_count": self.handshake_count
            }
            
            with open(DATA_FILE, "w") as f:
                json.dump(data, f, indent=4)
                
        except Exception as e:
            logging.error(f"[Digivice] Save error: {e}")

    def get_scaled_threshold(self, base_threshold: int) -> int:
        adjusted_age = max(0, self.age_days - 2)
        life_span = int(self.options.get('life_span', 15))
        age_factor = min(1.8, 1.0 + (adjusted_age / life_span))
        
        return max(10, int(base_threshold / age_factor))

    def check_evolution(self) -> str:
        current = self.current_form

        if current in ["agumon", "betamon", "gabumon"]:
            if self.exp < ROOKIE_EVOLVE_XP:
                return current

            candidates = []
            for condition in self.evolution_conditions["rookie"][current]:
                score = self._calculate_evolution_score(condition)
                
                if score >= 1.0:
                    candidates.append(condition['form'])

            if random.random() < 0.2:
                candidates.append('numemon')

            return random.choice(candidates) if candidates else 'numemon'

        elif current in self.evolution_conditions["champion"]:
            if self.exp < CHAMPION_EVOLVE_XP:
                return current

            condition = self.evolution_conditions["champion"][current]
            scores = self._calculate_evolution_scores(condition)

            if all(score >= 1.0 for score in scores):
                return condition['form']

            return current
            
        return current

    def _calculate_evolution_score(self, condition: Dict[str, Any]) -> float:
        score = 0
        if 'deauths' in condition:
            scaled = self.get_scaled_threshold(condition['deauths'])
            score += (self.deauth_count / scaled) * 1.2
        if 'handshakes' in condition:
            scaled = self.get_scaled_threshold(condition['handshakes'])
            score += (self.handshake_count / scaled) * 1.0
        if 'associations' in condition:
            scaled = self.get_scaled_threshold(condition['associations'])
            score += (self.assoc_count / scaled) * 0.8
            
        return score

    def _calculate_evolution_scores(self, condition: Dict[str, Any]) -> List[float]:
        scores = []
        
        if 'deauths' in condition:
            scaled = self.get_scaled_threshold(condition['deauths'])
            scores.append(self.deauth_count / scaled)
        if 'handshakes' in condition:
            scaled = self.get_scaled_threshold(condition['handshakes'])
            scores.append(self.handshake_count / scaled)
        if 'associations' in condition:
            scaled = self.get_scaled_threshold(condition['associations'])
            scores.append(self.assoc_count / scaled)
            
        return scores

    def update_evolution(self):
        new_form = self.check_evolution()
        if new_form != self.current_form:
            logging.info(f"[Digivice] Evolution! {self.current_form.title()} → {new_form.title()}")
            self.current_form = new_form
            self.modify_config()
            self.save_data()
            self.restart_device()

    def modify_config(self):
        try:
            config = pwnagotchi.config
            face_path = FACE_FOLDERS.get(self.current_form)
            
            if not face_path:
                logging.error(f"[Digivice] Missing face path for {self.current_form}")
                return
                
            config.setdefault("ui", {}).setdefault("faces", {})
            for face_type in FACE_TYPES:
                config["ui"]["faces"][face_type] = f"{face_path}{face_type}.png"
            
            save_config(config, "/etc/pwnagotchi/config.toml")
        except Exception as e:
            logging.error(f"[Digivice] Config error: {e}")

    def on_ui_setup(self, ui):
        ui.add_element('name', Text(color=BLACK, value=' ', position=(200, 200), font=fonts.Medium))
        ui.add_element('current_form', Text(color=BLACK, value="", position=(1, 14), font=fonts.Bold))
        ui.add_element('clock', LabeledValue(color=BLACK, label="", value="", position=(74, 0), 
                                          label_font=fonts.Small, text_font=fonts.Bold))
        
        if self.options.get('digistats', True):
            self._setup_digistats_ui(ui)

    def _setup_digistats_ui(self, ui):
        ui.add_element('age_icon', Bitmap(AGE_ICON_PATH, xy=(94, 26), color=BLACK))
        ui.add_element('age', LabeledValue(color=BLACK, label='', value="", 
                                        position=(98, 22), label_font=fonts.Bold, text_font=fonts.Medium))
        
        ui.add_element('handshakes', LabeledValue(color=BLACK, label='H:', value="0", 
                                              position=(52, 22), label_font=fonts.Bold, text_font=fonts.Medium))
        ui.add_element('associations', LabeledValue(color=BLACK, label='A:', value="0", 
                                                position=(52, 32), label_font=fonts.Bold, text_font=fonts.Medium))
        ui.add_element('deauths', LabeledValue(color=BLACK, label='D:', value="0", 
                                           position=(52, 42), label_font=fonts.Bold, text_font=fonts.Medium))
        ui.add_element('xp_count', LabeledValue(color=BLACK, label='XP:', value="", 
                                             position=(52, 52), label_font=fonts.Bold, text_font=fonts.Medium))
        
        xpbar_x, xpbar_y = map(int, self.options.get('xpbar_position', '53,64').split(','))
        self.exp_bar_rect = Rect(xy=(xpbar_x, xpbar_y, xpbar_x + 60, xpbar_y + 8), color=BLACK)
        self.exp_bar_fill = FilledRect(xy=(xpbar_x + 1, xpbar_y + 1, xpbar_x + 1, xpbar_y + 7), color=BLACK)
        ui.add_element('exp_bar_rect', self.exp_bar_rect)
        ui.add_element('exp_bar_fill', self.exp_bar_fill)
        
        ui.add_element('channel', LabeledValue(color=BLACK, label='CH', value="00", 
                                            position=(2, 0), label_font=fonts.Bold, text_font=fonts.Medium))
        ui.add_element('aps', LabeledValue(color=BLACK, label='APS', value="00", 
                                        position=(30, 0), label_font=fonts.Bold, text_font=fonts.Medium))
        ui.add_element('shakes', LabeledValue(color=BLACK, label='PWND ', value='0 (00)', 
                                           position=(2, 109), label_font=fonts.Bold, text_font=fonts.Medium))
        ui.add_element('mode', Text(value='AUTO', position=(224, 109), font=fonts.Bold, color=BLACK))
        
        window_border = Rect(xy=(0, 0, 249, 121), color=BLACK)
        ui.add_element('window_border', window_border)
        digivice_border = Rect(xy=(0, 14, 123, 76), color=BLACK)
        ui.add_element('digivice_border', digivice_border)
        status_divider = Line(xy=(123, 76, 250, 76), color=BLACK, width=1)
        ui.add_element('status_divider', status_divider)

    def on_ui_update(self, ui):
        ui.set('current_form', self.current_form.title())
        
        now = datetime.datetime.now()
        self.age_days = (now - self.start_time).days
        time_str = now.strftime("%I:%M %p")
        ui.set('clock', time_str)
        
        if self.options.get('digistats', True):
            self._update_digistats_ui(ui)

        life_span = int(self.options.get('life_span', 15))
        if self.age_days >= life_span:
            self._reset_digimon_lifecycle()

    def _update_digistats_ui(self, ui):
        ui.set('age', f"{self.age_days}A")
        ui.set('handshakes', f"{self.handshake_count}")
        ui.set('associations', f"{self.assoc_count}")
        ui.set('deauths', f"{self.deauth_count}")
        
        max_exp = CHAMPION_EVOLVE_XP if self.current_form in self.evolution_conditions["champion"] else ROOKIE_EVOLVE_XP
        xp_percentage = min(100, (self.exp / max_exp) * 100) if max_exp > 0 else 0
        ui.set('xp_count', f"{int(xp_percentage)}%")
        
        xpbar_x, xpbar_y = map(int, self.options.get('xpbar_position', '53,64').split(','))
        bar_width = int((xp_percentage / 100) * 60)
        self.exp_bar_fill.xy = (xpbar_x + 1, xpbar_y + 1, xpbar_x + 1 + bar_width, xpbar_y + 7)

    def _reset_digimon_lifecycle(self):
        logging.info("[Digivice] Life-span reset triggered")
        self.current_form = random.choice(["agumon", "betamon", "gabumon"])
        self.start_time = datetime.datetime.now()
        self.exp = 0
        self.assoc_count = 0
        self.deauth_count = 0
        self.handshake_count = 0
        self.save_data()
        self.modify_config()
        self.restart_device()

    def restart_device(self):
        try:
            os.system('sync')
            
            if hasattr(self, 'agent') and self.agent:
                view = self.agent.view()
                view.set('status', "Evolving...")
                view.set('face', EVOLVE_ICON_PATH)
                view.update(force=True)
                
            os.system("sudo systemctl restart pwnagotchi")
        except Exception as e:
            logging.error(f"[Digivice] Restart failed: {e}")

    def on_handshake(self, agent, filename, access_point, client_station):
        self.agent = agent
        self.exp += HANDSHAKE_XP
        self.handshake_count += 1
        self.save_data()
        self.update_evolution()

    def on_association(self, agent, access_point):
        self.agent = agent
        self.exp += ASSOCIATION_XP
        self.assoc_count += 1
        self.save_data()
        self.update_evolution()

    def on_deauthentication(self, agent, access_point, client_station):
        self.agent = agent
        self.exp += DEAUTH_XP
        self.deauth_count += 1
        self.save_data()
        self.update_evolution()
