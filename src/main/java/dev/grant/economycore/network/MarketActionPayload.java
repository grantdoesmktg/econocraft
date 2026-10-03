package dev.grant.economycore.network;

import dev.grant.economycore.EconomyCore;
import dev.grant.economycore.block.MarketCrateBlockEntity;
import dev.grant.economycore.market.MarketService;
import dev.grant.economycore.menu.MarketMenu;
import io.netty.buffer.ByteBuf;
import net.minecraft.network.chat.Component;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.neoforged.neoforge.network.handling.IPayloadContext;

/** Client -> server: a button press in the Market Crate screen. */
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
            case SELL_STACK -> report(player, crate.sellSlot(level, msg.slot()));
            case SELL_ALL_OF_ITEM -> {
                if (msg.slot() >= 0 && msg.slot() < MarketCrateBlockEntity.SLOTS) {
                    ItemStack s = crate.getItems().getStackInSlot(msg.slot());
                    if (!s.isEmpty()) report(player, crate.sellAllOf(level, s.getItem()));
                }
            }
            case SELL_EVERYTHING -> {
                long coins = crate.sellEverything(level);
                player.displayClientMessage(Component.translatable("message.economy_core.sold_everything", coins), true);
            }
            case TOGGLE_AUTOSELL -> crate.setAutoSell(!crate.isAutoSell());
            case WITHDRAW -> {
                long paid = MarketService.withdraw(player);
                player.displayClientMessage(Component.translatable("message.economy_core.withdrew", paid), true);
            }
            default -> { }
        }
        menu.sendSync(player);
    }

    private static void report(ServerPlayer player, MarketService.Sale sale) {
        if (sale == null || sale.units() == 0) return;
        player.displayClientMessage(Component.translatable("message.economy_core.sold",
                sale.units(), sale.item().getDescription(), sale.coins()), true);
    }
}
