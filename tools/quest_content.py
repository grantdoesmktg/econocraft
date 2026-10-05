"""
All quest book content: chapters, quests, tasks, rewards and copy. Edit here, then run tools/build_quests.py.

Quest fields:
  key       stable id (never change it once players have progress; text can change freely)
  title, subtitle, text (list of lines; '&6' style colour codes allowed)
  icon      item id
  tasks     list of: ('item', id, count[, consume]), ('check',), ('dim', dimension), ('kill', entity, n),
            ('adv', advancement), ('stage', stage)
  coins     coin reward (paid as Lightman's coin items)
  items     extra item rewards: [(id, count)]
  deps      dependencies (quest keys, 'chapter/quest' for other chapters). Default: previous main-line quest.
  side      parent quest key: a side quest hanging off the main line
  gate      (tier, lifetime_earnings, fee): tier unlock quest (checks earnings, takes the fee in coins,
            grants stage economy:tier_N and sets the market tier)
  optional  true = not needed for chapter completion
"""

DATA_SNBT = """{
\tdefault_autoclaim_rewards: "disabled"
\tdefault_consume_items: false
\tdefault_quest_disable_jei: false
\tdefault_quest_shape: "circle"
\tdefault_reward_team: true
\tdisable_gui: false
\tdrop_loot_crates: false
\temergency_items: [
\t\t{ count: 1, id: "minecraft:water_bucket" }
\t\t{ count: 1, id: "minecraft:spruce_sapling" }
\t\t{ count: 1, id: "minecraft:cooked_beef" }
\t]
\temergency_items_cooldown: 600
\tgrid_scale: 0.5d
\tlock_message: "Finish the quests before this one first."
\tpause_game: false
\tprogression_mode: "linear"
\tversion: 13
}
"""

GROUPS = [
    {'key': 'progression', 'title': '&6&l★ Progression'},
    {'key': 'mods_island', 'title': '&b&l⚙ Mods: The Island'},
    {'key': 'mods_frontier', 'title': '&a&l⚙ Mods: The Frontier'},
    {'key': 'mods_endgame', 'title': '&d&l⚙ Mods: Endgame'},
    {'key': 'reference', 'title': '&e&l✎ Reference'},
]

P = 'progression'
M = 'mods'
R = 'reference'

CHAPTERS = []


def chapter(key, group, title, icon, subtitle, quests):
    CHAPTERS.append({'key': key, 'group': group, 'title': title, 'icon': icon, 'subtitle': subtitle, 'quests': quests})


# =====================================================================================================
# PROGRESSION
# =====================================================================================================

chapter('getting_started', P, 'Welcome Ashore', 'economy_core:market_crate',
        'Tier 0, Castaway. One tree, one island, zero coins. Let us fix that.', [
    {'key': 'welcome', 'title': 'Welcome to the Economy Pack', 'icon': 'tiab:time_in_a_bottle',
     'subtitle': 'Tick the checkmark to claim your starter kit',
     'items': [('tiab:time_in_a_bottle', 1), ('economy_core:market_crate', 1), ('economy_core:supply_market', 1)], 'personal_rewards': True,
     'text': [
         'Tiny island, one tree, no chest. Rude, I know.',
         '',
         'Here is the deal: almost everything in this pack can be bought, and I am going to show you how to afford it. You sell what you make, and the coins buy machines, tiers and eventually a whole overworld.',
         '',
         'Starter kit: a &6Time in a Bottle&r, a &6Market Crate&r (you sell here) and a &6Supply Market&r (you buy here: machines, seeds, meshes). Do not sell the crate. I will know.',
     ]},
    {'key': 'logs', 'title': 'Timber!', 'icon': 'minecraft:spruce_log', 'tasks': [('item', 'minecraft:spruce_log', 8)], 'coins': 20,
     'text': ['Punch the tree. Yes, really. We have all been there.',
              '',
              'Leave a few leaves for the next quest. Trust me on this one.']},
    {'key': 'crook', 'title': 'Hooked', 'icon': 'exdeorum:crook', 'tasks': [('item', 'exdeorum:crook', 1)], 'coins': 20,
     'text': ['Break leaves with a &6crook&r and you get double the saplings, plus a 1 in 100 shot at a &6silkworm&r.',
              '',
              'Keep every sapling. Trees are your whole economy right now.']},
    {'key': 'saplings', 'title': 'Plant Everything', 'icon': 'minecraft:spruce_sapling', 'tasks': [('item', 'minecraft:spruce_sapling', 4)], 'coins': 30,
     'text': ['Spruce stays small unless you plant four in a square. Unless you want a skyscraper, plant them apart.',
              '',
              '&6Squat Grow&r is installed: crouch next to saplings and crops and they grow faster. Go on, nobody is watching.']},
    {'key': 'silkworm', 'title': 'Worm Farm', 'icon': 'exdeorum:silkworm', 'tasks': [('item', 'exdeorum:silkworm', 1)], 'coins': 50,
     'text': ['Use the silkworm on a tree\'s leaves. It slowly infests the whole tree, and fully infested leaves drop &6string&r.',
              '',
              'String means sieve meshes. Sieve meshes mean ore. Ore means money. You see the plan.']},
    {'key': 'barrel', 'title': 'Dirt From Nothing', 'icon': 'exdeorum:spruce_barrel', 'tasks': [('item', 'exdeorum:spruce_barrel', 1)], 'coins': 40,
     'text': ['Saplings, leaves and old food go into a &6barrel&r and come out as dirt.',
              '',
              'More dirt, more island. More island, more trees.']},
    {'key': 'first_sale', 'title': 'Your First Paycheck', 'icon': 'lightmanscurrency:coin_copper',
     'subtitle': 'Sell anything at the Market Crate',
     'tasks': [('adv', 'economy_core:earned/1')], 'coins': 50,
     'text': ['Next up is a cobble generator, and it costs &6300&r. Nobody is handing you 300. Here is how you earn it.',
              '',
              '&61. Sell what you have.&r String from your silkworm tree and spare logs both sell. Drop them in the &6Market Crate&r, put a stack in the side slot and hit &6Sell this stack&r. Hover anything in your inventory to see what it sells for.',
              '',
              '&62. Start a proper farm.&r Break grass for wheat seeds, or buy potato and carrot seeds at the &6Supply Market&r. Hoe dirt next to water. Out of water? The quest book has an &6Emergency Items&r button: a water bucket, a sapling and a steak, once every 10 minutes.',
              '',
              '&63. Fart on your crops.&r Crouch next to them over and over and they grow faster. It is called Squat Grow, it is installed, and nobody can see you.',
              '',
              '&64. Sell a mix.&r Every different good you sell pulls the others back up to full price. Ten kinds of crop beat a mountain of wheat.']},
    {'key': 'cobblegen', 'title': 'Cobble, Please', 'icon': 'ftbstuff:stone_cobblestone_generator',
     'tasks': [('item', 'ftbstuff:stone_cobblestone_generator', 1)], 'coins': 50,
     'text': ['The shop sells a &6stone cobblestone generator&r for 300. Infinite rock, no lava needed.',
              '',
              'Fair warning: cobble is the cheapest thing in the pack, and flooding the market with it drops it to a quarter of its price. It is filler money and hammer food, not a career.',
              '',
              'Speaking of lava: you will not find a lava bucket for sale. A &6crucible&r melts cobblestone into lava. That is the only lava you get. Treat it with respect.']},
    {'key': 'hammer', 'title': 'Smash It', 'icon': 'exdeorum:stone_hammer', 'tasks': [('item', 'minecraft:gravel', 16)], 'coins': 40,
     'text': ['Hammer cobble into gravel, gravel into sand, sand into dust.',
              '',
              'Each one sieves into different goodies. Gravel is the ore one.']},
    {'key': 'sieve', 'title': 'Sift Through Your Problems', 'icon': 'exdeorum:spruce_sieve',
     'tasks': [('item', 'exdeorum:iron_ore_chunk', 4)], 'coins': 60,
     'text': ['Put a &6string mesh&r in a &6sieve&r and feed it gravel. Out come iron, copper and gold chunks.',
              '',
              'Press &6U&r on the sieve in JEI to see every possible drop.']},
    {'key': 'diminishing', 'title': 'Diminishing Returns 101', 'icon': 'minecraft:cobblestone', 'tasks': [('adv', 'economy_core:diminished')], 'coins': 30,
     'text': ['Completes the first time you sell something below 90% of its fair price.', '', 'Sell 64 of the same thing and the price slides toward half. Island basics (cobble, gravel, sand, dust, logs) slide all the way to a quarter.',
              '',
              'Sell a &6variety&r of other goods and the price climbs back. The crate\'s tooltips tell you how many different goods you still need to sell.',
              '',
              'Rotate, do not dump. Your wallet will thank you.']},
    {'key': 'processing', 'title': 'Processing Pays', 'icon': 'minecraft:iron_ingot', 'tasks': [('item', 'minecraft:iron_ingot', 1)], 'coins': 80,
     'text': ['Four iron chunks are worth about 48. Smelt them into an ingot and it is worth 100.',
              '',
              'Processing roughly doubles value. Remember that. It never stops being true in this pack.']},
    {'key': 'tiab', 'title': 'Time Is Money', 'icon': 'tiab:time_in_a_bottle', 'side': 'processing', 'optional': True, 'tasks': [('item', 'tiab:time_in_a_bottle', 1)], 'coins': 30,
     'text': ['Your &6Time in a Bottle&r banks time while you play. Right-click a furnace, sapling or machine to speed it up.',
              '',
              'It is there so you never grind for something you have already earned. Spend it on slow things.']},
    {'key': 'gate', 'title': 'Gate: Tinkerer', 'icon': 'create:cogwheel', 'gate': (1, 4000, 2000),
     'subtitle': 'Earn 4,000 lifetime, hand in 2,000 in coins',
     'text': ['You need &64,000 lifetime earnings&r, and you hand in &62,000 in coins&r as the fee.',
              '',
              'Withdraw coins from the Market Crate and submit them here (it wants two &6emerald coins&r). Yes, it is a fee. Welcome to capitalism.',
              '',
              'Unlocks tier 1: iron cobble line, Create, Botany Pots and fish traps.']},
])

