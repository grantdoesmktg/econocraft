package dev.grant.economycore.network;

import dev.grant.economycore.EconomyCore;
import io.netty.buffer.ByteBuf;
import net.minecraft.core.BlockPos;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.ResourceLocation;

/**
 * Server -> client: play a sale celebration (or a quiet deposit notice).
 * The server decides the tier (1..8, 0 = no celebration); the client does all the visuals and sounds.
 */
public record MarketFxPayload(int kind, long amount, int tier, BlockPos pos) implements CustomPacketPayload {
    public static final int KIND_SALE = 0, KIND_AUTOSELL = 1, KIND_DEPOSIT = 2, KIND_PREVIEW = 3,
            /** A player's very first sale: the full, deeply unnecessary show. Sent to that player only. */
            KIND_FIRST_SALE = 4;

    public static final Type<MarketFxPayload> TYPE =
            new Type<>(ResourceLocation.fromNamespaceAndPath(EconomyCore.MODID, "market_fx"));

    public static final StreamCodec<ByteBuf, MarketFxPayload> CODEC = StreamCodec.composite(
            ByteBufCodecs.VAR_INT, MarketFxPayload::kind,
            ByteBufCodecs.VAR_LONG, MarketFxPayload::amount,
            ByteBufCodecs.VAR_INT, MarketFxPayload::tier,
            BlockPos.STREAM_CODEC, MarketFxPayload::pos,
            MarketFxPayload::new);

    @Override
    public Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }
}
