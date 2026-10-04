package dev.grant.economycore.market;

import net.minecraft.advancements.AdvancementHolder;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.scores.Objective;
import net.minecraft.world.scores.ReadOnlyScoreInfo;
import net.minecraft.world.scores.ScoreHolder;
import net.minecraft.world.scores.Scoreboard;
import net.minecraft.world.scores.criteria.ObjectiveCriteria;
import net.neoforged.neoforge.items.ItemHandlerHelper;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * Server-side selling logic: applies {@link PriceMath} to the saved market state,
 * credits the seller's balance and keeps the scoreboard objectives up to date.
 */
public final class MarketService {
    public static final String TIER_OBJECTIVE = "market_tier";
    public static final String EARNED_OBJECTIVE = "market_earned";

    private MarketService() {}

    /** Which saturation scope a seller uses. Global for v0.1; return uuid.toString() for per-player prices. */
    public static String scopeFor(UUID seller) {
        return MarketData.GLOBAL_SCOPE;
    }

    public static String itemId(Item item) {
        return BuiltInRegistries.ITEM.getKey(item).toString();
    }

    // ---------------------------------------------------------------- quotes

    /** What the next unit would sell for, and how much variety is still needed to fully recover. */
    public record Quote(double unitPrice, double fairPrice, int distinctRemaining) {}

    public static Quote quote(MinecraftServer server, UUID seller, String sellerName, Item item) {
        MarketPrices.Pricing p = MarketPrices.get(item);
        if (p == null) return null;
        MarketConfig.Tier tier = MarketPrices.config().tier(getTier(server, sellerName));
        MarketData.ItemState st = MarketData.get(server).peek(scopeFor(seller), itemId(item));
        double saved = st == null ? 0 : st.saturation;
        int since = st == null ? 0 : st.distinctSince.size();
        double eff = PriceMath.effectiveSaturation(saved, since, tier.variety);
        return new Quote(PriceMath.unitPrice(p.base(), p.maxDrop(), eff), p.base(),
                PriceMath.distinctRemaining(saved, since, tier.variety));
    }

    /** Coins that selling {@code units} right now would pay, without changing anything. */
    public static long preview(MinecraftServer server, UUID seller, String sellerName, Item item, int units) {
        MarketPrices.Pricing p = MarketPrices.get(item);
        if (p == null || units <= 0) return 0;
        MarketConfig.Tier tier = MarketPrices.config().tier(getTier(server, sellerName));
        MarketData.ItemState st = MarketData.get(server).peek(scopeFor(seller), itemId(item));
        double start = st == null ? 0 : PriceMath.effectiveSaturation(st.saturation, st.distinctSince.size(), tier.variety);
        return (long) Math.floor(PriceMath.sell(p.base(), p.maxDrop(), p.softCap(), start, units).total());
    }

    // ---------------------------------------------------------------- selling

    /** Result of one sell action. */
    public record Sale(Item item, int units, long coins) {}

    /**
     * Sell {@code units} of one item as a single action. The caller has already removed the items.
     * Returns coins credited (rounded down; at least 0).
     */
    public static Sale sell(MinecraftServer server, UUID seller, String sellerName, Item item, int units) {
        return sell(server, seller, sellerName, item, units, units);
    }

