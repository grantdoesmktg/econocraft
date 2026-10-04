package dev.grant.economycore.network;

import dev.grant.economycore.EconomyCore;
import dev.grant.economycore.shop.ShopService;
import io.netty.buffer.ByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;
import net.neoforged.neoforge.network.handling.IPayloadContext;

/** Client -> server: buy {@code lots} of shop entry {@code index}. */
public record ShopBuyPayload(int index, int lots) implements CustomPacketPayload {
    public static final Type<ShopBuyPayload> TYPE =
            new Type<>(ResourceLocation.fromNamespaceAndPath(EconomyCore.MODID, "shop_buy"));

    public static final StreamCodec<ByteBuf, ShopBuyPayload> CODEC = StreamCodec.composite(
            ByteBufCodecs.VAR_INT, ShopBuyPayload::index,
            ByteBufCodecs.VAR_INT, ShopBuyPayload::lots,
            ShopBuyPayload::new);

    @Override
    public Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }

    public static void handle(ShopBuyPayload msg, IPayloadContext ctx) {
        if (ctx.player() instanceof ServerPlayer p) ShopService.buy(p, msg.index(), msg.lots());
    }
}
