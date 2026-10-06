package dev.grant.economycore.network;

import dev.grant.economycore.EconomyCore;
import dev.grant.economycore.market.MarketPrices;
import dev.grant.economycore.market.MarketService;
import io.netty.buffer.ByteBuf;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;

import java.util.ArrayList;
import java.util.List;

/**
 * Server -> client: what every sellable item sells for right now for this player's team, so any item tooltip
 * (inventory, chests, JEI) can show its market value. Sent on login and whenever the team's prices change.
 */
public record PricesPayload(List<Entry> entries) implements CustomPacketPayload {
    public static final Type<PricesPayload> TYPE =
            new Type<>(ResourceLocation.fromNamespaceAndPath(EconomyCore.MODID, "prices"));

    /** rarity: 0 = none, 1..4 = common..legendary (fish). */
    public record Entry(String itemId, double price, double fair, int rarity) {
        public static final StreamCodec<ByteBuf, Entry> CODEC = StreamCodec.composite(
                ByteBufCodecs.STRING_UTF8, Entry::itemId,
                ByteBufCodecs.DOUBLE, Entry::price,
                ByteBufCodecs.DOUBLE, Entry::fair,
                ByteBufCodecs.VAR_INT, Entry::rarity,
                Entry::new);
    }

    public static final StreamCodec<ByteBuf, PricesPayload> CODEC = StreamCodec.composite(
            Entry.CODEC.apply(ByteBufCodecs.list()), PricesPayload::entries,
            PricesPayload::new);

    @Override
    public Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }

    /** Current price of every sellable item for this player's team. */
    public static PricesPayload build(ServerPlayer sp) {
        List<Entry> list = new ArrayList<>();
        String name = sp.getGameProfile().getName();
        for (var item : MarketPrices.all()) {
            MarketService.Quote q = MarketService.quote(sp.server, sp.getUUID(), name, item);
            if (q == null) continue;
            list.add(new Entry(BuiltInRegistries.ITEM.getKey(item).toString(),
                    Math.round(q.unitPrice() * 100) / 100.0, q.fairPrice(), MarketPrices.rarity(item)));
        }
        return new PricesPayload(list);
    }
}
