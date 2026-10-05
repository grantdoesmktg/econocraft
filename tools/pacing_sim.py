"""
Pacing simulator for the Economy Pack: plays an efficient player minute by minute and reports how long each tier takes.

Run:  python3 tools/pacing_sim.py            -> PACING-REPORT.md
      python3 tools/pacing_sim.py --hours 60  (simulate longer)

What is real (read from the pack):
  - sell prices, categories, soft caps and variety recovery (market_catalog.py, same math as Economy Core's PriceMath)
  - shop machine prices (market_catalog.MACHINES / SUPPLIES)
  - tier gates (lifetime earnings + coin fee)
  - Ex Deorum sieve odds per mesh (from the KubeJS export), FTB cobble generator / auto-hammer and
    Ex Compressum auto-sieve speeds (from the instance configs)

What is assumed (the RATES / ACTIVITIES / LINES tables below): how fast a player works by hand, and what a
machine line produces. Tweak those and rerun. The player is efficient but not a speedrunner: no exploits,
no money loops beyond what the shop allows, and play time only (machines don't run while offline).
"""
import argparse
import glob
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import build_sieve  # noqa: E402
import market_catalog as M  # noqa: E402

PACK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import paths  # noqa: E402
EXPORT = paths.export_dir()

# Target pace: cumulative play hours to reach each tier (low, high). Outside this range gets flagged.
TARGET_HOURS = {1: (1, 2), 2: (3, 5), 3: (6, 10), 4: (10, 15), 5: (15, 20), 6: (20, 30)}

GATES = {1: (4_000, 2_000), 2: (24_000, 10_000), 3: (96_000, 40_000), 4: (350_000, 80_000),
         5: (1_050_000, 150_000), 6: (2_800_000, 300_000)}

# ------------------------------------------------------------------ prices (mirror of Economy Core PriceMath)

SELL = {s[0]: s for s in M.SELL}
CATS = M.SELL_CATEGORIES
VARIETY = M.MARKET_TIERS  # (variety, min_units, min_value) per tier


def price_of(item):
    return SELL[item][3]


def max_drop(item):
    """How far below fair value a flooded price can fall; floors come from market_catalog."""
    return 1 - M.floor_of(SELL[item][2])


def sell_total(base, max_drop, soft_cap, s0, n):
    """Closed form of PriceMath.sell: total coins and end saturation for n units (n may be fractional)."""
    if n <= 0:
        return 0.0, s0
    q = math.exp(-1.0 / soft_cap)
    sum_s = n - (1 - s0) * (1 - q ** n) / (1 - q)
    total = base * (n - max_drop * sum_s)
    return total, 1 - (1 - s0) * q ** n


class Market:
    def __init__(self):
        self.sat = {}       # item -> saturation right after its last sale
        self.since = {}     # item -> set of distinct goods sold (qualifying) since

    def eff(self, item, tier):
        v = VARIETY[min(tier, len(VARIETY) - 1)][0]
        s = self.sat.get(item, 0.0)
        return s * max(0.0, 1 - len(self.since.get(item, ())) / v)

    def unit_price(self, item, tier):
        return price_of(item) * (1 - max_drop(item) * self.eff(item, tier))

    def sell(self, item, units, tier):
        if units <= 0:
            return 0.0
        _, min_units, min_value = VARIETY[min(tier, len(VARIETY) - 1)]
        cap = CATS[SELL[item][2]][0]
        coins, end = sell_total(price_of(item), max_drop(item), cap, self.eff(item, tier), units)
        self.sat[item] = end
        self.since[item] = set()
        if units >= min_units or coins >= min_value:
            for other, seen in self.since.items():
                if other != item:
                    seen.add(item)
        return coins


# ------------------------------------------------------------------ sieve odds from the game export

