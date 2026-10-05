package dev.grant.economycore.client;

import dev.grant.economycore.network.ShopBuyPayload;
import dev.grant.economycore.network.ShopSyncPayload;
import net.minecraft.ChatFormatting;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.components.EditBox;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.neoforged.neoforge.network.PacketDistributor;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/**
 * The Supply Market screen, styled like a wooden market stall.
 * Tier tabs across the top (one shelf per market tier, so new players aren't buried), a Machines/Supplies toggle,
 * search (searches every tier), a scrolling grid, and a detail panel with price, buy-back, quantity and Buy.
 */
public class ShopScreen extends Screen {
    private static final int W = 300, H = 210;
    private static final int COLS = 9, ROWS = 6, CELL = 18;
    private static final int GRID_X = 10, GRID_Y = 54;
    private static final int PANEL_X = 182;
    private static final int TIERS = 7;
    private static final String[] CATS = {"machines", "supplies"};
    /** Lifetime earnings and coin fee for each tier's gate quest (matches the quest book). */
    private static final long[][] GATES = {{0, 0}, {4000, 2000}, {24000, 10000}, {96000, 40000}, {350000, 80000}, {1050000, 150000}, {2800000, 300000}};

    // Wood-and-canvas palette.
    private static final int WOOD_DARK = 0xFF3B2716, WOOD = 0xFF6B4A2B;
    private static final int CANVAS = 0xFFE8D9B5, CANVAS_DARK = 0xFFC9B48A, INK = 0xFF3B2716;
    private static final int GOLD = 0xFFFFC94A, RED = 0xFFC0392B, GREEN = 0xFF2E7D32, MUTED = 0xFF8C7B5A;
    /** Light-on-wood palette for tabs and the detail panel. */
    private static final int CREAM = 0xFFF4EBD0, PANEL = 0xFF4A3322, LOCKED_TAB = 0xFF8A7458, SOFT = 0xFFC9B48A,
            SOFT_RED = 0xFFFF8A7A, SOFT_GREEN = 0xFF9BE58A;

    private int left, top;
    private int tier = -1;          // which tier shelf is shown
    private String cat = "machines";
    private int scroll;
    private int selected = -1;      // index into ClientShopCache.entries
    private int lots = 1;
    private EditBox search;
    private Button buy;
    private final List<Integer> visible = new ArrayList<>();

    public ShopScreen() {
        super(Component.translatable("gui.economy_core.shop_title"));
    }

    @Override
    protected void init() {
        left = (width - W) / 2;
        top = (height - H) / 2;
        if (tier < 0) tier = Mth.clamp(ClientShopCache.tier, 0, TIERS - 1); // open on your current tier
        search = new EditBox(font, left + GRID_X + 110, top + 37, COLS * CELL - 110, 12, Component.translatable("gui.economy_core.shop_search"));
        search.setHint(Component.translatable("gui.economy_core.shop_search").withStyle(ChatFormatting.GRAY));
        search.setResponder(s -> { scroll = 0; refilter(); });
        addRenderableWidget(search);

        int px = left + PANEL_X;
        addRenderableWidget(Button.builder(Component.literal("-"), b -> setLots(lots - 1)).bounds(px + 8, top + 138, 16, 16).build());
        addRenderableWidget(Button.builder(Component.literal("+"), b -> setLots(lots + 1)).bounds(px + 84, top + 138, 16, 16).build());
        addRenderableWidget(Button.builder(Component.literal("x8"), b -> setLots(lots == 1 ? 8 : lots + 8)).bounds(px + 8, top + 157, 30, 14).build());
        addRenderableWidget(Button.builder(Component.literal("x64"), b -> setLots(64)).bounds(px + 40, top + 157, 30, 14).build());
        addRenderableWidget(Button.builder(Component.literal("1"), b -> setLots(1)).bounds(px + 72, top + 157, 28, 14).build());
        buy = addRenderableWidget(Button.builder(Component.translatable("gui.economy_core.shop_buy"), b -> doBuy())
                .bounds(px + 8, top + 176, 92, 20).build());
        refilter();
    }

    /** Called when fresh data arrives from the server (after a purchase, or a tier change). */
    public void onSync() {
        refilter();
    }

    private void setLots(int n) {
        lots = Mth.clamp(n, 1, 64);
    }

    private void doBuy() {
        if (selected >= 0) PacketDistributor.sendToServer(new ShopBuyPayload(selected, lots));
    }

    private boolean searching() {
        return search != null && !search.getValue().isBlank();
    }