    /**
     * @param qualifyingUnits units to use for the variety check. Auto-sell sells in small chunks, so it passes
     *                        the running total for that item, letting a stream of chunks count like one batch.
     */
    public static Sale sell(MinecraftServer server, UUID seller, String sellerName, Item item, int units, int qualifyingUnits) {
        MarketPrices.Pricing p = MarketPrices.get(item);
        if (p == null || units <= 0) return new Sale(item, 0, 0);

        MarketData data = MarketData.get(server);
        String scope = scopeFor(seller);
        String id = itemId(item);
        MarketConfig.Tier tier = MarketPrices.config().tier(getTier(server, sellerName));

        // Start from the recovered (effective) saturation, then sell unit by unit.
        MarketData.ItemState st = data.state(scope, id);
        double start = PriceMath.effectiveSaturation(st.saturation, st.distinctSince.size(), tier.variety);
        PriceMath.SaleResult r = PriceMath.sell(p.base(), p.maxDrop(), p.softCap(), start, units);
        long coins = (long) Math.floor(r.total());

        // Selling this item again restarts its recovery.
        st.saturation = r.endSaturation();
        st.distinctSince.clear();

        // A big enough sale counts as "variety" for every other depressed item.
        boolean qualifies = Math.max(units, qualifyingUnits) >= tier.minUnits || coins >= tier.minValue;
        if (qualifies) {
            var it = data.scope(scope).entrySet().iterator();
            while (it.hasNext()) {
                Map.Entry<String, MarketData.ItemState> e = it.next();
                if (e.getKey().equals(id)) continue;
                MarketData.ItemState other = e.getValue();
                other.distinctSince.add(id);
                // Fully recovered at the highest tier's variety: forget it to keep the save small.
                if (other.distinctSince.size() >= maxVariety()) it.remove();
            }
        }

        MarketData.Account acc = data.account(seller);
        acc.balance += coins;
        acc.earned += coins;
        acc.sold.add(id);
        boolean diminished = PriceMath.unitPrice(p.base(), p.maxDrop(), start) < 0.9 * p.base();
        data.setDirty();
        setScore(server, sellerName, EARNED_OBJECTIVE, (int) Math.min(Integer.MAX_VALUE, acc.earned));
        ServerPlayer online = server.getPlayerList().getPlayer(seller);
        if (online != null) {
            awardMilestones(online, acc.earned, coins);
            if (acc.sold.size() >= 5) award(online, "distinct/5");
            if (diminished) award(online, "diminished");
        }
        return new Sale(item, units, coins);
    }

    private static int maxVariety() {
        int max = 0;
        for (MarketConfig.Tier t : MarketPrices.config().tiers) max = Math.max(max, t.variety);
        return max <= 0 ? 10 : max;
    }

    // ---------------------------------------------------------------- milestones (read by quest gates)

    /**
     * Grant the earnings advancements the player has reached, plus any single-sale advancements for this sale.
     * Pass saleCoins = 0 to only check lifetime earnings (e.g. on login, after offline auto-selling).
     */
    public static void awardMilestones(ServerPlayer player, long lifetimeEarned, long saleCoins) {
        MarketConfig cfg = MarketPrices.config();
        for (Long m : cfg.earningsMilestones) {
            if (m != null && lifetimeEarned >= m) award(player, "earned/" + m);
        }
        for (Long m : cfg.saleMilestones) {
            if (m != null && saleCoins >= m) award(player, "sale/" + m);
        }
    }

    /** Grant economy_core:<path> if it exists and isn't done yet. */
    public static void award(ServerPlayer player, String path) {
        AdvancementHolder adv = player.server.getAdvancements()
                .get(ResourceLocation.fromNamespaceAndPath("economy_core", path));
        if (adv == null) return;
        var progress = player.getAdvancements().getOrStartProgress(adv);
        if (progress.isDone()) return;
        for (String criterion : progress.getRemainingCriteria()) player.getAdvancements().award(adv, criterion);
    }

    /** Auto-sell chunk size for a market tier: 2 units at tier 0, doubling per tier, capped at a full stack. */
    public static int autosellChunk(int tier) {
        return (int) Math.min(64, 2L << Math.min(tier, 5));
    }

    // ---------------------------------------------------------------- deposit

    /** Coins put back into a crate: straight to the balance. Not a sale (no earnings, no price effects). */
    public static void deposit(MinecraftServer server, UUID owner, long amount) {
        if (amount <= 0) return;
        MarketData data = MarketData.get(server);
        data.account(owner).balance += amount;
        data.setDirty();
    }

    // ---------------------------------------------------------------- celebrations

    /** 1..8 for a sale of this size, or 0 if celebrations are switched off. */
    public static int celebrationTier(long coins) {
        MarketConfig cfg = MarketPrices.config();
        if (!cfg.celebrationsEnabled || coins <= 0) return 0;
        int tier = 1;
        for (Long t : cfg.celebrations) if (t != null && coins >= t) tier++;
        return Math.min(tier, 8);
    }

    // ---------------------------------------------------------------- withdraw

    /** At most this many coins of one kind per click, so a huge balance doesn't flood the floor. */
    private static final int MAX_COINS_PER_WITHDRAW = 576;