chapter('tinkerer', P, 'Gears and Greens', 'create:cogwheel',
        'Tier 1, Tinkerer. Your first real production lines.', [
    {'key': 'iron_gen', 'title': 'Upgrade the Rock Pile', 'icon': 'ftbstuff:iron_cobblestone_generator', 'deps': ['getting_started/gate'],
     'tasks': [('item', 'ftbstuff:iron_cobblestone_generator', 1)], 'coins': 150,
     'text': ['Upgrade your stone generator: the iron one is &6crafted from it&r (check JEI). Faster cobble. Feed it into everything.']},
    {'key': 'auto_hammer', 'title': 'Hands Off the Hammer', 'icon': 'ftbstuff:iron_auto_hammer',
     'tasks': [('item', 'ftbstuff:iron_auto_hammer', 1)], 'coins': 150,
     'text': ['Generator into &6auto-hammer&r into sieve. Your first production line.',
              '',
              'Admire it. Then make it bigger. See Mods: FTB Stuff & Things for the upgrade ladder.']},
    {'key': 'meshes', 'title': 'Better Meshes', 'icon': 'exdeorum:iron_mesh', 'tasks': [('item', 'exdeorum:iron_mesh', 1)], 'coins': 100,
     'text': ['Flint mesh, then iron mesh. Better mesh, better drops.',
              '',
              'The iron mesh is where sieving starts paying properly.']},
    {'key': 'water_wheel', 'title': 'Spin Me Right Round', 'icon': 'create:water_wheel', 'tasks': [('item', 'create:water_wheel', 1)], 'coins': 150,
     'text': ['&6Create&r runs on rotation, and a water wheel is free rotation forever.',
              '',
              'If gears scare you, peek at Mods: Create. If they do not, carry on, genius.']},
    {'key': 'crushing', 'title': 'Crush It', 'icon': 'create:crushing_wheel', 'tasks': [('item', 'create:crushing_wheel', 2)], 'coins': 250,
     'text': ['Crushing ore chunks gives bonus output: more ingots per chunk, more coins per hour.',
              '',
              'Math! The fun kind.']},
    {'key': 'pots', 'title': 'Pot Plants', 'icon': 'botanypots:terracotta_hopper_botany_pot',
     'tasks': [('item', 'botanypots:terracotta_hopper_botany_pot', 1)], 'coins': 150,
     'text': ['Crops in a box that empties itself into a hopper.',
              '',
              'Put a row of these over a chest and you are a farmer now. Congratulations, farmer.']},
    {'key': 'fish', 'title': "Gone Fishin'", 'icon': 'fishermens_trap:fishtrap', 'tasks': [('item', 'fishermens_trap:fishtrap', 1)], 'coins': 120,
     'text': ['Bait it, drop it in water, pipe it into the crate.',
              '',
              'Fish sell steadily and you did not even hold a rod.']},
    {'key': 'stew', 'title': 'Fancy Food', 'icon': 'farmersdelight:beef_stew', 'tasks': [('item', 'farmersdelight:beef_stew', 1)], 'coins': 150,
     'text': ['A raw potato sells for 3. A bowl of stew sells for 60.',
              '',
              'You see where I am going with this. Mods: Farmer\'s Delight has the recipes worth making.']},
    {'key': 'zinc', 'title': 'Zinc and Brass Dreams', 'icon': 'create:zinc_ingot', 'tasks': [('item', 'create:zinc_ingot', 4)], 'coins': 100,
     'text': ['Zinc chunks come out of sieves. Smelt and save some.',
              '',
              'Brass is next tier\'s best friend.']},
    {'key': 'autosell', 'title': 'Hands-Free Selling', 'icon': 'minecraft:hopper', 'tasks': [('adv', 'economy_core:autosell')], 'coins': 150,
     'text': ['Hopper into crate, flip &6Auto-sell&r on, walk away. Passive income!',
              '',
              'One warning: auto-selling a single item all day caps out fast. Feed the crate a mix.']},
    {'key': 'streams', 'title': 'Five Streams', 'icon': 'minecraft:chest', 'tasks': [('adv', 'economy_core:distinct/5')], 'coins': 200,
     'text': ['Ore, crops, fish, food, wood. The market rewards variety.',
              '',
              'Five steady streams beat one giant one, every time. Completes once you have sold five different goods.']},
    {'key': 'gate', 'title': 'Gate: Engineer', 'icon': 'cyclic:user', 'gate': (2, 24000, 10000),
     'subtitle': 'Earn 24,000 lifetime, hand in 10,000 in coins',
     'text': ['You built a factory out of gears and a fish trap. That is basically engineering.',
              '',
              'Hand in &61 diamond coin&r and have &624,000 lifetime earnings&r.',
              '',
              'Unlocks tier 2: auto-sieves, Cyclic, mob farms and better storage.']},
])

