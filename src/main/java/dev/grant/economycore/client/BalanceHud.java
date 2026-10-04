package dev.grant.economycore.client;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.screens.PauseScreen;
import net.minecraft.world.item.ItemStack;

/**
 * The always-on balance counter in the bottom-left corner: on the HUD and on top of every in-game screen,
 * sitting just right of where JEI puts its bookmarks button.
 */
public final class BalanceHud {
    public static long balance;
    public static boolean known;

    private BalanceHud() {}

    public static void render(GuiGraphics g) {
        Minecraft mc = Minecraft.getInstance();
        if (!known || mc.player == null || mc.options.hideGui || mc.screen instanceof PauseScreen) return;
        String text = String.format("%,d", balance);
        int w = mc.font.width(text) + 24;
        int x = 26, y = g.guiHeight() - 20;
        var pose = g.pose();
        pose.pushPose();
        pose.translate(0, 0, 450); // above screen contents and tooltips' backgrounds
        g.fill(x, y, x + w, y + 18, 0xA0101018);
        g.fill(x, y, x + w, y + 1, 0xFFD4A017);
        g.renderItem(new ItemStack(ShopScreen.coin(balance >= 1000 ? "coin_emerald" : "coin_gold")), x + 2, y + 1);
        g.drawString(mc.font, text, x + 20, y + 5, 0xFFFFD54F, true);
        pose.popPose();
    }

    public static void set(long value) {
        balance = value;
        known = true;
        ClientMarketCache.balance = value;
    }
}
