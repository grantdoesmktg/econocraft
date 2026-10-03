package dev.grant.economycore.client;

import dev.grant.economycore.network.MarketSyncPayload;
import net.neoforged.neoforge.network.handling.IPayloadContext;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/** Latest market info sent by the server, used by the Market screen. */
public final class ClientMarketCache {
    public static long balance;
    public static long earned;
    public static int tier;
    public static Map<String, MarketSyncPayload.Entry> prices = new HashMap<>();
    public static List<MarketSyncPayload.Coin> coins = List.of();
    public static long sellStackValue, sellAllValue;
    public static int sellAllUnits;


    private ClientMarketCache() {}

    public static void handle(MarketSyncPayload msg, IPayloadContext ctx) {
        balance = msg.balance();
        earned = msg.earned();
        tier = msg.tier();
        Map<String, MarketSyncPayload.Entry> m = new HashMap<>();
        for (MarketSyncPayload.Entry e : msg.entries()) m.put(e.itemId(), e);
        prices = m;
        coins = msg.coins();
        sellStackValue = msg.sellStackValue();
        sellAllValue = msg.sellAllValue();
        sellAllUnits = msg.sellAllUnits();
    }
}
