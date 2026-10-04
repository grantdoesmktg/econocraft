package dev.grant.economycore.market;

import com.mojang.authlib.GameProfile;
import net.minecraft.server.MinecraftServer;
import net.neoforged.fml.ModList;

import java.util.Optional;
import java.util.Set;
import java.util.UUID;

/**
 * Market accounts are shared per FTB Teams team, so everyone in a party shares one balance, one set of
 * earnings milestones and one market tier. Without FTB Teams (or before it's ready) each player is their own team.
 */
public final class TeamHelper {
    private TeamHelper() {}

    private static boolean loaded() {
        return ModList.get().isLoaded("ftbteams");
    }

    /** The id market money is stored under: the player's FTB team, or the player themselves. */
    public static UUID accountId(UUID player) {
        if (player == null || !loaded()) return player;
        try {
            return FtbTeams.teamId(player).orElse(player);
        } catch (Throwable t) {
            return player;
        }
    }

    /** Everyone sharing the player's account (including the player). */
    public static Set<UUID> members(UUID player) {
        if (player == null || !loaded()) return Set.of(player);
        try {
            Set<UUID> m = FtbTeams.members(player);
            return m.isEmpty() ? Set.of(player) : m;
        } catch (Throwable t) {
            return Set.of(player);
        }
    }

    /** True if both players share a market account. */
    public static boolean sameTeam(UUID a, UUID b) {
        return a != null && b != null && accountId(a).equals(accountId(b));
    }

    public static String nameOf(MinecraftServer server, UUID id) {
        var online = server.getPlayerList().getPlayer(id);
        if (online != null) return online.getGameProfile().getName();
        Optional<GameProfile> p = server.getProfileCache() == null ? Optional.empty() : server.getProfileCache().get(id);
        return p.map(GameProfile::getName).orElse("");
    }

    /** Kept in its own class so FTB Teams classes only load when the mod is present. */
    private static final class FtbTeams {
        static Optional<UUID> teamId(UUID player) {
            var api = dev.ftb.mods.ftbteams.api.FTBTeamsAPI.api();
            if (api == null || !api.isManagerLoaded()) return Optional.empty();
            return api.getManager().getTeamForPlayerID(player).map(dev.ftb.mods.ftbteams.api.Team::getId);
        }

        static Set<UUID> members(UUID player) {
            var api = dev.ftb.mods.ftbteams.api.FTBTeamsAPI.api();
            if (api == null || !api.isManagerLoaded()) return Set.of();
            return api.getManager().getTeamForPlayerID(player).map(t -> Set.copyOf(t.getMembers())).orElse(Set.of());
        }
    }
}