chapter('engineer', P, 'Let the Machines Do It', 'cyclic:user',
        'Tier 2, Engineer. The island runs itself. Start saving for the Frontier.', [
    {'key': 'gold_line', 'title': 'Gold Standard', 'icon': 'ftbstuff:gold_auto_hammer', 'deps': ['tinkerer/gate'],
     'tasks': [('item', 'ftbstuff:gold_cobblestone_generator', 1), ('item', 'ftbstuff:gold_auto_hammer', 1)], 'coins': 400,
     'text': ['Craft the gold upgrades from your iron generator and auto-hammer. Faster everything. Now your sieves are the bottleneck, which is a good problem to have.']},
    {'key': 'auto_sieve', 'title': 'Sieve Squad', 'icon': 'excompressum:auto_sieve', 'tasks': [('item', 'excompressum:auto_sieve', 1)], 'coins': 500,
     'text': ['Sieving by hand was character building. You have enough character now.']},
    {'key': 'user', 'title': 'Click Click Click', 'icon': 'cyclic:user', 'tasks': [('item', 'cyclic:user', 1)], 'coins': 500,
     'text': ['I would consider looking into &6Cyclic&r about now, just saying.',
              '',
              'The &6User&r clicks things for you: harvest, place, use items. Mods: Cyclic has the useful tricks.']},
    {'key': 'power_exchange', 'title': 'Power to the People', 'icon': 'economy_core:power_exchange',
     'tasks': [('item', 'economy_core:power_exchange', 1)], 'coins': 500,
     'text': ['The &6Power Exchange&r buys electricity. Pipe FE into it from any generator and your team earns coins every second.',
              '',
              'It pays on a curve: 100 FE/t earns about 70 coins a minute, and every 10x more power pays about 4x more. '
              'All your team\'s exchanges share one curve, so build a bigger power plant, not more exchanges.',
              '',
              'Your first power is a Cyclic generator. By the late game, reactors turn into serious money.']},
    {'key': 'collector', 'title': 'Vacuum Cleaner', 'icon': 'cyclic:collector', 'tasks': [('item', 'cyclic:collector', 1)], 'coins': 300,
     'text': ['Sucks up items in an area. Pair it with anything that drops stuff on the floor.']},
    {'key': 'harvest', 'title': 'Reap and Sow', 'icon': 'cyclic:harvester', 'tasks': [('item', 'cyclic:harvester', 1)], 'coins': 500,
     'text': ['Harvester plus planter, or Create\'s mechanical harvester: full crop automation.',
              '',
              'Plant, grow, harvest, sell, repeat. You are now a farming conglomerate.']},
    {'key': 'brass', 'title': 'Brass Tacks', 'icon': 'create:precision_mechanism', 'tasks': [('item', 'create:precision_mechanism', 1)], 'coins': 600,
     'text': ['Mix copper and zinc into brass, then build a &6precision mechanism&r.',
              '',
              'They sell for 450 and unlock fancier Create machines. Worth the sequenced-assembly headache. Probably.']},
    {'key': 'mobs', 'title': 'Mob Squad', 'icon': 'mob_grinding_utils:dreadful_dirt',
     'tasks': [('item', 'mob_grinding_utils:dreadful_dirt', 1), ('item', 'mob_grinding_utils:spikes', 1)], 'coins': 400,
     'text': ['Hostile mobs spawn on &6dreadful dirt&r even in daylight. Add spikes, a fan and an absorption hopper and you have a mob farm.',
              '',
              'Bones, string, gunpowder, ender pearls: all sellable. See Mods: Mob Grinding Utils.']},
    {'key': 'xp', 'title': 'Bottled Experience', 'icon': 'mob_grinding_utils:xp_tap', 'side': 'mobs', 'optional': True,
     'tasks': [('item', 'mob_grinding_utils:xp_tap', 1)], 'coins': 300,
     'text': ['Mob farms make XP too. Store it. Enchanting gets important soon.']},
    {'key': 'storage', 'title': 'Storage Wars', 'icon': 'storagedrawers:oak_full_drawers_1', 'tasks': [('item', 'storagedrawers:oak_full_drawers_1', 1)], 'coins': 300,
     'text': ['You are drowning in cobble. It happens to the best of us.',
              '',
              'Mods: Storage compares drawers, Sophisticated Storage and Tom\'s storage. Hint: Tom\'s is the easy one.']},
    {'key': 'big_sale', 'title': 'The Big Picture', 'icon': 'lightmanscurrency:coin_emerald', 'tasks': [('adv', 'economy_core:sale/1000')], 'coins': 500,
     'text': ['Make a single sale worth 1,000 or more.',
              '',
              'Feel the sparkle? That is a tier 4 celebration. They get much, much bigger.']},
    {'key': 'gate', 'title': 'Gate: Buy the Frontier', 'icon': 'economy_core:frontier_gateway', 'gate': (3, 96000, 40000),
     'items': [('economy_core:frontier_gateway', 1)], 'personal_rewards': True,
     'subtitle': 'Earn 96,000 lifetime, hand in 40,000 in coins',
     'text': ['Out there is a whole overworld: villages, diamonds, dungeons and Mystical Agriculture. The best purchase you will ever make. Pack a lunch.',
              '',
              'Hand in &64 diamond coins&r and have &696,000 lifetime earnings&r.',
              '',
              'Unlocks tier 3: the Frontier, Mystical Agriculture, villages, diamonds and structures. Everyone on the team gets a &6Frontier Gateway&r.']},
])

chapter('pioneer', P, 'Land Ho!', 'minecraft:filled_map',
        'Tier 3, Pioneer. A whole world to explore and sell.', [
    {'key': 'arrive', 'title': 'Through the Gateway', 'icon': 'economy_core:frontier_gateway', 'deps': ['engineer/gate'], 'tasks': [('dim', 'minecraft:overworld')], 'coins': 1000,
     'text': ['Place your &6Frontier Gateway&r on the island and right-click it.', '', 'Real ground! Trees that are not yours!',
              '',
              'Watch out for creepers. You forgot about those, did you not?',
              '',
              'The gateway you land next to takes you home. Place another gateway anywhere out here to move your landing spot.']},
    {'key': 'home', 'title': 'Set Up Camp', 'icon': 'waystones:waystone', 'tasks': [('item', 'waystones:waystone', 1)], 'coins': 500,
     'text': ['Place a &6waystone&r and type &6/sethome&r.',
              '',
              '&6/home&r, &6/warp&r and &6/back&r mean you never get lost. &6/setwarp name&r saves a spot.']},
    {'key': 'diamond', 'title': 'Shiny', 'icon': 'minecraft:diamond', 'tasks': [('item', 'minecraft:diamond', 1)], 'coins': 1000,
     'text': ['Diamonds only exist out here. They sell for 800 each.',
              '',
              'The price drops fast though, so sell a few at a time between other goods.']},
    {'key': 'compass', 'title': 'Compass Points', 'icon': 'naturescompass:naturescompass', 'tasks': [('item', 'naturescompass:naturescompass', 1)], 'coins': 500,
     'text': ['Find biomes and structures without wandering for an hour. There is an &6Explorer\'s Compass&r for structures too.']},
    {'key': 'dungeon', 'title': 'Dungeon Crawl', 'icon': 'minecraft:name_tag', 'tasks': [('item', 'minecraft:name_tag', 1)], 'coins': 1500,
     'text': ['Structures hide treasure: hearts of the sea, totems, enchanted books.',
              '',
              'Sell the shiny stuff, keep the useful stuff. Name tags only come from loot chests, so bring one back to prove you went.']},
    {'key': 'altar', 'title': 'Mystical Beginnings', 'icon': 'mysticalagriculture:infusion_altar',
     'tasks': [('item', 'mysticalagriculture:infusion_altar', 1)], 'coins': 1500,
     'text': ['Mystical Agriculture finally unlocks! Grow resources as crops.',
              '',
              'Mods: Mystical Agriculture walks you through it.']},
    {'key': 'inferium', 'title': 'Inferium Farmer', 'icon': 'mysticalagriculture:inferium_essence',
     'tasks': [('item', 'mysticalagriculture:inferium_essence', 16)], 'coins': 800,
     'text': ['Essence sells cheaply on purpose. It is worth far more turned into resource seeds.']},
    {'key': 'frontier_fish', 'title': 'Fish of the Frontier', 'icon': 'aquaculture:tuna', 'tasks': [('item', 'aquaculture:tuna', 1)], 'coins': 800,
     'text': ['Different biomes, different fish. Some sell for 60 each. Tuna lives in the ocean.']},
    {'key': 'villagers', 'title': 'Village People', 'icon': 'minecraft:emerald', 'tasks': [('item', 'minecraft:emerald', 4)], 'coins': 500,
     'text': ['Villagers trade emeralds, and emeralds sell.',
              '',
              '&6Easy Villagers&r puts them in a block if you would rather not deal with their attitude.']},
    {'key': 'gate', 'title': 'Gate: Cultivator', 'icon': 'minecraft:blaze_rod', 'gate': (4, 350000, 80000),
     'subtitle': 'Earn 350,000 lifetime, hand in 80,000 in coins',
     'text': ['Turn the heat up.',
              '',
              'Hand in &68 diamond coins&r and have &6350,000 lifetime earnings&r.',
              '',
              'Unlocks tier 4: the Nether, Mekanism, power and Hostile Neural Networks.']},
])

