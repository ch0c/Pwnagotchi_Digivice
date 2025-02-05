import logging
import os
import json
import time
import random
from datetime import datetime
import pwnagotchi
import pwnagotchi.plugins as plugins
import pwnagotchi.ui.fonts as fonts
from pwnagotchi.ui.components import LabeledValue, Rect, FilledRect, Line, Bitmap
from pwnagotchi.ui.view import BLACK, WHITE
from pwnagotchi.utils import save_config
from PIL import Image

FACE_FOLDERS = {
    "agumon": "/custom-faces/agumon/",
    "greymon": "/custom-faces/greymon/",
    "metal greymon": "/custom-faces/metalgreymon/",
    "numemon": "/custom-faces/numemon/",
    "monzaemon": "/custom-faces/monzaemon/",
    "gabumon": "/custom-faces/gabumon/",
    "kabuterimon": "/custom-faces/kabuterimon/",
    "garurumon": "/custom-faces/garurumon/",
    "skull greymon": "/custom-faces/skullgreymon/",
    "metal garurumon": "/custom-faces/metalgarurumon/",
}
EXP_FILE = "/etc/pwnagotchi/exp_data.json"
AGE_ICON_PATH = "/custom-faces/age.png"
EVOLVE_ICON_PATH = "/custom-faces/evolve.png"

