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
import market_catalog as M  # noqa: E402

PACK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPORT = os.path.expanduser('~/Library/Application Support/PrismLauncher/instances/Economy Test/minecraft/local/kubejs/export')

# Target pace: cumulative play hours to reach each tier (low, high). Outside this range gets flagged.
TARGET_HOURS = {1: (1, 2), 2: (3, 5), 3: (6, 10), 4: (10, 15), 5: (15, 20), 6: (20, 30)}

GATES = {1: (2_000, 1_000), 2: (12_000, 5_000), 3: (48_000, 20_000), 4: (175_000, 40_000),
         5: (525_000, 75_000), 6: (1_400_000, 150_000)}

# ------------------------------------------------------------------ prices (mirror of Economy Core PriceMath)

SELL = {s[0]: s for s in M.SELL}
CATS = M.SELL_CATEGORIES
VARIETY = M.MARKET_TIERS  # (variety, min_units, min_value) per tier


def price_of(item):
    return SELL[item][3]


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
        return price_of(item) * (1 - 0.5 * self.eff(item, tier))

    def sell(self, item, units, tier):
        if units <= 0:
            return 0.0
        _, min_units, min_value = VARIETY[min(tier, len(VARIETY) - 1)]
        cap = CATS[SELL[item][2]][0]
        coins, end = sell_total(price_of(item), 0.5, cap, self.eff(item, tier), units)
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

