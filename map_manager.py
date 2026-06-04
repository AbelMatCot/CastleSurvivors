from gamedata import *

def get_tile_for_cell(col_idx, row_idx, target_types, tile_dict, grid, oob_is_target=True):
    N = (row_idx == 0 and oob_is_target) or (row_idx > 0 and grid[row_idx - 1][col_idx] in target_types)
    S = (row_idx == row - 1 and oob_is_target) or (row_idx < row - 1 and grid[row_idx + 1][col_idx] in target_types)
    W = (col_idx == 0 and oob_is_target) or (col_idx > 0 and grid[row_idx][col_idx - 1] in target_types)
    E = (col_idx == col - 1 and oob_is_target) or (col_idx < col - 1 and grid[row_idx][col_idx + 1] in target_types)
    key = (int(N), int(S), int(W), int(E))
    return tile_dict.get(key, tile_dict.get((1, 1, 1, 1)))

def update_ruin_masks(r, c, grid, ruin_masks):
    mask = 0
    if r > 0 and grid[r - 1][c] == wall: mask += 1
    if c < col - 1 and grid[r][c + 1] == wall: mask += 2
    if r < row - 1 and grid[r + 1][c] == wall: mask += 4
    if c > 0 and grid[r][c - 1] == wall: mask += 8

    if mask == 0:
        if (r, c) in ruin_masks:
            del ruin_masks[(r, c)]
    else:
        ruin_masks[(r, c)] = mask

def update_wall_masks(r, c, grid, wall_masks, ruin_masks):
    mask = 0
    if r > 0 and (grid[r - 1][c] == wall or (r - 1, c) in ruin_masks): mask += 1
    if c < col - 1 and (grid[r][c + 1] == wall or (r, c + 1) in ruin_masks): mask += 2
    if r < row - 1 and (grid[r + 1][c] == wall or (r + 1, c) in ruin_masks): mask += 4
    if c > 0 and (grid[r][c - 1] == wall or (r, c - 1) in ruin_masks): mask += 8
    wall_masks[(r, c)] = mask

def update_neighbors_walls(r, c, grid, wall_masks, ruin_masks):
    for nr, nc in [(r, c), (r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]:
        if 0 <= nr < row and 0 <= nc < col:
            if grid[nr][nc] == wall:
                update_wall_masks(nr, nc, grid, wall_masks, ruin_masks)
            if (nr, nc) in ruin_masks:
                update_ruin_masks(nr, nc, grid, ruin_masks)

def generate_initial_grid():
    grid = [[0 for _ in range(col)] for _ in range(row)]
    for y in range(row):
        for x in range(col):
            if x == 0 or x == col - 1 or y == 0 or y == row - 1:
                grid[y][x] = mountain
            elif x < margin or x >= col - margin or y < margin or y >= row - margin:
                grid[y][x] = forbid
            else:
                grid[y][x] = allow

    grid[11][11] = castle
    grid[11][12] = castle
    grid[12][11] = castle
    grid[12][12] = castle
    return grid