chapter('cultivator', P, 'Some Like It Hot', 'minecraft:blaze_rod',
        'Tier 4, Cultivator. The Nether, real machines and your first boss.', [
    {'key': 'nether', 'title': 'Portal Party', 'icon': 'minecraft:obsidian', 'deps': ['pioneer/gate'],
     'tasks': [('dim', 'minecraft:the_nether')], 'coins': 2000,
     'text': ['Amplified Nether is tall. Very tall. Bring blocks.']},
    {'key': 'blaze', 'title': 'Fortress of Blaze', 'icon': 'minecraft:blaze_rod', 'tasks': [('item', 'minecraft:blaze_rod', 4)], 'coins': 1500,
     'text': ['Blaze rods sell for 60 and fuel half the mods in the pack. YUNG\'s fortresses are bigger than you remember.']},
    {'key': 'enrich', 'title': 'Doubling Down', 'icon': 'mekanism:enrichment_chamber',
     'tasks': [('item', 'mekanism:enrichment_chamber', 1)], 'coins': 3000,
     'text': ['Two dusts per ore. Mods: Mekanism if you have never touched it.',
              '',
              'If you have, you know the drill. Literally.']},
    {'key': 'power_powah', 'title': 'Unlimited Power: Powah', 'icon': 'powah:furnator_starter', 'deps': ['enrich'],
     'tasks': [('item', 'powah:furnator_starter', 1)], 'coins': 2000,
     'text': ['Machines want electricity now. Pick ONE of the three power quests: any of them unlocks the next step.',
              '',
              '&6Powah&r is the simple option: a Furnator burns fuel into power.']},
    {'key': 'power_ca', 'title': 'Unlimited Power: Alternator', 'icon': 'createaddition:alternator', 'deps': ['enrich'], 'side': 'power_powah',
     'tasks': [('item', 'createaddition:alternator', 1)], 'coins': 2000,
     'text': ['Already deep into Create? &6Create Crafts & Additions&r turns your gears into electricity with an alternator.',
              '',
              'Any one of the three power quests unlocks the next step.']},
    {'key': 'power_mek', 'title': 'Unlimited Power: Heat Generator', 'icon': 'mekanismgenerators:heat_generator', 'deps': ['enrich'], 'side': 'power_powah',
     'tasks': [('item', 'mekanismgenerators:heat_generator', 1)], 'coins': 2000,
     'text': ['Mekanism fan? A &6heat generator&r next to lava is cheap, reliable power.',
              '',
              'Any one of the three power quests unlocks the next step.']},
    {'key': 'wither', 'title': 'The Wither', 'icon': 'minecraft:nether_star', 'deps_any': ['power_powah', 'power_ca', 'power_mek'],
     'tasks': [('item', 'minecraft:nether_star', 1)], 'coins': 5000,
     'text': ['Forty thousand coins for one star.',
              '',
              'Bring a bow, a sword and a healthy disrespect for skeletons.']},
    {'key': 'hnn', 'title': 'Neural Networks', 'icon': 'hostilenetworks:sim_chamber',
     'tasks': [('item', 'hostilenetworks:deep_learner', 1), ('item', 'hostilenetworks:sim_chamber', 1)], 'coins': 3000,
     'text': ['Train a data model on a mob, then farm it without the mob. Science!',
              '',
              'Mods: Hostile Neural Networks explains the setup.']},
    {'key': 'feast', 'title': 'Feast Mode', 'icon': 'farmersdelight:roast_chicken_block',
     'tasks': [('item', 'farmersdelight:roast_chicken_block', 1)], 'coins': 2000,
     'text': ['Feasts sell for 400. Create mechanical crafters can make them for you.']},
    {'key': 'debris', 'title': 'Ancient Debris', 'icon': 'minecraft:netherite_scrap', 'tasks': [('item', 'minecraft:netherite_scrap', 1)], 'coins': 3000,
     'text': ['Scrap sells for 2,500. Or keep it. Netherite gear is nice.']},
    {'key': 'paxel', 'title': 'Paxel Power', 'icon': 'mekanismtools:osmium_paxel', 'side': 'enrich', 'optional': True,
     'tasks': [('item', 'mekanismtools:osmium_paxel', 1)], 'coins': 1000,
     'text': ['Pickaxe, axe and shovel in one. Your hotbar thanks you.']},
    {'key': 'gadget', 'title': 'Gotta Go Fast', 'icon': 'mininggadgets:mininggadget', 'side': 'power_powah', 'optional': True,
     'tasks': [('item', 'mininggadgets:mininggadget', 1)], 'coins': 1500,
     'text': ['Power-hungry toys that save hours. Charge them.']},
    {'key': 'gate', 'title': 'Gate: Industrialist', 'icon': 'twilightforest:naga_trophy', 'gate': (5, 1050000, 150000),
     'subtitle': 'Earn 1,050,000 lifetime, hand in 150,000 in coins',
     'text': ['From fish traps to factories. Look at you.',
              '',
              'Hand in &61 netherite and 5 diamond coins&r and have &61,050,000 lifetime earnings&r.',
              '',
              'Unlocks tier 5: the Twilight Forest, the End and the Mekanism ore ladder.']},
])

chapter('industrialist', P, 'Into the Woods', 'twilightforest:naga_trophy',
        'Tier 5, Industrialist. Bosses are the payday.', [
    {'key': 'twilight', 'title': 'Twilight Zone', 'icon': 'twilightforest:twilight_portal_miniature_structure', 'deps': ['cultivator/gate'],
     'tasks': [('dim', 'twilightforest:twilight_forest')], 'coins': 3000,
     'text': ['Dig a 2x2 pool of water, ring it with flowers, throw in a diamond.',
              '',
              'Mods: Twilight Forest has the boss order and what each trophy sells for.']},
    {'key': 'naga', 'title': 'Snake Charmer', 'icon': 'twilightforest:naga_trophy', 'tasks': [('item', 'twilightforest:naga_trophy', 1)], 'coins': 3000,
     'text': ['Trophies sell big: 15,000 for this one. Every boss has one.']},
    {'key': 'lich', 'title': 'Lich, Please', 'icon': 'twilightforest:lich_trophy', 'tasks': [('item', 'twilightforest:lich_trophy', 1)], 'coins': 4000,
     'text': ['Keep a scepter or sell it for 8,000. Your call.']},
    {'key': 'minoshroom', 'title': 'Maze Runner', 'icon': 'twilightforest:minoshroom_trophy', 'tasks': [('item', 'twilightforest:minoshroom_trophy', 1)], 'coins': 5000,
     'text': ['The maze is the hard part. The bull is the fun part.']},
    {'key': 'hydra', 'title': 'Three Heads Are Better', 'icon': 'twilightforest:hydra_trophy', 'tasks': [('item', 'twilightforest:hydra_trophy', 1)], 'coins': 8000,
     'text': ['60,000 coins of angry dragon. Fire resistance recommended.']},
    {'key': 'knights', 'title': 'Knights to Remember', 'icon': 'twilightforest:knight_phantom_trophy', 'tasks': [('item', 'twilightforest:knight_phantom_trophy', 1)], 'coins': 7000,
     'text': ['Six ghost knights, one trophy. Worth 50,000.']},
    {'key': 'urghast', 'title': 'Ghastly', 'icon': 'twilightforest:ur_ghast_trophy', 'tasks': [('item', 'twilightforest:ur_ghast_trophy', 1)], 'coins': 9000,
     'text': ['The Dark Tower is a climb. The view (and the 75,000) is worth it.']},
    {'key': 'snow', 'title': 'Ice Ice Baby', 'icon': 'twilightforest:snow_queen_trophy',
     'tasks': [('item', 'twilightforest:alpha_yeti_trophy', 1), ('item', 'twilightforest:snow_queen_trophy', 1)], 'coins': 10000,
     'text': ['The Snow Queen pays 90,000.',
              '',
              'Sell her trophy with the Yeti\'s in one go and you are in MEGA SALE territory.']},
    {'key': 'ore_factory', 'title': 'Ore Factory', 'icon': 'mekanism:purification_chamber',
     'tasks': [('item', 'mekanism:purification_chamber', 1)], 'coins': 6000,
     'text': ['Craft a purification chamber from your enrichment chamber: triple ore, then quadruple. Mekanism\'s ore ladder is the best money machine in the pack.']},
    {'key': 'dragon', 'title': 'The End', 'icon': 'minecraft:dragon_egg', 'tasks': [('kill', 'minecraft:ender_dragon', 1)], 'coins': 10000,
     'text': ['The egg sells for 150,000. Yes, really.',
              '',
              'Elytra from end ships sell for 50,000 each. Nullscape makes the End much prettier.']},
    {'key': 'gate', 'title': 'Gate: Tycoon', 'icon': 'minecraft:nether_star', 'gate': (6, 2800000, 300000),
     'subtitle': 'Earn 2,800,000 lifetime, hand in 300,000 in coins',
     'text': ['You are rich. Let us make you lazy.',
              '',
              'Hand in &63 netherite coins&r and have &62,800,000 lifetime earnings&r.',
              '',
              'Unlocks tier 6: AE2, Industrial Foregoing and the endgame toys.']},
])

chapter('tycoon', P, 'Money Is No Object', 'minecraft:nether_star',
        'Tier 6, Tycoon. Everything is unlocked. Go wild.', [
    {'key': 'top', 'title': 'Welcome to the Top', 'icon': 'lightmanscurrency:coin_netherite', 'deps': ['industrialist/gate'], 'coins': 5000,
     'text': ['Everything is unlocked. From here on, this chapter is a list of toys.']},
    {'key': 'ae2', 'title': 'Me, Myself and AE', 'icon': 'ae2:controller', 'tasks': [('item', 'ae2:controller', 1)], 'coins': 10000,
     'text': ['Applied Energistics: storage that thinks.',
              '',
              'If it looks like a lot, it is. Mods: Storage has the gentle version.']},
    {'key': 'if', 'title': 'Industrial Strength', 'icon': 'industrialforegoing:plant_gatherer',
     'tasks': [('item', 'industrialforegoing:plant_gatherer', 1)], 'coins': 10000,
     'text': ['Pure convenience. You have earned it.']},
    {'key': 'fly', 'title': 'Fly Away', 'icon': 'angelring:angel_ring', 'tasks': [('item', 'angelring:angel_ring', 1)], 'coins': 8000,
     'text': ['Creative flight. Your knees thank you.']},
    {'key': 'draconic', 'title': 'Draconic', 'icon': 'draconicevolution:draconium_core', 'tasks': [('item', 'draconicevolution:draconium_core', 1)], 'coins': 15000,
     'text': ['Here be overpowered things. You are allowed now.']},
    {'key': 'mega', 'title': 'MEGA SALE', 'icon': 'minecraft:dragon_egg', 'tasks': [('adv', 'economy_core:sale/150000')], 'coins': 20000,
     'text': ['Make a single sale worth 150,000 or more.',
              '',
              'Fireworks, the totem animation, the works. You did it.']},
    {'key': 'four_million', 'title': 'Eight Million', 'icon': 'lightmanscurrency:coin_netherite',
     'tasks': [('adv', 'economy_core:earned/8000000')], 'coins': 50000,
     'text': ['Reach 8,000,000 lifetime earnings. The end goal.',
              '',
              'Congratulations, Tycoon. Now go build something ridiculous.']},
])

