package dev.grant.economycore.network;

import dev.grant.economycore.EconomyCore;
import dev.grant.economycore.block.MarketCrateBlockEntity;
import dev.grant.economycore.market.MarketData;
import dev.grant.economycore.market.MarketPrices;
import dev.grant.economycore.market.MarketService;
import io.netty.buffer.ByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;

import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;

/**
 * Server -> client: everything the Market screen shows. Prices for items in the crate, the sell slot
 * and the viewer's inventory; balance info; coin denominations; and what the sell-slot buttons would pay.
 */
public record MarketSyncPayload(long balance, long earned, int tier, List<Entry> entries, List<Coin> coins,
                                long sellStackValue, long sellAllValue, int sellAllUnits) implements CustomPacketPayload {
    public static final Type<MarketSyncPayload> TYPE =
            new Type<>(ResourceLocation.fromNamespaceAndPath(EconomyCore.MODID, "market_sync"));

    public record Entry(String itemId, double price, double fair, int remaining) {
        public static final StreamCodec<ByteBuf, Entry> CODEC = StreamCodec.composite(
                ByteBufCodecs.STRING_UTF8, Entry::itemId,
                ByteBufCodecs.DOUBLE, Entry::price,
                ByteBufCodecs.DOUBLE, Entry::fair,
                ByteBufCodecs.VAR_INT, Entry::remaining,
                Entry::new);
    }

    /** A coin item and its value, largest first. */
    public record Coin(String itemId, long value) {
        public static final StreamCodec<ByteBuf, Coin> CODEC = StreamCodec.composite(
                ByteBufCodecs.STRING_UTF8, Coin::itemId,
                ByteBufCodecs.VAR_LONG, Coin::value,
                Coin::new);
    }

    private static final StreamCodec<ByteBuf, List<Entry>> ENTRIES = Entry.CODEC.apply(ByteBufCodecs.list());
    private static final StreamCodec<ByteBuf, List<Coin>> COINS = Coin.CODEC.apply(ByteBufCodecs.list());

    // composite() only supports 6 fields, so this one is written out by hand.
    public static final StreamCodec<ByteBuf, MarketSyncPayload> CODEC = StreamCodec.of(
            (buf, p) -> {
                ByteBufCodecs.VAR_LONG.encode(buf, p.balance());
                ByteBufCodecs.VAR_LONG.encode(buf, p.earned());
                ByteBufCodecs.VAR_INT.encode(buf, p.tier());
                ENTRIES.encode(buf, p.entries());
                COINS.encode(buf, p.coins());
                ByteBufCodecs.VAR_LONG.encode(buf, p.sellStackValue());
                ByteBufCodecs.VAR_LONG.encode(buf, p.sellAllValue());
                ByteBufCodecs.VAR_INT.encode(buf, p.sellAllUnits());
            },
            buf -> new MarketSyncPayload(
                    ByteBufCodecs.VAR_LONG.decode(buf),
                    ByteBufCodecs.VAR_LONG.decode(buf),
                    ByteBufCodecs.VAR_INT.decode(buf),
                    ENTRIES.decode(buf),
                    COINS.decode(buf),
                    ByteBufCodecs.VAR_LONG.decode(buf),
                    ByteBufCodecs.VAR_LONG.decode(buf),
                    ByteBufCodecs.VAR_INT.decode(buf)));

    @Override
    public Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }

    public static MarketSyncPayload build(ServerPlayer player, MarketCrateBlockEntity crate) {
        String name = player.getGameProfile().getName();
        Set<Item> seen = new LinkedHashSet<>();
        for (int i = 0; i < crate.getItems().getSlots(); i++) collect(seen, crate.getItems().getStackInSlot(i));
        collect(seen, crate.getSellSlot().getStackInSlot(0));
        for (ItemStack s : player.getInventory().items) collect(seen, s);

        List<Entry> entries = new ArrayList<>();
        for (Item item : seen) {
            var q = MarketService.quote(player.server, player.getUUID(), name, item);
            if (q != null) entries.add(new Entry(MarketService.itemId(item), q.unitPrice(), q.fairPrice(), q.distinctRemaining()));
        }

        List<Coin> coins = new ArrayList<>();
        MarketPrices.config().coins.forEach((id, value) -> {
            if (value != null && value > 0) coins.add(new Coin(id, value));
        });
        coins.sort((a, b) -> Long.compare(b.value(), a.value()));

        // What the two sell-slot buttons would pay right now.
        long stackValue = 0, allValue = 0;
        int allUnits = 0;
        ItemStack sel = crate.getSellSlot().getStackInSlot(0);
        if (MarketPrices.isSellable(sel)) {
            stackValue = MarketService.preview(player.server, player.getUUID(), name, sel.getItem(), sel.getCount());
            allUnits = sel.getCount();
            for (int i = 0; i < crate.getItems().getSlots(); i++) {
                ItemStack s = crate.getItems().getStackInSlot(i);
                if (!s.isEmpty() && s.getItem() == sel.getItem()) allUnits += s.getCount();
            }
            allValue = MarketService.preview(player.server, player.getUUID(), name, sel.getItem(), allUnits);
        }

        MarketData.Account acc = MarketData.get(player.server).account(player.getUUID());
        int tier = MarketService.getTier(player.server, name);
        return new MarketSyncPayload(acc.balance, acc.earned, tier, entries, coins, stackValue, allValue, allUnits);
    }

    private static void collect(Set<Item> seen, ItemStack s) {
        if (MarketPrices.isSellable(s)) seen.add(s.getItem());
    }
}