    private void refilter() {
        visible.clear();
        String q = search == null ? "" : search.getValue().toLowerCase(Locale.ROOT).trim();
        List<ShopSyncPayload.Entry> all = ClientShopCache.entries;
        for (int i = 0; i < all.size(); i++) {
            ShopSyncPayload.Entry e = all.get(i);
            if (!e.category().equals(cat)) continue;
            if (q.isEmpty()) {
                if (e.tier() != tier) continue;   // one shelf per tier
            } else if (!stackOf(e).getHoverName().getString().toLowerCase(Locale.ROOT).contains(q)) {
                continue;                         // search looks across every tier
            }
            visible.add(i);
        }
        visible.sort((a, b) -> {
            var x = all.get(a); var y = all.get(b);
            if (x.tier() != y.tier()) return Integer.compare(x.tier(), y.tier());
            return Long.compare(x.price(), y.price());
        });
    }

    private static ItemStack stackOf(ShopSyncPayload.Entry e) {
        ResourceLocation id = ResourceLocation.tryParse(e.itemId());
        Item item = id == null ? Items.BARRIER : BuiltInRegistries.ITEM.get(id);
        return new ItemStack(item, Math.max(1, e.count()));
    }

    private int tierTabWidth() {
        return (W - 20) / TIERS;
    }

    // ------------------------------------------------------------ input

    @Override
    public boolean mouseClicked(double mx, double my, int button) {
        int tw = tierTabWidth();
        for (int t = 0; t < TIERS; t++) {
            int tx = left + 10 + t * tw, ty = top + 19;
            if (mx >= tx && mx < tx + tw - 2 && my >= ty && my < ty + 14) {
                tier = t; scroll = 0; selected = -1;
                if (search != null) search.setValue("");
                refilter();
                return true;
            }
        }
        for (int c = 0; c < CATS.length; c++) {
            int cx = left + GRID_X + c * 54, cy = top + 37;
            if (mx >= cx && mx < cx + 52 && my >= cy && my < cy + 12) {
                cat = CATS[c]; scroll = 0; selected = -1; refilter();
                return true;
            }
        }
        int cell = cellAt(mx, my);
        if (cell >= 0) {
            selected = visible.get(cell);
            lots = 1;
            return true;
        }
        return super.mouseClicked(mx, my, button);
    }

    @Override
    public boolean mouseScrolled(double mx, double my, double dx, double dy) {
        int maxScroll = Math.max(0, (visible.size() + COLS - 1) / COLS - ROWS);
        scroll = Mth.clamp(scroll - (int) Math.signum(dy), 0, maxScroll);
        return true;
    }

    private int cellAt(double mx, double my) {
        int gx = left + GRID_X, gy = top + GRID_Y;
        if (mx < gx || my < gy || mx >= gx + COLS * CELL || my >= gy + ROWS * CELL) return -1;
        int idx = ((int) (my - gy) / CELL + scroll) * COLS + (int) (mx - gx) / CELL;
        return idx < visible.size() ? idx : -1;
    }

    @Override
    public void tick() {
        if (buy != null) {
            ShopSyncPayload.Entry e = selectedEntry();
            buy.active = e != null && e.tier() <= ClientShopCache.tier && ClientShopCache.balance >= e.price() * lots;
        }
    }

    private ShopSyncPayload.Entry selectedEntry() {
        return selected >= 0 && selected < ClientShopCache.entries.size() ? ClientShopCache.entries.get(selected) : null;
    }

    // ------------------------------------------------------------ drawing

    /**
     * Screen.render() calls this before the widgets. The blur and the stall artwork both go here, so nothing we
     * draw ends up underneath the blur (that is what smeared the title and tabs before).
     */
    @Override
    public void renderBackground(GuiGraphics g, int mx, int my, float pt) {
        super.renderBackground(g, mx, my, pt);
        drawFrame(g);
    }

    @Override
    public void render(GuiGraphics g, int mx, int my, float pt) {
        super.render(g, mx, my, pt); // background + frame, then widgets
        drawGrid(g);
        drawPanel(g);
        drawTooltip(g, mx, my);
    }