# =====================================================================================================
# MODS (optional deep dives)
# =====================================================================================================

chapter('mod_exdeorum', M, 'Ex Deorum', 'exdeorum:oak_sieve',
        'Sieves, barrels, crucibles and crooks. Unlocks at the start.', [
    {'key': 'intro', 'title': 'Dirt Into Riches', 'icon': 'exdeorum:oak_sieve', 'coins': 10,
     'text': ['The ancient art of turning dirt into diamonds. Well, into iron. Diamonds are Frontier-only here.',
              '',
              'Skip this tab if you have played Ex Nihilo before.']},
    {'key': 'crook', 'title': 'Crooks', 'icon': 'exdeorum:crook', 'tasks': [('item', 'exdeorum:crook', 1)], 'coins': 10,
     'text': ['Double saplings from leaves, and a small silkworm chance. The bone crook is sturdier.']},
    {'key': 'silk', 'title': 'Silkworms and String', 'icon': 'exdeorum:silkworm', 'tasks': [('item', 'minecraft:string', 4)], 'coins': 20,
     'text': ['Use a silkworm on leaves, wait for the whole tree to go white, break it for string.',
              '',
              'Cooked silkworms are a snack. Questionable, but a snack.']},
    {'key': 'barrel', 'title': 'Barrels', 'icon': 'exdeorum:oak_barrel', 'coins': 10,
     'text': ['Compost organic stuff into dirt. Fill with water and add dust for clay. Experiment!']},
    {'key': 'crucible', 'title': 'Crucibles', 'icon': 'exdeorum:porcelain_crucible', 'tasks': [('item', 'exdeorum:porcelain_crucible', 1)], 'coins': 20,
     'text': ['Melts cobblestone into lava. It needs heat underneath: a torch works, lava works better.',
              '',
              'This is the only source of lava in the pack.']},
    {'key': 'meshes', 'title': 'Mesh Ladder', 'icon': 'exdeorum:diamond_mesh', 'coins': 20,
     'text': ['String, flint, iron, diamond, netherite. Each mesh finds more and better stuff.',
              '',
              'Press U on a mesh in JEI for its drop table.']},
])

chapter('mod_ftbstuff', M, 'FTB Stuff & Things', 'ftbstuff:iron_cobblestone_generator',
        'Cobble generators and auto-hammers. Unlocks at the start.', [
    {'key': 'intro', 'title': 'Infinite Rocks', 'icon': 'ftbstuff:stone_cobblestone_generator', 'coins': 10,
     'text': ['Generators make cobble, auto-hammers crush it. Buy the first one of each from the shop, then &6craft each upgrade from the one below&r. Each tier is faster.']},
    {'key': 'ladder', 'title': 'The Upgrade Ladder', 'icon': 'ftbstuff:gold_auto_hammer', 'coins': 20,
     'text': ['Stone (tier 0), iron (tier 1), gold (tier 2), diamond (tier 4), netherite (tier 5).',
              '',
              'Match your hammer speed to your generator speed, or one of them sits idle.']},
    {'key': 'basalt', 'title': 'Basalt Generators', 'icon': 'ftbstuff:stone_basalt_generator', 'coins': 20,
     'text': ['From tier 4: basalt for Nether-style sieving.']},
])

chapter('mod_create', M, 'Create', 'create:cogwheel',
        'Rotation, processing and contraptions. Unlocks at tier 1.', [
    {'key': 'intro', 'title': 'The Rabbit Hole', 'icon': 'create:cogwheel', 'coins': 20,
     'text': ['If you know Create, skip this. If you do not, welcome to the best rabbit hole in Minecraft.',
              '',
              'Hold &6W&r over any Create block for a Ponder animation that explains it. Seriously, use Ponder.']},
    {'key': 'power', 'title': 'Rotation and Stress', 'icon': 'create:water_wheel', 'coins': 30,
     'text': ['Sources (water wheels, windmills) make rotation. Machines use stress. Too much stress and everything stops.',
              '',
              'Goggles show the numbers.']},
    {'key': 'crushing', 'title': 'Crushing and Washing', 'icon': 'create:crushing_wheel', 'coins': 30,
     'text': ['Crushing wheels turn ore chunks into crushed ore plus bonus. An encased fan over water washes it into more nuggets.',
              '',
              'This is your first ore-multiplying line.']},
    {'key': 'belts', 'title': 'Belts and Funnels', 'icon': 'create:shaft', 'coins': 20,
     'text': ['Belts move items, funnels pull them on and off, chutes drop them down. Pipe everything to a Market Crate at the end.']},
    {'key': 'brass', 'title': 'Brass', 'icon': 'create:brass_ingot', 'tasks': [('item', 'create:brass_ingot', 4)], 'coins': 40,
     'text': ['Copper plus zinc in a mixer (needs heat from a blaze burner). Brass makes the smart machines.']},
    {'key': 'sequenced', 'title': 'Sequenced Assembly', 'icon': 'create:precision_mechanism', 'coins': 40,
     'text': ['Multi-step recipes on a belt. Precision mechanisms are the first, and they sell for 900.']},
])

chapter('mod_create_addons', M, 'Create Add-ons', 'createaddition:electric_motor',
        'Electricity, engines and enchanting for Create. Tier 1 to 4.', [
    {'key': 'ca', 'title': 'Crafts & Additions', 'icon': 'createaddition:alternator', 'coins': 30,
     'text': ['Alternators turn rotation into power, electric motors turn power into rotation. The bridge between Create and every power mod.']},
    {'key': 'newage', 'title': 'Create: New Age', 'icon': 'create_new_age:basic_energiser', 'coins': 30,
     'text': ['Another flavor of electricity for Create, with magnetic generators and reactors later on.']},
    {'key': 'diesel', 'title': 'Diesel Generators', 'icon': 'createdieselgenerators:diesel_engine', 'coins': 30,
     'text': ['Burn fuel for big rotation. Oil comes from the Frontier.']},
    {'key': 'cei', 'title': 'Enchantment Industry', 'icon': 'create_enchantment_industry:blaze_enchanter', 'coins': 30,
     'text': ['Turns XP from your mob farm into enchanted books automatically. Pairs beautifully with Mob Grinding Utils.']},
])

chapter('mod_botany', M, 'Botany Pots', 'botanypots:terracotta_hopper_botany_pot',
        'Farming without the walking. Unlocks at tier 1.', [
    {'key': 'intro', 'title': 'Pots 101', 'icon': 'botanypots:terracotta_botany_pot', 'coins': 10,
     'text': ['Put soil in the pot, then a seed. It grows and you collect.',
              '',
              'The &6hopper botany pot&r outputs into whatever is below it.']},
    {'key': 'soil', 'title': 'Better Soil', 'icon': 'minecraft:bone_meal', 'coins': 10,
     'text': ['Some soils grow faster. JEI shows growth times for every crop and soil combo.']},
    {'key': 'mystical', 'title': 'Mystical Pots', 'icon': 'mysticalagriculture:inferium_seeds', 'coins': 20,
     'text': ['From tier 4, Mystical Agriculture seeds grow in pots too. Compact resource farms!']},
])

chapter('mod_food', M, "Farmer's Delight and Cooking", 'farmersdelight:cooking_pot',
        'Cook stuff, sell it for more. Unlocks at tier 1.', [
    {'key': 'intro', 'title': 'Cook, Sell, Repeat', 'icon': 'farmersdelight:cooking_pot', 'tasks': [('item', 'farmersdelight:cooking_pot', 1)], 'coins': 20,
     'text': ['Cook stuff. Sell stuff. Cook fancier stuff. Sell it for more.',
              '',
              'The cooking pot needs heat underneath.']},
    {'key': 'crops', 'title': 'New Crops', 'icon': 'farmersdelight:tomato', 'coins': 10,
     'text': ['Tomatoes, cabbages, onions and rice. Seeds are in the shop.']},
    {'key': 'meals', 'title': 'Meals That Pay', 'icon': 'farmersdelight:beef_stew', 'coins': 20,
     'text': ['Stews and pasta sell for 60 to 80. That is twenty potatoes\' worth of profit in one bowl.']},
    {'key': 'feasts', 'title': 'Feasts', 'icon': 'farmersdelight:roast_chicken_block', 'coins': 30,
     'text': ['Feasts sell for 400 each from tier 4. Create mechanical crafters can make them for you.']},
    {'key': 'kitchen', 'title': 'Cooking for Blockheads', 'icon': 'cookingforblockheads:cooking_table', 'coins': 20,
     'text': ['A kitchen multiblock that shows every recipe you can make from what you have. Great for lazy chefs.']},
    {'key': 'variety', 'title': 'Spice of Life', 'icon': 'minecraft:golden_carrot', 'coins': 10,
     'text': ['Eating a variety of foods gives you bonus hearts. The theme of this pack is variety, in case you had not noticed.']},
])