class Digivice(plugins.Plugin):
    __author__ = 'choc'
    __version__ = '1.0.1'
    __license__ = 'GPL3'
    __description__ = 'Digivice Plugin with Age & EXP Evolution'

    def __init__(self):
        self.exp = 0
        self.age_days = 0
        self.current_form = None
        self.start_time = None  
        self.last_evolution_check = 0  
        self.last_exp = 0
        self.last_age_days = 0
        self.assoc_count = 0
        self.deauth_count = 0
        self.handshake_count = 0
        self.starter = None

    def on_loaded(self):
        """Load configuration options and initialize data."""
        self.starter = self.options.get("starter", "random").lower()
        if self.starter not in ["agumon", "gabumon", "random"]:
            logging.warning(f"[Digivice] Invalid starter '{self.starter}'. Defaulting to 'random'.")
            self.starter = "random"
        logging.info(f"[Digivice] Plugin loaded. Starter Digimon: {self.starter}")
        self.load_data()

    def load_data(self):
        """Load EXP and age data from a single JSON file."""
        try:
            if os.path.exists(EXP_FILE):
                with open(EXP_FILE, "r") as f:
                    data = json.load(f)
                    self.exp = data.get("exp", 0)
                    self.current_form = data.get("current_form")
                    start_time_str = data.get("start_time")
                    if start_time_str:
                        self.start_time = datetime.fromisoformat(start_time_str)
                    else:
                        self.start_time = datetime.now()
                    
                    if self.current_form not in FACE_FOLDERS:
                        logging.warning(f"[Digivice] Invalid current_form '{self.current_form}'. Resetting to starter.")
                        self.current_form = self.select_starting_digimon()
                    
                    self.age_days = (datetime.now() - self.start_time).days
            else:
                logging.info("[Digivice] EXP file not found. Initializing new data.")
                self.current_form = self.select_starting_digimon()
                self.start_time = datetime.now()
                self.save_data(first_time=True)
                self.modify_config()
                self.restart_device()
        except json.JSONDecodeError as je:
            logging.error(f"[Digivice] JSON decode error: {je}. Resetting data.")
            self.current_form = self.select_starting_digimon()
            self.start_time = datetime.now()
            self.exp = 0
            self.save_data(first_time=True)
            self.modify_config()
            self.restart_device()
        except Exception as e:
            logging.error(f"[Digivice] Error loading data: {e}. Resetting data.")
            self.current_form = self.select_starting_digimon()
            self.start_time = datetime.now()
            self.exp = 0
            self.save_data(first_time=True)
            self.modify_config()
            self.restart_device()

    def select_starting_digimon(self):
        """Select starting Digimon based on the config option."""
        if self.starter == "random":
            return random.choice(["agumon", "gabumon"])
        return self.starter

    def save_data(self, first_time=False):
        """Save EXP, evolution form, and start time to JSON."""
        try:
            if first_time or self.start_time is None:
                self.start_time = datetime.now() 
            data = {
                "exp": self.exp,
                "current_form": self.current_form,
                "start_time": self.start_time.isoformat(),
            }
            with open(EXP_FILE, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            logging.error(f"[Digivice] Error saving data: {e}")

    def get_evolution_stage(self):
        """Determine evolution based on EXP and Age."""
        if self.age_days < 2:
            return self.current_form

        if self.current_form == "agumon":
            return "greymon" if self.exp >= 500 else "numemon"
        if self.current_form == "greymon" and self.exp >= 1000:
            return "metal greymon"
        if self.current_form == "numemon" and self.exp >= 1000:
            return "monzaemon"

        if self.current_form == "gabumon":
            return "kabuterimon" if self.exp >= 500 else "garurumon"
        if self.current_form == "kabuterimon" and self.exp >= 1000:
            return "skull greymon"
        if self.current_form == "garurumon" and self.exp >= 1000:
            return "metal garurumon"

        return self.current_form

    def update_face_folder(self):
        """Update face folder if evolution occurs."""
        new_form = self.get_evolution_stage()
        if new_form != self.current_form:
            logging.info(f"[Digivice] Evolving into {new_form}")
            self.current_form = new_form
            self.modify_config()
            self.save_data()
            self.restart_device()

    def modify_config(self):
        """Modify the face paths in config.toml."""
        try:
            config = pwnagotchi.config
            face_path = FACE_FOLDERS[self.current_form]

            if "ui" not in config:
                config["ui"] = {}
            if "faces" not in config["ui"]:
                config["ui"]["faces"] = {}

            for key in [
                "look_r", "look_l", "look_r_happy", "look_l_happy", "sleep", "sleep2",
                "awake", "bored", "intense", "cool", "happy", "excited", "grateful",
                "motivated", "demotivated", "smart", "lonely", "sad", "angry",
                "friend", "broken", "debug", "upload", "upload1", "upload2"
            ]:
                config["ui"]["faces"][key] = f"{face_path}{key}.png"

            save_config(config, "/etc/pwnagotchi/config.toml")
            logging.info("[Digivice] Updated face folder in config.toml")
        except KeyError as ke:
            logging.error(f"[Digivice] KeyError in modify_config: {ke}. Ensure the current_form '{self.current_form}' exists in FACE_FOLDERS.")
        except Exception as e:
            logging.error(f"[Digivice] Error modifying config.toml: {e}")

    def on_ui_setup(self, ui):
        """Add EXP bar, Age counter, and Current Form to UI."""
        window_border = Rect(xy=(0, 0, 249, 121), color=BLACK)
        ui.add_element('window_border', window_border)

        digivice_border = Rect(xy=(0, 14, 123, 76), color=BLACK)
        ui.add_element('digivice_border', digivice_border)
        
        status_border = Rect(xy=(123, 14, 249, 65), color=BLACK)
        ui.add_element('status_border', status_border)

        lower_divider = Line(xy=(123, 76, 123, 108), color=BLACK, width=1)
        ui.add_element('lower_divider', lower_divider)

        ui.add_element('current_form', LabeledValue(color=BLACK, label='', value="", position=(2, 14), label_font=fonts.Small, text_font=fonts.Bold))
        
        self.age_icon = Bitmap(AGE_ICON_PATH, xy=(94, 18), color=BLACK)
        ui.add_element('age_icon', self.age_icon)
        
        ui.add_element('age', LabeledValue(color=BLACK, label='', value="", position=(103, 14), label_font=fonts.Bold, text_font=fonts.Medium))
        
        ui.add_element('handsk_count', LabeledValue(color=BLACK, label='H:', value="0", position=(52, 28), label_font=fonts.Bold, text_font=fonts.Medium))
        ui.add_element('assoc_count', LabeledValue(color=BLACK, label='A:', value="0", position=(52, 38), label_font=fonts.Bold, text_font=fonts.Medium))
        ui.add_element('deauth_count', LabeledValue(color=BLACK, label='D:', value="0", position=(86, 38), label_font=fonts.Bold, text_font=fonts.Medium))

        if self.options['xpbar']:
            ui.add_element('xp_count', LabeledValue(color=BLACK, label='XP:', value="", position=(52, 50), label_font=fonts.Bold, text_font=fonts.Medium))
            xpbar_x, xpbar_y = map(int, self.options['xpbar_position'].split(','))
            self.exp_bar_rect = Rect(xy=(xpbar_x, xpbar_y, xpbar_x + 60, xpbar_y + 8), color=BLACK)
            ui.add_element('exp_bar_rect', self.exp_bar_rect)
            self.exp_bar_fill = FilledRect(xy=(xpbar_x + 1, xpbar_y + 1, xpbar_x + 1, xpbar_y + 7), color=BLACK) 
            ui.add_element('exp_bar_fill', self.exp_bar_fill) 

    def on_ui_update(self, ui):
        """Updates the UI with EXP progress, Age, and Current Form."""
        if self.current_form is None:
            logging.error("[Digivice] current_form is None! Resetting to starter.")
            self.current_form = self.select_starting_digimon()
            if self.start_time is None:
                self.start_time = datetime.now()
            self.save_data()

        if self.start_time:
            current_age = (datetime.now() - self.start_time).days
            if current_age >= 5:
                logging.info("[Digivice] 5-day cycle reached! Resetting Digimon...")
                self.current_form = random.choice(["agumon", "gabumon"])
                self.start_time = datetime.now()
                self.exp = 0
                self.age_days = 0
                self.save_data()
                self.modify_config()
                self.restart_device()
                return
            self.age_days = current_age

        if self.exp != self.last_exp or self.age_days != self.last_age_days:
            self.last_exp = self.exp
            self.last_age_days = self.age_days
            self.update_face_folder()

        if self.options['xpbar']:
            xp_percentage = min(100, int((self.exp / 1000) * 100))
            ui.set('xp_count', f"{xp_percentage}%")
            xpbar_x, xpbar_y = map(int, self.options['xpbar_position'].split(','))
            bar_width = int((xp_percentage / 100) * 60)
            self.exp_bar_fill.xy = (xpbar_x + 1, xpbar_y + 1, xpbar_x + 1 + bar_width, xpbar_y + 7)

        ui.set('current_form', self.current_form.title())
        ui.set('age', f"{self.age_days}A")
        ui.set('assoc_count', f"{self.assoc_count}")
        ui.set('deauth_count', f"{self.deauth_count}")
        ui.set('handsk_count', f"{self.handshake_count}")

    def restart_device(self):
        """Restart the device after updating the config."""
        try:
            logging.info("[Digivice] Syncing filesystem before reboot...")
            os.system('sync') 

            if hasattr(self, 'agent') and self.agent is not None:
                view = self.agent.view()
                view.set('face', EVOLVE_ICON_PATH)
                view.update(force=True) 
            
            time.sleep(2)
            logging.info("[Digivice] Rebooting device after face update...")
            os.system("sudo systemctl restart pwnagotchi")
        except Exception as e:
            logging.error(f"[Digivice] Error during restart: {e}")
        
    def on_ready(self, agent):
        """Check for evolution when the device is ready."""
        logging.info("[Digivice] Plugin loaded and ready!")
        self.agent = agent  
        self.update_face_folder()

    def on_handshake(self, agent, filename, access_point, client_station):
        """Gain EXP from handshakes and check for evolution."""
        self.exp += 10
        self.handshake_count += 1
        self.save_data()  

    def on_association(self, agent, access_point):
        """Gain EXP from associations and check for evolution."""
        self.exp += 1
        self.assoc_count += 1
        self.save_data()  
        
    def on_deauthentication(self, agent, access_point, client_station):
        """Gain EXP from deauthentication attacks and check for evolution."""
        self.exp += 2
        self.deauth_count += 1
        self.save_data()
