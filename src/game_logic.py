import random
from gamedata import *
from Entities.spawn import Spawn
from Entities.effects import Effect
from gamedata import UI_TOWER_NAMES, TOWER_DESCRIPTIONS, PASSIVE_DESCRIPTIONS


def get_valid_border(spawn_type, forced_initial_spawns, spawn_counts):
    if spawn_type == "wildcard":
        return random.choice(["North", "South", "East", "West"])
    else:
        if len(forced_initial_spawns) > 0:
            return forced_initial_spawns.pop(0)
        min_count = min(spawn_counts.values())
        valid_borders = [b for b, c in spawn_counts.items() if c - min_count < 2]
        if not valid_borders:
            valid_borders = ["North", "South", "East", "West"]
        return random.choice(valid_borders)


def setup_spawn_point(spwn_grp, effects_group, grid, spawn_type, forced_initial_spawns, spawn_counts, existing_spawns_pos, assets):
    side = get_valid_border(spawn_type, forced_initial_spawns, spawn_counts)
    if not side: return

    valid_pos = False
    attempts = 0
    center = 0

    while not valid_pos and attempts < 50:
        center = random.randint(2, col - 3)
        conflict = False
        for pos in existing_spawns_pos[side]:
            if abs(center - pos) <= 2:
                conflict = True
                break
        if not conflict:
            valid_pos = True
        attempts += 1

    if not valid_pos: return

    existing_spawns_pos[side].append(center)
    spawn_counts[side] += 1

    if side == "North":
        spawn_x, spawn_y = center, -1
        grid[0][center] = margin
        fx_base = offsetX + (center * grid_size) + 15
        fy_base = 0 * grid_size + 15
    elif side == "South":
        spawn_x, spawn_y = center, row
        grid[row - 1][center] = margin
        fx_base = offsetX + (center * grid_size) + 15
        fy_base = (row - 1) * grid_size + 15
    elif side == "West":
        spawn_x, spawn_y = -1, center
        grid[center][0] = margin
        fx_base = offsetX + 0 * grid_size + 15
        fy_base = (center * grid_size) + 15
    elif side == "East":
        spawn_x, spawn_y = col, center
        grid[center][col - 1] = margin
        fx_base = offsetX + (col - 1) * grid_size + 15
        fy_base = (center * grid_size) + 15

    new_spawn = Spawn(spawn_x, spawn_y)
    spwn_grp.add(new_spawn)

    offsets = [(0, 0, 0.0), (-14, 8, 0.15), (14, 18, 0.3)]
    for ox, oy, dly in offsets:
        dust = Effect(fx_base + ox, fy_base + oy, assets.dust_sheet, scale_size=70, fps=11, delay=dly)
        effects_group.add(dust)


# ¡OJO AL NUEVO PARÁMETRO 'lang' AL FINAL!
def get_level_up_cards(player_level, active_towers, tower_levels, active_passives, passive_levels, lang):
    fallback_cards = [
        {"title": lang.get("card_heal_title", "Heal Castle"), "desc": lang.get("passive_desc_heal",
                                                                               PASSIVE_DESCRIPTIONS[
                                                                                   "heal"]), "type": "heal", "id": "heal", "lvl": 8},
        {"title": lang.get("card_gold_title", "Gold Bag"), "desc": lang.get("passive_desc_goldbag",
                                                                            PASSIVE_DESCRIPTIONS[
                                                                                "goldbag"]), "type": "gold", "id": "goldbag", "lvl": 8},
        {"title": lang.get("card_gems_title", "Gems"), "desc": lang.get("passive_desc_gems_5", PASSIVE_DESCRIPTIONS[
            "gems_5"]), "type": "gems_5", "id": "gems", "lvl": 8}
    ]

    if player_level > 50:
        return fallback_cards

    pool = []
    has_free_slot = None in active_towers

    for t_id in ["arrow", "fireball", "kunai", "laser", "lightning", "thorns", "smite"]:
        lvl = tower_levels[t_id]
        name = lang.get(f"tower_name_{t_id}", UI_TOWER_NAMES[t_id])
        if lvl == 0:
            if has_free_slot:
                desc = lang.get(f"tower_desc_{t_id}_1", TOWER_DESCRIPTIONS[t_id][1])
                pool.append({"title": name, "desc": desc, "type": "upgrade_tower", "id": t_id, "lvl": 1})
        elif lvl < 8:
            desc = lang.get(f"tower_desc_{t_id}_{lvl + 1}", TOWER_DESCRIPTIONS[t_id][lvl + 1])
            pool.append({"title": name, "desc": desc, "type": "upgrade_tower", "id": t_id, "lvl": lvl + 1})

    passive_names = {
        "damage": "Damage", "firerate": "Firerate", "range": "Range/Area",
        "health": "Max Health", "regen": "Health Regen", "armor": "Armor",
        "counter": "Counter", "gold": "Extra Gold", "xp": "Extra XP", "crit": "Critical"
    }

    for p_id, lvl in passive_levels.items():
        name = lang.get(f"passive_name_{p_id}", passive_names.get(p_id, ""))
        desc = lang.get(f"passive_desc_{p_id}", PASSIVE_DESCRIPTIONS.get(p_id, ""))

        if lvl == 0:
            if len(active_passives) < 6:
                pool.append({"title": name, "desc": desc, "type": "unlock_passive", "id": p_id, "lvl": 1})
        elif lvl < 4:
            pool.append({"title": name, "desc": desc, "type": "upgrade_passive", "id": p_id, "lvl": lvl + 1})

    random.shuffle(pool)
    cards = pool[:3]

    if len(cards) == 0:
        return fallback_cards

    return cards