chapter('mod_fishing', M, 'Fishing', 'fishermens_trap:fishtrap',
        'Traps, rods and lava fishing. Unlocks at tier 1.', [
    {'key': 'trap', 'title': "Fishermen's Trap", 'icon': 'fishermens_trap:fishtrap', 'coins': 10,
     'text': ['Bait it, put it in water, empty it with a hopper. Fish while you sleep.']},
    {'key': 'aquaculture', 'title': 'Aquaculture', 'icon': 'aquaculture:iron_fishing_rod', 'coins': 20,
     'text': ['Better rods, hooks and bait. From the Frontier on, every biome has its own fish, and some sell for 60.']},
    {'key': 'lava', 'title': 'Lava Fishing', 'icon': 'minecraft:lava_bucket', 'coins': 30,
     'text': ['Nether Depths Upgrade adds fish to Nether lava from tier 4. Bring fire resistance. Obviously.']},
])

chapter('mod_cyclic', M, 'Cyclic', 'cyclic:user',
        'A toolbox of automation blocks. Unlocks at tier 2.', [
    {'key': 'intro', 'title': 'The Five That Matter', 'icon': 'cyclic:user', 'coins': 20,
     'text': ['Cyclic is a huge toolbox. For making money, five tools matter: User, Collector, Harvester, Planter and Breaker.']},
    {'key': 'user', 'title': 'User', 'icon': 'cyclic:user', 'coins': 30,
     'text': ['A fake player that right or left clicks. Give it shears for wool, a sword for mobs, bone meal for crops. Get creative.']},
    {'key': 'collector', 'title': 'Item Collector', 'icon': 'cyclic:collector', 'coins': 20,
     'text': ['A vacuum hopper with an adjustable area. Put it next to anything that drops items.']},
    {'key': 'harvester', 'title': 'Harvester and Planter', 'icon': 'cyclic:harvester', 'coins': 30,
     'text': ['Harvests ripe crops in an area. The planter replants. Together: an infinite farm.']},
    {'key': 'breaker', 'title': 'Breaker and Placer', 'icon': 'cyclic:breaker', 'coins': 20,
     'text': ['Break and place blocks automatically. Pair with a cobble generator if you are feeling retro.']},
])

chapter('mod_excompressum', M, 'Ex Compressum', 'excompressum:auto_sieve',
        'Auto-sieves. Unlocks at tier 2.', [
    {'key': 'auto', 'title': 'Auto-Sieve', 'icon': 'excompressum:auto_sieve', 'coins': 30,
     'text': ['Sieves for you. Feed it with a hopper, empty it with another. Add a mesh first, obviously.']},
])

chapter('mod_mobs', M, 'Mob Grinding Utils', 'mob_grinding_utils:dreadful_dirt',
        'A mob farm in a kit. Unlocks at tier 2.', [
    {'key': 'dirt', 'title': 'Dreadful and Delightful', 'icon': 'mob_grinding_utils:dreadful_dirt', 'coins': 20,
     'text': ['Dreadful dirt spawns hostile mobs even in daylight. Delightful dirt spawns passive ones. Both are bought from the shop.']},
    {'key': 'kill', 'title': 'Spikes and Saws', 'icon': 'mob_grinding_utils:saw', 'coins': 30,
     'text': ['Spikes hurt mobs that walk on them. The mob masher (saw) kills with looting upgrades. Players do not get the drops from spikes, so use the saw for good loot.']},
    {'key': 'move', 'title': 'Fans and Conveyors', 'icon': 'mob_grinding_utils:fan', 'coins': 20,
     'text': ['Push mobs into a killing spot with fans and entity conveyors.']},
    {'key': 'collect', 'title': 'Absorption Hopper', 'icon': 'mob_grinding_utils:absorption_hopper', 'coins': 20,
     'text': ['Collects drops and XP. Filter what goes where, then pipe the loot to a Market Crate.']},
    {'key': 'xp', 'title': 'XP Storage', 'icon': 'mob_grinding_utils:xpsolidifier', 'coins': 20,
     'text': ['Tanks and taps store XP, the solidifier turns it into items. Save it for enchanting.']},
])

chapter('mod_storage', M, 'Storage', 'storagedrawers:oak_full_drawers_1',
        'Drawers, chests, networks. Pick what suits you.', [
    {'key': 'intro', 'title': 'Pick Your Poison', 'icon': 'minecraft:chest', 'coins': 10,
     'text': ['Oh, so you do not like AE, so you came to the storage page instead. Smart. Here is the cheat sheet:',
              '',
              '&6Drawers&r: lots of one item. &6Sophisticated Storage&r: upgradable chests. &6Tom\'s&r: a simple early network. &6Refined Storage&r: mid-game network. &6AE2&r: endgame, at tier 6.']},
    {'key': 'drawers', 'title': 'Storage Drawers', 'icon': 'storagedrawers:oak_full_drawers_1', 'coins': 10,
     'text': ['Great for cobble, dirt and the other stuff you have 40,000 of.']},
    {'key': 'sophisticated', 'title': 'Sophisticated Storage and Backpacks', 'icon': 'sophisticatedbackpacks:backpack', 'coins': 20,
     'text': ['Chests and backpacks you can upgrade: bigger, magnets, auto-pickup, filters. The backpack magnet upgrade is a lifesaver.']},
    {'key': 'toms', 'title': "Tom's Simple Storage", 'icon': 'toms_storage:storage_terminal', 'coins': 20,
     'text': ['A terminal that sees every connected chest. Cheap, simple and very good. Most players never need more.']},
    {'key': 'rs', 'title': 'Refined Storage', 'icon': 'refinedstorage:controller', 'coins': 20,
     'text': ['A real storage network with autocrafting, for when Tom\'s is not enough.']},
])

chapter('mod_mystical', M, 'Mystical Agriculture', 'mysticalagriculture:inferium_essence',
        'Grow ores on plants. Unlocks at tier 3 (the Frontier).', [
    {'key': 'intro', 'title': 'Grow Ores on Plants', 'icon': 'mysticalagriculture:inferium_seeds', 'coins': 30,
     'text': ['Grow ores. On plants. Do not think about it too hard.',
              '',
              'Locked until you buy the Frontier.']},
    {'key': 'essence', 'title': 'Essence Tiers', 'icon': 'mysticalagriculture:prudentium_essence', 'coins': 30,
     'text': ['Inferium, prudentium, tertium, imperium, supremium. Each tier crafts the next and unlocks better seeds.']},
    {'key': 'altar', 'title': 'The Infusion Altar', 'icon': 'mysticalagriculture:infusion_altar', 'coins': 40,
     'text': ['Crafts resource seeds from essence and the resource itself. Put pedestals around it.']},
    {'key': 'sell', 'title': 'Sell Smart', 'icon': 'minecraft:iron_ingot', 'coins': 30,
     'text': ['Essence sells for about a fifth of what it crafts on purpose. Grow resource crops and sell the resources instead.']},
])

chapter('mod_explore', M, 'Exploration and Structures', 'naturescompass:naturescompass',
        'Where the loot is. Unlocks at tier 3.', [
    {'key': 'compasses', 'title': 'Compasses', 'icon': 'explorerscompass:explorerscompass', 'coins': 20,
     'text': ['Nature\'s Compass finds biomes, Explorer\'s Compass finds structures. Both are in the shop.']},
    {'key': 'structures', 'title': 'What Is Out There', 'icon': 'minecraft:chest', 'coins': 30,
     'text': ['Better dungeons, mineshafts, strongholds and fortresses, plus towns, towers, taverns and huge When Dungeons Arise structures.']},
    {'key': 'sell_loot', 'title': 'Loot Worth Selling', 'icon': 'minecraft:heart_of_the_sea', 'coins': 30,
     'text': ['Hearts of the sea 5,000, totems 2,500, tridents 4,000, echo shards 1,500. Enchanted books: keep the good ones.']},
    {'key': 'travel', 'title': 'Getting Around', 'icon': 'waystones:waystone', 'coins': 20,
     'text': ['Waystones for fast travel, /home and /warp for everything else, FTB Chunks map to see where you have been.']},
])

