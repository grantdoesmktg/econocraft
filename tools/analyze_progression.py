"""
Progression analyzer for the Economy Pack.

Reads the real game data dumped by `/kubejs export debug` (recipes after all mods and our KubeJS changes,
item tags, loot tables) plus our market catalog, quest book and tier locks, then works out what a player can
obtain at each market tier and reports:

  1. Skips: things obtainable before the tier they are meant for.
  2. Gaps: things the quest book (or market) expects at a tier that can't be obtained by then.
  3. Money loops: buy from the shop, craft, sell for more than it cost.
  4. Unpriced bulk outputs: things a tier's farms produce that the market won't buy.

Run: python3 tools/analyze_progression.py  ->  PROGRESSION-REPORT.md

It is a model, not the game: fluids are treated as available, chance outputs as guaranteed, and the world
sources per tier (below) are hand-written. Treat findings as leads to check, not verdicts.
"""
import glob
import json
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))
import build_locks as L  # noqa: E402
import market_catalog as M  # noqa: E402
import quest_content as Q  # noqa: E402

PACK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import paths  # noqa: E402
EXPORT = paths.export_dir()
TIERS = range(7)

# ------------------------------------------------------------------ world sources (hand-written model)

ISLAND = [  # tier 0: the Isles (void island, plains biome), shop, island mob spawns, fishing
    'minecraft:spruce_log', 'minecraft:spruce_sapling', 'minecraft:spruce_leaves', 'minecraft:dirt', 'minecraft:grass_block',
    'minecraft:cobblestone', 'minecraft:water_bucket', 'minecraft:bucket', 'minecraft:apple', 'minecraft:stick',
    'exdeorum:silkworm', 'minecraft:string',
    # passive mobs on grass
    'minecraft:beef', 'minecraft:leather', 'minecraft:porkchop', 'minecraft:mutton', 'minecraft:white_wool',
    'minecraft:chicken', 'minecraft:egg', 'minecraft:feather',
    # hostile mobs at night
    'minecraft:rotten_flesh', 'minecraft:bone', 'minecraft:arrow', 'minecraft:spider_eye', 'minecraft:gunpowder', 'minecraft:ender_pearl',
    # fishing (fish + vanilla treasure/junk)
    'minecraft:cod', 'minecraft:salmon', 'minecraft:tropical_fish', 'minecraft:pufferfish', 'minecraft:name_tag', 'minecraft:saddle',
    'minecraft:nautilus_shell', 'minecraft:bow', 'minecraft:fishing_rod', 'minecraft:lily_pad', 'minecraft:bowl', 'minecraft:ink_sac',
    'minecraft:tripwire_hook', 'minecraft:enchanted_book',
]
FRONTIER = [  # tier 3: the real overworld
    'minecraft:diamond', 'minecraft:emerald', 'minecraft:coal', 'minecraft:raw_iron', 'minecraft:raw_copper', 'minecraft:raw_gold',
    'minecraft:redstone', 'minecraft:lapis_lazuli', 'minecraft:amethyst_shard', 'minecraft:obsidian', 'minecraft:cobbled_deepslate',
    'minecraft:sand', 'minecraft:clay_ball', 'minecraft:sugar_cane', 'minecraft:cactus', 'minecraft:bamboo', 'minecraft:kelp',
    'minecraft:cocoa_beans', 'minecraft:sweet_berries', 'minecraft:melon_slice', 'minecraft:pumpkin', 'minecraft:honeycomb',
    'minecraft:oak_log', 'minecraft:birch_log', 'minecraft:jungle_log', 'minecraft:acacia_log', 'minecraft:dark_oak_log',
    'minecraft:mangrove_log', 'minecraft:cherry_log', 'minecraft:slime_ball', 'minecraft:heart_of_the_sea', 'minecraft:totem_of_undying',
    'minecraft:trident', 'minecraft:echo_shard', 'mekanism:raw_osmium', 'mekanism:raw_tin', 'mekanism:raw_lead', 'mekanism:raw_uranium',
    'mekanism:fluorite_gem', 'create:raw_zinc', 'mysticalagriculture:inferium_essence', 'mysticalagriculture:prosperity_shard',
    # Frontier-only mobs, biomes and structures
    'minecraft:glow_berries', 'minecraft:rabbit_foot', 'minecraft:glow_ink_sac', 'minecraft:phantom_membrane',
    'minecraft:prismarine_shard', 'minecraft:prismarine_crystals', 'minecraft:armadillo_scute', 'minecraft:turtle_scute',
    'minecraft:breeze_rod', 'minecraft:goat_horn', 'minecraft:wet_sponge', 'minecraft:sniffer_egg', 'minecraft:heavy_core',
]
NETHER = [  # tier 4
    'minecraft:netherrack', 'minecraft:soul_sand', 'minecraft:soul_soil', 'minecraft:quartz', 'minecraft:glowstone_dust',
    'minecraft:nether_wart', 'minecraft:magma_cream', 'minecraft:blaze_rod', 'minecraft:ghast_tear', 'minecraft:wither_skeleton_skull',
    'minecraft:ancient_debris', 'minecraft:basalt', 'minecraft:blackstone', 'minecraft:gold_nugget', 'minecraft:crimson_stem',
    'minecraft:warped_stem', 'minecraft:nether_star',
]
END_TWILIGHT = [  # tier 5
    'minecraft:end_stone', 'minecraft:chorus_fruit', 'minecraft:shulker_shell', 'minecraft:elytra', 'minecraft:dragon_egg',
    'minecraft:dragon_breath', 'minecraft:dragon_head',
]
WORLD = {0: ISLAND, 3: FRONTIER, 4: NETHER, 5: END_TWILIGHT}
LOOT_TIER = [(r'twilightforest', 5), (r'end_city|/end/|ender_dragon', 5), (r'nether|bastion|fortress|ruined_portal_nether', 4)]