# Active play at each tier: {item: units per minute}. The player spends every free minute on the best one.
ACTIVITIES = {
    'farm crops by hand': (0, {'minecraft:wheat': 6, 'minecraft:potato': 6, 'minecraft:carrot': 6, 'minecraft:sugar_cane': 6,
                               'minecraft:pumpkin': 1, 'minecraft:melon_slice': 6}),
    'chop trees': (0, {'minecraft:oak_log': 10}),
    'cook food': (1, {'farmersdelight:beef_stew': 0.6, 'farmersdelight:pasta_with_meatballs': 0.4}),
    'mine the Frontier': (3, {'minecraft:diamond': 0.35, 'minecraft:emerald': 0.08, 'minecraft:iron_ingot': 2,
                              'minecraft:gold_ingot': 0.5, 'minecraft:redstone': 4, 'minecraft:lapis_lazuli': 2}),
    'explore Frontier structures': (3, {'minecraft:rabbit_foot': 0.08, 'minecraft:iron_horse_armor': 0.03,
                                        'minecraft:golden_horse_armor': 0.02, 'minecraft:diamond_horse_armor': 0.01,
                                        'minecraft:heart_of_the_sea': 0.006, 'minecraft:totem_of_undying': 0.004,
                                        'minecraft:trident': 0.004, 'minecraft:echo_shard': 0.02, 'minecraft:sniffer_egg': 0.003,
                                        'minecraft:heavy_core': 0.002, 'minecraft:breeze_rod': 0.3, 'minecraft:goat_horn': 0.01,
                                        'minecraft:wet_sponge': 0.02, 'minecraft:turtle_scute': 0.02, 'minecraft:diamond': 0.1}),
    'fish the Frontier (Aquaculture)': (3, {'aquaculture:tuna': 0.3, 'aquaculture:atlantic_halibut': 0.3, 'aquaculture:arapaima': 0.2,
                                            'aquaculture:catfish': 0.3, 'aquaculture:smallmouth_bass': 0.3, 'minecraft:heart_of_the_sea': 0.002}),
    'raid the Nether': (4, {'minecraft:netherite_scrap': 0.1, 'minecraft:blaze_rod': 1.2, 'minecraft:ghast_tear': 0.15,
                            'minecraft:wither_skeleton_skull': 0.04, 'minecraft:quartz': 6}),
    'hunt Twilight bosses': (5, {'twilightforest:naga_trophy': 0.004, 'twilightforest:lich_trophy': 0.004,
                                 'twilightforest:minoshroom_trophy': 0.003, 'twilightforest:hydra_trophy': 0.003,
                                 'twilightforest:knight_phantom_trophy': 0.003, 'twilightforest:ur_ghast_trophy': 0.002,
                                 'twilightforest:alpha_yeti_trophy': 0.003, 'twilightforest:snow_queen_trophy': 0.002,
                                 'twilightforest:naga_scale': 0.05, 'twilightforest:steeleaf_ingot': 0.5,
                                 'twilightforest:ironwood_ingot': 0.3, 'twilightforest:knightmetal_ingot': 0.2,
                                 'twilightforest:carminite': 0.1, 'twilightforest:fiery_ingot': 0.03}),
    'fight the Wither': (4, {'minecraft:nether_star': 0.008}),
    'raid the End': (5, {'minecraft:shulker_shell': 0.3, 'minecraft:elytra': 0.01, 'minecraft:dragon_head': 0.005,
                         'minecraft:dragon_breath': 0.2}),
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
ONE_OFFS = {'Create crushing wheels (ore x1.75)': (1, 2 * 2000 + 2 * 800 + 600, 1.75),
            'Mekanism enrichment (ore x2)': (4, 25000 + 30000 + 15000, 2.0)}
PAYBACK_LIMIT = 180   # only buy a line that pays for itself within this many minutes


# ------------------------------------------------------------------ simulation

def run(hours, hand=1.0):
    mk = Market()
    tier, balance, earned = 0, 250.0, 0.0   # starter kit: Market Crate + Supply Market + Time in a Bottle
    mesh = None
    ore_mult = 1.0
    owned = {k: 0 for k in LINES}
    one_offs = set()
    busy = 0
    log, tier_times, sources = [], {0: 0}, {}
    window = []
    by_item = {}

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
        for name, (t, flow) in ACTIVITIES.items():
            if t <= tier:
                options[name] = {i: n * hand for i, n in flow.items()}
        return max(options.items(), key=lambda kv: value(kv[1]))

    for minute in range(int(hours * 60)):
        # 1. Tier gate: pay as soon as it qualifies.
        nxt = tier + 1
        if nxt in GATES and earned >= GATES[nxt][0] and balance >= GATES[nxt][1]:
            balance -= GATES[nxt][1]
            tier = nxt
            tier_times[tier] = minute
            log.append((minute, f'**Tier {tier} ({M.TIERS[tier][0]})** reached; paid {GATES[tier][1]:,} gate fee'))
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
                busy += SETUP_MIN
                log.append((minute, f'Bought {name} ({cost:,})'))
        if not saving_for_gate:
            best, best_payback = None, PAYBACK_LIMIT
            for name, (t, cost, cap, flow) in LINES.items():
                if t > tier or owned[name] >= cap or cost > balance:
                    continue
                gain = line_gain(name, flow, owned, value, sieve_yield)
                if gain > 0 and cost / gain < best_payback:
                    best, best_payback = name, cost / gain
            if best:
                balance -= LINES[best][1]
                owned[best] += 1
                busy += SETUP_MIN
                if owned[best] in (1, 2, 4, 8, 12, 16):
                    log.append((minute, f'Bought {best} #{owned[best]} ({LINES[best][1]:,}, pays back in {best_payback:.0f} min)'))

        # 3. Production this minute: raw lines, hand work, then converters (cobble -> gravel -> sieves, gold -> mechanisms).
        pool = {}

        def is_converter(name):
            return any(r < 0 and i in SELL for i, r in LINES[name][3].items())

        for name, n in owned.items():
            if n and not is_converter(name):
                for item, rate in LINES[name][3].items():
                    pool[item] = pool.get(item, 0) + rate * n
        if busy > 0:
            busy -= 1
            activity = 'setting up machines'
        else:
            activity, flow = best_activity()
            for item, n in flow.items():
                pool[item] = pool.get(item, 0) + n
        for name, n in owned.items():
            if not n or not is_converter(name):
                continue
            flow = LINES[name][3]
            ins = {i: -r * n for i, r in flow.items() if r < 0}
            frac = min(1.0, *(pool.get(i, 0) / need for i, need in ins.items()))
            for i, need in ins.items():
                pool[i] = pool.get(i, 0) - need * frac
            for i, r in flow.items():
                if r > 0:
                    pool[i] = pool.get(i, 0) + r * n * frac
        for item, n in sieve_yield(pool.pop('sieve_ops', 0)).items():
            pool[item] = pool.get(item, 0) + n
        # 4. Sell everything sellable.
        got = 0.0
        for item, n in pool.items():
            if item in SELL and n > 0:
                c = mk.sell(item, n, tier)
                got += c
                by_item[(tier, item)] = by_item.get((tier, item), 0) + c
        balance += got
        earned += got
        sources[(tier, activity)] = sources.get((tier, activity), 0) + 1
        window.append(got)
        if tier == 6 and minute - tier_times[6] > 60:
            break
    return dict(log=log, tier_times=tier_times, owned=owned, earned=earned, sources=sources, window=window,
                mesh=mesh, minutes=minute + 1, by_item=by_item)


def line_gain(name, flow, owned, value, sieve_yield):
    """Coins per minute one more copy of this line would add, at current prices."""
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
    ap.add_argument('--hours', type=float, default=40)
    args = ap.parse_args()
    for m, _, _ in MESHES:
        ODDS[m] = sieve_odds('gravel', m)
    if not ODDS['string']:
        sys.exit(f'No sieve recipes found under {EXPORT}. Run /kubejs export debug in game first.')
    r = run(args.hours)
    write_report(r, args.hours)


def write_report(r, hours):
    tt = r['tier_times']
    L = ['# Economy Pack: Pacing Report', '',
         'Generated by `tools/pacing_sim.py`: an efficient player simulated minute by minute against the real prices,',
         'price drop-off, shop costs and tier gates. Hand speeds and machine outputs are estimates (tables at the top',
         'of the script). Play time only; machines are assumed off while nobody is online.', '',
         '## Time to each tier', '',
         '| Tier | Reached at (play hours) | Time in previous tier | Target | Verdict |', '|---|---|---|---|---|']
    prev = 0
    for t in range(1, 7):
        lo, hi = TARGET_HOURS[t]
        if t in tt:
            h = tt[t] / 60
            verdict = 'too fast' if h < lo else ('too slow' if h > hi else 'on target')
            L.append(f'| {t} {M.TIERS[t][0]} | {h:.1f} | {(tt[t] - prev) / 60:.1f} h | {lo}-{hi} h | {verdict} |')
            prev = tt[t]
        else:
            L.append(f'| {t} {M.TIERS[t][0]} | not reached in {hours:.0f} h | | {lo}-{hi} h | **too slow** |')
    L += ['', '## Income rate', '', '| Play hour | Coins earned that hour |', '|---|---|']
    w = r['window']
    for h in range(0, len(w) // 60 + 1, max(1, len(w) // 60 // 20 or 1)):
        L.append(f'| {h} | {sum(w[h * 60:(h + 1) * 60]):,.0f} |')
    L += ['', '## Where the money came from (top 5 goods per tier)', '', '| Tier | Good | Coins | Share |', '|---|---|---|---|']
    for t in range(7):
        rows = sorted(((c, i) for (tt_, i), c in r['by_item'].items() if tt_ == t), reverse=True)
        total = sum(c for c, _ in rows) or 1
        for c, i in rows[:5]:
            L.append(f'| {t} | {SELL[i][1]} | {c:,.0f} | {100 * c / total:.0f}% |')
    L += ['', '## What the player spent time on', '', '| Tier | Activity | Minutes |', '|---|---|---|']
    for (t, a), n in sorted(r['sources'].items()):
        L.append(f'| {t} | {a} | {n} |')
    L += ['', '## Machines owned at the end', '']
    L += [f'- {n}x {name}' for name, n in r['owned'].items() if n] or ['None']
    L += ['', '## Timeline', '']
    L += [f'- {m // 60}h{m % 60:02d}: {e}' for m, e in r['log']]
    L.append('')
    out = os.path.join(PACK, 'PACING-REPORT.md')
    open(out, 'w').write('\n'.join(L))
    print(f'Wrote {out}')
    for t in range(1, 7):
        print(f'  tier {t}: ' + (f'{tt[t] / 60:.1f} h' if t in tt else 'not reached'))


if __name__ == '__main__':
    main()
