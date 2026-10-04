package dev.grant.economycore.frontier;

import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.NbtUtils;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.saveddata.SavedData;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/**
 * Where each team lands in the Frontier, and where each player last left the Isles from (their way home).
 * Saved in the overworld data folder as economy_core_frontier.dat.
 */
public class FrontierData extends SavedData {
    private static final String FILE = "economy_core_frontier";

    public record Spot(ResourceKey<Level> dimension, BlockPos pos) {}

    /** team id -> landing gateway position in the Frontier (overworld) */
    private final Map<UUID, BlockPos> landings = new HashMap<>();
    /** player id -> the gateway they last used to leave for the Frontier */
    private final Map<UUID, Spot> returns = new HashMap<>();

    public static FrontierData get(MinecraftServer server) {
        return server.overworld().getDataStorage()
                .computeIfAbsent(new SavedData.Factory<>(FrontierData::new, FrontierData::load, null), FILE);
    }

    public BlockPos landing(UUID team) { return landings.get(team); }

    public void setLanding(UUID team, BlockPos pos) {
        landings.put(team, pos.immutable());
        setDirty();
    }

    public Spot returnSpot(UUID player) { return returns.get(player); }

    public void setReturn(UUID player, ResourceKey<Level> dim, BlockPos pos) {
        returns.put(player, new Spot(dim, pos.immutable()));
        setDirty();
    }

    @Override
    public CompoundTag save(CompoundTag tag, HolderLookup.Provider registries) {
        CompoundTag l = new CompoundTag();
        landings.forEach((id, pos) -> l.put(id.toString(), NbtUtils.writeBlockPos(pos)));
        tag.put("Landings", l);
        CompoundTag r = new CompoundTag();
        returns.forEach((id, spot) -> {
            CompoundTag t = new CompoundTag();
            t.putString("Dim", spot.dimension().location().toString());
            t.put("Pos", NbtUtils.writeBlockPos(spot.pos()));
            r.put(id.toString(), t);
        });
        tag.put("Returns", r);
        return tag;
    }

    public static FrontierData load(CompoundTag tag, HolderLookup.Provider registries) {
        FrontierData d = new FrontierData();
        CompoundTag l = tag.getCompound("Landings");
        for (String k : l.getAllKeys()) {
            try {
                NbtUtils.readBlockPos(l, k).ifPresent(p -> d.landings.put(UUID.fromString(k), p));
            } catch (IllegalArgumentException ignored) { }
        }
        CompoundTag r = tag.getCompound("Returns");
        for (String k : r.getAllKeys()) {
            try {
                CompoundTag t = r.getCompound(k);
                ResourceLocation dim = ResourceLocation.tryParse(t.getString("Dim"));
                if (dim == null) continue;
                NbtUtils.readBlockPos(t, "Pos").ifPresent(p ->
                        d.returns.put(UUID.fromString(k), new Spot(ResourceKey.create(Registries.DIMENSION, dim), p)));
            } catch (IllegalArgumentException ignored) { }
        }
        return d;
    }
}