CHUNK_TO_INGOT = {'exdeorum:iron_ore_chunk': 'minecraft:iron_ingot', 'exdeorum:copper_ore_chunk': 'minecraft:copper_ingot',
                  'exdeorum:gold_ore_chunk': 'minecraft:gold_ingot', 'exdeorum:zinc_ore_chunk': 'create:zinc_ingot'}


def sieve_odds(block, mesh):
    out = {}
    for f in glob.glob(os.path.join(EXPORT, 'recipes', 'exdeorum', 'sieve', block, mesh, '*.json')):
        d = json.load(open(f))
        a = d['result_amount']
        n = a['n'] * a['p'] if isinstance(a, dict) and 'p' in a else (a.get('value', 1) if isinstance(a, dict) else a)
        out[d['result']['id']] = out.get(d['result']['id'], 0) + n * d['result'].get('count', 1)
    # Goods rescaled by tools/build_sieve.py: use the snapshot x scale, whatever state the export is in.
    for item in build_sieve.SCALE:
        out.pop(item, None)
    out.update(build_sieve.base_odds(block, mesh))
    return out


MESHES = [  # (mesh, tier available, cost)  -- iron mesh is tier-locked to 1, diamond sold at tier 2
    ('string', 0, 40), ('flint', 1, 150), ('iron', 1, 600), ('diamond', 2, 4000)]

# ------------------------------------------------------------------ assumptions

# Hand work: units per minute while the player is doing it.
HAND_SIEVE_OPS = 30        # gravel sifted per minute by hand, including making the gravel (mine cobble, hammer it)
AUTO_SIEVE_OPS = 60 * 20 * 0.0075   # Ex Compressum autoSieveSpeed 0.0075 progress/tick = 9 ops/min
COBBLE_GEN = 60            # FTB stone cobblestone generator: 1 per 20 ticks
AUTO_HAMMER = 60 * 20 / 50  # FTB iron auto-hammer: 50 ticks per block = 24/min
SETUP_MIN = 4              # play minutes spent placing and wiring each purchased line

# Active play at each tier: (tier, {item: units per minute while actually doing it}, travel minutes per active minute).
# Travel is getting there and back: walking to ore, finding structures, crossing the Nether, locating the next boss.
# The player spends every free minute on whichever activity pays best once travel is included.
TWILIGHT_KILL = {  # one Twilight boss kill (bosses come in order; trophy prices differ, so average over the eight)
    **{f'twilightforest:{b}_trophy': 1 / 8 for b in ('naga', 'lich', 'minoshroom', 'hydra', 'knight_phantom', 'ur_ghast',
                                                      'alpha_yeti', 'snow_queen')},
    'twilightforest:naga_scale': 1.5, 'twilightforest:steeleaf_ingot': 6, 'twilightforest:ironwood_ingot': 4,
    'twilightforest:knightmetal_ingot': 3, 'twilightforest:carminite': 1, 'twilightforest:fiery_ingot': 0.5}
BOSS_FIGHT_MIN = 10

