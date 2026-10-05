package dev.grant.economycore.network;

import dev.grant.economycore.EconomyCore;
import dev.grant.economycore.block.MarketCrateBlockEntity;
import dev.grant.economycore.market.MarketService;
import dev.grant.economycore.menu.MarketMenu;
import io.netty.buffer.ByteBuf;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.neoforged.neoforge.network.handling.IPayloadContext;

/** Client -> server: a button press in the Market Crate screen. For WITHDRAW, slot = coin index (largest first), -1 = mixed. */
public record MarketActionPayload(int action, int slot) implements CustomPacketPayload {
    public static final int SELL_STACK = 0, SELL_ALL_OF_ITEM = 1, SELL_EVERYTHING = 2, TOGGLE_AUTOSELL = 3, WITHDRAW = 4;

    public static final Type<MarketActionPayload> TYPE =
            new Type<>(ResourceLocation.fromNamespaceAndPath(EconomyCore.MODID, "market_action"));

    public static final StreamCodec<ByteBuf, MarketActionPayload> CODEC = StreamCodec.composite(
            ByteBufCodecs.VAR_INT, MarketActionPayload::action,
            ByteBufCodecs.VAR_INT, MarketActionPayload::slot,
            MarketActionPayload::new);

    @Override
    public Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }

    /** Runs on the server thread. Only acts on the crate the player currently has open and owns. */
    public static void handle(MarketActionPayload msg, IPayloadContext ctx) {
        if (!(ctx.player() instanceof ServerPlayer player)) return;
        if (!(player.containerMenu instanceof MarketMenu menu) || !menu.stillValid(player)) return;
        MarketCrateBlockEntity crate = menu.getCrate();
        if (!crate.isOwner(player) || !(crate.getLevel() instanceof ServerLevel level)) return;

        switch (msg.action()) {
            case SELL_STACK -> report(player, crate, level, crate.sellSelectedStack(level));
            case SELL_ALL_OF_ITEM -> report(player, crate, level, crate.sellAllOfSelected(level));
            case SELL_EVERYTHING -> {
                long coins = crate.sellEverything(level);
                if (coins > 0) {
                    MarketService.firstSale(player, coins, crate.getBlockPos());
                    player.displayClientMessage(Component.translatable("message.economy_core.sold_everything",
                            String.format("%,d", coins)).withStyle(ChatFormatting.GOLD), true);
                    crate.notifyOwner(level, MarketFxPayload.KIND_SALE, coins);
                }
            }
            case TOGGLE_AUTOSELL -> crate.setAutoSell(!crate.isAutoSell());
            case WITHDRAW -> {
                long paid = MarketService.withdraw(player, msg.slot());
                player.displayClientMessage(Component.translatable("message.economy_core.withdrew",
                        String.format("%,d", paid)).withStyle(ChatFormatting.GOLD), true);
            }
            default -> { }
        }
        menu.sendSync(player);
    }

    private static void report(ServerPlayer player, MarketCrateBlockEntity crate, ServerLevel level, MarketService.Sale sale) {
        if (sale == null || sale.units() == 0) return;
        player.displayClientMessage(Component.translatable("message.economy_core.sold",
                String.format("%,d", sale.coins()), sale.units(), sale.item().getDescription()).withStyle(ChatFormatting.GOLD), true);
        crate.notifyOwner(level, MarketFxPayload.KIND_SALE, sale.coins());
        MarketService.firstSale(player, sale.coins(), crate.getBlockPos());
    }
}