    /**
     * Pay out the player's balance as coin items. coinIndex = position in the configured coins sorted
     * largest first; -1 = mix of denominations, largest first. Whatever can't be paid exactly stays.
     */
    public static long withdraw(ServerPlayer player, int coinIndex) {
        if (coinIndex < 0) return withdraw(player);
        MarketData data = MarketData.get(player.server);
        MarketData.Account acc = data.account(player.getUUID());
        List<Map.Entry<Item, Long>> coins = sortedCoins();
        if (coinIndex >= coins.size()) return 0;
        var c = coins.get(coinIndex);
        long n = Math.min(acc.balance / c.getValue(), MAX_COINS_PER_WITHDRAW);
        if (n <= 0) return 0;
        acc.balance -= n * c.getValue();
        give(player, c.getKey(), n);
        data.setDirty();
        return n * c.getValue();
    }

    private static List<Map.Entry<Item, Long>> sortedCoins() {
        List<Map.Entry<Item, Long>> coins = new ArrayList<>();
        for (var e : MarketPrices.config().coins.entrySet()) {
            ResourceLocation id = ResourceLocation.tryParse(e.getKey());
            if (id == null || !BuiltInRegistries.ITEM.containsKey(id) || e.getValue() == null || e.getValue() <= 0) continue;
            coins.add(Map.entry(BuiltInRegistries.ITEM.get(id), e.getValue()));
        }
        coins.sort((a, b) -> Long.compare(b.getValue(), a.getValue()));
        return coins;
    }

    private static void give(ServerPlayer player, Item item, long n) {
        int max = new ItemStack(item).getMaxStackSize();
        while (n > 0) {
            int g = (int) Math.min(n, max);
            ItemHandlerHelper.giveItemToPlayer(player, new ItemStack(item, g));
            n -= g;
        }
    }

    /** Pay out the player's balance in coin items, largest denominations first. Remainder stays. */
    public static long withdraw(ServerPlayer player) {
        MarketData data = MarketData.get(player.server);
        MarketData.Account acc = data.account(player.getUUID());
        List<Map.Entry<Item, Long>> coins = new ArrayList<>();
        for (var e : MarketPrices.config().coins.entrySet()) {
            ResourceLocation id = ResourceLocation.tryParse(e.getKey());
            if (id == null || !BuiltInRegistries.ITEM.containsKey(id) || e.getValue() <= 0) continue;
            coins.add(Map.entry(BuiltInRegistries.ITEM.get(id), e.getValue()));
        }
        coins.sort((a, b) -> Long.compare(b.getValue(), a.getValue()));

        long paid = 0;
        for (var c : coins) {
            long n = acc.balance / c.getValue();
            if (n <= 0) continue;
            acc.balance -= n * c.getValue();
            paid += n * c.getValue();
            int max = new ItemStack(c.getKey()).getMaxStackSize();
            while (n > 0) {
                int give = (int) Math.min(n, max);
                ItemHandlerHelper.giveItemToPlayer(player, new ItemStack(c.getKey(), give));
                n -= give;
            }
        }
        data.setDirty();
        return paid;
    }

    // ---------------------------------------------------------------- scoreboard

    public static void ensureObjectives(MinecraftServer server) {
        objective(server, TIER_OBJECTIVE, "Market Tier");
        objective(server, EARNED_OBJECTIVE, "Market Earnings");
    }

    private static Objective objective(MinecraftServer server, String name, String display) {
        Scoreboard sb = server.getScoreboard();
        Objective o = sb.getObjective(name);
        if (o == null) {
            o = sb.addObjective(name, ObjectiveCriteria.DUMMY, Component.literal(display),
                    ObjectiveCriteria.RenderType.INTEGER, false, null);
        }
        return o;
    }

    public static int getTier(MinecraftServer server, String playerName) {
        if (playerName == null || playerName.isEmpty()) return 0;
        Objective o = server.getScoreboard().getObjective(TIER_OBJECTIVE);
        if (o == null) return 0;
        ReadOnlyScoreInfo info = server.getScoreboard().getPlayerScoreInfo(ScoreHolder.forNameOnly(playerName), o);
        return info == null ? 0 : Math.max(0, info.value());
    }

    public static void setTier(MinecraftServer server, String playerName, int tier) {
        setScore(server, playerName, TIER_OBJECTIVE, tier);
    }

    private static void setScore(MinecraftServer server, String playerName, String objective, int value) {
        if (playerName == null || playerName.isEmpty()) return;
        Objective o = objective(server, objective, objective);
        server.getScoreboard().getOrCreatePlayerScore(ScoreHolder.forNameOnly(playerName), o).set(value);
    }
}
