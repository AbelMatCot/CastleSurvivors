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
THORNS_VALUES = [0, 2, 4, 7, 10]

UI_TOWER_NAMES = {
    "arrow": "Archer Tower", "fireball": "Fireball", "kunai": "Kunai Volley",
    "laser": "Ice Beam", "lightning": "Chain Lightning", "thorns": "Thorns Ground"
}

TOWER_DESCRIPTIONS = {
    "arrow": {
        1: "High range and firerate. Arrows can penetrate enemies at higher levels.",
        2: "Damage increased.", 3: "Firerate increased. Tower limit increased.",
        4: "Now arrows can penetrate one enemy.", 5: "Damage increased. Tower limit increased.",
        6: "Firerate increased.", 7: "Arrows can penetrate two enemies. Tower limit increased.",
        8: "Range, damage and firerate greatly increased."
    },
    "fireball": {
        1: "High damage, low firerate. Projectiles explode dealing damage in an area.",
        2: "Damage increased.", 3: "Firerate increased. Area increased.",
        4: "Damage increased. Tower limit increased.", 5: "Range increased. Firerate increased.",
        6: "Damage increased. Area increased.", 7: "Tower limit increased.",
        8: "Range, damage, firerate and area greatly increased."
    },
    "kunai": {
        1: "High firerate. Shoots multiple projectiles at higher levels.",
        2: "Firerate increased.", 3: "Number of projectiles increased.",
        4: "Damage increased. Tower limit increased.", 5: "Number of projectiles increased.",
        6: "Range increased. Firerate increased.", 7: "Tower limit increased.",
        8: "Range, damage, firerate and number of projectiles greatly increased."
    },
    "laser": {
        1: "Low damage, but slows enemies down.",
        2: "Damage increased.", 3: "Range increased. Slow increased.",
        4: "Damage increased. Tower limit increased.", 5: "Range increased. Slow increased.",
        6: "Damage increased.", 7: "Tower limit increased.",
        8: "Range, damage and slow greatly increased."
    },
    "lightning": {
        1: "High firerate, low damage. Projectiles bounce between enemies.",
        2: "Damage increased.", 3: "Firerate increased. Bounce range increased.",
        4: "Bounces increased. Tower limit increased.", 5: "Damage increased.",
        6: "Bounces increased. Firerate increased.", 7: "Tower limit increased.",
        8: "Range, damage, firerate and bounces greatly increased."
    },
    "thorns": {
        1: "Spawns a thorny patch under enemies that deals damage over time.",
        2: "Damage increased.", 3: "Patch area and maximum target limit increased.",
        4: "Damage and tower limit increased. Range slightly increased.",
        5: "Patch attack speed increased. Max target limit increased.",
        6: "Damage and patch area increased.", 7: "Range and tower limit increased. Max target limit increased.",
        8: "High damage, large area and extremely fast tick rate."
    }
}

PASSIVE_DESCRIPTIONS = {
    "damage": "Increases the damage of all your towers by 5% per level.",
    "firerate": "Increases the attack speed of all your towers by 5% per level.",
    "range": "Increases the range and area of effect of your towers by 5% per level.",
    "health": "Increases Castle and Wall maximum health by 5% per level.",
    "regen": "Regenerates 1% of Castle health per second per level.",
    "armor": "Reduces incoming damage to Castle and Walls by 5% per level.",
    "thorns": "Enemies taking damage from walls or castle take damage back.",
    "gold": "Increases gold earned from enemies by 5% per level.",
    "xp": "Increases experience earned from enemies by 5% per level.",
    "crit": "10% chance per level to deal 150% damage."
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
    14: {"Basic": 20, "Fast": 15, "Flyer": 15, "Tank": 25, "Shooter": 15, "Generator": 10}
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
