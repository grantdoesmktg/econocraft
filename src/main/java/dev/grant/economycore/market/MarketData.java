package dev.grant.economycore.market;

import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.StringTag;
import net.minecraft.nbt.Tag;
import net.minecraft.server.MinecraftServer;
import net.minecraft.world.level.saveddata.SavedData;

import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

/**
 * World-saved market state (stored in the overworld's data folder as economy_core_market.dat).
 *
 * Item saturation lives under a "scope". v0.1 uses one global scope shared by everyone;
 * switching to per-player prices later only means passing the player's UUID as the scope.
 * Balances and lifetime earnings are always per player.
 */
public class MarketData extends SavedData {
    public static final String GLOBAL_SCOPE = "global";
    private static final String FILE = "economy_core_market";

    /** Saturation right after the last sale, plus the other distinct goods sold since. */
    public static class ItemState {
        public double saturation;
        public final Set<String> distinctSince = new HashSet<>();
    }

    public static class Account {
        public long balance;
        public long earned;
        /** Distinct items this player has ever sold (for the "five streams" quest). */
        public final Set<String> sold = new HashSet<>();
    }

    private final Map<String, Map<String, ItemState>> scopes = new HashMap<>();
    private final Map<UUID, Account> accounts = new HashMap<>();

    public static MarketData get(MinecraftServer server) {
        return server.overworld().getDataStorage()
                .computeIfAbsent(new SavedData.Factory<>(MarketData::new, MarketData::load, null), FILE);
    }

    public Map<String, ItemState> scope(String scope) {
        return scopes.computeIfAbsent(scope, k -> new HashMap<>());
    }

    public ItemState state(String scope, String itemId) {
        return scope(scope).computeIfAbsent(itemId, k -> new ItemState());
    }

    /** Read-only lookup; null if the item has never been sold in this scope. */
    public ItemState peek(String scope, String itemId) {
        Map<String, ItemState> m = scopes.get(scope);
        return m == null ? null : m.get(itemId);
    }

    public Account account(UUID player) {
        return accounts.computeIfAbsent(player, k -> new Account());
    }

    public void resetItem(String scope, String itemId) {
        Map<String, ItemState> m = scopes.get(scope);
        if (m != null) m.remove(itemId);
        setDirty();
    }

    public void resetAll(String scope) {
        scopes.remove(scope);
        setDirty();
    }

    @Override
    public CompoundTag save(CompoundTag tag, HolderLookup.Provider registries) {
        CompoundTag scopesTag = new CompoundTag();
        scopes.forEach((scope, items) -> {
            CompoundTag itemsTag = new CompoundTag();
            items.forEach((id, st) -> {
                CompoundTag s = new CompoundTag();
                s.putDouble("S", st.saturation);
                ListTag d = new ListTag();
                st.distinctSince.forEach(x -> d.add(StringTag.valueOf(x)));
                s.put("D", d);
                itemsTag.put(id, s);
            });
            scopesTag.put(scope, itemsTag);
        });
        tag.put("Scopes", scopesTag);

        CompoundTag acc = new CompoundTag();
        accounts.forEach((uuid, a) -> {
            CompoundTag t = new CompoundTag();
            t.putLong("Balance", a.balance);
            t.putLong("Earned", a.earned);
            ListTag sold = new ListTag();
            a.sold.forEach(x -> sold.add(StringTag.valueOf(x)));
            t.put("Sold", sold);
            acc.put(uuid.toString(), t);
        });
        tag.put("Accounts", acc);
        return tag;
    }

    public static MarketData load(CompoundTag tag, HolderLookup.Provider registries) {
        MarketData data = new MarketData();
        CompoundTag scopesTag = tag.getCompound("Scopes");
        for (String scope : scopesTag.getAllKeys()) {
            CompoundTag itemsTag = scopesTag.getCompound(scope);
            Map<String, ItemState> items = data.scope(scope);
            for (String id : itemsTag.getAllKeys()) {
                CompoundTag s = itemsTag.getCompound(id);
                ItemState st = new ItemState();
                st.saturation = s.getDouble("S");
                ListTag d = s.getList("D", Tag.TAG_STRING);
                for (int i = 0; i < d.size(); i++) st.distinctSince.add(d.getString(i));
                items.put(id, st);
            }
        }
        CompoundTag acc = tag.getCompound("Accounts");
        for (String key : acc.getAllKeys()) {
            try {
                CompoundTag t = acc.getCompound(key);
                Account a = new Account();
                a.balance = t.getLong("Balance");
                a.earned = t.getLong("Earned");
                ListTag sold = t.getList("Sold", Tag.TAG_STRING);
                for (int i = 0; i < sold.size(); i++) a.sold.add(sold.getString(i));
                data.accounts.put(UUID.fromString(key), a);
            } catch (IllegalArgumentException ignored) {
                // skip malformed uuid
            }
        }
        return data;
    }
}