# Recipe types the model can't judge (they need a specific mob, or exotic fluids/chemicals it treats as free).
IGNORE_TYPES = {'mob_grinding_utils:beheading', 'mekanism:nucleosynthesizing', 'create:filling', 'create:emptying',
                'mekanism:reaction', 'mekanism:chemical_infusing', 'mekanism:pigment_extracting'}
# Planting a seed gives the crop (not a recipe in the data).
PLANTING = {'minecraft:wheat_seeds': 'minecraft:wheat', 'minecraft:potato': 'minecraft:potato', 'minecraft:carrot': 'minecraft:carrot',
            'minecraft:beetroot_seeds': 'minecraft:beetroot', 'minecraft:melon_seeds': 'minecraft:melon_slice',
            'minecraft:pumpkin_seeds': 'minecraft:pumpkin', 'minecraft:sugar_cane': 'minecraft:sugar_cane',
            'farmersdelight:cabbage_seeds': 'farmersdelight:cabbage', 'farmersdelight:tomato_seeds': 'farmersdelight:tomato',
            'farmersdelight:onion': 'farmersdelight:onion', 'farmersdelight:rice': 'farmersdelight:rice',
            'minecraft:spruce_sapling': 'minecraft:spruce_log'}

OUTPUT_KEYS = re.compile(r'^(result|results|output|outputs|main_output|secondary_output|byproduct|byproducts|item_output|'
                         r'output_item|outputItem|result_item|drops|products|extra_outputs|secondaryOutput|mainOutput)$')
SLOT_LIST_KEYS = re.compile(r'^(ingredients|inputs|input_items|items|itemInputs|materials)$')
STRING_INPUT_KEYS = re.compile(r'^(mesh|catalyst|tool)$')


# ------------------------------------------------------------------ load data

def load_tags():
    tags = {}
    base = os.path.join(EXPORT, 'tags', 'minecraft', 'item')
    for f in glob.glob(os.path.join(base, '**', '*.json'), recursive=True):
        rel = os.path.relpath(f, base)[:-5]
        ns, path = rel.split(os.sep, 1)
        try:
            tags[f'{ns}:{path.replace(os.sep, "/")}'] = set(json.load(open(f)))
        except Exception:
            pass
    # Expand nested tag references ("#c:glass_blocks/cheap", "#forge:glass?").
    def expand(tag, seen):
        out = set()
        for v in tags.get(tag, ()):
            if v.startswith('#'):
                ref = v[1:].rstrip('?')
                if ref not in seen:
                    seen.add(ref)
                    out |= expand(ref, seen)
            else:
                out.add(v.rstrip('?'))
        return out
    return {t: expand(t, {t}) for t in tags}


