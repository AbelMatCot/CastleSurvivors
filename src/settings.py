import os
import configparser
import pygame

config = configparser.ConfigParser()
config_file = "config.ini"

if not os.path.exists(config_file):
    config["Keybinds"] = {
        "slot_1": "1", "slot_2": "2", "slot_3": "3", "slot_4": "4",
        "wall": "w", "sell": "q", "repair": "e", "repair_all": "r",
        "toggle_hp": "v"
    }
    config["Settings"] = {
        "legible_font": "False",
        "health_bars_mode": "0",
        "language": "en"
    }
    with open(config_file, "w") as f:
        config.write(f)
else:
    config.read(config_file)
    if "Settings" not in config:
        config["Settings"] = {"legible_font": "False", "health_bars_mode": "0", "language": "en"}
        with open(config_file, "w") as f:
            config.write(f)
    else:
        # Añadimos la comprobación específica para el idioma
        if "language" not in config["Settings"]:
            config["Settings"]["language"] = "en"
            with open(config_file, "w") as f:
                config.write(f)

    if "toggle_hp" not in config["Keybinds"]:
        config["Keybinds"]["toggle_hp"] = "v"
        with open(config_file, "w") as f:
            config.write(f)

use_legible_font = config.getboolean("Settings", "legible_font", fallback=False)
health_bars_mode = config.getint("Settings", "health_bars_mode", fallback=0)
language = config.get("Settings", "language", fallback="en")

def get_key(key_str):
    try:
        return getattr(pygame, f"K_{key_str.lower()}")
    except AttributeError:
        return pygame.K_UNKNOWN

controls = {
    "slot_1": get_key(config["Keybinds"]["slot_1"]),
    "slot_2": get_key(config["Keybinds"]["slot_2"]),
    "slot_3": get_key(config["Keybinds"]["slot_3"]),
    "slot_4": get_key(config["Keybinds"]["slot_4"]),
    "wall": get_key(config["Keybinds"]["wall"]),
    "sell": get_key(config["Keybinds"]["sell"]),
    "repair": get_key(config["Keybinds"]["repair"]),
    "repair_all": get_key(config["Keybinds"]["repair_all"]),
    "toggle_hp": get_key(config["Keybinds"]["toggle_hp"])
}

if "borderless_fullscreen" not in config["Settings"]:
    config["Settings"]["resolution"] = "1280x720"
    config["Settings"]["borderless_fullscreen"] = "False"
    with open(config_file, "w") as f:
        config.write(f)

res_str = config.get("Settings", "resolution", fallback="1280x720")
res_x, res_y = map(int, res_str.split("x"))
resolution = (res_x, res_y)
borderless_fullscreen = config.getboolean("Settings", "borderless_fullscreen", fallback=False)