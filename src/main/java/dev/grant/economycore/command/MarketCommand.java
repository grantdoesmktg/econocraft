package dev.grant.economycore.command;

import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.arguments.LongArgumentType;
import dev.grant.economycore.network.MarketFxPayload;
import net.neoforged.neoforge.network.PacketDistributor;
import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.exceptions.CommandSyntaxException;
import dev.grant.economycore.market.MarketData;
import dev.grant.economycore.market.MarketPrices;
import dev.grant.economycore.market.MarketService;
import net.minecraft.commands.CommandBuildContext;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.arguments.EntityArgument;
import net.minecraft.commands.arguments.item.ItemArgument;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.Item;

/**
 * /market reload | balance | earnings | price <item> | reset <item>|all | tier set <n> [players]
 * reload, reset and tier need operator permission (level 2).
 */
public final class MarketCommand {
    private MarketCommand() {}

    public static void register(CommandDispatcher<CommandSourceStack> d, CommandBuildContext ctx) {
        d.register(Commands.literal("market")
                .then(Commands.literal("reload").requires(s -> s.hasPermission(2))
                        .executes(c -> {
                            String msg = MarketPrices.reload();
                            c.getSource().sendSuccess(() -> Component.literal(msg), true);
                            return 1;
                        }))
                .then(Commands.literal("balance").executes(c -> {
                    ServerPlayer p = c.getSource().getPlayerOrException();
                    long bal = MarketData.get(p.server).account(p.getUUID()).balance;
                    c.getSource().sendSuccess(() -> Component.translatable("command.economy_core.balance", bal), false);
                    return 1;
                }))
                .then(Commands.literal("earnings").executes(c -> {
                    ServerPlayer p = c.getSource().getPlayerOrException();
                    long earned = MarketData.get(p.server).account(p.getUUID()).earned;
                    c.getSource().sendSuccess(() -> Component.translatable("command.economy_core.earnings", earned), false);
                    return 1;
                }))
                .then(Commands.literal("price")
                        .then(Commands.argument("item", ItemArgument.item(ctx)).executes(MarketCommand::price)))
                .then(Commands.literal("reset").requires(s -> s.hasPermission(2))
                        .then(Commands.literal("all").executes(c -> {
                            MarketData.get(c.getSource().getServer()).resetAll(MarketData.GLOBAL_SCOPE);
                            c.getSource().sendSuccess(() -> Component.translatable("command.economy_core.reset_all"), true);
                            return 1;
                        }))
                        .then(Commands.argument("item", ItemArgument.item(ctx)).executes(c -> {
                            Item item = ItemArgument.getItem(c, "item").getItem();
                            MarketData.get(c.getSource().getServer()).resetItem(MarketData.GLOBAL_SCOPE, MarketService.itemId(item));
                            c.getSource().sendSuccess(() -> Component.translatable("command.economy_core.reset_item", item.getDescription()), true);
                            return 1;
                        })))
                .then(Commands.literal("celebrate").requires(s -> s.hasPermission(2))
                        .then(Commands.argument("amount", LongArgumentType.longArg(1)).executes(c -> {
                            ServerPlayer p = c.getSource().getPlayerOrException();
                            long amount = LongArgumentType.getLong(c, "amount");
                            int tier = MarketService.celebrationTier(amount);
                            PacketDistributor.sendToPlayer(p, new MarketFxPayload(MarketFxPayload.KIND_PREVIEW, amount, tier, p.blockPosition()));
                            c.getSource().sendSuccess(() -> Component.translatable("command.economy_core.celebrate", amount, tier), false);
                            return 1;
                        })))
                .then(Commands.literal("tier").requires(s -> s.hasPermission(2))
                        .then(Commands.literal("set")
                                .then(Commands.argument("tier", IntegerArgumentType.integer(0, 100))
                                        .executes(c -> setTier(c, java.util.List.of(c.getSource().getPlayerOrException())))
                                        .then(Commands.argument("players", EntityArgument.players())
                                                .executes(c -> setTier(c, EntityArgument.getPlayers(c, "players"))))))));
    }

    private static int price(CommandContext<CommandSourceStack> c) throws CommandSyntaxException {
        ServerPlayer p = c.getSource().getPlayerOrException();
        Item item = ItemArgument.getItem(c, "item").getItem();
        var q = MarketService.quote(p.server, p.getUUID(), p.getGameProfile().getName(), item);
        if (q == null) {
            c.getSource().sendFailure(Component.translatable("command.economy_core.not_sellable", item.getDescription()));
            return 0;
        }
        int pct = (int) Math.round(100.0 * q.unitPrice() / Math.max(1e-9, q.fairPrice()));
        c.getSource().sendSuccess(() -> Component.translatable("command.economy_core.price", item.getDescription(),
                String.format("%.1f", q.unitPrice()), pct, String.format("%.1f", q.fairPrice()), q.distinctRemaining()), false);
        return 1;
    }

    private static int setTier(CommandContext<CommandSourceStack> c, java.util.Collection<ServerPlayer> players) {
        int tier = IntegerArgumentType.getInteger(c, "tier");
        for (ServerPlayer p : players) MarketService.setTier(c.getSource().getServer(), p.getGameProfile().getName(), tier);
        c.getSource().sendSuccess(() -> Component.translatable("command.economy_core.tier_set", players.size(), tier), true);
        return players.size();
    }
}
