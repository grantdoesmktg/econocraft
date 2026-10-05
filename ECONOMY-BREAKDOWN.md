# What the economy rewards, tier by tier

From `tools/pacing_sim.py` (PACING-REPORT.md has the full tables). The simulator credits every coin to the setup or
activity that produced it, for three players: a **Rusher** (progression only), a **Typical** player and an
**Explorer** (40% of play time spent exploring and building). Shares are of the coins earned during that tier.
These are model results: machine outputs and hand speeds are estimates, and only the setups listed in the
script can earn.

## Tier by tier (after the 2026-10-05 rebalance: sieves cut to x0.35 ore / x0.45 gems, Power Exchange added)

| Tier | What pays (Typical player) | Notes across players |
|---|---|---|
| 0 Castaway | Cobblestone generators 95%, hand farming 5% | the same for everyone |
| 1 Tinkerer | Cobble generators 56%, hand sieving 35%, precision mechanisms 9% | Rusher sieves more by hand (47%) |
| 2 Engineer | Cobble 30%, **Cyclic generators into the Power Exchange 28%**, mob farm 18%, precision mechanisms 11% | power 23-38% |
| 3 Pioneer | **Frontier mining 26%**, Cyclic power 20%, mob farm 16%, iron golem farm 15% | Frontier mining 12-40% |
| 4 Cultivator | **Nether raids 24%**, auto-sieves 17%, iron golem farm 14%, power 13%, mob farm 12% | the most varied tier |
| 5 Industrialist | **Reactor + turbine 46%**, HNN chambers 31%, Twilight bosses 9% | bosses 0-23% |
| 6 Tycoon | **Reinforced reactor 50%**, HNN 18%, reactors 16%, bosses 8% | power 60-70% |

Auto-sieves now earn 4-21% from tier 4 on (they were 54-81%). Time to tier 6: Rusher 21.7 h, Typical 27.6 h,
Explorer 31.8 h.

## Before the rebalance (gates x2, sieves x0.5)

| Tier | What paid (Typical player) |
|---|---|
| 0 | Cobblestone generators 94%, hand sieving 6% |
| 1 | Cobble generators 49%, hand sieving 40%, precision mechanisms 10% |
| 2 | Cobble 23%, mob farm 22%, auto-sieves 17%, precision mechanisms 17%, hand sieving 14% |
| 3 | **Auto-sieves 70%**, mob farm 14%, Frontier mining 6% |
| 4 | **Auto-sieves 71%**, Nether raids 17%, mob farm 8% |
| 5 | HNN twilight chambers 48%, auto-sieves 32%, Twilight bosses 14% |
| 6 | HNN chambers 44%, auto-sieves 27%, Twilight bosses 24% |

## What the old numbers meant (fixed by the rebalance)

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

## Power: the Power Exchange (Economy Core 0.9.6)

A block sold in the Supply Market at tier 2 for 5,000. Pipe FE in from any mod and the team earns coins every second,
counted as lifetime earnings. All of a team's exchanges share one curve, so more blocks don't pay more:

coins per minute = 70 x (team FE per tick / 100) ^ 0.6  (power_base and power_exponent in market.json)

| Team power | Coins per minute |
|---|---|
| 100 FE/t (one Cyclic generator) | ~70 |
| 1,000 FE/t | ~280 |
| 10,000 FE/t | ~1,100 |
| 100,000 FE/t (big reactor) | ~4,400 |
| 1,000,000 FE/t (Draconic) | ~17,600 |

Every 10x more power pays about 4x more. The Powah Energizing Orb idea (pricing charged snowballs and crystals) is
no longer needed for this, but still works as a later extra.
