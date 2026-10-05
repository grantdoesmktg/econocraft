# Economy Pack (Econocraft): notes for Claude sessions

Read `HANDOFF.md` first (status, open items, what needs an in-game check), then `DESIGN-NOTES.md` (decisions).
Grant prefers that you run commands yourself, show a plan before big builds, and give exact in-game commands.

## Cloud sessions (the usual case)
There's no Minecraft here, so the loop is: change generators or mod code, verify with the tools and a build,
commit, push `main`, and tell Grant what to check in game. Add those checks to HANDOFF.md "Needs an in-game check".

- **Pushing `main` ships to players.** Grant's Prism instance installs from
  https://raw.githubusercontent.com/grantdoesmktg/econocraft/main/pack.toml on every launch. Push only working states.
- **packwiz**: if `packwiz` isn't installed, `go install github.com/packwiz/packwiz@latest` (binary in ~/go/bin).
  Run `packwiz refresh` after any change to pack files, before committing. Generated docs are in `.packwizignore`.
- **Tools** (`python3 tools/<name>.py`, standard library only): they fall back to the committed snapshots in
  `tools/data/` when the Prism instance isn't present. The snapshot is the game as of its last export; new recipes or
  mods won't show in `analyze_progression.py` until Grant re-exports.
  - `market_catalog.py`: sell prices, shop, market.json, MARKET.md
  - `build_locks.py`: tier locks (ProgressiveStages rules) and recipe removals (KubeJS)
  - `build_sieve.py`: sieve drop scaling (KubeJS); never rescale from a fresh export, it's already scaled
  - `build_quests.py` + `quest_content.py`: the FTB Quests book
  - `pacing_sim.py`: time to each tier for three player types -> PACING-REPORT.md (keep POWER_BASE/EXP and GATES
    in sync with market_catalog.py and quest_content.py)
  - `analyze_progression.py`: tier skips, gaps and money loops -> PROGRESSION-REPORT.md
- **Building the mod in the cloud**: cloud containers can't reach maven.neoforged.net, so push the change to a
  branch named `mod-build/<version>`. GitHub Actions (.github/workflows/build-mod.yml) builds it, swaps the jar into
  mods/, runs packwiz refresh and commits back to that branch; fetch it, check, then fast-forward main.
- **Economy Core** (`economy-core/`): needs Java 21. `./fetch_libs.sh`, bump `mod_version`, `./gradlew build`, then
  replace `mods/economy_core-*.jar` with the new jar and `packwiz refresh`. Gate numbers also live in the mod
  (ShopScreen.GATES, MarketConfig defaults, data/economy_core/advancement/earned/).
- **Releases**: bump `version` in pack.toml, refresh, commit, push, `git tag vX && git push origin vX`,
  `gh release create vX --prerelease`. Don't attach an .mrpack (it would bundle CurseForge-only mods).
- Quest text: escape `&` as `\&`; quest ids are generated from keys, so renaming a key resets that quest's progress.

## On Grant's Mac
Same repo at ~/Modpacks/economy-pack. The Prism instance "Economy Test" pulls from GitHub. ~/Modpacks/server-test is a
local dedicated server for boot tests. After in-game changes, `/kubejs export debug` then
`python3 tools/paths.py --snapshot` refreshes the cloud snapshot.
