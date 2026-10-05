"""Builds the Economy Pack starting island for Skyblock Builder:
a 5x5x3 block of dirt topped with grass and one small spruce tree in the middle
(a single spruce sapling never grows into a giant tree; only a 2x2 of saplings does). No chest, no extra items.

Run: python3 tools/make_island.py  -> config/skyblockbuilder/templates/islands/economy_island.nbt
"""
import os
from collections import deque

import nbt

W, D = 5, 5          # island footprint
GROUND = 3           # dirt, dirt, grass
TRUNK = 7            # log height above the grass
WOOD = 'spruce'
CX, CZ = W // 2, D // 2

blocks = {}  # (x, y, z) -> (name, props)
for x in range(W):
    for z in range(D):
        for y in range(GROUND):
            top = y == GROUND - 1
            blocks[(x, y, z)] = ('minecraft:grass_block', {'snowy': 'false'}) if top else ('minecraft:dirt', {})

base = GROUND
logs = [(CX, base + i, CZ) for i in range(TRUNK)]
for p in logs:
    blocks[p] = (f'minecraft:{WOOD}_log', {'axis': 'y'})

# Small-spruce cone: bare trunk at the bottom, alternating wide and narrow rings, pointed top.
top_log = base + TRUNK - 1
leaves = set()
LAYERS = ((-4, 2, True), (-3, 1, True), (-2, 2, True), (-1, 1, False), (0, 1, True), (1, 0, False))
for dy, radius, cut_corners in LAYERS:
    y = top_log + dy
    for dx in range(-radius, radius + 1):
        for dz in range(-radius, radius + 1):
            if cut_corners and abs(dx) == radius and abs(dz) == radius:
                continue
            pos = (CX + dx, y, CZ + dz)
            if pos not in blocks:
                leaves.add(pos)

# Leaf "distance" = steps to the nearest log (what the game stores), so the tree behaves naturally:
# chop the trunk and the leaves decay, dropping saplings and apples.
dist = {p: 0 for p in logs}
q = deque(logs)
while q:
    p = q.popleft()
    for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
        n = (p[0] + d[0], p[1] + d[1], p[2] + d[2])
        if n in leaves and n not in dist:
            dist[n] = dist[p] + 1
            q.append(n)
for p in leaves:
    blocks[p] = (f'minecraft:{WOOD}_leaves', {'distance': str(min(7, dist.get(p, 7))), 'persistent': 'false', 'waterlogged': 'false'})

palette, index, out_blocks = [], {}, []
for pos, (name, props) in sorted(blocks.items(), key=lambda kv: (kv[0][1], kv[0][0], kv[0][2])):
    key = (name, tuple(sorted(props.items())))
    if key not in index:
        index[key] = len(palette)
        entry = {'Name': name}
        if props:
            entry['Properties'] = dict(props)
        palette.append(entry)
    out_blocks.append({'pos': [nbt.Tag(nbt.INT, c) for c in pos], 'state': index[key]})

xs = [p[0] for p in blocks]; ys = [p[1] for p in blocks]; zs = [p[2] for p in blocks]
size = [max(xs) + 1, max(ys) + 1, max(zs) + 1]
root = {
    'size': [nbt.Tag(nbt.INT, s) for s in size],
    'entities': nbt.Tag(nbt.LIST, []),
    'blocks': out_blocks,
    'palette': palette,
    'DataVersion': 3955,  # Minecraft 1.21.1
}
pack = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(pack, 'config', 'skyblockbuilder', 'templates', 'islands', 'economy_island.nbt')
os.makedirs(os.path.dirname(out), exist_ok=True)
nbt.save(out, root)
print(f'Wrote {out}: size {size}, {len(out_blocks)} blocks ({len(leaves)} leaves)')
