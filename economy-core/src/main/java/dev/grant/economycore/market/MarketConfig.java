package dev.grant.economycore.market;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.annotations.SerializedName;

import java.io.IOException;
import java.io.Reader;
import java.io.Writer;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Raw contents of config/economy_core/market.json. Plain data, parsed with Gson.
 * {@link MarketPrices} turns the item/tag keys into real items once registries and tags are loaded.
 */
public class MarketConfig {
    private static final Gson GSON = new GsonBuilder().setPrettyPrinting().disableHtmlEscaping().create();

    /** Lowest price as a fraction of fair value, used when a category doesn't set max_drop. */
    @SerializedName("floor_default")
    public double floorDefault = 0.5;

    @SerializedName("autosell_interval_ticks")
    public int autosellIntervalTicks = 100;

    /** Turn the sale celebration effects on or off. */
    @SerializedName("celebrations_enabled")
    public boolean celebrationsEnabled = true;

    /**
     * Minimum coins in one sell action for celebration tiers 2..8 (tier 1 is anything below the first).
     * Small gaps early so new players see them often, wider gaps later, last one is the MEGA tier.
     */
    public List<Long> celebrations = new ArrayList<>(List.of(50L, 200L, 600L, 2000L, 7500L, 30000L, 150000L));

    /**
     * Lifetime earnings milestones. Crossing one grants the advancement economy_core:earned/<amount>,
     * which quest gates check. Keep in sync with data/economy_core/advancement/earned/.
     */
    @SerializedName("earnings_milestones")
    public List<Long> earningsMilestones = new ArrayList<>(List.of(1L, 2000L, 12000L, 48000L, 175000L, 525000L, 1400000L, 4000000L));

    /** Single-sale milestones: a sale worth at least this grants economy_core:sale/<amount>. */
    @SerializedName("sale_milestones")
    public List<Long> saleMilestones = new ArrayList<>(List.of(1000L, 150000L));

    /** Index = tier number (read from the market_tier scoreboard objective). */
    public List<Tier> tiers = new ArrayList<>();

    public Map<String, Category> categories = new LinkedHashMap<>();

    /** Key is an item id ("minecraft:iron_ingot") or an item tag ("#c:ingots/iron"). */
    public Map<String, ItemEntry> items = new LinkedHashMap<>();

    /** Coin item id -> value in the smallest unit. Withdrawals pay largest coins first. */
    public Map<String, Long> coins = new LinkedHashMap<>();

    public static class Tier {
        /** Distinct other goods that must be sold for a depressed item to fully recover. */
        public int variety;
        /** A sale counts toward variety if it is at least this many units... */
        @SerializedName("min_units")
        public int minUnits;
        /** ...or at least this much money. */
        @SerializedName("min_value")
        public long minValue;

        public Tier() {}

        public Tier(int variety, int minUnits, long minValue) {
            this.variety = variety;
            this.minUnits = minUnits;
            this.minValue = minValue;
        }
    }

    public static class Category {
        /** Units until the price has dropped about 2/3 of the way to the floor. */
        @SerializedName("soft_cap")
        public double softCap = 32;
        /** Fraction of fair value the price can drop. 0.5 = floor at 50%. Null = use floor_default. */
        @SerializedName("max_drop")
        public Double maxDrop;

        public Category() {}

        public Category(double softCap, Double maxDrop) {
            this.softCap = softCap;
            this.maxDrop = maxDrop;
        }
    }

    public static class ItemEntry {
        public double base;
        public String category = "misc";

        public ItemEntry() {}

        public ItemEntry(double base, String category) {
            this.base = base;
            this.category = category;
        }
    }

    public Tier tier(int index) {
        if (tiers.isEmpty()) return new Tier(7, 8, 50);
        return tiers.get(Math.max(0, Math.min(index, tiers.size() - 1)));
    }

    public static MarketConfig loadOrCreate(Path file) throws IOException {
        if (!Files.exists(file)) {
            MarketConfig defaults = defaults();
            Files.createDirectories(file.getParent());
            try (Writer w = Files.newBufferedWriter(file)) {
                GSON.toJson(defaults, w);
            }
            return defaults;
        }
        try (Reader r = Files.newBufferedReader(file)) {
            MarketConfig cfg = GSON.fromJson(r, MarketConfig.class);
            return cfg == null ? defaults() : cfg;
        }
    }

