package dev.grant.economycore.client;

import dev.grant.economycore.network.MarketSyncPayload;
import net.neoforged.neoforge.network.handling.IPayloadContext;

import java.util.HashMap;
import java.util.Map;

/** Latest market info sent by the server, used by the Market screen for tooltips and labels. */
public final class ClientMarketCache {
    public static long balance;
    public static long earned;
    public static int tier;
    public static Map<String, MarketSyncPayload.Entry> prices = new HashMap<>();

    private ClientMarketCache() {}

    public static void handle(MarketSyncPayload msg, IPayloadContext ctx) {
        balance = msg.balance();
        earned = msg.earned();
        tier = msg.tier();
        Map<String, MarketSyncPayload.Entry> m = new HashMap<>();
        for (MarketSyncPayload.Entry e : msg.entries()) m.put(e.itemId(), e);
        prices = m;
    }
}
