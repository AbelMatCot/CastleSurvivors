GAME_VERSION = "0.8.5"

# =====================================================================
# VALORES DE LA CUADRÍCULA (GRID) Y DIMENSIONES
# =====================================================================
allow = 0
forbid = 1
wall = 2
castle = 3
margin = 4
spawn = 5
spawn_zone = 6
mountain = 7
turret = 8

width_gameboard = 720
height_gameboard = 720
offsetX = 280
grid_size = 30
col = 24
row = 24

# =====================================================================
# ESTADÍSTICAS BÁSICAS Y NOMBRES
# =====================================================================
TOWER_BASE_HP = [0, 50, 55, 65, 80, 100, 125, 150, 200]
COUNTER_VALUES = [0, 2, 4, 7, 10]

UI_TOWER_NAMES = {
    "arrow": "Archer Tower", "fireball": "Fireball", "kunai": "Kunai Volley",
    "laser": "Ice Beam", "lightning": "Chain Lightning", "thorns": "Spikes Ground","smite": "Holy Smite"
}

TOWER_DESCRIPTIONS = {
    "arrow": {
        1: "High range and firerate. Arrows can penetrate enemies at higher levels.",
        2: "Damage increased.",
        3: "Firerate and tower limit increased.",
        4: "Now arrows can penetrate one enemy.",
        5: "Damage and tower limit increased.",
        6: "Firerate increased.",
        7: "Arrows can penetrate two enemies. Tower limit increased.",
        8: "Range, damage and firerate greatly increased."
    },
    "fireball": {
        1: "Projectiles explode dealing high damage in an area.",
        2: "Damage increased.",
        3: "Firerate and area increased.",
        4: "Damage and tower limit increased.",
        5: "Range and firerate increased.",
        6: "Damage and area increased.",
        7: "Tower limit increased.",
        8: "Range, damage, firerate and area greatly increased."
    },
    "kunai": {
        1: "High firerate. Shoots multiple projectiles at higher levels.",
        2: "Firerate increased.",
        3: "Number of projectiles increased.",
        4: "Damage and Tower limit increased.",
        5: "Number of projectiles increased.",
        6: "Range and firerate increased.",
        7: "Tower limit increased.",
        8: "Range, damage, firerate and number of projectiles greatly increased."
    },
    "laser": {
        1: "Low damage, but slows enemies down.",
        2: "Damage increased.",
        3: "Range and slow increased.",
        4: "Damage and tower limit increased.",
        5: "Range and slow increased.",
        6: "Damage increased.",
        7: "Tower limit increased.",
        8: "Range, damage and slow greatly increased."
    },
    "lightning": {
        1: "Projectiles bounce between close enemies.",
        2: "Damage increased.",
        3: "Firerate and bounce range increased.",
        4: "Bounces and tower limit increased.",
        5: "Damage increased.",
        6: "Bounces and firerate increased.",
        7: "Tower limit increased.",
        8: "Range, damage, firerate and bounces greatly increased."
    },
    "thorns": {
        1: "Spikes rise from the ground dealing damage over time in an area.",
        2: "Damage increased.",
        3: "Spikes' spawn rate increased.",
        4: "Damage and tower limit increased.",
        5: "Range and area of effect increased.",
        6: "Spikes' spawn rate increased.",
        7: "Tower limit increased.",
        8: "Range, damage, spawn rate and area of effect greatly increased."
    },
    "smite": {
        1: "Low firerate, high damage. Summons a holy hammer that deals damage in an area",
        2: "Firerate increased.",
        3: "Damage increased.",
        4: "Area and tower limit increased.",
        5: "Range and firerate increased.",
        6: "Damage increased.",
        7: "Tower limit increased.",
        8: "Range, damage, firerate and area greatly increased."
    }
}