ACTIVITIES = {
    'farm crops by hand': (0, {'minecraft:wheat': 6, 'minecraft:potato': 6, 'minecraft:carrot': 6, 'minecraft:sugar_cane': 6,
                               'minecraft:pumpkin': 1, 'minecraft:melon_slice': 6}, 0),
    'chop trees': (0, {'minecraft:oak_log': 10}, 0),
    'cook food': (1, {'farmersdelight:beef_stew': 0.6, 'farmersdelight:pasta_with_meatballs': 0.4}, 0),
    'mine the Frontier': (3, {'minecraft:diamond': 0.4, 'minecraft:emerald': 0.08, 'minecraft:iron_ingot': 2.2,
                              'minecraft:gold_ingot': 0.5, 'minecraft:redstone': 4, 'minecraft:lapis_lazuli': 2}, 0.15),
    'explore Frontier structures': (3, {'minecraft:rabbit_foot': 0.15, 'minecraft:iron_horse_armor': 0.05,
                                        'minecraft:golden_horse_armor': 0.03, 'minecraft:diamond_horse_armor': 0.015,
                                        'minecraft:heart_of_the_sea': 0.01, 'minecraft:totem_of_undying': 0.006,
                                        'minecraft:trident': 0.006, 'minecraft:echo_shard': 0.03, 'minecraft:sniffer_egg': 0.005,
                                        'minecraft:heavy_core': 0.003, 'minecraft:breeze_rod': 0.5, 'minecraft:goat_horn': 0.015,
                                        'minecraft:wet_sponge': 0.03, 'minecraft:turtle_scute': 0.03, 'minecraft:diamond': 0.15}, 0.6),
    'fish the Frontier (Aquaculture)': (3, {'aquaculture:tuna': 0.3, 'aquaculture:atlantic_halibut': 0.3, 'aquaculture:arapaima': 0.2,
                                            'aquaculture:catfish': 0.3, 'aquaculture:smallmouth_bass': 0.3,
                                            'minecraft:heart_of_the_sea': 0.002}, 0.1),
    # wither skulls get turned into Wither fights: 3 skulls -> 1 nether star (fight time folded into the rate)
    'raid the Nether': (4, {'minecraft:netherite_scrap': 0.12, 'minecraft:blaze_rod': 1.5, 'minecraft:ghast_tear': 0.2,
                            'minecraft:nether_star': 0.012, 'minecraft:quartz': 6}, 0.5),
    'hunt Twilight bosses': (5, {i: n / BOSS_FIGHT_MIN for i, n in TWILIGHT_KILL.items()}, 2.5),
    'raid the End': (5, {'minecraft:shulker_shell': 0.4, 'minecraft:elytra': 0.015, 'minecraft:dragon_head': 0.008,
                         'minecraft:dragon_breath': 0.2}, 1.0),
}

# One-off trips when a tier opens, in play minutes with no hand income (machines keep running):
# finding a village and biomes, building a Nether portal and finding a fortress, the Twilight portal and the End.
TRIPS = {3: ('scouting the Frontier', 20), 4: ('Nether portal and finding a fortress', 40),
         5: ('Twilight portal, stronghold and the Ender Dragon', 60)}

# Player profiles. hand: speed at hand work; travel: multiplier on travel and trips; roses: share of play time spent
# on things that don't earn (exploring mods, building, decorating); setup: minutes per machine bought; payback: how
# patient they are about buying machines (minutes).
PROFILES = {
    'Rusher': dict(hand=1.0, travel=1.0, roses=0.0, setup=4, payback=180,
                   desc='Only progression. Knows the pack, optimal routes, no detours.'),
    'Typical': dict(hand=0.75, travel=1.5, roses=0.2, setup=8, payback=180,
                    desc='Plays for progress but builds a base and tries things; a fifth of the time goes to non-earning play.'),
    'Explorer': dict(hand=0.6, travel=2.0, roses=0.4, setup=12, payback=180,
                     desc='Smells the roses: explores mods, builds, wanders. 40% of play time earns nothing directly.'),
}