chapter('mod_tools', M, 'Tools and Building', 'mekanismtools:osmium_paxel',
        'Work smarter, or at least faster.', [
    {'key': 'sticks', 'title': 'Construction Sticks', 'icon': 'constructionstick:iron_stick', 'coins': 10,
     'text': ['Extend a row or wall of blocks in one click. Better sticks place more.']},
    {'key': 'gadgets', 'title': 'Building and Mining Gadgets', 'icon': 'buildinggadgets2:gadget_building', 'coins': 20,
     'text': ['Building gadgets copy, paste and fill. Mining gadgets laser through stone. Both need power.']},
    {'key': 'effortless', 'title': 'Effortless Building', 'icon': 'minecraft:bricks', 'coins': 10,
     'text': ['Build modes for lines, walls, floors and mirrored builds. Check the keybinds.']},
    {'key': 'paxels', 'title': 'Paxels', 'icon': 'mekanismtools:osmium_paxel', 'coins': 20,
     'text': ['Mekanism Tools makes paxels (pickaxe, axe and shovel in one) from every Mekanism metal.']},
    {'key': 'silent', 'title': 'Silent Gear', 'icon': 'silentgear:blueprint_paper', 'coins': 20,
     'text': ['Build tools from parts and materials. Deep if you want it, ignorable if you do not.']},
    {'key': 'tiab', 'title': 'Time in a Bottle Tips', 'icon': 'tiab:time_in_a_bottle', 'coins': 10,
     'text': ['Each use speeds a block up more but costs more banked time. Best on slow single machines and growing saplings.']},
])

chapter('mod_mekanism', M, 'Mekanism', 'mekanism:enrichment_chamber',
        'Ore multiplication and serious machines. Unlocks at tier 4.', [
    {'key': 'intro', 'title': 'One Machine at a Time', 'icon': 'mekanism:steel_casing', 'coins': 30,
     'text': ['Skip this if you know Mekanism. If you do not: it is a lot, so we will go one machine at a time.']},
    {'key': 'x2', 'title': '2x: Enrichment Chamber', 'icon': 'mekanism:enrichment_chamber', 'coins': 40,
     'text': ['Ore into two dusts. Smelt the dusts. Double ingots. Start here.']},
    {'key': 'x3', 'title': '3x: Purification Chamber', 'icon': 'mekanism:purification_chamber', 'coins': 50,
     'text': ['Ore plus oxygen into clumps. Three per ore. Crafted from an enrichment chamber. Tier 5.']},
    {'key': 'x4', 'title': '4x: Chemical Injection', 'icon': 'mekanism:chemical_injection_chamber', 'coins': 60,
     'text': ['Shards from hydrogen chloride. Four per ore. Crafted from a purification chamber. Tier 5, and it pays for itself fast.']},
    {'key': 'power', 'title': 'Generators', 'icon': 'mekanismgenerators:heat_generator', 'coins': 40,
     'text': ['Heat generators near lava early, wind and solar later, gas-burning for serious power.']},
])

chapter('mod_power', M, 'Power', 'powah:energy_cell_starter',
        'Electricity: the stuff that makes the other stuff go. Unlocks at tier 4.', [
    {'key': 'powah', 'title': 'Powah', 'icon': 'powah:furnator_starter', 'coins': 30,
     'text': ['Simple tiered generators, cells and cables. Buy a starter Furnator and Energy Cell, then craft each upgrade from the tier below (hardened at tier 5, the fancy ones at tier 6).']},
    {'key': 'flux', 'title': 'Flux Networks', 'icon': 'fluxnetworks:flux_point', 'coins': 30,
     'text': ['Wireless power. Plugs and points instead of cables everywhere.']},
    {'key': 'reactors', 'title': 'Extreme Reactors', 'icon': 'bigreactors:basic_reactorcasing', 'coins': 40,
     'text': ['Big multiblock reactors for big power. Late game, very satisfying.']},
])

chapter('mod_hnn', M, 'Hostile Neural Networks', 'hostilenetworks:sim_chamber',
        'Farm mobs without the mobs. Unlocks at tier 4.', [
    {'key': 'learner', 'title': 'Deep Learner', 'icon': 'hostilenetworks:deep_learner', 'coins': 30,
     'text': ['Put data models in the deep learner and kill mobs to train them.']},
    {'key': 'chamber', 'title': 'Simulation Chamber', 'icon': 'hostilenetworks:sim_chamber', 'coins': 40,
     'text': ['Trained models plus power plus prediction matrices make predictions. Predictions sell, or turn into loot.']},
    {'key': 'fabricator', 'title': 'Loot Fabricator', 'icon': 'hostilenetworks:loot_fabricator', 'coins': 40,
     'text': ['Turns predictions into the mob\'s drops. Pick whichever sells better.']},
])

chapter('mod_nether', M, 'The Nether', 'minecraft:netherrack',
        'Taller, meaner, more profitable. Unlocks at tier 4.', [
    {'key': 'tips', 'title': 'Survival Tips', 'icon': 'minecraft:potion', 'coins': 20,
     'text': ['Amplified Nether is very tall. Fire resistance, blocks to bridge with and a waystone at the portal.']},
    {'key': 'fortress', 'title': 'Fortresses', 'icon': 'minecraft:nether_bricks', 'coins': 30,
     'text': ['YUNG\'s fortresses are huge. Blazes for rods, wither skeletons for skulls (3,000 each, or summon the Wither).']},
    {'key': 'debris', 'title': 'Ancient Debris', 'icon': 'minecraft:ancient_debris', 'coins': 30,
     'text': ['Low down, rare and worth 2,500 per scrap.']},
])

chapter('mod_twilight', M, 'Twilight Forest', 'twilightforest:naga_trophy',
        'Eight bosses, eight trophies, a lot of coins. Unlocks at tier 5.', [
    {'key': 'portal', 'title': 'Getting There', 'icon': 'minecraft:poppy', 'coins': 30,
     'text': ['2x2 water pool, flowers all around, throw a diamond in. Stand back.']},
    {'key': 'order', 'title': 'Boss Order', 'icon': 'twilightforest:lich_trophy', 'coins': 40,
     'text': ['Naga, Lich, Minoshroom, Hydra, Knight Phantoms, Ur-Ghast, Alpha Yeti, Snow Queen.',
              '',
              'Each one unlocks the next area. Skipping ahead gets you weather and darkness.']},
    {'key': 'payday', 'title': 'Trophy Prices', 'icon': 'twilightforest:snow_queen_trophy', 'coins': 40,
     'text': ['Naga 15,000, Lich 25,000, Minoshroom 30,000, Knight Phantom 50,000, Hydra 60,000, Alpha Yeti 60,000, Ur-Ghast 75,000, Snow Queen 90,000.',
              '',
              'Boss drops sell too: fiery blood and tears 6,000, scepters 8,000.']},
])

chapter('mod_end', M, 'The End', 'minecraft:end_stone',
        'Dragon, cities and elytra. Unlocks at tier 5.', [
    {'key': 'dragon', 'title': 'The Dragon', 'icon': 'minecraft:dragon_egg', 'coins': 40,
     'text': ['Kill it, sell the egg for 150,000. Dragon\'s breath sells too.']},
    {'key': 'cities', 'title': 'End Cities', 'icon': 'minecraft:shulker_shell', 'coins': 40,
     'text': ['Shulker shells 1,500, elytra 50,000, dragon heads 25,000. Nullscape makes the islands far more interesting.']},
])

chapter('mod_endgame', M, 'Just Dire Things and Draconic', 'draconicevolution:draconium_core',
        'Here be overpowered things. Tier 5 to 6.', [
    {'key': 'jdt', 'title': 'Just Dire Things', 'icon': 'justdirethings:ferricore_ingot', 'coins': 40,
     'text': ['Tiered gadgets and goo that transforms blocks. Very strong, so it sits late.']},
    {'key': 'draconic', 'title': 'Draconic Evolution', 'icon': 'draconicevolution:draconium_core', 'coins': 50,
     'text': ['Endgame tools, armor and absurd power storage. The final flex.']},
])

chapter('mod_ae2_if', M, 'AE2 and Industrial Foregoing', 'ae2:controller',
        'The deep end. Tier 6.', [
    {'key': 'ae2', 'title': 'AE2 Basics', 'icon': 'ae2:controller', 'coins': 50,
     'text': ['The deep end. Bring floaties.',
              '',
              'Controller, drive, terminal and some storage cells. Autocrafting comes later. There is a guide book in the mod (press G over AE2 items).']},
    {'key': 'if', 'title': 'Industrial Foregoing', 'icon': 'industrialforegoing:plant_gatherer', 'coins': 50,
     'text': ['Big convenient machines: plant gatherers, mob crushers and more. Pure quality of life.']},
])

