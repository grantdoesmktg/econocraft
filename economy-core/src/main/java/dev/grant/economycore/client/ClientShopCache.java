package dev.grant.economycore.client;

import dev.grant.economycore.network.ShopSyncPayload;
import net.minecraft.client.Minecraft;
import net.neoforged.neoforge.network.handling.IPayloadContext;

import java.util.List;

/** Latest shop data from the server. Opens the shop screen when the server says so. */
public final class ClientShopCache {
    public static long balance;
    public static int tier;
    public static List<ShopSyncPayload.Entry> entries = List.of();

    private ClientShopCache() {}

    public static void handle(ShopSyncPayload msg, IPayloadContext ctx) {
        balance = msg.balance();
        tier = msg.tier();
        entries = msg.entries();
        Minecraft mc = Minecraft.getInstance();
        if (mc.screen instanceof ShopScreen shop) shop.onSync();
        else if (msg.open()) mc.setScreen(new ShopScreen());
    }
}
