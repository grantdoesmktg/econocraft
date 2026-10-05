package dev.grant.economycore.shop;

import com.google.gson.Gson;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.mojang.logging.LogUtils;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.Item;
import net.neoforged.fml.loading.FMLPaths;
import org.slf4j.Logger;

import java.io.Reader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

/**
 * The Supply Market's stock, from config/economy_core/shop.json (generated from tools/market_catalog.py).
 * Entries with a buyback value are machines: they're stamped with that value and sell back at the crate for it.
 */
public final class ShopCatalog {
    private static final Logger LOG = LogUtils.getLogger();

    public record Entry(Item item, String itemId, int count, long price, int tier, String category, long buyback) {}

    private static List<Entry> entries = List.of();

    private ShopCatalog() {}

    public static Path file() {
        return FMLPaths.CONFIGDIR.get().resolve("economy_core").resolve("shop.json");
    }

    public static String reload() {
        List<Entry> out = new ArrayList<>();
        int skipped = 0;
        try {
            Path f = file();
            if (!Files.exists(f)) {
                Files.createDirectories(f.getParent());
                Files.writeString(f, "{ \"entries\": [] }\n");
            }
            try (Reader r = Files.newBufferedReader(f)) {
                JsonObject root = new Gson().fromJson(r, JsonObject.class);
                JsonArray arr = root == null ? new JsonArray() : root.getAsJsonArray("entries");
                for (var el : arr) {
                    JsonObject o = el.getAsJsonObject();
                    String id = o.get("item").getAsString();
                    ResourceLocation rl = ResourceLocation.tryParse(id);
                    if (rl == null || !BuiltInRegistries.ITEM.containsKey(rl)) { skipped++; continue; }
                    out.add(new Entry(BuiltInRegistries.ITEM.get(rl), id,
                            o.has("count") ? o.get("count").getAsInt() : 1,
                            o.get("price").getAsLong(),
                            o.has("tier") ? o.get("tier").getAsInt() : 0,
                            o.has("category") ? o.get("category").getAsString() : "supplies",
                            o.has("buyback") ? o.get("buyback").getAsLong() : 0));
                }
            }
        } catch (Exception e) {
            LOG.error("[Economy Core] Could not read {}: {}", file(), e.toString());
            return "Error reading shop.json: " + e.getMessage();
        }
        entries = List.copyOf(out);
        String msg = "Shop loaded: " + entries.size() + " listings" + (skipped > 0 ? " (" + skipped + " skipped: unknown item)" : "");
        LOG.info("[Economy Core] {}", msg);
        return msg;
    }

    public static List<Entry> entries() {
        return entries;
    }
}
