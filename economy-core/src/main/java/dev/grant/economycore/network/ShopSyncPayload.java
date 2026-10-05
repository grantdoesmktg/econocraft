package dev.grant.economycore.network;

import dev.grant.economycore.EconomyCore;
import io.netty.buffer.ByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.ResourceLocation;

import java.util.List;

/** Server -> client: the shop's stock plus the buyer's balance and tier. open = also open the screen. */
public record ShopSyncPayload(long balance, int tier, boolean open, List<Entry> entries) implements CustomPacketPayload {
    public static final Type<ShopSyncPayload> TYPE =
            new Type<>(ResourceLocation.fromNamespaceAndPath(EconomyCore.MODID, "shop_sync"));

    public record Entry(String itemId, int count, long price, int tier, String category, long buyback) {
        public static final StreamCodec<ByteBuf, Entry> CODEC = StreamCodec.composite(
                ByteBufCodecs.STRING_UTF8, Entry::itemId,
                ByteBufCodecs.VAR_INT, Entry::count,
                ByteBufCodecs.VAR_LONG, Entry::price,
                ByteBufCodecs.VAR_INT, Entry::tier,
                ByteBufCodecs.STRING_UTF8, Entry::category,
                ByteBufCodecs.VAR_LONG, Entry::buyback,
                Entry::new);
    }

    public static final StreamCodec<ByteBuf, ShopSyncPayload> CODEC = StreamCodec.composite(
            ByteBufCodecs.VAR_LONG, ShopSyncPayload::balance,
            ByteBufCodecs.VAR_INT, ShopSyncPayload::tier,
            ByteBufCodecs.BOOL, ShopSyncPayload::open,
            Entry.CODEC.apply(ByteBufCodecs.list()), ShopSyncPayload::entries,
            ShopSyncPayload::new);

    @Override
    public Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }
}
