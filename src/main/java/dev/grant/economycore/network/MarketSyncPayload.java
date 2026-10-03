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

/** Server -> client: current prices for items in the crate and the viewer's inventory, plus balance info. */
public record MarketSyncPayload(long balance, long earned, int tier, List<Entry> entries) implements CustomPacketPayload {
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

    public static final StreamCodec<ByteBuf, MarketSyncPayload> CODEC = StreamCodec.composite(
            ByteBufCodecs.VAR_LONG, MarketSyncPayload::balance,
            ByteBufCodecs.VAR_LONG, MarketSyncPayload::earned,
            ByteBufCodecs.VAR_INT, MarketSyncPayload::tier,
            Entry.CODEC.apply(ByteBufCodecs.list()), MarketSyncPayload::entries,
            MarketSyncPayload::new);

    @Override
    public Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }

    public static MarketSyncPayload build(ServerPlayer player, MarketCrateBlockEntity crate) {
        Set<Item> seen = new LinkedHashSet<>();
        for (int i = 0; i < crate.getItems().getSlots(); i++) collect(seen, crate.getItems().getStackInSlot(i));
        for (ItemStack s : player.getInventory().items) collect(seen, s);

        List<Entry> entries = new ArrayList<>();
        for (Item item : seen) {
            var q = MarketService.quote(player.server, player.getUUID(), player.getGameProfile().getName(), item);
            if (q != null) entries.add(new Entry(MarketService.itemId(item), q.unitPrice(), q.fairPrice(), q.distinctRemaining()));
        }
        MarketData.Account acc = MarketData.get(player.server).account(player.getUUID());
        int tier = MarketService.getTier(player.server, player.getGameProfile().getName());
        return new MarketSyncPayload(acc.balance, acc.earned, tier, entries);
    }

    private static void collect(Set<Item> seen, ItemStack s) {
        if (MarketPrices.isSellable(s)) seen.add(s.getItem());
    }
}