chapter('mod_qol', M, 'Quality of Life', 'minecraft:filled_map',
        'The little things. Unlocked from the start.', [
    {'key': 'map', 'title': 'FTB Chunks', 'icon': 'minecraft:map', 'coins': 10,
     'text': ['Press M for the map. Claim chunks so nothing griefs your base, and force-load chunks to keep machines running.']},
    {'key': 'commands', 'title': 'Never Lost', 'icon': 'minecraft:compass', 'coins': 10,
     'text': ['/sethome, /home, /setwarp, /warp, /back, /spawn and /tpa. Getting home is never a problem.']},
    {'key': 'graves', 'title': 'Graves', 'icon': 'gravestone:gravestone', 'coins': 10,
     'text': ['Die and your items go into a grave where you fell. Nobody touches it but you.']},
    {'key': 'misc', 'title': 'Little Helpers', 'icon': 'trashcans:item_trash_can', 'coins': 10,
     'text': ['Trash cans for junk, magnets for pickup, elevators for going up, Clumps for XP lag, Mouse Tweaks for your sanity.']},
])

# =====================================================================================================
# REFERENCE
# =====================================================================================================

chapter('ref_market', R, 'The Market', 'economy_core:market_crate',
        'How selling works.', [
    {'key': 'selling', 'title': 'Selling', 'icon': 'economy_core:market_crate',
     'text': ['Put goods in the Market Crate. Use the side slot to sell one stack or all of an item, or Sell everything.',
              '',
              'Auto-sell sells a chunk every half second, starting the moment it is on and the moment goods arrive. Chunks are 2 items at tier 0 and double every tier (4, 8, 16, 32) up to a full stack at tier 5.']},
    {'key': 'prices', 'title': 'Prices and Variety', 'icon': 'minecraft:cobblestone',
     'text': ['Every unit sold lowers that item\'s price a little, never below half. Selling a variety of other goods restores it.',
              '',
              'Later tiers need more variety and bigger batches to recover.']},
    {'key': 'coins', 'title': 'Coins', 'icon': 'lightmanscurrency:coin_gold',
     'text': ['Click a coin icon at the bottom of the crate panel to withdraw your balance as exactly that coin. Shift-click for a mix, largest first.',
              '',
              'Put coins back in the crate to deposit them. Deposit 20 emerald coins, withdraw 2 diamond coins: the crate doubles as a coin exchange.',
              '',
              'Copper 1, iron 10, gold 100, emerald 1,000, diamond 10,000, netherite 100,000.']},
    {'key': 'celebrate', 'title': 'Sale Celebrations', 'icon': 'minecraft:firework_rocket',
     'text': ['The bigger the sale, the bigger the party. Eight tiers, from grey pocket change to MEGA SALE.']},
])

chapter('ref_shop', R, 'The Shop', 'lightmanscurrency:coin_emerald',
        'What is bought and what is crafted.', [
    {'key': 'machines', 'title': 'Machines Are Bought', 'icon': 'ftbstuff:iron_auto_hammer',
     'text': ['Machines that work on their own come only from the shop. Shafts, belts, pipes and cables are still crafted.']},
    {'key': 'buyback', 'title': 'Buy-Back', 'icon': 'economy_core:market_crate',
     'text': ['Machines sell back to the crate for 90% of their price at tiers 0 to 2, 85% at tiers 3 to 4 and 80% at tiers 5 to 6.']},
    {'key': 'supplies', 'title': 'Supplies', 'icon': 'minecraft:wheat_seeds',
     'text': ['Seeds, meshes, compasses and other supplies cost about four times their sell price. Convenient, never profitable.']},
])

chapter('ref_tiers', R, 'Tiers and Gates', 'minecraft:filled_map',
        'What each tier costs and unlocks.', [
    {'key': 'table', 'title': 'The Tiers', 'icon': 'minecraft:filled_map',
     'text': ['0 Castaway: start',
              '1 Tinkerer: 4,000 lifetime, 2,000 fee',
              '2 Engineer: 24,000 lifetime, 10,000 fee',
              '3 Pioneer (Frontier): 96,000 lifetime, 40,000 fee',
              '4 Cultivator (Nether): 350,000 lifetime, 80,000 fee',
              '5 Industrialist (Twilight, End): 1,050,000 lifetime, 150,000 fee',
              '6 Tycoon: 2,800,000 lifetime, 300,000 fee']},
])

chapter('ref_faq', R, 'FAQ', 'minecraft:book',
        'Questions everybody asks.', [
    {'key': 'craft', 'title': "Why can't I craft this machine?", 'icon': 'minecraft:crafting_table',
     'text': ['Machines are shop-only, and some items are locked until a later tier. JEI shows a lock on locked items.']},
    {'key': 'crate', 'title': "Why won't the crate take my item?", 'icon': 'economy_core:market_crate',
     'text': ['Not everything sells. Hover over an item in the crate screen: if there is no price line, the market does not buy it.']},
    {'key': 'lava', 'title': 'Where is lava?', 'icon': 'exdeorum:porcelain_crucible',
     'text': ['Crucible plus cobblestone plus heat. That is the only way, on purpose.']},
    {'key': 'low', 'title': 'My price is low, help!', 'icon': 'minecraft:cobblestone',
     'text': ['You sold too much of one thing. Sell other goods for a while and it comes back. The tooltip says how many more.']},
    {'key': 'commands', 'title': 'Commands', 'icon': 'minecraft:command_block',
     'text': ['/home, /sethome, /warp, /setwarp, /back, /spawn, /tpa, /market balance, /market price <item>']},
])


# =====================================================================================================
# DESIGN: groups, colour themes and banners
# =====================================================================================================

MOD_GROUPS = {
    'mods_island': ['mod_exdeorum', 'mod_ftbstuff', 'mod_create', 'mod_create_addons', 'mod_botany', 'mod_food',
                    'mod_fishing', 'mod_cyclic', 'mod_excompressum', 'mod_mobs', 'mod_storage', 'mod_tools', 'mod_qol'],
    'mods_frontier': ['mod_mystical', 'mod_explore', 'mod_mekanism', 'mod_power', 'mod_hnn', 'mod_nether'],
    'mods_endgame': ['mod_twilight', 'mod_end', 'mod_endgame', 'mod_ae2_if'],
}
for ch in CHAPTERS:
    for g, keys in MOD_GROUPS.items():
        if ch['key'] in keys:
            ch['group'] = g

# Per chapter: Minecraft colour code for titles, tier label (progression only), banner colours (top, bottom, accent).
THEMES = {
    'getting_started': ('a', 'TIER 0', '#b6f27a', '#3f9a2b', '#8fd14f'),
    'tinkerer':        ('e', 'TIER 1', '#ffe27a', '#c98a1a', '#f0b429'),
    'engineer':        ('b', 'TIER 2', '#9be8ff', '#2b7fbf', '#4fc3f7'),
    'pioneer':         ('2', 'TIER 3', '#c9f7a8', '#2e7d32', '#66bb6a'),
    'cultivator':      ('c', 'TIER 4', '#ffb08a', '#b3261e', '#ff7043'),
    'industrialist':   ('5', 'TIER 5', '#e4b8ff', '#6a1b9a', '#ba68c8'),
    'tycoon':          ('6', 'TIER 6', '#fff3b0', '#d4a017', '#ffd54f'),
}
GROUP_THEME = {'mods_island': 'b', 'mods_frontier': 'a', 'mods_endgame': 'd', 'reference': 'e'}
GROUP_BANNER = {'mods_island': ('#9be8ff', '#2b7fbf', '#4fc3f7'), 'mods_frontier': ('#c9f7a8', '#2e7d32', '#66bb6a'),
                'mods_endgame': ('#e4b8ff', '#6a1b9a', '#ba68c8'), 'reference': ('#fff3b0', '#d4a017', '#ffd54f')}

BANNERS = {}
for ch in CHAPTERS:
    if ch['key'] in THEMES:
        code, tier, top, bottom, accent = THEMES[ch['key']]
        ch['theme'], ch['tier_label'] = code, tier
        BANNERS[ch['key']] = {'title': ch['title'].upper(), 'subtitle': tier + ' - ' + ch['subtitle'].split('.')[0].split(', ')[-1].upper(),
                              'top': top, 'bottom': bottom, 'accent': accent}
    else:
        ch['theme'] = GROUP_THEME[ch['group']]
        top, bottom, accent = GROUP_BANNER[ch['group']]
        unlock = [part.strip(' .') for part in ch['subtitle'].split('. ') if 'nlock' in part]
        BANNERS[ch['key']] = {'title': ch['title'].upper(), 'subtitle': unlock[0].upper() if unlock else '',
                              'top': top, 'bottom': bottom, 'accent': accent}