# Machine lines the player can buy: name -> (tier, coin cost, max copies, {item: units/min}; negative = consumes).
# 'hand_sieve' outputs are added separately (they depend on the mesh owned and the ore multiplier).
LINES = {
    'cobble generator': (0, 300, 4, {'minecraft:cobblestone': COBBLE_GEN}),
    "fishermen's trap": (1, 1200 + 200, 6, {'minecraft:cod': 0.5, 'minecraft:salmon': 0.25, 'minecraft:tropical_fish': 0.1,
                                            'minecraft:pufferfish': 0.05}),
    'botany pot (potatoes)': (1, 600 + 12, 16, {'minecraft:potato': 1.0}),
    'precision mechanisms': (1, 3 * 2500 + 1500 + 800 + 1000, 1, {'minecraft:gold_ingot': -2, 'create:precision_mechanism': 2}),
    'mob farm': (2, 1500 + 800 + 2500, 4, {'minecraft:rotten_flesh': 4, 'minecraft:bone': 3, 'minecraft:string': 2,
                                           'minecraft:gunpowder': 1, 'minecraft:spider_eye': 1, 'minecraft:ender_pearl': 0.3}),
    # one auto-sieve plus the share of an iron auto-hammer (24/min) needed to keep it fed with gravel
    'auto-sieve': (2, 10000 + round(1200 * AUTO_SIEVE_OPS / AUTO_HAMMER), 16,
                   {'minecraft:cobblestone': -AUTO_SIEVE_OPS, 'sieve_ops': AUTO_SIEVE_OPS}),
    'brass mixing': (2, 3000 + 800 + 1500 + 800, 1, {'minecraft:copper_ingot': -2, 'create:zinc_ingot': -2, 'create:brass_ingot': 4}),
    'iron golem farm': (3, 15000, 8, {'minecraft:iron_ingot': 1.0}),
    'villager crop farm': (3, 5000 + 4000, 6, {'minecraft:wheat': 3, 'minecraft:potato': 3, 'minecraft:carrot': 3}),
    'Mystical Ag pot (prudentium)': (3, 600 + 2000 + 8000 / 8, 12, {'mysticalagriculture:prudentium_essence': 0.6}),
    'Mystical Ag pot (imperium)': (4, 600 + 9000, 12, {'mysticalagriculture:imperium_essence': 0.5}),
    'HNN simulation chamber': (4, 30000 + 5000 + 15000, 8, {'hostilenetworks:nether_prediction': 3}),
    'Mystical Ag pot (supremium)': (5, 600 + 25000, 12, {'mysticalagriculture:supremium_essence': 0.4}),
    'HNN twilight chamber': (5, 30000 + 5000 + 20000, 8, {'hostilenetworks:twilight_prediction': 3}),
}
# Power Exchange (Economy Core): team-wide FE/t in, coins out. coins/min = BASE * (FE_per_tick / 100) ** EXP.
POWER_BASE, POWER_EXP = 70.0, 0.6   # keep in sync with market_catalog.py (market.json)
EXCHANGE = ('Power Exchange', 2, 5000)


def exchange_coins(fe_per_tick):
    return POWER_BASE * (fe_per_tick / 100) ** POWER_EXP if fe_per_tick > 0 else 0.0


# Generators: (tier, cost incl. fuel automation, cap, {'FE': FE per tick}). Fuel is assumed self-sustaining.
POWER_LINES = {
    'Cyclic fuel generator': (2, 3000, 6, {'FE': 80}),
    'Mekanism heat generator': (4, 15000 + 3000, 8, {'FE': 80}),
    'Powah furnator + energy cell': (4, 6000 + 3000, 8, {'FE': 60}),
    'Create windmill + alternator': (4, 5000 + 8000, 6, {'FE': 400}),
    'Mekanism gas-burning generator': (5, 80000 + 20000, 4, {'FE': 4000}),
    'Extreme Reactors passive reactor': (5, 60000 + 60000, 2, {'FE': 8000}),
    'Extreme Reactors reactor + turbine': (5, 60000 + 50000 + 140000, 2, {'FE': 30000}),
    'Reinforced reactor + turbine': (6, 200000 + 200000, 2, {'FE': 100000}),
}
LINES.update(POWER_LINES)

ONE_OFFS = {'Create crushing wheels (ore x1.75)': (1, 2 * 2000 + 2 * 800 + 600, 1.75),
            'Mekanism enrichment (ore x2)': (4, 25000 + 30000 + 15000, 2.0)}
PAYBACK_LIMIT = 180   # only buy a line that pays for itself within this many minutes


# ------------------------------------------------------------------ simulation

