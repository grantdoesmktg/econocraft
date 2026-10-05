"""
Generates the tier locks for the Economy Pack:
  - config/progressivestages/stages/tier_N/rules.toml  (mods, items and dimensions locked until tier N)
  - kubejs/server_scripts/economy_locks.js              (recipe removals: sieve gems, coin minting, buy-only machines)

Run: python3 tools/build_locks.py
A ProgressiveStages "lock" rule in stage tier_N applies to every player whose team does not have tier_N yet.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import market_catalog as M  # noqa: E402

PACK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Whole mods locked until a tier. Libraries and quality-of-life mods are never locked.
MOD_LOCKS = {
    1: ['create', 'farmersdelight', 'botanypots', 'fishermens_trap', 'cookingforblockheads', 'farmingforblockheads'],
    # Construction Sticks open from the start (Grant, 2026-10-05): building shouldn't wait on tiers.
    2: ['cyclic', 'mob_grinding_utils', 'excompressum', 'waystones', 'toms_storage', 'buildinggadgets2'],
    3: ['mysticalagriculture', 'naturescompass', 'explorerscompass', 'refinedstorage', 'easy_villagers'],
    4: ['mekanism', 'mekanismgenerators', 'mekanismtools', 'powah', 'createaddition', 'create_new_age',
        'createdieselgenerators', 'create_enchantment_industry', 'hostilenetworks', 'mininggadgets', 'ironjetpacks'],
    5: ['bigreactors', 'justdirethings'],
    6: ['ae2', 'industrialforegoing', 'draconicevolution', 'angelring', 'fluxnetworks'],
}

# Single items locked until a tier (mostly tiered machines inside otherwise-open mods).
ITEM_LOCKS = {
    6: ['powah:furnator_blazing', 'powah:furnator_niotic', 'powah:furnator_spirited', 'powah:furnator_nitro',
        'powah:energy_cell_blazing', 'powah:energy_cell_niotic', 'powah:energy_cell_spirited', 'powah:energy_cell_nitro'],
    # Upgrade tiers of shop machine families: crafted from the tier below, unlocked with their market tier.
    1: ['ftbstuff:iron_cobblestone_generator', 'ftbstuff:iron_auto_hammer', 'exdeorum:iron_mesh'],
    2: ['ironfurnaces:gold_furnace',
        'ftbstuff:gold_cobblestone_generator', 'ftbstuff:gold_auto_hammer', 'exdeorum:diamond_mesh'],
    3: ['ironfurnaces:diamond_furnace'],
    4: ['ironfurnaces:emerald_furnace',
        'farmersdelight:roast_chicken_block', 'farmersdelight:stuffed_pumpkin_block', 'farmersdelight:honey_glazed_ham_block',
        'farmersdelight:shepherds_pie_block', 'farmersdelight:rice_roll_medley_block',
        'mysticalagriculture:tertium_essence', 'mysticalagriculture:imperium_essence',
        # Nether loot that modded overworld structures can hand out early.
        'minecraft:netherite_scrap', 'minecraft:wither_skeleton_skull',
        'ftbstuff:diamond_cobblestone_generator', 'ftbstuff:diamond_auto_hammer', 'ftbstuff:stone_basalt_generator',
        'ftbstuff:iron_basalt_generator', 'ftbstuff:gold_basalt_generator', 'exdeorum:netherite_mesh'],
    5: ['ironfurnaces:netherite_furnace', 'powah:furnator_hardened', 'powah:energy_cell_hardened',
        'mekanism:purification_chamber', 'mekanism:chemical_injection_chamber',
        'mysticalagriculture:supremium_essence',
        # Mystical Agriculture's Twilight Forest crops belong with the Twilight Forest.
        'mysticalagriculture:steeleaf_essence', 'mysticalagriculture:steeleaf_seeds', 'mysticalagriculture:ironwood_essence',
        'mysticalagriculture:ironwood_seeds', 'mysticalagriculture:knightmetal_essence', 'mysticalagriculture:knightmetal_seeds',
        'mysticalagriculture:fiery_ingot_essence', 'mysticalagriculture:fiery_ingot_seeds',
        # End loot that modded overworld structures can hand out early.
        'minecraft:elytra', 'minecraft:shulker_shell', 'minecraft:dragon_breath',
        'ftbstuff:netherite_cobblestone_generator', 'ftbstuff:netherite_auto_hammer',
        'ftbstuff:diamond_basalt_generator', 'ftbstuff:netherite_basalt_generator'],
}

# Dimensions locked until a tier (by portal and by teleport).
DIM_LOCKS = {
    3: ['minecraft:overworld'],
    4: ['minecraft:the_nether'],
    5: ['twilightforest:twilight_forest', 'minecraft:the_end'],
}

# Recipe ids removed outright (regexes, KubeJS syntax).
REMOVE_RECIPE_IDS = [
    # Gems are Frontier-only: no diamonds, emeralds or netherite from any sieve.
    r'/^exdeorum:(compressed_)?sieve\/.*\/(diamond|emerald|netherite_scrap|ancient_debris|ghast_tear)$/',
    # Lightman's coin mint would turn a diamond (800) into a diamond coin (10,000). Coins only come from the market.
    r'/^lightmanscurrency:coin_mint\//',
    # Farming for Blockheads' own market trades seeds for emeralds; the Supply Market replaces it.
    r'/^farmingforblockheads:market$/',
]

# Turn on once the Supply Catalog shop exists; until then machines stay craftable so they can be obtained.
SHOP_LIVE = True

# Supplies that are buy-only too (crafting rule: an item is either craftable or sold, never both).
BUY_ONLY_SUPPLIES = ['constructionstick:netherite_stick']


def rules_toml(tier):
    out = [f'# Locks for market tier {tier}. Generated by tools/build_locks.py; edit that file instead.',
           f'# Every player whose team lacks economy:tier_{tier} is affected.', '']
    prio = 900
    for i, d in enumerate(DIM_LOCKS.get(tier, [])):
        for action in ('portal', 'teleport'):
            out += ['[[rules]]', f'id = "economy:tier_{tier}_{action}_{i}"', 'effect = "lock"', f'action = "{action}"',
                    f'priority = {prio}', f'targets.dimensions = ["{d}"]', '']
            prio += 1
    mods = MOD_LOCKS.get(tier, [])
    if mods:
        out += ['[[rules]]', f'id = "economy:tier_{tier}_mods"', 'effect = "lock"', 'action = "access"', f'priority = {prio}',
                'targets.items = [' + ', '.join(f'"mod:{m}"' for m in mods) + ']', '']
        prio += 1
    items = ITEM_LOCKS.get(tier, [])
    if items:
        out += ['[[rules]]', f'id = "economy:tier_{tier}_items"', 'effect = "lock"', 'action = "access"', f'priority = {prio}',
                'targets.items = [' + ', '.join(f'"{i}"' for i in items) + ']', '']
    return '\n'.join(out)


def kubejs_script():
    # Hand tools stay craftable: the Ex Deorum barrel, sieve and crucible are manual, and the island needs them
    # before the first sale. The gateway is a quest reward and shop item with no recipe of its own anyway.
    machines = [m[0] for m in M.MACHINES if not m[0].startswith('exdeorum:') and m[0] != 'economy_core:frontier_gateway']
    lines = [
        '// Economy Pack recipe locks. Generated by tools/build_locks.py; edit that file instead.',
        '',
        '// Machines are bought from the shop, not crafted. Flip on together with the Supply Catalog.',
        f'const SHOP_LIVE = {"true" if SHOP_LIVE else "false"}',
        '',
        'const BUY_ONLY = [',
    ]
    lines += [f"  '{m}'," for m in machines + BUY_ONLY_SUPPLIES]
    lines += [
        ']',
        '',
        'ServerEvents.recipes(event => {',
    ]
    for rx in REMOVE_RECIPE_IDS:
        lines.append(f'  event.remove({{ id: {rx} }})')
    lines += [
        '  if (SHOP_LIVE) {',
        '    BUY_ONLY.forEach(id => event.remove({ output: id }))',
        "    // Every other botany pot variant would dodge the shop. Buy the terracotta pot; the hopper pot is crafted from it.",
        "    event.remove({ output: /^botanypots:.*botany_pot$/, not: { id: 'botanypots:botanypots/crafting/terracotta_hopper_botany_pot' } })",
        '  }',
        '})',
        '',
    ]
    return '\n'.join(lines)


def main():
    for tier in range(1, 7):
        d = os.path.join(PACK, 'config', 'progressivestages', 'stages', f'tier_{tier}')
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, 'rules.toml'), 'w').write(rules_toml(tier))
    js = os.path.join(PACK, 'kubejs', 'server_scripts', 'economy_locks.js')
    os.makedirs(os.path.dirname(js), exist_ok=True)
    open(js, 'w').write(kubejs_script())

    # Sanity check: every locked item id exists.
    from item_index import build_index, JARS
    idx = build_index(JARS)
    namespaces = {i.split(':')[0] for i in idx}
    missing = [i for t in ITEM_LOCKS.values() for i in t if i not in idx]
    missing += [f'mod:{m}' for t in MOD_LOCKS.values() for m in t if m not in namespaces]
    print('rules.toml for tiers 1-6 and economy_locks.js written')
    print('Unknown ids/mods:', missing or 'none')


if __name__ == '__main__':
    main()
