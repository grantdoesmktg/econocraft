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

    /** note = an optional one-liner shown under the item in the shop (a tagline). */
    public record Entry(String itemId, int count, long price, int tier, String category, long buyback, String note) {
        public static final StreamCodec<ByteBuf, Entry> CODEC = StreamCodec.of(
                (buf, e) -> {
                    ByteBufCodecs.STRING_UTF8.encode(buf, e.itemId());
                    ByteBufCodecs.VAR_INT.encode(buf, e.count());
                    ByteBufCodecs.VAR_LONG.encode(buf, e.price());
                    ByteBufCodecs.VAR_INT.encode(buf, e.tier());
                    ByteBufCodecs.STRING_UTF8.encode(buf, e.category());
                    ByteBufCodecs.VAR_LONG.encode(buf, e.buyback());
                    ByteBufCodecs.STRING_UTF8.encode(buf, e.note());
                },
                buf -> new Entry(ByteBufCodecs.STRING_UTF8.decode(buf), ByteBufCodecs.VAR_INT.decode(buf),
                        ByteBufCodecs.VAR_LONG.decode(buf), ByteBufCodecs.VAR_INT.decode(buf),
                        ByteBufCodecs.STRING_UTF8.decode(buf), ByteBufCodecs.VAR_LONG.decode(buf),
                        ByteBufCodecs.STRING_UTF8.decode(buf)));
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
