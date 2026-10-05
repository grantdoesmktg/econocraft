package dev.grant.economycore.market;

/**
 * Pure pricing math for the Market. No Minecraft classes, so it can be unit tested directly.
 *
 * Model (per item):
 *   - saturation s in [0, 1]. Price per unit = base * (1 - maxDrop * s).
 *     With maxDrop = 0.5 the price never falls below 50% of fair value.
 *   - Every unit sold is paid at the current price, then saturation grows:
 *     s = 1 - (1 - s) * exp(-1 / softCap). softCap is "how many units until the price is ~2/3 of the way down".
 *   - Recovery is driven by variety, not time. Each item remembers S (saturation right after its last sale)
 *     and how many *other* distinct goods have been sold (in qualifying amounts) since then.
 *     Effective saturation = S * max(0, 1 - distinctSince / V), where V comes from the player's tier.
 */
public final class PriceMath {
    private PriceMath() {}

    /** Saturation after accounting for recovery from selling other goods. */
    public static double effectiveSaturation(double savedSaturation, int distinctSince, int varietyNeeded) {
        if (varietyNeeded <= 0) return 0.0;
        double recovered = Math.max(0.0, 1.0 - (double) distinctSince / varietyNeeded);
        return clamp01(savedSaturation * recovered);
    }

    /** Price of one unit at the given saturation. */
    public static double unitPrice(double base, double maxDrop, double saturation) {
        return base * (1.0 - clamp01(maxDrop) * clamp01(saturation));
    }

    /** Saturation after one more unit is sold. */
    public static double nextSaturation(double saturation, double softCap) {
        if (softCap <= 0) return 1.0;
        return 1.0 - (1.0 - clamp01(saturation)) * Math.exp(-1.0 / softCap);
    }

    /** How many more distinct goods must be sold before this item is back at fair value. */
    public static int distinctRemaining(double savedSaturation, int distinctSince, int varietyNeeded) {
        if (savedSaturation <= 0.0) return 0;
        return Math.max(0, varietyNeeded - distinctSince);
    }

    /** Result of selling a batch of one item. */
    public record SaleResult(double total, double endSaturation, double firstUnitPrice, double lastUnitPrice) {}

    /** Sell {@code units} one at a time starting from {@code startSaturation}. */
    public static SaleResult sell(double base, double maxDrop, double softCap, double startSaturation, int units) {
        double s = clamp01(startSaturation);
        double total = 0.0;
        double first = unitPrice(base, maxDrop, s);
        double last = first;
        for (int i = 0; i < units; i++) {
            last = unitPrice(base, maxDrop, s);
            total += last;
            s = nextSaturation(s, softCap);
        }
        return new SaleResult(total, s, first, last);
    }

    private static double clamp01(double v) {
        return v < 0 ? 0 : (v > 1 ? 1 : v);
    }
}