TAGS = {}


def ing_options(node):
    """Acceptable items for one ingredient node (item, tag, list of alternatives)."""
    if isinstance(node, str):
        if node.startswith('#'):
            return set(TAGS.get(node[1:], set()))
        return {node} if ':' in node else set()
    if isinstance(node, list):
        out = set()
        for n in node:
            out |= ing_options(n)
        return out
    if isinstance(node, dict):
        if 'item' in node and isinstance(node['item'], str):
            return {node['item']}
        if 'tag' in node and isinstance(node['tag'], str):
            return set(TAGS.get(node['tag'], set()))
        if 'id' in node and isinstance(node['id'], str) and ('count' in node or len(node) <= 3):
            return {node['id']}
        for k in ('ingredient', 'itemInput', 'input', 'value'):
            if k in node:
                return ing_options(node[k])
    return set()


def collect_outputs(node, out):
    if isinstance(node, dict):
        if isinstance(node.get('id'), str) and 'fluid' not in node and 'amount' not in node:
            out.add(node['id'])
        elif isinstance(node.get('item'), str):
            out.add(node['item'])
        else:
            for v in node.values():
                collect_outputs(v, out)
    elif isinstance(node, list):
        for v in node:
            collect_outputs(v, out)
    elif isinstance(node, str) and ':' in node:
        out.add(node)


def parse_recipe(data):
    """-> (type, input slots: list[set], outputs: set)"""
    rtype = data.get('type', '')
    if rtype == 'create:sequenced_assembly':
        # Base ingredient plus each step's extra ingredient; the transitional item is internal. Main result only.
        slots = [ing_options(data.get('ingredient'))]
        transitional = (data.get('transitional_item') or data.get('transitionalItem') or {}).get('id')
        for step in data.get('sequence', []):
            for ing in step.get('ingredients', []):
                opts = ing_options(ing)
                if opts and transitional not in opts and not any('incomplete' in o for o in opts):
                    slots.append(opts)
        results = data.get('results', [])
        return rtype, [x for x in slots if x], ({results[0].get('id')} if results else set())
    slots, outputs = [], set()

    def walk(node, key=None):
        if isinstance(node, dict):
            for k, v in node.items():
                if k in ('type', 'neoforge:conditions', 'conditions', 'category', 'group', 'pattern', 'show_notification'):
                    continue
                if OUTPUT_KEYS.match(k):
                    collect_outputs(v, outputs)
                elif k == 'key' and isinstance(v, dict):
                    for ing in v.values():
                        opts = ing_options(ing)
                        if opts:
                            slots.append(opts)
                elif SLOT_LIST_KEYS.match(k) and isinstance(v, list):
                    for ing in v:
                        opts = ing_options(ing)
                        if opts:
                            slots.append(opts)
                elif STRING_INPUT_KEYS.match(k) and isinstance(v, (str, dict)):
                    opts = ing_options(v)
                    if opts:
                        slots.append(opts)
                elif isinstance(v, (dict, list)):
                    opts = ing_options(v) if isinstance(v, dict) and ('item' in v or 'tag' in v) else set()
                    if opts and 'fluid' not in v and 'amount' not in v:
                        slots.append(opts)
                    else:
                        walk(v, k)
        elif isinstance(node, list):
            for v in node:
                walk(v, key)

    walk(data)
    return rtype, slots, outputs


REMOVED = [re.compile(r[1:-1].replace('\\/', '/')) for r in L.REMOVE_RECIPE_IDS]  # JS /regex/ -> Python


def load_recipes():
    """All recipes from the export, including ones our script removed back then, re-filtered against the
    current locks (so the report reflects today's script even with an older export)."""
    buy_only = {m[0] for m in M.MACHINES if not m[0].startswith('exdeorum:') and m[0] != 'economy_core:frontier_gateway'}
    pot = re.compile(r'^botanypots:.*botany_pot$')
    recipes = []
    for base in ('recipes', 'removed_recipes'):
        for f in glob.glob(os.path.join(EXPORT, base, '**', '*.json'), recursive=True):
            try:
                data = json.load(open(f))
            except Exception:
                continue
            rid = os.path.relpath(f, os.path.join(EXPORT, base))[:-5].replace(os.sep, '/')
            rid = rid.replace('/', ':', 1)
            if any(rx.search(rid) for rx in REMOVED):
                continue
            rtype, slots, outputs = parse_recipe(data)
            outputs = {o for o in outputs if not o.startswith('minecraft:air')}
            if not outputs or outputs & buy_only:
                continue
            if any(pot.match(o) for o in outputs) and rid != 'botanypots:botanypots/crafting/terracotta_hopper_botany_pot':
                continue
            recipes.append((rid, rtype, slots, outputs))
    return recipes