    private void drawFrame(GuiGraphics g) {
        g.fill(left - 4, top - 4, left + W + 4, top + H + 4, WOOD_DARK);
        g.fill(left - 2, top - 2, left + W + 2, top + H + 2, WOOD);
        g.fill(left, top, left + W, top + H, CANVAS);
        // Striped awning with a scalloped edge.
        for (int x = 0; x < W; x += 20) {
            g.fill(left + x, top, left + Math.min(W, x + 10), top + 14, 0xFFB03A2E);
            g.fill(left + x + 10, top, left + Math.min(W, x + 20), top + 14, 0xFFF4EBD0);
        }
        for (int x = 0; x < W; x += 10) g.fill(left + x + 2, top + 14, left + x + 8, top + 16, (x / 10) % 2 == 0 ? 0xFFB03A2E : 0xFFF4EBD0);
        // Title on a wooden sign so it reads over the stripes.
        Component title = Component.translatable("gui.economy_core.shop_title").withStyle(ChatFormatting.BOLD);
        int tw = font.width(title) + 12;
        g.fill(left + (W - tw) / 2, top + 1, left + (W + tw) / 2, top + 13, WOOD_DARK);
        g.drawCenteredString(font, title, left + W / 2, top + 3, GOLD);

        // Tier tabs.
        int tabW = tierTabWidth();
        for (int t = 0; t < TIERS; t++) {
            int tx = left + 10 + t * tabW, ty = top + 19;
            boolean on = t == tier && !searching();
            boolean locked = t > ClientShopCache.tier;
            g.fill(tx, ty, tx + tabW - 2, ty + 14, on ? WOOD_DARK : (locked ? LOCKED_TAB : WOOD));
            String label = Component.translatable("gui.economy_core.shop_tab_long", t).getString();
            g.drawCenteredString(font, label, tx + (tabW - 2) / 2, ty + 3, on ? GOLD : (locked ? SOFT : CREAM));
        }
        // Machines / Supplies toggle.
        for (int c = 0; c < CATS.length; c++) {
            int cx = left + GRID_X + c * 54, cy = top + 37;
            boolean on = CATS[c].equals(cat);
            g.fill(cx, cy, cx + 52, cy + 12, on ? WOOD_DARK : WOOD);
            g.drawCenteredString(font, Component.translatable("gui.economy_core.shop_tab_" + CATS[c]), cx + 26, cy + 2, on ? GOLD : CREAM);
        }
        // Grid well and detail panel.
        g.fill(left + GRID_X - 2, top + GRID_Y - 2, left + GRID_X + COLS * CELL + 2, top + GRID_Y + ROWS * CELL + 2, WOOD);
        g.fill(left + PANEL_X, top + 37, left + W - 8, top + H - 8, PANEL);
    }

    private void drawGrid(GuiGraphics g) {
        int gx = left + GRID_X, gy = top + GRID_Y;
        for (int r = 0; r < ROWS; r++) {
            for (int c = 0; c < COLS; c++) {
                int x = gx + c * CELL, y = gy + r * CELL;
                g.fill(x, y, x + CELL - 1, y + CELL - 1, 0xFF8B6B45);
                g.fill(x + 1, y + 1, x + CELL - 1, y + CELL - 1, 0xFFD9C79E);
                int idx = (r + scroll) * COLS + c;
                if (idx >= visible.size()) continue;
                int entry = visible.get(idx);
                ShopSyncPayload.Entry e = ClientShopCache.entries.get(entry);
                ItemStack stack = stackOf(e);
                g.renderItem(stack, x + 1, y + 1);
                g.renderItemDecorations(font, stack, x + 1, y + 1);
                if (e.tier() > ClientShopCache.tier) g.fill(x + 1, y + 1, x + CELL - 1, y + CELL - 1, 0xAA2B2B2B);
                if (entry == selected) g.renderOutline(x, y, CELL - 1, CELL - 1, GOLD);
            }
        }
        if (visible.isEmpty()) {
            g.drawCenteredString(font, Component.translatable("gui.economy_core.shop_empty"), gx + COLS * CELL / 2, gy + ROWS * CELL / 2 - 4, 0xFFF4EBD0);
        }
        int rows = (visible.size() + COLS - 1) / COLS;
        if (rows > ROWS) {
            int barH = ROWS * CELL * ROWS / rows;
            int barY = gy + (ROWS * CELL - barH) * scroll / Math.max(1, rows - ROWS);
            g.fill(gx + COLS * CELL + 2, barY, gx + COLS * CELL + 5, barY + barH, GOLD);
        }
    }

