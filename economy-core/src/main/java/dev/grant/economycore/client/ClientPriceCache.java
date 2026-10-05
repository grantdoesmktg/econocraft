package dev.grant.economycore.client;

import dev.grant.economycore.network.PricesPayload;

import java.util.HashMap;
import java.util.Map;

/** What each item sells for right now (for this player's team), for item tooltips everywhere. */
public final class ClientPriceCache {
    private static Map<String, PricesPayload.Entry> prices = Map.of();

    private ClientPriceCache() {}

    public static void handle(PricesPayload msg) {
        Map<String, PricesPayload.Entry> m = new HashMap<>();
        for (PricesPayload.Entry e : msg.entries()) m.put(e.itemId(), e);
        prices = m;
    }

    public static PricesPayload.Entry get(String itemId) {
        return prices.get(itemId);
    }
}
