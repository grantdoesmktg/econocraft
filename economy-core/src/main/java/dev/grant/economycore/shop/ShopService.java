package dev.grant.economycore.shop;

import dev.grant.economycore.ModRegistry;
import dev.grant.economycore.market.MarketData;
import dev.grant.economycore.market.MarketService;
import dev.grant.economycore.network.ShopSyncPayload;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.neoforged.neoforge.items.ItemHandlerHelper;
import net.neoforged.neoforge.network.PacketDistributor;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/** Opening the shop and buying from it. Purchases are paid from the team's market balance. */
public final class ShopService {
    private record OpenShop(ResourceKey<Level> dim, BlockPos pos) {}

    private static final Map<UUID, OpenShop> OPEN = new HashMap<>();
    public static final int MAX_LOTS = 64;

    private ShopService() {}

    public static void open(ServerPlayer player, BlockPos pos) {
        OPEN.put(player.getUUID(), new OpenShop(player.level().dimension(), pos));
        sync(player, true);
    }

    public static void sync(ServerPlayer player, boolean open) {
        List<ShopSyncPayload.Entry> list = new ArrayList<>();
        for (ShopCatalog.Entry e : ShopCatalog.entries()) {
            list.add(new ShopSyncPayload.Entry(e.itemId(), e.count(), e.price(), e.tier(), e.category(), e.buyback(), e.note()));
        }
        long balance = MarketData.get(player.server).accountFor(player.getUUID()).balance;
        int tier = MarketService.getTier(player.server, player.getUUID());
        PacketDistributor.sendToPlayer(player, new ShopSyncPayload(balance, tier, open, list));
    }

    public static void buy(ServerPlayer player, int index, int lots) {
        OpenShop shop = OPEN.get(player.getUUID());
        if (shop == null || player.level().dimension() != shop.dim()
                || player.blockPosition().distSqr(shop.pos()) > 64
                || !player.level().getBlockState(shop.pos()).is(ModRegistry.SUPPLY_MARKET.get())) {
            return; // not standing at a Supply Market
        }
        List<ShopCatalog.Entry> entries = ShopCatalog.entries();
        if (index < 0 || index >= entries.size() || lots < 1) return;
        lots = Math.min(lots, MAX_LOTS);
        ShopCatalog.Entry e = entries.get(index);

        if (MarketService.getTier(player.server, player.getUUID()) < e.tier()) {
            player.displayClientMessage(Component.translatable("message.economy_core.shop_locked", e.tier()).withStyle(ChatFormatting.RED), true);
            return;
        }
        MarketData data = MarketData.get(player.server);
        MarketData.Account acc = data.accountFor(player.getUUID());
        long cost = e.price() * lots;
        if (acc.balance < cost) {
            player.displayClientMessage(Component.translatable("message.economy_core.shop_broke",
                    String.format("%,d", cost), String.format("%,d", acc.balance)).withStyle(ChatFormatting.RED), true);
            return;
        }
        acc.balance -= cost;
        data.setDirty();

        int total = e.count() * lots;
        int max = new ItemStack(e.item()).getMaxStackSize();
        while (total > 0) {
            int n = Math.min(total, max);
            ItemStack stack = new ItemStack(e.item(), n);
            // Machines carry their buy-back value, so only shop-bought ones can be sold back.
            if (e.buyback() > 0) stack.set(ModRegistry.PRICE_TAG.get(), e.buyback());
            ItemHandlerHelper.giveItemToPlayer(player, stack);
            total -= n;
        }
        player.level().playSound(null, player.blockPosition(), SoundEvents.VILLAGER_YES, SoundSource.PLAYERS, 0.6f, 1.1f);
        player.displayClientMessage(Component.translatable("message.economy_core.shop_bought",
                e.count() * lots, new ItemStack(e.item()).getHoverName(), String.format("%,d", cost)).withStyle(ChatFormatting.GOLD), true);
        sync(player, false);
    }
}