    /** The default file written on first run. Prices are in copper coins (1 iron coin = 10 copper). */
    public static MarketConfig defaults() {
        MarketConfig c = new MarketConfig();
        c.tiers.add(new Tier(4, 8, 50));
        c.tiers.add(new Tier(5, 16, 150));
        c.tiers.add(new Tier(6, 32, 400));
        c.tiers.add(new Tier(7, 48, 1000));
        c.tiers.add(new Tier(8, 64, 2500));
        c.tiers.add(new Tier(9, 96, 6000));
        c.tiers.add(new Tier(10, 128, 15000));

        c.categories.put("island", new Category(64, 0.5));
        c.categories.put("crops", new Category(64, 0.5));
        c.categories.put("fish", new Category(32, 0.5));
        c.categories.put("mob_drops", new Category(48, 0.5));
        c.categories.put("metals", new Category(32, 0.5));
        c.categories.put("gems", new Category(16, 0.5));
        c.categories.put("misc", new Category(32, null));

        // Island / sieve goods: cheap and plentiful.
        c.items.put("minecraft:cobblestone", new ItemEntry(1, "island"));
        c.items.put("minecraft:dirt", new ItemEntry(1, "island"));
        c.items.put("minecraft:gravel", new ItemEntry(2, "island"));
        c.items.put("minecraft:sand", new ItemEntry(2, "island"));
        c.items.put("minecraft:flint", new ItemEntry(4, "island"));
        c.items.put("exdeorum:iron_ore_chunk", new ItemEntry(12, "island"));
        c.items.put("exdeorum:gold_ore_chunk", new ItemEntry(20, "island"));
        c.items.put("exdeorum:copper_ore_chunk", new ItemEntry(6, "island"));
        // Crops.
        c.items.put("minecraft:wheat", new ItemEntry(3, "crops"));
        c.items.put("minecraft:potato", new ItemEntry(3, "crops"));
        c.items.put("minecraft:carrot", new ItemEntry(3, "crops"));
        c.items.put("minecraft:beetroot", new ItemEntry(4, "crops"));
        c.items.put("minecraft:pumpkin", new ItemEntry(8, "crops"));
        c.items.put("minecraft:melon_slice", new ItemEntry(2, "crops"));
        c.items.put("minecraft:sugar_cane", new ItemEntry(3, "crops"));
        // Fish.
        c.items.put("minecraft:cod", new ItemEntry(6, "fish"));
        c.items.put("minecraft:salmon", new ItemEntry(8, "fish"));
        c.items.put("minecraft:tropical_fish", new ItemEntry(15, "fish"));
        c.items.put("minecraft:pufferfish", new ItemEntry(15, "fish"));
        // Mob drops.
        c.items.put("minecraft:rotten_flesh", new ItemEntry(1, "mob_drops"));
        c.items.put("minecraft:bone", new ItemEntry(3, "mob_drops"));
        c.items.put("minecraft:string", new ItemEntry(3, "mob_drops"));
        c.items.put("minecraft:gunpowder", new ItemEntry(8, "mob_drops"));
        c.items.put("minecraft:ender_pearl", new ItemEntry(40, "mob_drops"));
        // Metals (tags so modded ingots count too).
        c.items.put("#c:ingots/copper", new ItemEntry(20, "metals"));
        c.items.put("#c:ingots/iron", new ItemEntry(100, "metals"));
        c.items.put("#c:ingots/gold", new ItemEntry(150, "metals"));
        // Gems.
        c.items.put("minecraft:lapis_lazuli", new ItemEntry(30, "gems"));
        c.items.put("minecraft:redstone", new ItemEntry(15, "gems"));
        c.items.put("minecraft:diamond", new ItemEntry(800, "gems"));
        c.items.put("minecraft:emerald", new ItemEntry(400, "gems"));

        // Lightman's Currency main chain: copper=1, iron=10, gold=100, emerald=1000, diamond=10000, netherite=100000.
        c.coins.put("lightmanscurrency:coin_netherite", 100000L);
        c.coins.put("lightmanscurrency:coin_diamond", 10000L);
        c.coins.put("lightmanscurrency:coin_emerald", 1000L);
        c.coins.put("lightmanscurrency:coin_gold", 100L);
        c.coins.put("lightmanscurrency:coin_iron", 10L);
        c.coins.put("lightmanscurrency:coin_copper", 1L);
        return c;
    }
}
