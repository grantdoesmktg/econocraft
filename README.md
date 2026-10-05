# Economy Pack (Econocraft)

A Minecraft 1.21.1 NeoForge modpack built around a coin economy. You start on a tiny island in the void, sell
what you produce at the Market Crate, buy machines from the Supply Market, and climb seven tiers, from Castaway
to Tycoon. On the way you buy access to the real overworld (the Frontier), the Nether, the End and the Twilight Forest.

- Minecraft 1.21.1, NeoForge 21.1.252, about 135 mods
- Single player or multiplayer: balances, tiers and quests are shared per FTB team
- Includes the Economy Core companion mod plus a full FTB Quests guide book
- Optional shaders (Iris): Good, Better and Best packs included

## Play it

### Prism Launcher (auto-updates)
1. Install [Prism Launcher](https://prismlauncher.org/) and Java 21.
2. Create an instance: **Minecraft 1.21.1**, loader **NeoForge 21.1.252**.
3. Download [packwiz-installer-bootstrap.jar](https://github.com/packwiz/packwiz-installer-bootstrap/releases/latest)
   and put it in the instance's `minecraft` folder (Edit instance > Open .minecraft).
4. Edit instance > Settings > Custom commands > **Pre-launch command**:
   ```
   "$INST_JAVA" -jar packwiz-installer-bootstrap.jar https://raw.githubusercontent.com/grantdoesmktg/econocraft/main/pack.toml
   ```
5. Give it at least 6 GB of memory (Settings > Java), then launch. Every launch pulls the latest pack.

### Shaders
Options > Video Settings > Shader Packs (or press **O**):
1. **Good**: MakeUp UltraFast. Light, works on almost anything.
2. **Better**: Complementary Reimagined. Close to vanilla, prettier.
3. **Best**: Complementary Unbound. The most dramatic and the heaviest.

## Run a server
Needs Java 21 and about 6 GB of RAM.
```sh
# 1. Install the NeoForge server
curl -LO https://maven.neoforged.net/releases/net/neoforged/neoforge/21.1.252/neoforge-21.1.252-installer.jar
java -jar neoforge-21.1.252-installer.jar --install-server .

# 2. Pull the server-side files of the pack (client-only mods are skipped)
curl -LO https://github.com/packwiz/packwiz-installer-bootstrap/releases/latest/download/packwiz-installer-bootstrap.jar
java -jar packwiz-installer-bootstrap.jar -g -s server https://raw.githubusercontent.com/grantdoesmktg/econocraft/main/pack.toml

# 3. Accept the EULA, set memory and start
echo "eula=true" > eula.txt
echo "-Xmx6G" >> user_jvm_args.txt
./run.sh nogui        # run.bat on Windows
```
Rerun step 2 while the server is stopped to update. Players and the server must be on the same pack version.

Useful admin commands: `/market balance|earnings|price`, `/market tier set <n>` (op), `/stage grant <player> <stage>`.

## For developers
This repo is a [packwiz](https://packwiz.infra.link/) pack.
- `packwiz serve` hosts it locally at http://localhost:8080/pack.toml. Run `packwiz refresh` after changing files.
- `tools/` holds the generators: prices and shop (`market_catalog.py`), tier locks (`build_locks.py`), quest book
  (`build_quests.py`) and a progression checker (`analyze_progression.py`). Generated files say so at the top; edit the
  generator, not the output.
- Design decisions are in `DESIGN-NOTES.md`; current status is in `HANDOFF.md`.
- `economy-core/` is the source of the Economy Core mod (NeoForge, Java 21); its built jar ships in `mods/`.
  Before building, put these four jars from the pack into `economy-core/libs/` (compile-only APIs):
  ftb-teams-neoforge-2101.1.11, ftb-library-neoforge-2101.1.37, SkyblockBuilder-21.1.37 and LibX-1.21.1-6.0.15.
  Then run `./gradlew build`.