def run(hours, hand=1.0, travel=1.0, roses=0.0, setup=SETUP_MIN, payback=None, **_):
    payback = payback or PAYBACK_LIMIT
    mk = Market()
    tier, balance, earned = 0, 250.0, 0.0   # starter kit: Market Crate + Supply Market + Time in a Bottle
    mesh = None
    ore_mult = 1.0
    owned = {k: 0 for k in LINES}
    one_offs = set()
    busy = 0
    busy_trip = [0]
    has_exchange = [False]
    roses_acc = 0.0
    log, tier_times, sources = [], {0: 0}, {}
    window = []
    by_item = {}
    by_source = {}

    def sieve_yield(ops):
        out = {}
        if not mesh:
            return out
        for item, n in ODDS[mesh].items():
            if item in CHUNK_TO_INGOT:
                ing = CHUNK_TO_INGOT[item]
                out[ing] = out.get(ing, 0) + n * ops / 4 * ore_mult
            elif item in SELL:
                out[item] = out.get(item, 0) + n * ops
        return out

    def value(flow):
        return sum(n * mk.unit_price(i, tier) for i, n in flow.items() if i in SELL and n > 0)

    def best_activity():
        options = {}
        if mesh:
            options['sieve by hand'] = sieve_yield(HAND_SIEVE_OPS * hand)
        for name, (t, flow, trav) in ACTIVITIES.items():
            if t <= tier:
                share = 1 / (1 + trav * travel)   # fraction of the time spent actually doing it
                options[name] = {i: n * hand * share for i, n in flow.items()}
        return max(options.items(), key=lambda kv: value(kv[1]))

    for minute in range(int(hours * 60)):
        # 1. Tier gate: pay as soon as it qualifies.
        nxt = tier + 1
        if nxt in GATES and earned >= GATES[nxt][0] and balance >= GATES[nxt][1]:
            balance -= GATES[nxt][1]
            tier = nxt
            tier_times[tier] = minute
            log.append((minute, f'**Tier {tier} ({M.TIERS[tier][0]})** reached; paid {GATES[tier][1]:,} gate fee'))
            if tier in TRIPS:
                trip = round(TRIPS[tier][1] * travel)
                busy_trip[0] += trip
                log.append((minute, f'{TRIPS[tier][0]} ({trip} min)'))
        saving_for_gate = nxt in GATES and earned >= GATES[nxt][0]

        # 2. Purchases: mesh upgrades, one-offs, then the best-payback line.
        for m, t, cost in MESHES:
            order = [x[0] for x in MESHES]
            if t <= tier and (mesh is None or order.index(m) > order.index(mesh)) and balance >= cost and not saving_for_gate:
                balance -= cost
                mesh = m
                log.append((minute, f'Bought {m} mesh ({cost:,})'))
        for name, (t, cost, mult) in ONE_OFFS.items():
            if name not in one_offs and t <= tier and balance >= cost and not saving_for_gate and earned > cost * 2:
                balance -= cost
                one_offs.add(name)
                ore_mult = max(ore_mult, mult)
                busy += setup
                log.append((minute, f'Bought {name} ({cost:,})'))
        if (not has_exchange[0] and tier >= EXCHANGE[1] and balance >= EXCHANGE[2] and not saving_for_gate
                and earned > EXCHANGE[2] * 2):
            balance -= EXCHANGE[2]
            has_exchange[0] = True
            busy += setup
            log.append((minute, f'Bought the {EXCHANGE[0]} ({EXCHANGE[2]:,})'))
        if not saving_for_gate:
            best, best_payback = None, payback
            for name, (t, cost, cap, flow) in LINES.items():
                if t > tier or owned[name] >= cap or cost > balance:
                    continue
                if name in POWER_LINES and not has_exchange[0]:
                    continue
                gain = line_gain(name, flow, owned, value, sieve_yield)
                if gain > 0 and cost / gain < best_payback:
                    best, best_payback = name, cost / gain
            if best:
                balance -= LINES[best][1]
                owned[best] += 1
                busy += setup
                if owned[best] in (1, 2, 4, 8, 12, 16):
                    log.append((minute, f'Bought {best} #{owned[best]} ({LINES[best][1]:,}, pays back in {best_payback:.0f} min)'))

        # 3. Production this minute: raw lines, hand work, then converters (cobble -> gravel -> sieves, gold -> mechanisms).
        pool = {}
        share = {}   # item -> {source: units}, to credit sales to the setup that made them

        def add(item, n, src):
            pool[item] = pool.get(item, 0) + n
            if n > 0:
                share.setdefault(item, {})
                share[item][src] = share[item].get(src, 0) + n

        def take(item, n):
            have = pool.get(item, 0)
            pool[item] = have - n
            if have > 0 and item in share:
                keep = max(0.0, 1 - n / have)
                share[item] = {k: v * keep for k, v in share[item].items()}

        def is_converter(name):
            return any(r < 0 and i in SELL for i, r in LINES[name][3].items())

        for name, n in owned.items():
            if n and not is_converter(name):
                for item, rate in LINES[name][3].items():
                    add(item, rate * n, name)
        roses_acc += roses
        if busy_trip[0] > 0:
            busy_trip[0] -= 1
            activity = 'travel: opening a new area'
        elif busy > 0:
            busy -= 1
            activity = 'setting up machines'
        elif roses_acc >= 1:
            roses_acc -= 1
            activity = 'exploring and building (no income)'
        else:
            activity, flow = best_activity()
            for item, n in flow.items():
                add(item, n, activity)
        for name, n in owned.items():
            if not n or not is_converter(name):
                continue
            flow = LINES[name][3]
            ins = {i: -r * n for i, r in flow.items() if r < 0}
            frac = min(1.0, *(pool.get(i, 0) / need for i, need in ins.items()))
            for i, need in ins.items():
                take(i, need * frac)
            for i, r in flow.items():
                if r > 0:
                    add(i, r * n * frac, name)
        share.pop('sieve_ops', None)
        for item, n in sieve_yield(pool.pop('sieve_ops', 0)).items():
            add(item, n, 'auto-sieve')
        # 4. Sell everything sellable, and cash in power at the exchange.
        got = 0.0
        fe = pool.pop('FE', 0) if has_exchange[0] else 0
        if fe:
            c = exchange_coins(fe)
            got += c
            by_item[(tier, 'power')] = by_item.get((tier, 'power'), 0) + c
            for src, u in share.pop('FE', {}).items():
                by_source[(tier, src)] = by_source.get((tier, src), 0) + c * u / fe
        pool.pop('FE', None)
        for item, n in pool.items():
            if item in SELL and n > 0:
                c = mk.sell(item, n, tier)
                got += c
                by_item[(tier, item)] = by_item.get((tier, item), 0) + c
                srcs = share.get(item, {})
                tot = sum(srcs.values()) or 1
                for src, u in srcs.items():
                    by_source[(tier, src)] = by_source.get((tier, src), 0) + c * u / tot
        balance += got
        earned += got
        sources[(tier, activity)] = sources.get((tier, activity), 0) + 1
        window.append(got)
        if tier == 6 and minute - tier_times[6] > 60:
            break
    return dict(log=log, tier_times=tier_times, owned=owned, earned=earned, sources=sources, window=window,
                mesh=mesh, minutes=minute + 1, by_item=by_item, by_source=by_source)