    private void drawPanel(GuiGraphics g) {
        int px = left + PANEL_X + 8, py = top + 41;
        ShopSyncPayload.Entry e = selectedEntry();
        if (e == null) {
            int shelf = searching() ? ClientShopCache.tier : tier;
            g.drawString(font, tierName(shelf).copy().withStyle(ChatFormatting.BOLD), px, py + 2, GOLD, false);
            g.drawString(font, Component.translatable("gui.economy_core.shop_tab_long", shelf), px, py + 13, SOFT, false);
            Component body = shelf > ClientShopCache.tier
                    ? Component.translatable("gui.economy_core.shop_shelf_locked", shelf, fmt(GATES[shelf][0]), fmt(GATES[shelf][1]))
                    : Component.translatable("gui.economy_core.shop_blurb_" + shelf);
            g.drawWordWrap(font, body, px, py + 28, 94, shelf > ClientShopCache.tier ? SOFT_RED : CREAM);
            return;
        }
        ItemStack stack = stackOf(e);
        var pose = g.pose();
        pose.pushPose();
        pose.translate(px + 31, py, 0);
        pose.scale(2f, 2f, 1f);
        g.renderItem(stack, 0, 0);
        pose.popPose();
        g.drawWordWrap(font, stack.getHoverName(), px, py + 36, 94, CREAM);

        int y = py + 60;
        if (e.tier() > ClientShopCache.tier) {
            g.drawWordWrap(font, Component.translatable("gui.economy_core.shop_tier", e.tier(), tierName(e.tier())), px, y, 94, SOFT_RED);
        } else {
            long cost = e.price() * lots;
            g.drawString(font, Component.translatable("gui.economy_core.shop_price", fmt(cost)), px, y,
                    ClientShopCache.balance >= cost ? SOFT_GREEN : SOFT_RED, false);
            if (e.buyback() > 0) {
                g.drawString(font, Component.translatable("gui.economy_core.shop_buyback", fmt(e.buyback())), px, y + 11, CREAM, false);
            } else {
                g.drawString(font, Component.translatable("gui.economy_core.shop_no_buyback"), px, y + 11, SOFT, false);
            }
        }
        // Quantity readout between the - and + buttons.
        g.drawCenteredString(font, "x" + lots + (e.count() > 1 ? " (" + e.count() * lots + ")" : ""), left + PANEL_X + 54, top + 142, 0xFFFFFF);
    }

    private static Component tierName(int t) {
        return Component.translatable("gui.economy_core.tier_name_" + Mth.clamp(t, 0, TIERS - 1));
    }

    private void drawTooltip(GuiGraphics g, int mx, int my) {
        int tw = tierTabWidth();
        for (int t = 0; t < TIERS; t++) {
            int tx = left + 10 + t * tw, ty = top + 19;
            if (mx >= tx && mx < tx + tw - 2 && my >= ty && my < ty + 14) {
                List<Component> tip = new ArrayList<>();
                tip.add(Component.translatable("gui.economy_core.shop_tab_long", t).append(" \u00b7 ").append(tierName(t)).withStyle(ChatFormatting.GOLD));
                if (t <= ClientShopCache.tier) {
                    tip.add(Component.translatable(t == ClientShopCache.tier ? "gui.economy_core.shop_tab_current" : "gui.economy_core.shop_tab_open").withStyle(ChatFormatting.GREEN));
                } else {
                    tip.add(Component.translatable("gui.economy_core.shop_tab_locked", fmt(GATES[t][0]), fmt(GATES[t][1])).withStyle(ChatFormatting.RED));
                }
                g.renderComponentTooltip(font, tip, mx, my);
                return;
            }
        }
        int cell = cellAt(mx, my);
        if (cell < 0) return;
        ShopSyncPayload.Entry e = ClientShopCache.entries.get(visible.get(cell));
        List<Component> lines = new ArrayList<>();
        lines.add(stackOf(e).getHoverName());
        if (e.tier() > ClientShopCache.tier) {
            lines.add(Component.translatable("gui.economy_core.shop_tier", e.tier(), tierName(e.tier())).withStyle(ChatFormatting.RED));
        } else {
            lines.add(Component.translatable("gui.economy_core.shop_price", fmt(e.price())).withStyle(ChatFormatting.GOLD));
            if (e.buyback() > 0) lines.add(Component.translatable("gui.economy_core.shop_buyback", fmt(e.buyback())).withStyle(ChatFormatting.GRAY));
        }
        if (searching()) lines.add(Component.translatable("gui.economy_core.shop_from_shelf", e.tier(), tierName(e.tier())).withStyle(ChatFormatting.DARK_GRAY));
        g.renderComponentTooltip(font, lines, mx, my);
    }

    static Item coin(String path) {
        Item i = BuiltInRegistries.ITEM.get(ResourceLocation.fromNamespaceAndPath("lightmanscurrency", path));
        return i == Items.AIR ? Items.GOLD_NUGGET : i;
    }

    private static String fmt(long v) {
        return String.format("%,d", v);
    }

    @Override
    public boolean isPauseScreen() {
        return false;
    }
}