PASSIVE_DESCRIPTIONS = {
    "damage": "Increases the damage of all your towers by 5% per level.",
    "firerate": "Increases the attack speed of all your towers by 5% per level.",
    "range": "Increases the range and area of effect of your towers by 5% per level.",
    "health": "Increases Castle and Wall maximum health by 5% per level.",
    "regen": "Regenerates 0,5% of Castle and structures health per second per level.",
    "armor": "Reduces incoming damage to Castle and Walls by 5% per level.",
    "counter": "Structures avoid damage while hurting the attacker.",
    "gold": "Increases gold earned from enemies by 5% per level.",
    "xp": "Increases experience earned from enemies by 5% per level.",
    "crit": "10% chance per level to deal 150% damage.",
    "heal": "Restores 20% of your Castle's maximum health.",
    "goldbag": "Adds 100 gold to your current stash.",
    "gems_5": "Grants 5 extra gems for permanent upgrades."
}

# =====================================================================
# OLEADAS Y ENEMIGOS
# =====================================================================
ENEMY_WEIGHTS = {
    "Basic": 1.0, "Fast": 1.0, "Swarmer": 0,
    "Shooter": 2.0, "Flyer": 2.0, "Tank": 4.0, "Generator": 15.0
}

WAVE_POOLS = {
    0: {"Basic": 100},
    2: {"Basic": 70, "Fast": 30},
    5: {"Basic": 50, "Fast": 30, "Flyer": 20},
    8: {"Basic": 40, "Fast": 20, "Flyer": 20, "Tank": 20},
    12: {"Basic": 30, "Fast": 15, "Flyer": 20, "Tank": 20, "Shooter": 15},
    14: {"Basic": 20, "Fast": 15, "Flyer": 15, "Tank": 25, "Shooter": 15, "Generator": 10},
    17: {"Basic": 20, "Fast": 15, "Flyer": 20, "Tank": 30, "Shooter": 10, "Generator": 5}
}

# =====================================================================
# MAPEOS VISUALES Y CONTROLES (BITMASKING Y TECLADO)
# =====================================================================
wall_mask_map = {
    10: (0, 0), 5: (1, 0), 15: (2, 0), 0: (3, 0),
    3: (0, 1), 6: (1, 1), 12: (2, 1), 9: (3, 1),
    1: (0, 2), 4: (1, 2), 8: (2, 2), 2: (3, 2),
    11: (0, 3), 7: (1, 3), 14: (2, 3), 13: (3, 3)
}

KEYMAP_COORDS = {
    "a": (0, 2), "b": (1, 2), "c": (2, 2), "d": (3, 2), "e": (4, 2), "f": (5, 2), "g": (6, 2), "h": (7, 2),
    "i": (0, 3), "j": (1, 3), "k": (2, 3), "l": (3, 3), "m": (4, 3), "n": (5, 3), "o": (6, 3), "p": (7, 3),
    "q": (0, 4), "r": (1, 4), "s": (2, 4), "t": (3, 4), "u": (4, 4), "v": (5, 4), "w": (6, 4), "x": (7, 4),
    "y": (0, 5), "z": (1, 5),
    "1": (0, 7), "2": (1, 7), "3": (2, 7), "4": (3, 7), "5": (2, 4), "6": (4, 7), "7": (5, 7), "8": (6, 7), "9": (7, 7),
    "0": (6, 3), "esc": (5, 6),
    "up": (0, 0), "down": (1, 0), "left": (2, 0), "right": (3, 0),
    "f1": (4, 0), "f2": (5, 0), "f3": (6, 0), "f4": (7, 0),
    "f5": (0, 1), "f6": (1, 1), "f7": (2, 1), "f8": (3, 1), "f9": (4, 1), "f10": (5, 1), "f11": (6, 1), "f12": (7, 1),
    ".": (2, 5), ",": (3, 5), "?": (4, 5), "/": (5, 5), "\\": (6, 5), "=": (7, 5),
    "'": (0, 6), "[": (1, 6), "]": (2, 6), "+": (3, 6), "-": (4, 6), ";": (6, 6)
}