def line_gain(name, flow, owned, value, sieve_yield):
    """Coins per minute one more copy of this line would add, at current prices."""
    if 'FE' in flow:
        fe = sum(LINES[n][3].get('FE', 0) * k for n, k in owned.items())
        return exchange_coins(fe + flow['FE']) - exchange_coins(fe)
    if name == 'auto-sieve':
        cobble = owned['cobble generator'] * COBBLE_GEN - owned[name] * AUTO_SIEVE_OPS
        if cobble < AUTO_SIEVE_OPS:
            return 0
        return value(sieve_yield(AUTO_SIEVE_OPS)) - value({'minecraft:cobblestone': AUTO_SIEVE_OPS})
    outs = {i: r for i, r in flow.items() if r > 0}
    ins = {i: -r for i, r in flow.items() if r < 0}
    if ins:
        return max(0.0, value(outs) - value(ins)) * 0.5   # converters are limited by supply; be conservative
    return value(outs)


ODDS = {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--hours', type=float, default=100)
    args = ap.parse_args()
    for m, _, _ in MESHES:
        ODDS[m] = sieve_odds('gravel', m)
    if not ODDS['string']:
        sys.exit(f'No sieve recipes found under {EXPORT}. Run /kubejs export debug in game first.')
    results = {name: run(args.hours, **prof) for name, prof in PROFILES.items()}
    write_report(results, args.hours)


def fmt_h(m):
    return f'{m / 60:.1f} h'


def write_report(results, hours):
    L = ['# Economy Pack: Pacing Report', '',
         'Generated by `tools/pacing_sim.py`: players simulated minute by minute against the real prices, price',
         'drop-off, shop costs, tier gates and sieve odds. Hand speeds, travel and machine outputs are estimates',
         '(tables at the top of the script). Play time only; machines are assumed off while nobody is online.', '',
         '## Profiles', '']
    for name, prof in PROFILES.items():
        L.append(f'- **{name}**: {prof["desc"]} (hand speed x{prof["hand"]}, travel x{prof["travel"]}, '
                 f'{int(prof["roses"] * 100)}% non-earning play)')
    L += ['', '## Play hours to reach each tier', '',
          '| Tier | ' + ' | '.join(results) + ' | Target |', '|---|' + '---|' * len(results) + '---|']
    for t in range(1, 7):
        cells = [fmt_h(r['tier_times'][t]) if t in r['tier_times'] else f'>{hours:.0f} h' for r in results.values()]
        lo, hi = TARGET_HOURS[t]
        L.append(f'| {t} {M.TIERS[t][0]} | ' + ' | '.join(cells) + f' | {lo}-{hi} h |')
    for name, r in results.items():
        tt = r['tier_times']
        L += ['', f'## {name}', '', '### Where the time went', '', '| Tier | Activity | Minutes |', '|---|---|---|']
        for (t, a), n in sorted(r['sources'].items()):
            L.append(f'| {t} | {a} | {n} |')
        L += ['', '### Which setups made the money (share of each tier\'s earnings)', '', '| Tier | Earned in tier | Setups |', '|---|---|---|']
        for t in range(7):
            rows = sorted(((c, src) for (tt_, src), c in r['by_source'].items() if tt_ == t), reverse=True)
            total = sum(c for c, _ in rows)
            if total:
                L.append(f'| {t} | {total:,.0f} | ' + '; '.join(f'{src} {100 * c / total:.0f}%' for c, src in rows[:6] if c / total >= 0.02) + ' |')
        L += ['', '### Where the money came from (top 5 goods per tier)', '', '| Tier | Good | Coins | Share |', '|---|---|---|---|']
        for t in range(7):
            rows = sorted(((c, i) for (tt_, i), c in r['by_item'].items() if tt_ == t), reverse=True)
            total = sum(c for c, _ in rows) or 1
            for c, i in rows[:5]:
                L.append(f'| {t} | {SELL[i][1] if i in SELL else "Power Exchange"} | {c:,.0f} | {100 * c / total:.0f}% |')
        L += ['', '### Timeline', '']
        L += [f'- {m // 60}h{m % 60:02d}: {e}' for m, e in r['log']]
    L.append('')
    out = os.path.join(PACK, 'PACING-REPORT.md')
    open(out, 'w').write('\n'.join(L))
    print(f'Wrote {out}')
    for name, r in results.items():
        print(f'  {name:9s}', ' '.join(f't{t}:{v / 60:.1f}' for t, v in r['tier_times'].items() if t))


if __name__ == '__main__':
    main()
