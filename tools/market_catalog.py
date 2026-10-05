"""
Single source of truth for the Economy Pack market catalog.

Run:  python3 tools/market_catalog.py
  -> writes MARKET.md and checks every item id against the installed mod jars.

Prices are in copper coins (1 iron coin = 10, 1 gold coin = 100, 1 emerald coin = 1,000).
Numbers follow the Progression & Economy Plan doc; tune them here, then regenerate.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

# --------------------------------------------------------------------------- selling (Market Crate buys these)
# Each category has a soft cap: how many units sold before the price is ~2/3 of the way down to its floor.
# The floor is the fraction of fair value a flooded price can drop to. Island basics (cobble, gravel, sand, dust)
# fall to 25% so spamming one block can't carry a tier; everything else stops at 50%.
FLOOR_DEFAULT = 0.5
FLOORS = {'island': 0.25}


def floor_of(category):
    return FLOORS.get(category, FLOOR_DEFAULT)
SELL_CATEGORIES = {
    'island':   (64, 'Island basics from cobble generators, hammers and trees'),
    'chunks':   (32, 'Ore chunks from Ex Deorum sieves'),
    'crops':    (64, 'Field and Botany Pot crops'),
    'food':     (24, "Cooked food (Farmer's Delight); processing pays"),
    'fish':     (32, "Fishing and Fishermen's Traps; Aquaculture species after the Frontier. Hand-caught fish pay well"),
    'mob':      (48, 'Mob farms (Mob Grinding Utils) and Hostile Neural Networks'),
    'metals':   (32, 'Smelted and processed metals'),
    'gems':     (16, 'Gems and rare minerals; diamond and emerald are Frontier-only'),
    'create':   (24, 'Create crafted components'),
    'essence':  (64, 'Mystical Agriculture essence (sells for ~20% of what it crafts)'),
    'exotic':   (16, 'Twilight Forest materials'),
    'bosses':   (8, 'Boss trophies and boss drops: the big payout for fighting'),
    'treasure': (16, 'Rare loot from exploring and the End'),
    'frontier': (24, 'Frontier-only goods: biome crops, overworld mob drops and structure loot'),
}

# (item id, name, category, fair price, tier, purpose / stream)
SELL = [
    # Tier 0: island start
    ('minecraft:cobblestone', 'Cobblestone', 'island', 0.5, 0, 'Filler income; mainly feeds hammers'),
    ('minecraft:dirt', 'Dirt', 'island', 0.5, 0, 'Filler income'),
    ('minecraft:gravel', 'Gravel', 'island', 1, 0, 'Hammered cobble; feeds sieves'),
    ('minecraft:sand', 'Sand', 'island', 1, 0, 'Hammered gravel; feeds sieves'),
    ('exdeorum:dust', 'Dust (Ex Deorum)', 'island', 1, 0, 'Hammered sand; feeds sieves'),
    ('ftbstuff:dust', 'Dust (FTB Stuff & Things)', 'island', 1, 0, 'Hammered sand; feeds sieves'),
    ('minecraft:flint', 'Flint', 'island', 2, 0, 'Sieve by-product'),
    ('minecraft:oak_log', 'Logs (any wood)', 'island', 2, 0, 'Tree farm income; sells by tag so spruce counts'),
    ('minecraft:charcoal', 'Charcoal', 'island', 3, 0, 'Smelted logs; processing pays'),
    ('exdeorum:copper_ore_chunk', 'Copper Ore Chunk', 'chunks', 6, 0, 'Sieving'),
    ('exdeorum:iron_ore_chunk', 'Iron Ore Chunk', 'chunks', 12, 0, 'Sieving'),
    ('exdeorum:gold_ore_chunk', 'Gold Ore Chunk', 'chunks', 20, 0, 'Sieving'),
    ('minecraft:melon_slice', 'Melon Slice', 'crops', 3, 0, 'Farming'),
    ('minecraft:wheat', 'Wheat', 'crops', 4, 0, 'Farming'),
    ('minecraft:potato', 'Potato', 'crops', 4, 0, 'Farming'),
    ('minecraft:carrot', 'Carrot', 'crops', 4, 0, 'Farming'),
    ('minecraft:sugar_cane', 'Sugar Cane', 'crops', 4, 0, 'Farming'),
    ('minecraft:beetroot', 'Beetroot', 'crops', 5, 0, 'Farming'),
    ('minecraft:pumpkin', 'Pumpkin', 'crops', 11, 0, 'Farming'),
    ('minecraft:baked_potato', 'Baked Potato', 'food', 5, 0, 'Cooking; processing pays'),
    ('minecraft:bread', 'Bread', 'food', 10, 0, 'Cooking; processing pays'),
    ('minecraft:copper_ingot', 'Copper Ingot', 'metals', 20, 0, 'Smelted chunks (any copper ingot counts)'),
    ('minecraft:iron_ingot', 'Iron Ingot', 'metals', 100, 0, 'Smelted chunks (any iron ingot counts)'),
    ('minecraft:gold_ingot', 'Gold Ingot', 'metals', 150, 0, 'Smelted chunks (any gold ingot counts)'),
    ('minecraft:redstone', 'Redstone', 'gems', 15, 0, 'Sieving'),
    ('minecraft:lapis_lazuli', 'Lapis Lazuli', 'gems', 30, 0, 'Sieving'),
    # Tier 1
    ('exdeorum:zinc_ore_chunk', 'Zinc Ore Chunk', 'chunks', 10, 0, 'Sieving (Create zinc)'),
    ('farmersdelight:tomato', 'Tomato', 'crops', 5, 1, "Farmer's Delight crops"),
    ('farmersdelight:cabbage', 'Cabbage', 'crops', 5, 1, "Farmer's Delight crops"),
    ('farmersdelight:onion', 'Onion', 'crops', 4, 1, "Farmer's Delight crops"),
    ('farmersdelight:rice', 'Rice', 'crops', 4, 1, "Farmer's Delight crops"),
    ('farmersdelight:beef_stew', 'Beef Stew', 'food', 60, 1, 'Cooking chain'),
    ('farmersdelight:pasta_with_meatballs', 'Pasta with Meatballs', 'food', 80, 1, 'Cooking chain'),
    ('farmersdelight:pasta_with_mutton_chop', 'Pasta with Mutton Chop', 'food', 80, 1, 'Cooking chain'),
    ('minecraft:cod', 'Raw Cod', 'fish', 9, 0, "Fishing / Fishermen's Trap"),
    ('minecraft:salmon', 'Raw Salmon', 'fish', 12, 0, "Fishing / Fishermen's Trap"),
    ('minecraft:tropical_fish', 'Tropical Fish', 'fish', 22, 0, "Fishing / Fishermen's Trap"),
    ('minecraft:pufferfish', 'Pufferfish', 'fish', 22, 0, "Fishing / Fishermen's Trap"),
    ('create:zinc_ingot', 'Zinc Ingot', 'metals', 40, 1, 'Smelted zinc chunks'),
    ('create:andesite_alloy', 'Andesite Alloy', 'metals', 15, 1, 'Create processing'),
    ('minecraft:quartz', 'Nether Quartz', 'gems', 20, 0, 'Sieving (crushed netherrack)'),
    ('minecraft:amethyst_shard', 'Amethyst Shard', 'gems', 25, 0, 'Sieving'),
    # Tier 2
    ('minecraft:rotten_flesh', 'Rotten Flesh', 'mob', 1, 0, 'Mob farm (dreadful dirt pad)'),
    ('minecraft:bone', 'Bone', 'mob', 3, 0, 'Mob farm'),
    ('minecraft:string', 'String', 'mob', 3, 0, 'Mob farm'),
    ('minecraft:spider_eye', 'Spider Eye', 'mob', 4, 0, 'Mob farm'),
    ('minecraft:gunpowder', 'Gunpowder', 'mob', 8, 0, 'Mob farm'),
    ('minecraft:slime_ball', 'Slimeball', 'mob', 12, 0, 'Mob farm'),
    ('minecraft:ender_pearl', 'Ender Pearl', 'mob', 40, 0, 'Mob farm'),
    ('create:brass_ingot', 'Brass Ingot', 'metals', 180, 1, 'Create mixing (copper + zinc)'),
    ('create:electron_tube', 'Electron Tube', 'create', 120, 1, 'Create crafting'),
    ('create:precision_mechanism', 'Precision Mechanism', 'create', 450, 1, 'Create sequenced assembly'),
    # Tier 3: Frontier
    # Emerald stays cheap: villagers pay 1 emerald for a few logs' worth of sticks, and villagers can be cured on the island.
    ('minecraft:emerald', 'Emerald', 'gems', 40, 3, 'Frontier mining and trading (removed from sieves)'),
    ('minecraft:diamond', 'Diamond', 'gems', 800, 3, 'Frontier mining (removed from sieves)'),
    ('aquaculture:atlantic_cod', 'Atlantic Cod', 'fish', 30, 3, 'Aquaculture, Frontier oceans'),
    ('aquaculture:atlantic_herring', 'Atlantic Herring', 'fish', 30, 3, 'Aquaculture, Frontier oceans'),
    ('aquaculture:pollock', 'Pollock', 'fish', 30, 3, 'Aquaculture, Frontier oceans'),
    ('aquaculture:bluegill', 'Bluegill', 'fish', 30, 3, 'Aquaculture, Frontier rivers'),
    ('aquaculture:perch', 'Perch', 'fish', 38, 3, 'Aquaculture, Frontier rivers'),
    ('aquaculture:brown_trout', 'Brown Trout', 'fish', 38, 3, 'Aquaculture, Frontier rivers'),
    ('aquaculture:carp', 'Carp', 'fish', 38, 3, 'Aquaculture, Frontier rivers'),
    ('aquaculture:smallmouth_bass', 'Smallmouth Bass', 'fish', 45, 3, 'Aquaculture, Frontier rivers'),
    ('aquaculture:rainbow_trout', 'Rainbow Trout', 'fish', 45, 3, 'Aquaculture, Frontier mountains'),
    ('aquaculture:catfish', 'Catfish', 'fish', 52, 3, 'Aquaculture, Frontier swamps'),
    ('aquaculture:gar', 'Gar', 'fish', 52, 3, 'Aquaculture, Frontier swamps'),
    ('aquaculture:atlantic_halibut', 'Atlantic Halibut', 'fish', 60, 3, 'Aquaculture, Frontier oceans'),
    ('aquaculture:pacific_halibut', 'Pacific Halibut', 'fish', 60, 3, 'Aquaculture, Frontier oceans'),
    ('aquaculture:muskellunge', 'Muskellunge', 'fish', 68, 3, 'Aquaculture, Frontier rivers'),
    ('aquaculture:tuna', 'Tuna', 'fish', 75, 3, 'Aquaculture, Frontier oceans'),
    ('aquaculture:piranha', 'Piranha', 'fish', 75, 3, 'Aquaculture, Frontier jungles'),
    ('aquaculture:tambaqui', 'Tambaqui', 'fish', 75, 3, 'Aquaculture, Frontier jungles'),
    ('aquaculture:arapaima', 'Arapaima', 'fish', 90, 3, 'Aquaculture, Frontier jungles'),
    # Frontier goods: things the island can't make, priced to make buying the overworld pay off.
    ('minecraft:cocoa_beans', 'Cocoa Beans', 'frontier', 8, 3, 'Jungle biomes'),
    ('minecraft:honeycomb', 'Honeycomb', 'frontier', 15, 3, 'Bee nests (Cyclic can multiply it, so keep it modest)'),
    ('minecraft:rabbit_foot', "Rabbit's Foot", 'frontier', 60, 3, 'Rabbits (deserts, taigas, snowy biomes)'),
    ('minecraft:armadillo_scute', 'Armadillo Scute', 'frontier', 80, 3, 'Armadillos (savannas and badlands)'),
    ('minecraft:turtle_scute', 'Turtle Scute', 'frontier', 200, 3, 'Turtle hatchlings growing up (beaches)'),
    ('minecraft:breeze_rod', 'Breeze Rod', 'frontier', 150, 3, 'Breezes in trial chambers'),
    ('minecraft:goat_horn', 'Goat Horn', 'frontier', 500, 3, 'Goats ramming stone (mountains)'),
    ('minecraft:iron_horse_armor', 'Iron Horse Armor', 'frontier', 300, 3, 'Structure chests'),
    ('minecraft:golden_horse_armor', 'Golden Horse Armor', 'frontier', 500, 3, 'Structure chests'),
    ('minecraft:diamond_horse_armor', 'Diamond Horse Armor', 'frontier', 2000, 3, 'Structure chests'),
    ('minecraft:wet_sponge', 'Wet Sponge', 'frontier', 1000, 3, 'Ocean monuments (elder guardians and sponge rooms)'),
    ('minecraft:sniffer_egg', 'Sniffer Egg', 'treasure', 4000, 3, 'Warm ocean ruins (suspicious sand)'),
    ('minecraft:heavy_core', 'Heavy Core', 'treasure', 15000, 3, 'Ominous vaults in trial chambers'),
    ('mysticalagriculture:inferium_essence', 'Inferium Essence', 'essence', 6, 3, 'Mystical Agriculture (locked until the Frontier)'),
    ('mysticalagriculture:prudentium_essence', 'Prudentium Essence', 'essence', 15, 3, 'Mystical Agriculture'),
    # Tier 4: Nether
    ('minecraft:blaze_rod', 'Blaze Rod', 'mob', 60, 4, 'Nether mob farm / HNN'),
    ('minecraft:ghast_tear', 'Ghast Tear', 'mob', 120, 4, 'Nether / HNN'),
    ('hostilenetworks:overworld_prediction', 'Overworld Prediction', 'mob', 25, 4, 'Hostile Neural Networks output'),
    ('hostilenetworks:nether_prediction', 'Nether Prediction', 'mob', 60, 4, 'Hostile Neural Networks output'),
    ('hostilenetworks:end_prediction', 'End Prediction', 'mob', 120, 4, 'Hostile Neural Networks output'),
    ('minecraft:netherite_scrap', 'Netherite Scrap', 'gems', 2500, 4, 'Nether mining'),
    ('mekanism:ingot_osmium', 'Osmium Ingot', 'metals', 60, 4, 'Mekanism ore processing'),
    ('mekanism:ingot_steel', 'Steel Ingot', 'metals', 160, 4, 'Mekanism processing'),
    ('mysticalagriculture:tertium_essence', 'Tertium Essence', 'essence', 40, 4, 'Mystical Agriculture'),
    ('mysticalagriculture:imperium_essence', 'Imperium Essence', 'essence', 100, 4, 'Mystical Agriculture'),
    ('farmersdelight:roast_chicken_block', 'Roast Chicken (feast)', 'food', 400, 4, 'Feast cooking'),
    ('farmersdelight:stuffed_pumpkin_block', 'Stuffed Pumpkin (feast)', 'food', 400, 4, 'Feast cooking'),
    ('farmersdelight:honey_glazed_ham_block', 'Honey Glazed Ham (feast)', 'food', 400, 4, 'Feast cooking'),
    ('farmersdelight:shepherds_pie_block', "Shepherd's Pie (feast)", 'food', 400, 4, 'Feast cooking'),
    ('farmersdelight:rice_roll_medley_block', 'Rice Roll Medley (feast)', 'food', 400, 4, 'Feast cooking'),
    # Tier 5: Twilight Forest
    ('mekanism:ingot_refined_obsidian', 'Refined Obsidian Ingot', 'metals', 900, 4, 'Mekanism advanced processing'),
    ('mysticalagriculture:supremium_essence', 'Supremium Essence', 'essence', 260, 5, 'Mystical Agriculture'),
    ('hostilenetworks:twilight_prediction', 'Twilight Prediction', 'mob', 150, 5, 'Hostile Neural Networks output'),
    ('twilightforest:steeleaf_ingot', 'Steeleaf', 'exotic', 150, 5, 'Twilight Forest'),
    ('twilightforest:ironwood_ingot', 'Ironwood Ingot', 'exotic', 300, 5, 'Twilight Forest'),
    ('twilightforest:carminite', 'Carminite', 'exotic', 400, 5, 'Twilight Forest'),
    ('twilightforest:knightmetal_ingot', 'Knightmetal Ingot', 'exotic', 800, 5, 'Twilight Forest'),
    ('twilightforest:fiery_ingot', 'Fiery Ingot', 'exotic', 2000, 5, 'Twilight Forest'),
    # Bosses: the main reward for venturing out. Trophies drop once per boss kill.
    ('minecraft:nether_star', 'Nether Star', 'bosses', 40000, 4, 'Wither kill'),
    ('minecraft:wither_skeleton_skull', 'Wither Skeleton Skull', 'treasure', 3000, 4, 'Fortress hunting (summons the Wither)'),
    ('twilightforest:naga_trophy', 'Naga Trophy', 'bosses', 15000, 5, 'Twilight boss: Naga'),
    ('twilightforest:naga_scale', 'Naga Scale', 'bosses', 1500, 5, 'Twilight boss: Naga'),
    ('twilightforest:lich_trophy', 'Lich Trophy', 'bosses', 25000, 5, 'Twilight boss: Lich'),
    ('twilightforest:twilight_scepter', 'Twilight Scepter', 'bosses', 8000, 5, 'Twilight boss: Lich'),
    ('twilightforest:lifedrain_scepter', 'Lifedrain Scepter', 'bosses', 8000, 5, 'Twilight boss: Lich'),
    ('twilightforest:zombie_scepter', 'Zombie Scepter', 'bosses', 8000, 5, 'Twilight boss: Lich'),
    ('twilightforest:fortification_scepter', 'Fortification Scepter', 'bosses', 8000, 5, 'Twilight boss: Lich'),
    ('twilightforest:minoshroom_trophy', 'Minoshroom Trophy', 'bosses', 30000, 5, 'Twilight boss: Minoshroom'),
    ('twilightforest:meef_stroganoff', 'Meef Stroganoff', 'bosses', 2500, 5, 'Twilight boss: Minoshroom'),
    ('twilightforest:hydra_trophy', 'Hydra Trophy', 'bosses', 60000, 5, 'Twilight boss: Hydra'),
    ('twilightforest:hydra_chop', 'Hydra Chop', 'bosses', 3000, 5, 'Twilight boss: Hydra'),
    ('twilightforest:fiery_blood', 'Fiery Blood', 'bosses', 6000, 5, 'Twilight boss: Hydra'),
    ('twilightforest:knight_phantom_trophy', 'Knight Phantom Trophy', 'bosses', 50000, 5, 'Twilight boss: Knight Phantoms'),
    ('twilightforest:armor_shard', 'Armor Shard', 'exotic', 400, 5, 'Twilight Knight Phantoms / Goblins'),
    ('twilightforest:ur_ghast_trophy', 'Ur-Ghast Trophy', 'bosses', 75000, 5, 'Twilight boss: Ur-Ghast'),
    ('twilightforest:fiery_tears', 'Fiery Tears', 'bosses', 6000, 5, 'Twilight boss: Ur-Ghast'),
    ('twilightforest:alpha_yeti_trophy', 'Alpha Yeti Trophy', 'bosses', 60000, 5, 'Twilight boss: Alpha Yeti'),
    ('twilightforest:alpha_yeti_fur', 'Alpha Yeti Fur', 'bosses', 2000, 5, 'Twilight boss: Alpha Yeti'),
    ('twilightforest:ice_bomb', 'Ice Bomb', 'bosses', 1500, 5, 'Twilight boss: Alpha Yeti'),
    ('twilightforest:snow_queen_trophy', 'Snow Queen Trophy', 'bosses', 90000, 5, 'Twilight boss: Snow Queen'),
    ('twilightforest:magic_beans', 'Magic Beans', 'treasure', 5000, 5, 'Twilight loot'),
    ('twilightforest:borer_essence', 'Borer Essence', 'exotic', 300, 5, 'Twilight mobs'),
    ('minecraft:heart_of_the_sea', 'Heart of the Sea', 'treasure', 5000, 3, 'Frontier treasure maps'),
    ('minecraft:totem_of_undying', 'Totem of Undying', 'treasure', 2500, 3, 'Raids and woodland mansions'),
    ('minecraft:trident', 'Trident', 'treasure', 4000, 3, 'Drowned'),
    ('minecraft:echo_shard', 'Echo Shard', 'treasure', 1500, 3, 'Ancient cities'),
    ('minecraft:shulker_shell', 'Shulker Shell', 'treasure', 1500, 5, 'End cities'),
    ('minecraft:dragon_breath', "Dragon's Breath", 'bosses', 800, 5, 'Ender Dragon fight'),
    ('minecraft:dragon_head', 'Dragon Head', 'bosses', 25000, 5, 'End ships'),
    ('minecraft:elytra', 'Elytra', 'treasure', 50000, 5, 'End ships'),
    ('minecraft:dragon_egg', 'Dragon Egg', 'bosses', 150000, 5, 'Ender Dragon kill (MEGA SALE)'),
]

# --------------------------------------------------------------------------- buying (Supply Catalog sells these)
# Machines: buy-only (recipe removed), fixed price, sell back to the crate for a share of what you paid (BUYBACK by tier).
BUYBACK = {0: 0.90, 1: 0.90, 2: 0.90, 3: 0.85, 4: 0.85, 5: 0.80, 6: 0.80}
# (item id, name, price, tier, purpose)
MACHINES = [
    # Tier 0
    ('economy_core:market_crate', 'Market Crate', 250, 0, 'Selling and storage. Buy extras to feed separate production lines; all crates share your team balance'),
    ('ftbstuff:stone_cobblestone_generator', 'Stone Cobblestone Generator', 300, 0, 'Cobble line'),
    # Tier 1
    ('ftbstuff:iron_auto_hammer', 'Iron Auto-Hammer', 1200, 1, 'Cobble to gravel to sand to dust'),
    ('create:water_wheel', 'Water Wheel', 800, 1, 'Create power'),
    ('create:millstone', 'Millstone', 800, 1, 'Create milling'),
    ('create:mechanical_press', 'Mechanical Press', 1500, 1, 'Create pressing'),
    ('create:encased_fan', 'Encased Fan', 600, 1, 'Create bulk washing/smelting'),
    ('create:mechanical_drill', 'Mechanical Drill', 900, 1, 'Create block breaking'),
    ('create:deployer', 'Deployer', 2500, 1, 'Create auto-use (early auto-clicker)'),
    ('create:crushing_wheel', 'Crushing Wheel (each)', 2000, 1, 'Ore doubling with Create'),
    ('botanypots:terracotta_botany_pot', 'Botany Pot', 600, 1, 'Compact crop growing'),
    ('fishermens_trap:fishtrap', "Fishermen's Trap", 1200, 1, 'Automatic fishing'),
    # Tier 2
    ('excompressum:auto_sieve', 'Auto-Sieve', 10000, 2, 'Automatic sieving'),
    ('economy_core:power_exchange', 'Power Exchange', 5000, 2, 'Pipe in power (FE), earn coins. One payout curve per team'),
    ('create:mechanical_harvester', 'Mechanical Harvester', 2000, 2, 'Create crop harvesting'),
    ('create:blaze_burner', 'Blaze Burner (with blaze)', 3000, 2, 'Heat for Create mixing (brass) without a trip to the Nether'),
    ('create:mechanical_arm', 'Mechanical Arm', 3000, 2, 'Create item handling'),
    ('cyclic:collector', 'Item Collector (vacuum)', 4000, 2, 'Vacuum hopper'),
    ('cyclic:user', 'User (auto-clicker)', 6000, 2, 'Automatic right/left click'),
    ('cyclic:harvester', 'Harvester', 8000, 2, 'Area crop harvesting'),
    ('cyclic:breaker', 'Block Breaker', 2000, 2, 'Automatic block breaking'),
    ('cyclic:placer', 'Block Placer', 2000, 2, 'Automatic block placing'),
    ('mob_grinding_utils:dreadful_dirt', 'Dreadful Dirt', 1500, 2, 'Hostile mob spawning pad'),
    ('mob_grinding_utils:delightful_dirt', 'Delightful Dirt', 1000, 2, 'Passive mob spawning pad'),
    ('mob_grinding_utils:spikes', 'Spikes', 800, 2, 'Mob killing'),
    ('mob_grinding_utils:fan', 'Mob Fan', 1200, 2, 'Pushing mobs'),
    ('mob_grinding_utils:entity_conveyor', 'Entity Conveyor', 600, 2, 'Moving mobs'),
    ('mob_grinding_utils:absorption_hopper', 'Absorption Hopper', 2500, 2, 'Collecting drops and XP'),
    ('mob_grinding_utils:saw', 'Mob Masher (saw)', 4000, 2, 'Mob killing with looting'),
    ('mob_grinding_utils:xp_tap', 'XP Tap', 1500, 2, 'XP storage'),
    ('mob_grinding_utils:tank', 'Tank', 1500, 2, 'XP/fluid storage'),
    ('mob_grinding_utils:xpsolidifier', 'XP Solidifier', 3000, 2, 'XP into items'),
    # Tier 3
    ('mysticalagriculture:infusion_altar', 'Infusion Altar', 8000, 3, 'Mystical Agriculture seed crafting'),
    ('economy_core:frontier_gateway', 'Frontier Gateway', 2000, 3, 'Travel between your island and the Frontier (one free per player from the tier 3 gate)'),
    # Tier 4
    ('ftbstuff:stone_basalt_generator', 'Stone Basalt Generator', 10000, 4, 'Basalt for Nether sieving'),
    ('create:mechanical_crafter', 'Mechanical Crafter (each)', 2000, 4, 'Create auto-crafting (feasts)'),
    ('mekanism:crusher', 'Crusher', 25000, 4, 'Mekanism processing'),
    ('mekanism:enrichment_chamber', 'Enrichment Chamber', 30000, 4, 'Mekanism 2x ore'),
    ('mekanismgenerators:heat_generator', 'Heat Generator', 15000, 4, 'Mekanism power'),
    ('hostilenetworks:deep_learner', 'Deep Learner', 10000, 4, 'Training data models'),
    ('hostilenetworks:data_model', 'Data Model (per mob)', 5000, 4, 'One mob type'),
    ('hostilenetworks:sim_chamber', 'Simulation Chamber', 30000, 4, 'Simulated mob farming'),
    ('hostilenetworks:loot_fabricator', 'Loot Fabricator', 25000, 4, 'Predictions into drops'),
    # Tier 5
    ('mekanismgenerators:wind_generator', 'Wind Generator', 20000, 5, 'Mekanism power'),
    ('mekanismgenerators:solar_generator', 'Solar Generator', 15000, 5, 'Mekanism power'),
    ('mekanismgenerators:gas_burning_generator', 'Gas-Burning Generator', 80000, 5, 'Mekanism power'),
    # Round-out mods (power, furnaces, villagers, routing, endgame)
    ('ironfurnaces:iron_furnace', 'Iron Furnace', 800, 1, 'Faster smelting'),
    ('modularrouters:modular_router', 'Modular Router', 3000, 2, 'Programmable item routing'),
    ('easy_villagers:trader', 'Villager Trader Block', 4000, 3, 'Trade with a villager in a block'),
    ('easy_villagers:farmer', 'Villager Farmer Block', 5000, 3, 'Villager crop farm'),
    ('easy_villagers:breeder', 'Villager Breeder', 5000, 3, 'Breed villagers'),
    ('easy_villagers:auto_trader', 'Auto Trader', 12000, 3, 'Automated villager trading'),
    ('easy_villagers:iron_farm', 'Iron Farm Block', 15000, 3, 'Compact iron golem farm'),
    ('powah:furnator_starter', 'Furnator (Starter)', 6000, 4, 'Powah power from fuel'),
    ('powah:energy_cell_starter', 'Energy Cell (Starter)', 3000, 4, 'Power storage'),
    ('createaddition:alternator', 'Alternator', 5000, 4, 'Create rotation to power'),
    ('createaddition:electric_motor', 'Electric Motor', 5000, 4, 'Power to Create rotation'),
    ('createaddition:rolling_mill', 'Rolling Mill', 4000, 4, 'Rods and wires'),
    ('create_new_age:basic_motor', 'Basic Motor (New Age)', 5000, 4, 'Power to rotation'),
    ('create_new_age:generator_coil', 'Generator Coil', 8000, 4, 'Rotation to power'),
    ('createdieselgenerators:diesel_engine', 'Diesel Engine', 10000, 4, 'Fuel to rotation'),
    ('create_enchantment_industry:blaze_enchanter', 'Blaze Enchanter', 12000, 4, 'Automatic enchanting'),
    ('create_enchantment_industry:printer', 'Printer', 10000, 4, 'Copy books and enchantments'),
    ('bigreactors:basic_reactorcontroller', 'Reactor Controller', 60000, 5, 'Extreme Reactors core'),
    ('bigreactors:basic_turbinecontroller', 'Turbine Controller', 50000, 5, 'Extreme Reactors turbine'),
    ('justdirethings:clickert1', 'Clicker (Tier 1)', 15000, 5, 'Auto-clicker'),
    ('justdirethings:blockbreakert1', 'Block Breaker (Tier 1)', 10000, 5, 'Automatic breaking'),
    ('justdirethings:blockplacert1', 'Block Placer (Tier 1)', 10000, 5, 'Automatic placing'),
    ('justdirethings:generatort1', 'Generator (Tier 1)', 20000, 5, 'Power'),
    ('fluxnetworks:flux_controller', 'Flux Controller', 100000, 6, 'Wireless power network'),
    ('fluxnetworks:flux_plug', 'Flux Plug', 20000, 6, 'Wireless power in'),
    ('fluxnetworks:flux_point', 'Flux Point', 20000, 6, 'Wireless power out'),
    ('bigreactors:reinforced_reactorcontroller', 'Reinforced Reactor Controller', 200000, 6, 'Late reactors'),
    ('draconicevolution:generator', 'Draconic Generator', 150000, 6, 'Draconic power'),
    ('draconicevolution:grinder', 'Mob Grinder (Draconic)', 120000, 6, 'Mob killing'),
    ('draconicevolution:energy_core', 'Energy Core', 300000, 6, 'Huge power storage'),
    # Tier 6
    ('ae2:controller', 'ME Controller', 500000, 6, 'AE2 storage network (quality of life)'),
    ('ae2:drive', 'ME Drive', 100000, 6, 'AE2 storage (quality of life)'),
    ('industrialforegoing:plant_gatherer', 'Plant Gatherer', 150000, 6, 'Industrial Foregoing (quality of life)'),
    ('industrialforegoing:mob_crusher', 'Mob Crusher', 250000, 6, 'Industrial Foregoing (quality of life)'),
    ('industrialforegoing:fermentation_station', 'Fermentation Station', 100000, 6, 'Industrial Foregoing (quality of life)'),
]

# Supplies: consumables and materials, ~4x the fair sell price. Not buy-only; normal market sell price applies.
SUPPLIES = [
    ('minecraft:water_bucket', 'Water Bucket', 20, 0, 'Infinite water source'),
    ('minecraft:oak_sapling', 'Oak Sapling', 10, 0, 'Starting a tree farm'),
    ('minecraft:wheat_seeds', 'Wheat Seeds', 5, 0, 'Starting crops'),
    ('minecraft:potato', 'Potato (seed)', 12, 0, 'Starting crops'),
    ('minecraft:carrot', 'Carrot (seed)', 12, 0, 'Starting crops'),
    ('minecraft:melon_seeds', 'Melon Seeds', 10, 0, 'Starting crops'),
    ('minecraft:pumpkin_seeds', 'Pumpkin Seeds', 10, 0, 'Starting crops'),
    ('minecraft:sugar_cane', 'Sugar Cane (seed)', 12, 0, 'Starting crops'),
    ('exdeorum:string_mesh', 'String Mesh', 40, 0, 'Sieve mesh'),
    ('constructionstick:netherite_stick', 'Netherite Construction Stick', 100, 0, 'Building helper; buy-only'),
    ('minecraft:bone_meal', 'Bone Meal', 8, 0, 'Growth boost'),
    ('exdeorum:flint_mesh', 'Flint Mesh', 150, 1, 'Better sieve mesh'),
    ('exdeorum:iron_mesh', 'Iron Mesh', 600, 1, 'Better sieve mesh'),
    ('create:shaft', 'Shaft', 8, 1, 'Create starter kit (also craftable)'),
    ('create:cogwheel', 'Cogwheel', 12, 1, 'Create starter kit (also craftable)'),
    ('create:andesite_casing', 'Andesite Casing', 40, 1, 'Create starter kit (also craftable)'),
    ('farmersdelight:tomato_seeds', 'Tomato Seeds', 15, 1, "Farmer's Delight crops"),
    ('farmersdelight:cabbage_seeds', 'Cabbage Seeds', 15, 1, "Farmer's Delight crops"),
    ('aquaculture:worm', 'Worm (bait)', 10, 1, 'Fishing bait'),
    ('exdeorum:diamond_mesh', 'Diamond Mesh', 4000, 2, 'Best early sieve mesh'),
    ('minecraft:redstone', 'Redstone', 60, 2, 'Machine control'),
    ('naturescompass:naturescompass', "Nature's Compass", 3000, 3, 'Finding biomes in the Frontier'),
    ('explorerscompass:explorerscompass', "Explorer's Compass", 3000, 3, 'Finding structures in the Frontier'),
    ('waystones:waystone', 'Waystone', 5000, 3, 'Fast travel home'),
    ('waystones:warp_stone', 'Warp Stone', 8000, 3, 'Fast travel from anywhere'),
    ('aquaculture:iron_fishing_rod', 'Iron Fishing Rod', 1000, 3, 'Aquaculture fishing'),
    ('aquaculture:gold_fishing_rod', 'Gold Fishing Rod', 2500, 3, 'Aquaculture fishing'),
    ('mysticalagriculture:inferium_seeds', 'Inferium Seeds', 2000, 3, 'Mystical Agriculture starter'),
    ('mysticalagriculture:prosperity_seed_base', 'Prosperity Seed Base', 1500, 4, 'Mystical Agriculture seed crafting'),
    ('mysticalagriculture:soulium_seed_base', 'Soulium Seed Base', 3000, 4, 'Mob seed crafting'),
    ('mekanism:basic_control_circuit', 'Basic Control Circuit', 800, 4, 'Mekanism parts (also craftable)'),
    ('mekanism:steel_casing', 'Steel Casing', 2500, 4, 'Mekanism parts (also craftable)'),
    ('aquaculture:diamond_fishing_rod', 'Diamond Fishing Rod', 8000, 4, 'Aquaculture fishing'),
    ('twilightforest:magic_map_focus', 'Magic Map Focus', 5000, 5, 'Twilight Forest navigation'),
    ('twilightforest:charm_of_life_1', 'Charm of Life', 15000, 5, 'Twilight Forest safety'),
    ('aquaculture:neptunium_fishing_rod', 'Neptunium Fishing Rod', 40000, 5, 'Best fishing'),
    ('ae2:certus_quartz_crystal', 'Certus Quartz Crystal', 400, 6, 'AE2 starter material'),
    ('ae2:logic_processor', 'Logic Processor', 2000, 6, 'AE2 parts'),
]

TIERS = {
    0: ('Castaway', 'Island', 'start'),
    1: ('Tinkerer', 'Island', '4,000 lifetime / 2,000 fee'),
    2: ('Engineer', 'Island', '24,000 / 10,000'),
    3: ('Pioneer', 'Frontier', '96,000 / 40,000'),
    4: ('Cultivator', 'Frontier + Nether', '350,000 / 80,000'),
    5: ('Industrialist', '+ Twilight Forest', '1,050,000 / 150,000'),
    6: ('Tycoon', 'Everything', '2,800,000 / 300,000'),
}


def fmt(n):
    return f'{n:,}'


def coins(n):
    """Readable coin breakdown, e.g. 4,605 -> 4e 6g 5c."""
    parts = []
    for value, letter in ((100000, 'n'), (10000, 'd'), (1000, 'e'), (100, 'g'), (10, 'i'), (1, 'c')):
        if n >= value:
            parts.append(f'{n // value}{letter}')
            n %= value
    return ' '.join(parts) or '0c'


def build_md():
    out = []
    w = out.append
    w('# Economy Pack: Market Catalog')
    w('')
    w('Every item the market buys from players and every item the shop sells, by tier. '
      'Generated by `tools/market_catalog.py`; edit that file, not this one.')
    w('')
    w('**Money:** prices are in copper coins. 1 iron coin = 10, 1 gold coin = 100, 1 emerald coin = 1,000, '
      '1 diamond coin = 10,000, 1 netherite coin = 100,000. The coin column shows the same amount as coins '
      '(n = netherite, d = diamond, e = emerald, g = gold, i = iron, c = copper).')
    w('')
    w('**Purposes:**')
    w('- **Income:** goods you sell at the Market Crate. The price drops a little with each unit sold (never below 50% '
      'of fair) and recovers when you sell a variety of other goods.')
    w('- **Automation:** machines you can only buy from the shop (their recipes are removed). Fixed price, and they '
      'sell back to the crate for 90% of what you paid at tiers 0-2, 85% at tiers 3-4 and 80% at tiers 5-6, '
      'with no price drop for selling many.')
    w('- **Machine families:** the shop sells the first machine of each family (stone cobblestone generator, iron auto-hammer, '
      'stone basalt generator, iron furnace, starter Furnator and Energy Cell, enrichment chamber, botany pot). Higher tiers '
      'are crafted by upgrading the one below, and each upgrade unlocks with its market tier.')
    w('- **Supply:** consumables and materials sold by the shop at about 4x their fair sell price, as a convenience.')
    w('')
    w('## Tiers')
    w('')
    w('| Tier | Name | Where | Gate to enter (lifetime earnings / fee in coins) |')
    w('|---|---|---|---|')
    for t, (name, where, gate) in TIERS.items():
        w(f'| {t} | {name} | {where} | {gate} |')
    w('')
    w('## Totals')
    w('')
    w(f'- Income goods: {len(SELL)}')
    w(f'- Automation machines: {len(MACHINES)}')
    w(f'- Supplies: {len(SUPPLIES)}')
    w('')

    w('## Selling: what the Market Crate buys (Income)')
    w('')
    w('Soft cap = units sold before the price is about two thirds of the way down to the floor. '
      'Smaller soft cap = price drops faster. Floor = the lowest a flooded price can go.')
    w('')
    w('| Category | Soft cap | Floor | What it covers |')
    w('|---|---|---|---|')
    for k, (cap, desc) in SELL_CATEGORIES.items():
        w(f'| {k} | {cap} | {floor_of(k) * 100:.0f}% | {desc} |')
    w('')
    for t in TIERS:
        rows = [r for r in SELL if r[4] == t]
        if not rows:
            continue
        w(f'### Tier {t}: {TIERS[t][0]}')
        w('')
        w('| Item | ID | Category | Fair price | Coins | Floor | Purpose / stream |')
        w('|---|---|---|---|---|---|---|')
        for iid, name, cat, price, _, purpose in rows:
            flo = price * floor_of(cat)
            w(f'| {name} | `{iid}` | {cat} | {fmt(price)} | {coins(price)} | {fmt(int(flo) if flo == int(flo) else flo)} '
              f'| {purpose} |')
        w('')

    w('## Buying: Automation (buy-only, fixed price, 80-90% sell-back)')
    w('')
    for t in TIERS:
        rows = [r for r in MACHINES if r[3] == t]
        if not rows:
            continue
        w(f'### Tier {t}: {TIERS[t][0]}')
        w('')
        w(f'Sells back for {int(BUYBACK[t] * 100)}% of the price.')
        w('')
        w('| Machine | ID | Price | Coins | Sells back for | Purpose |')
        w('|---|---|---|---|---|---|')
        for iid, name, price, _, purpose in rows:
            w(f'| {name} | `{iid}` | {fmt(price)} | {coins(price)} | {fmt(round(price * BUYBACK[t]))} | {purpose} |')
        w('')

    w('## Buying: Supplies (about 4x fair, also obtainable other ways)')
    w('')
    for t in TIERS:
        rows = [r for r in SUPPLIES if r[3] == t]
        if not rows:
            continue
        w(f'### Tier {t}: {TIERS[t][0]}')
        w('')
        w('| Item | ID | Price | Coins | Purpose |')
        w('|---|---|---|---|---|')
        for iid, name, price, _, purpose in rows:
            w(f'| {name} | `{iid}` | {fmt(price)} | {coins(price)} | {purpose} |')
        w('')

    w('## Not for sale on purpose')
    w('')
    w('- **Hand tools (crook, hammers, barrels, sieves, crucibles):** craft-only, never sold by the shop, so nothing craftable can be bought or sold back for profit.')
    w('- **Lava buckets:** lava only comes from melting cobblestone in an Ex Deorum crucible.')
    w('- **Diamonds, emeralds and netherite before the Frontier:** removed from sieve drops, so they only come from the Frontier.')
    w('- **Mystical Agriculture before tier 3:** seeds, essence and the infusion altar are locked until the Frontier is bought.')
    w('- **AE2 and Industrial Foregoing before tier 6:** late-game quality of life only.')
    w('- **Enchanted books:** they all share one item id, so pricing them by enchantment and level needs a small Economy Core feature (planned).')
    w('- **Coins:** putting coins in the crate deposits them to your balance; they are not a sellable good.')
    w('')
    return '\n'.join(out)


def check_ids():
    from item_index import build_index, JARS
    idx = build_index(JARS)
    missing = [r[0] for r in SELL + MACHINES + SUPPLIES if r[0] not in idx]
    dupes = {r[0] for r in SELL if [s[0] for s in SELL].count(r[0]) > 1}
    return missing, dupes


# One-liners shown in the shop tooltip (the Broker's commentary).
SHOP_NOTES = {
    'constructionstick:netherite_stick': 'Wow, netherite, huh? Nobody should be punished for wanting to build stuff.',
}


def build_shop_json():
    """config/economy_core/shop.json for the Supply Market: machines (stamped, sell back) and supplies."""
    import json
    entries = []
    for iid, name, price, tier, purpose in MACHINES:
        entries.append({'item': iid, 'count': 1, 'price': price, 'tier': tier, 'category': 'machines',
                        'buyback': round(price * BUYBACK[tier])})
    for iid, name, price, tier, purpose in SUPPLIES:
        e = {'item': iid, 'count': 1, 'price': price, 'tier': tier, 'category': 'supplies', 'buyback': 0}
        if iid in SHOP_NOTES:
            e['note'] = SHOP_NOTES[iid]
        entries.append(e)
    return json.dumps({'_comment': 'Generated by tools/market_catalog.py; edit that file instead.', 'entries': entries}, indent=2)


# Ingots sell by tag so modded copies (e.g. Create, Mekanism) count too.
SELL_AS_TAG = {
    'minecraft:oak_log': '#minecraft:logs_that_burn',   # the island is spruce; every wood log sells
    'minecraft:copper_ingot': '#c:ingots/copper',
    'minecraft:iron_ingot': '#c:ingots/iron',
    'minecraft:gold_ingot': '#c:ingots/gold',
}

# Market tiers: index = market tier. variety = distinct goods needed for a depressed item to recover;
# a sale counts toward variety at min_units units or min_value coins.
MARKET_TIERS = [(4, 8, 50), (5, 16, 150), (6, 32, 400), (7, 48, 1000), (8, 64, 2500), (9, 96, 6000), (10, 128, 15000)]

COINS = {
    'lightmanscurrency:coin_netherite': 100000,
    'lightmanscurrency:coin_diamond': 10000,
    'lightmanscurrency:coin_emerald': 1000,
    'lightmanscurrency:coin_gold': 100,
    'lightmanscurrency:coin_iron': 10,
    'lightmanscurrency:coin_copper': 1,
}


def build_market_json():
    """config/economy_core/market.json for the Market Crate: every sell price, category and coin value."""
    import json
    items = {}
    for iid, name, cat, price, tier, purpose in SELL:
        items[SELL_AS_TAG.get(iid, iid)] = {'base': price, 'category': cat}
    return json.dumps({
        '_comment': 'Generated by tools/market_catalog.py; edit that file instead.',
        'floor_default': 0.5,
        'autosell_interval_ticks': 100,
        'celebrations_enabled': True,
        'celebrations': [50, 200, 600, 2000, 7500, 30000, 150000],
        'earnings_milestones': [1, 4000, 24000, 96000, 350000, 1050000, 2800000, 8000000],
        'sale_milestones': [1000, 150000],
        # Power Exchange: coins/min = power_base * (team FE per tick / 100) ** power_exponent (keep pacing_sim in sync)
        'power_base': 70.0,
        'power_exponent': 0.6,
        'tiers': [{'variety': v, 'min_units': u, 'min_value': m} for v, u, m in MARKET_TIERS],
        'categories': {c: {'soft_cap': cap, 'max_drop': round(1 - floor_of(c), 4)}
                       for c, (cap, _) in SELL_CATEGORIES.items()},
        'items': items,
        'coins': COINS,
    }, indent=2)


if __name__ == '__main__':
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    shop = os.path.join(root, 'config', 'economy_core', 'shop.json')
    os.makedirs(os.path.dirname(shop), exist_ok=True)
    open(shop, 'w').write(build_shop_json())
    open(os.path.join(os.path.dirname(shop), 'market.json'), 'w').write(build_market_json())
    with open(os.path.join(root, 'MARKET.md'), 'w') as f:
        f.write(build_md())
    missing, dupes = check_ids()
    print(f'MARKET.md written: {len(SELL)} income, {len(MACHINES)} machines, {len(SUPPLIES)} supplies')
    print('Unknown item ids:', missing or 'none')
    print('Duplicate sell entries:', sorted(dupes) or 'none')
