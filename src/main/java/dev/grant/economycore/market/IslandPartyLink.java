package dev.grant.economycore.market;

import com.mojang.logging.LogUtils;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.neoforged.fml.ModList;
import org.slf4j.Logger;

import java.util.Optional;
import java.util.UUID;

/**
 * Keeps Skyblock Builder island teams and FTB Teams parties in step, so everyone on an island shares
 * quest progress, stages and the market wallet without a second step.
 *
 * Every few seconds, for each online player on a (non-spawn) island team:
 *  - if a teammate is already in an FTB party, the player is force-added to that party;
 *  - if nobody has a party yet, the player creates one named after the island.
 * Players who already chose a different party are left alone.
 */
public final class IslandPartyLink {
    private static final Logger LOG = LogUtils.getLogger();
    private static final int PERIOD = 100;

    private IslandPartyLink() {}

    public static void tick(MinecraftServer server) {
        if (server.getTickCount() % PERIOD != 0) return;
        if (!ModList.get().isLoaded("skyblockbuilder") || !ModList.get().isLoaded("ftbteams")) return;
        try {
            for (ServerPlayer p : server.getPlayerList().getPlayers()) Impl.sync(server, p);
        } catch (Throwable t) {
            LOG.debug("[Economy Core] island/party sync skipped: {}", t.toString());
        }
    }

    /** Separate class so the optional mods' classes only load when both are present. */
    private static final class Impl {
        static void sync(MinecraftServer server, ServerPlayer player) {
            var sbb = de.melanx.skyblockbuilder.data.SkyblockSavedData.get(server.overworld());
            var island = sbb.getTeamFromPlayer(player.getUUID());
            if (island == null || island.isSpawn()) return;

            var api = dev.ftb.mods.ftbteams.api.FTBTeamsAPI.api();
            if (api == null || !api.isManagerLoaded()) return;
            var manager = api.getManager();
            var mine = manager.getTeamForPlayerID(player.getUUID()).orElse(null);
            if (mine == null) return;

            // A party some islander already belongs to.
            Optional<dev.ftb.mods.ftbteams.api.Team> party = Optional.empty();
            for (UUID member : island.getPlayers()) {
                var t = manager.getTeamForPlayerID(member);
                if (t.isPresent() && t.get().isPartyTeam()) { party = t; break; }
            }

            if (party.isPresent()) {
                if (mine.getId().equals(party.get().getId()) || mine.isPartyTeam()) return; // already linked, or chose their own party
                run(server, server.createCommandSourceStack().withSuppressedOutput(),
                        "ftbteams force-add " + party.get().getId() + " " + player.getGameProfile().getName());
            } else if (!mine.isPartyTeam()) {
                String name = island.getName().replaceAll("[^A-Za-z0-9_ -]", "").trim();
                if (name.isEmpty()) name = player.getGameProfile().getName() + "'s Island";
                run(server, player.createCommandSourceStack().withSuppressedOutput().withPermission(2),
                        "ftbteams party create " + name);
            }
        }

        private static void run(MinecraftServer server, net.minecraft.commands.CommandSourceStack src, String cmd) {
            server.getCommands().performPrefixedCommand(src, cmd);
        }
    }
}
