package dev.grant.economycore.market;

import com.mojang.logging.LogUtils;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.tags.TagKey;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.neoforged.fml.loading.FMLPaths;
import org.slf4j.Logger;

import java.nio.file.Path;
import java.util.HashMap;
import java.util.Map;

/**
 * The loaded config, with item/tag keys resolved to real items. Server-side singleton.
 * Explicit item ids override tag entries.
 */
public final class MarketPrices {
    private static final Logger LOG = LogUtils.getLogger();

    public record Pricing(double base, double softCap, double maxDrop, String category) {}

    private static MarketConfig config = MarketConfig.defaults();
    private static Map<Item, Pricing> prices = new HashMap<>();

    private MarketPrices() {}

    public static Path configFile() {
        return FMLPaths.CONFIGDIR.get().resolve("economy_core").resolve("market.json");
    }

    /** Load (or create) the config file and resolve it. Call after tags are available. */
    public static synchronized String reload() {
        try {
            config = MarketConfig.loadOrCreate(configFile());
        } catch (Exception e) {
            LOG.error("[Economy Core] Could not read {}: {}", configFile(), e.toString());
            return "Error reading market.json: " + e.getMessage();
        }
        return resolve();
    }

    /** Re-resolve item tags (e.g. after /reload changed tags). */
    public static synchronized String resolve() {
        Map<Item, Pricing> fromTags = new HashMap<>();
        Map<Item, Pricing> explicit = new HashMap<>();
        int unknown = 0;
        for (var e : config.items.entrySet()) {
            String key = e.getKey();
            MarketConfig.ItemEntry entry = e.getValue();
            Pricing p = pricingFor(entry);
            if (key.startsWith("#")) {
                ResourceLocation id = ResourceLocation.tryParse(key.substring(1));
                if (id == null) { unknown++; continue; }
                var tag = BuiltInRegistries.ITEM.getTag(TagKey.create(Registries.ITEM, id));
                if (tag.isEmpty()) { unknown++; continue; }
                for (Holder<Item> h : tag.get()) fromTags.put(h.value(), p);
            } else {
                ResourceLocation id = ResourceLocation.tryParse(key);
                if (id == null || !BuiltInRegistries.ITEM.containsKey(id)) { unknown++; continue; }
                explicit.put(BuiltInRegistries.ITEM.get(id), p);
            }
        }
        fromTags.putAll(explicit);
        fromTags.remove(Items.AIR);
        prices = fromTags;
        String msg = "Market prices loaded: " + prices.size() + " sellable items"
                + (unknown > 0 ? " (" + unknown + " config entries skipped: unknown item/tag or mod not installed)" : "");
        LOG.info("[Economy Core] {}", msg);
        return msg;
    }

    private static Pricing pricingFor(MarketConfig.ItemEntry entry) {
        MarketConfig.Category cat = config.categories.getOrDefault(entry.category, new MarketConfig.Category());
        double maxDrop = cat.maxDrop != null ? cat.maxDrop : (1.0 - config.floorDefault);
        return new Pricing(entry.base, cat.softCap, maxDrop, entry.category);
    }

    public static Pricing get(Item item) {
        return prices.get(item);
    }

    public static boolean isSellable(ItemStack stack) {
        return !stack.isEmpty() && prices.containsKey(stack.getItem());
    }

    public static MarketConfig config() {
        return config;
    }
}