def load_loot():
    """item -> earliest tier it can come from a structure chest."""
    loot = {}
    base = os.path.join(EXPORT, 'minecraft', 'loot_table')
    for f in glob.glob(os.path.join(base, '**', '*.json'), recursive=True):
        rel = os.path.relpath(f, base).replace(os.sep, '/')
        if '/chests/' not in rel and not rel.split('/')[1:2] == ['chests'] and 'chest' not in rel:
            continue
        tier = 3
        for pat, t in LOOT_TIER:
            if re.search(pat, rel):
                tier = t
                break
        try:
            txt = open(f).read()
        except Exception:
            continue
        for item in re.findall(r'"name"\s*:\s*"([a-z0-9_.-]+:[a-z0-9_/.-]+)"', txt):
            loot[item] = min(loot.get(item, 99), tier)
    return loot


# ------------------------------------------------------------------ tiers of things

def mod_lock_tier(item):
    ns = item.split(':')[0]
    best = 0
    for t, mods in L.MOD_LOCKS.items():
        if ns in mods:
            best = max(best, t)
    for t, items in L.ITEM_LOCKS.items():
        if item in items:
            best = max(best, t)
    return best


def station_tier(rtype):
    ns = rtype.split(':')[0] if ':' in rtype else 'minecraft'
    for t, mods in L.MOD_LOCKS.items():
        if ns in mods:
            return t
    return 0


def shop_items():
    """item -> (tier, price, is_machine)"""
    out = {}
    for iid, name, price, tier, purpose in M.MACHINES:
        out[iid] = (tier, price, True)
    for iid, name, price, tier, purpose in M.SUPPLIES:
        if iid not in out or price < out[iid][1]:
            out[iid] = (tier, price, False)
    return out


def quest_items():
    """(chapter, quest title, item, chapter tier) for every item task in the progression chapters."""
    chapter_tier = {'getting_started': 0, 'tinkerer': 1, 'engineer': 2, 'pioneer': 3, 'cultivator': 4, 'industrialist': 5, 'tycoon': 6}
    out = []
    for ch in Q.CHAPTERS:
        if ch['key'] not in chapter_tier:
            continue
        for q in ch['quests']:
            for t in q.get('tasks', []):
                if t[0] == 'item':
                    out.append((ch['title'], q['title'], t[1], chapter_tier[ch['key']]))
    return out


# ------------------------------------------------------------------ simulation

EXTRA = []  # (item, tier, why) filled in main()


def extra_sources():
    out = []
    try:
        registry = json.load(open(os.path.join(EXPORT, 'registries', 'item.json')))
    except Exception:
        registry = {}
    for item in registry:
        if item.startswith('twilightforest:'):
            out.append((item, 5, 'Twilight Forest (bosses, loot, mobs)'))
    for s_ in M.SELL:
        if s_[0].startswith('aquaculture:'):
            out.append((s_[0], 3, 'Aquaculture fishing in Frontier biomes'))
        if s_[0].startswith('hostilenetworks:') and s_[0].endswith('_prediction'):
            out.append((s_[0], s_[4], 'Hostile Neural Networks simulation chamber'))
    chapter_tier = {'getting_started': 0, 'tinkerer': 1, 'engineer': 2, 'pioneer': 3, 'cultivator': 4, 'industrialist': 5, 'tycoon': 6}
    for ch in Q.CHAPTERS:
        t = chapter_tier.get(ch['key'])
        if t is None:
            continue
        for q in ch['quests']:
            for item, n in q.get('items', []):
                gate_t = q['gate'][0] if q.get('gate') else t
                out.append((item, gate_t, f'quest reward: {q["title"]}'))
    return out


