package dev.grant.economycore.market;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class PriceMathTest {
    private static final double BASE = 100, DROP = 0.5, SOFT_CAP = 32;

    @Test
    void firstUnitSellsAtFairValue() {
        var r = PriceMath.sell(BASE, DROP, SOFT_CAP, 0.0, 1);
        assertEquals(100.0, r.firstUnitPrice(), 1e-9);
        assertEquals(100.0, r.total(), 1e-9);
    }

    @Test
    void after64UnitsPriceIsAbout57() {
        var r = PriceMath.sell(BASE, DROP, SOFT_CAP, 0.0, 64);
        double next = PriceMath.unitPrice(BASE, DROP, r.endSaturation());
        assertEquals(56.8, next, 0.2);
    }

    @Test
    void priceApproachesButNeverGoesBelowFloor() {
        var r = PriceMath.sell(BASE, DROP, SOFT_CAP, 0.0, 5000);
        double next = PriceMath.unitPrice(BASE, DROP, r.endSaturation());
        assertTrue(next >= 50.0, "never below 50% of fair value");
        assertEquals(50.0, next, 0.01);
    }

    @Test
    void sevenDistinctSalesAtTier3RestoreFairValue() {
        double s = PriceMath.sell(BASE, DROP, SOFT_CAP, 0.0, 64).endSaturation();
        double eff = PriceMath.effectiveSaturation(s, 7, 7);
        assertEquals(100.0, PriceMath.unitPrice(BASE, DROP, eff), 1e-9);
        assertEquals(0, PriceMath.distinctRemaining(s, 7, 7));
    }

    @Test
    void threeDistinctSalesAtTier3PartiallyRecover() {
        double s = PriceMath.sell(BASE, DROP, SOFT_CAP, 0.0, 64).endSaturation();
        double eff = PriceMath.effectiveSaturation(s, 3, 7);
        double price = PriceMath.unitPrice(BASE, DROP, eff);
        // 1 - 0.5 * 0.8647 * (4/7) = ~75.3
        assertEquals(75.3, price, 0.5);
        assertEquals(4, PriceMath.distinctRemaining(s, 3, 7));
    }

    @Test
    void sellingAStackHasDiminishingReturns() {
        var one = PriceMath.sell(BASE, DROP, SOFT_CAP, 0.0, 1);
        var stack = PriceMath.sell(BASE, DROP, SOFT_CAP, 0.0, 64);
        assertTrue(stack.total() < 64 * one.total());
        assertTrue(stack.lastUnitPrice() < stack.firstUnitPrice());
    }

    @Test
    void untouchedItemHasNothingToRecover() {
        assertEquals(0, PriceMath.distinctRemaining(0.0, 0, 7));
    }
}
