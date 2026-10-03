package dev.grant.economycore.client;

import dev.grant.economycore.network.MarketSyncPayload;
import net.minecraft.Util;
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

    /** Last balance increase, for the floating "+N" in the screen. */
    public static long lastGain;
    public static long lastGainAtMs;
    private static boolean initialized;

    private ClientMarketCache() {}

    public static void handle(MarketSyncPayload msg, IPayloadContext ctx) {
        if (initialized && msg.balance() > balance) {
            lastGain = msg.balance() - balance;
            lastGainAtMs = Util.getMillis();
        }
        initialized = true;
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