def simulate(recipes, loot, shop):
    first = {}      # item -> earliest tier
    how = {}        # item -> explanation
    removed_machines = {m[0] for m in M.MACHINES}

    def add(item, tier, why):
        if item not in first or tier < first[item]:
            first[item] = tier
            how[item] = why

    for tier in TIERS:
        for t, items in WORLD.items():
            if t <= tier:
                for i in items:
                    add(i, t, 'world')
        for item, t in loot.items():
            if t <= tier:
                add(item, t, 'structure loot')
        for item, (t, price, machine) in shop.items():
            if t <= tier:
                add(item, t, f'shop ({price:,})')
        for item, t, why in EXTRA:
            if t <= tier:
                add(item, t, why)
        changed = True
        while changed:
            changed = False
            # Items locked by ProgressiveStages can't be held before their tier, so they can't be used either.
            have = {i for i, t in first.items() if t <= tier and mod_lock_tier(i) <= tier}
            for seed, crop in PLANTING.items():
                if seed in have and (crop not in first or first[crop] > tier):
                    add(crop, max(first[seed], mod_lock_tier(crop)), f'planting {seed}')
                    changed = True
            for rid, rtype, slots, outputs in recipes:
                if rtype in IGNORE_TYPES or station_tier(rtype) > tier:
                    continue
                if all(slot & have for slot in slots):
                    for o in outputs:
                        if o not in first or first[o] > tier:
                            add(o, tier, f'recipe {rid} ({rtype})')
                            changed = True
    return first, how


# ------------------------------------------------------------------ report

