package dev.grant.economycore.power;

import dev.grant.economycore.market.MarketPrices;
import dev.grant.economycore.market.MarketService;
import dev.grant.economycore.market.TeamHelper;
import net.minecraft.server.MinecraftServer;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/**
 * Turns power into coins. Every Power Exchange adds the FE it receives to its team's total for the current second;
 * once a second the team is paid by one curve over all its exchanges, so extra blocks don't multiply the payout:
 *   coins per minute = power_base * (FE per tick / 100) ^ power_exponent   (market.json)
 * With the exponent below 1, 10x more power pays about 4x more, so big plants always earn more but can't run away.
 */
public final class PowerExchangeService {
    private PowerExchangeService() {}

    /** Live numbers per team account, for the block's display. */
    public record Rate(double fePerTick, double coinsPerMinute) {}

    private static final Map<UUID, Long> received = new HashMap<>();
    private static final Map<UUID, UUID> payee = new HashMap<>();
    private static final Map<UUID, Double> remainder = new HashMap<>();
    private static final Map<UUID, Rate> rates = new HashMap<>();
    private static int ticks;

    public static void receive(UUID owner, long fe) {
        UUID team = TeamHelper.accountId(owner);
        received.merge(team, fe, Long::sum);
        payee.putIfAbsent(team, owner);
    }

    public static Rate rateFor(UUID owner) {
        return rates.getOrDefault(TeamHelper.accountId(owner), new Rate(0, 0));
    }

    public static double coinsPerMinute(double fePerTick) {
        if (fePerTick <= 0) return 0;
        var cfg = MarketPrices.config();
        return cfg.powerBase * Math.pow(fePerTick / 100.0, cfg.powerExponent);
    }

    public static void tick(MinecraftServer server) {
        if (++ticks < 20) return;
        ticks = 0;
        rates.clear();
        for (var e : received.entrySet()) {
            UUID team = e.getKey();
            double fePerTick = e.getValue() / 20.0;
            double cpm = coinsPerMinute(fePerTick);
            double due = cpm / 60.0 + remainder.getOrDefault(team, 0.0);
            long whole = (long) Math.floor(due);
            remainder.put(team, due - whole);
            MarketService.creditIncome(server, payee.get(team), whole);
            rates.put(team, new Rate(fePerTick, cpm));
        }
        received.clear();
        payee.clear();
    }
}
