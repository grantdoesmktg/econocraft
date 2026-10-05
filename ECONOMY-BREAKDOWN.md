# What the economy rewards, tier by tier

From `tools/pacing_sim.py` (PACING-REPORT.md has the full tables). The simulator credits every coin to the setup or
activity that produced it, for three players: a **Rusher** (progression only), a **Typical** player and an
**Explorer** (40% of play time spent exploring and building). Shares are of the coins earned during that tier.
These are model results: machine outputs and hand speeds are estimates, and only the setups listed in the
script can earn.

## Tier by tier

| Tier | What pays (Typical player) | Range across players |
|---|---|---|
| 0 Castaway | Cobblestone generators selling raw cobble 94%, hand sieving 6% | cobble 64-97% |
| 1 Tinkerer | Cobble generators 49%, hand sieving 40%, precision mechanisms 10% | hand sieving 22-52% |
| 2 Engineer | A mix: cobble 23%, mob farm 22%, auto-sieves 17%, precision mechanisms 17%, hand sieving 14% | the most varied tier |
| 3 Pioneer | **Auto-sieves 70%**, mob farm 14%, Frontier mining 6% | auto-sieves 54-77%; Frontier mining 0-21% |
| 4 Cultivator | **Auto-sieves 71%**, Nether raids 17%, mob farm 8% | auto-sieves 60-81%; Nether 6-30% |
| 5 Industrialist | **HNN twilight simulation chambers 48%**, auto-sieves 32%, Twilight bosses 14% | bosses 5-31% |
| 6 Tycoon | HNN chambers 44%, auto-sieves 27%, Twilight bosses 24% | bosses 13-42% |

## What that means

1. **The real engine is one setup copied many times.** From the Frontier on, a row of 16 auto-sieves fed by
   cobble generators earns most of the money, even after the sieve cut. The economy rewards scale more than variety.
2. **Raw cobblestone is the opening economy.** Four cheap generators selling cobble at 1 coin outearn everything
   else at tier 0 and still matter at tier 2. It's simple and works, but it's the least interesting thing in the pack.
3. **The Frontier is mostly an unlock, not a payday.** Mining and exploring only pay well for a player who goes
   out on purpose (21% for the Rusher, 6% for Typical, almost nothing for the Explorer). Most players earn their
   Frontier-tier money back home at the sieves.
4. **Fighting pays at the top.** Twilight bosses are 14-42% of late income, and the Nether is a real option at tier 4.
5. **These setups earn nothing worth buying:** power of any kind, Mystical Agriculture (essence prices are too
   low to pay back seeds and pots), Botany Pots, fish traps, villager crop farms, feasts, most of Create beyond
   precision mechanisms and brass, and the Mekanism ore ladder (a small boost on top of sieving). AE2 and
   Industrial Foregoing are quality of life by design.

## Power: not rewarded today

Generators are a pure cost. Nothing turns energy into coins except indirectly (HNN chambers and Mekanism need power,
but the simulator doesn't even count it). A big reactor build earns exactly as much as no reactor.

**The cleanest way to reward power is Powah's Energizing Orb.** Its recipes state their energy cost, and the orb's
throughput is capped by the energizing rods, so it can't run away:

| Item | Inputs | Energy |
|---|---|---|
| Charged Snowball | 1 snowball (snow golems make them for free) | 500,000 FE |
| Blazing Crystal | 1 blaze rod | 120,000 FE |
| Niotic Crystal | 1 diamond | 300,000 FE |
| Spirited Crystal | 1 emerald | 1,000,000 FE |
| Nitro Crystal (x16) | nether star, 2 redstone blocks, blazing crystal block | 20,000,000 FE |

Price each one at its inputs plus a fixed rate per FE, in a new "power" sell category with its own price drop-off.
The charged snowball becomes pure power-to-coins (a snow golem farm feeding an orb), and the crystals give a reason to
build bigger reactors. Mekanism antimatter pellets could be a top-end extra. The coins-per-FE rate is the key number
and needs care, because late-game generators make enormous amounts of energy; I'd add power setups to the simulator
and pick the rate there before shipping.