def main():
    global TAGS
    if not os.path.isdir(EXPORT):
        sys.exit(f'No export at {EXPORT}. Run /kubejs export debug in game first.')
    TAGS = load_tags()
    recipes = load_recipes()
    loot = load_loot()
    shop = shop_items()
    EXTRA.extend(extra_sources())
    first, how = simulate(recipes, loot, shop)

    def eff(item):
        t = first.get(item)
        return None if t is None else max(t, mod_lock_tier(item))

    lines = ['# Economy Pack: Progression Report', '',
             f'Generated by `tools/analyze_progression.py` from the game export ({len(recipes):,} recipes, '
             f'{len(TAGS):,} item tags, {len(loot):,} items found in structure loot).', '',
             'This is a model: fluids count as available, chance drops as guaranteed, and world sources per tier are '
             'hand-written. Findings are leads to check, not verdicts.', '']

    # 1. Skips: sellable goods obtainable before their catalog tier.
    skips = []
    for iid, name, cat, price, tier, purpose in M.SELL:
        t = eff(iid)
        if t is not None and t < tier:
            skips.append((tier - t, name, iid, tier, t, how.get(iid, '')))
    skips.sort(reverse=True)
    lines += ['## 1. Skips: goods obtainable before their tier', '',
              'A good sold at the market that can be made earlier than the catalog assumes means income arrives early.', '']
    if skips:
        lines += ['| Item | Meant for tier | Available at | How |', '|---|---|---|---|']
        lines += [f'| {n} (`{i}`) | {mt} | {at} | {h} |' for _, n, i, mt, at, h in skips]
    else:
        lines.append('None found.')
    lines.append('')

    # Buy-only machines that are still craftable.
    craftable_machines = []
    machine_ids = {m[0]: m for m in M.MACHINES}
    for rid, rtype, slots, outputs in recipes:
        for o in outputs & set(machine_ids):
            craftable_machines.append((machine_ids[o][1], o, rid, rtype))
    lines += ['### Buy-only machines that still have a recipe', '']
    if craftable_machines:
        lines += ['| Machine | Recipe | Type |', '|---|---|---|']
        lines += [f'| {n} (`{o}`) | `{r}` | {t} |' for n, o, r, t in sorted(set(craftable_machines))]
    else:
        lines.append('None: every shop machine is buy-only.')
    lines.append('')

    # 2. Gaps: quest items not obtainable by their chapter's tier.
    gaps = []
    for chapter, quest, item, tier in quest_items():
        t = eff(item)
        if t is None or t > tier:
            gaps.append((chapter, quest, item, tier, 'never' if t is None else t))
    lines += ['## 2. Gaps: quest items not obtainable in time', '']
    if gaps:
        lines += ['| Chapter | Quest | Item | Chapter tier | First available |', '|---|---|---|---|---|']
        lines += [f'| {c} | {q} | `{i}` | {t} | {a} |' for c, q, i, t, a in gaps]
    else:
        lines.append('None: every progression quest item is obtainable by its chapter.')
    lines.append('')

    # Upgrade tiers: every tier-locked item should be obtainable at the tier it unlocks.
    stuck = []
    for t, items in L.ITEM_LOCKS.items():
        for i in items:
            e = eff(i)
            if e is None or e > t:
                stuck.append((i, t, 'never' if e is None else e))
    lines += ['### Tier-locked items that can\'t be obtained when they unlock', '',
              'Upgrade tiers of shop machine families (crafted from the tier below) and other tier-locked items.', '']
    lines += [f'- `{i}`: unlocks at tier {t}, first obtainable {a}' for i, t, a in stuck] or ['None: every upgrade path works.']
    lines.append('')

    never = [(n, i, t) for i, n, c, p, t, pu in M.SELL if eff(i) is None]
    lines += ['### Market goods that can never be obtained (in this model)', '']
    lines += [f'- {n} (`{i}`), tier {t}' for n, i, t in never] or ['None.']
    lines.append('')

    # 3. Money loops: shop-bought inputs -> sellable output worth more.
    sell_price = {s[0]: s[3] for s in M.SELL}
    loops = []
    for rid, rtype, slots, outputs in recipes:
        sold = [o for o in outputs if o in sell_price]
        if not sold or not slots:
            continue
        cost, tier_needed, ok = 0, station_tier(rtype), True
        for slot in slots:
            buyable = [(shop[i][1], shop[i][0]) for i in slot if i in shop and not shop[i][2]]
            free = [i for i in slot if eff(i) is not None and i not in sell_price and i not in shop]
            if buyable:
                price, t = min(buyable)
                cost += price
                tier_needed = max(tier_needed, t)
            elif free:
                continue  # obtainable for free-ish (world/craft); not part of a pure buy loop
            else:
                ok = False
                break
        value = sum(sell_price[o] for o in sold)
        if ok and cost > 0 and value > cost:
            loops.append((value - cost, rid, ', '.join(sold), cost, value, tier_needed))
    loops.sort(reverse=True)
    lines += ['## 3. Money loops: buy supplies, craft, sell for more', '']
    if loops:
        lines += ['| Profit per craft | Recipe | Sells | Supplies cost | Sell value | Tier |', '|---|---|---|---|---|---|']
        lines += [f'| {p:,} | `{r}` | {s} | {c:,} | {v:,} | {t} |' for p, r, s, c, v, t in loops[:40]]
    else:
        lines.append('None found.')
    lines.append('')

    # 4. Unpriced bulk outputs by tier (things farms make that the market won't buy).
    bulk_types = re.compile(r'(sieve|hammer|crushing|milling|crusher|harvest|compressed)')
    unpriced = defaultdict(set)
    for rid, rtype, slots, outputs in recipes:
        if not bulk_types.search(rtype):
            continue
        t = station_tier(rtype)
        for o in outputs:
            if o not in sell_price and eff(o) is not None:
                unpriced[max(t, eff(o))].add(o)
    lines += ['## 4. Unpriced bulk outputs', '',
              'Outputs of sieves, hammers, crushers and harvest machines that the market does not buy. '
              'Worth pricing if players will have stacks of them.', '']
    for t in TIERS:
        if unpriced[t]:
            items = sorted(unpriced[t])
            lines.append(f'- **Tier {t}** ({len(items)}): ' + ', '.join(f'`{i}`' for i in items[:40]) + (' ...' if len(items) > 40 else ''))
    lines.append('')

    # Summary of availability by tier.
    counts = defaultdict(int)
    for i in first:
        counts[eff(i)] += 1
    lines += ['## Items obtainable by tier (cumulative model)', '']
    total = 0
    for t in TIERS:
        total += counts[t]
        lines.append(f'- Tier {t}: {total:,} items')
    lines.append('')

    out = os.path.join(PACK, 'PROGRESSION-REPORT.md')
    open(out, 'w').write('\n'.join(lines))
    print(f'Wrote {out}: {len(skips)} skips, {len(set(craftable_machines))} craftable machines, {len(gaps)} gaps, '
          f'{len(never)} never-obtainable goods, {len(loops)} money loops')


if __name__ == '__main__':
    main()
