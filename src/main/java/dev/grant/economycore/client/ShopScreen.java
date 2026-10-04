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
 * The Supply Market screen: category tabs, search, a scrolling grid of listings, and a detail panel
 * with price, buy-back value, quantity and Buy. Styled like a wooden market stall.
 */
public class ShopScreen extends Screen {
    private static final int W = 300, H = 206;
    private static final int COLS = 9, ROWS = 6, CELL = 18;
    private static final int GRID_X = 10, GRID_Y = 52;
    private static final int PANEL_X = 182;
    private static final String[] TABS = {"machines", "supplies"};

    // Wood-and-canvas palette.
    private static final int WOOD_DARK = 0xFF3B2716, WOOD = 0xFF6B4A2B, WOOD_LIGHT = 0xFF8A6239;
    private static final int CANVAS = 0xFFE8D9B5, CANVAS_DARK = 0xFFC9B48A, INK = 0xFF3B2716;
    private static final int GOLD = 0xFFFFC94A, RED = 0xFFC0392B, GREEN = 0xFF2E7D32;

    private int left, top;
    private String tab = "machines";
    private int scroll;
    private int selected = -1;     // index into ClientShopCache.entries
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
        search = new EditBox(font, left + GRID_X, top + 34, COLS * CELL, 12, Component.translatable("gui.economy_core.shop_search"));
        search.setHint(Component.translatable("gui.economy_core.shop_search").withStyle(ChatFormatting.GRAY));
        search.setResponder(s -> { scroll = 0; refilter(); });
        addRenderableWidget(search);

        int px = left + PANEL_X;
        addRenderableWidget(Button.builder(Component.literal("-"), b -> setLots(lots - 1)).bounds(px + 8, top + 136, 16, 16).build());
        addRenderableWidget(Button.builder(Component.literal("+"), b -> setLots(lots + 1)).bounds(px + 84, top + 136, 16, 16).build());
        addRenderableWidget(Button.builder(Component.literal("x8"), b -> setLots(lots == 1 ? 8 : lots + 8)).bounds(px + 8, top + 156, 30, 14).build());
        addRenderableWidget(Button.builder(Component.literal("x64"), b -> setLots(64)).bounds(px + 40, top + 156, 30, 14).build());
        addRenderableWidget(Button.builder(Component.literal("1"), b -> setLots(1)).bounds(px + 72, top + 156, 28, 14).build());
        buy = addRenderableWidget(Button.builder(Component.translatable("gui.economy_core.shop_buy"), b -> doBuy())
                .bounds(px + 8, top + 174, 92, 20).build());
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

    private void refilter() {
        visible.clear();
        String q = search == null ? "" : search.getValue().toLowerCase(Locale.ROOT);
        List<ShopSyncPayload.Entry> all = ClientShopCache.entries;
        for (int i = 0; i < all.size(); i++) {
            ShopSyncPayload.Entry e = all.get(i);
            if (!e.category().equals(tab)) continue;
            if (!q.isEmpty() && !stackOf(e).getHoverName().getString().toLowerCase(Locale.ROOT).contains(q)) continue;
            visible.add(i);
        }
        // Unlocked first, then by tier and price.
        visible.sort((a, b) -> {
            var x = all.get(a); var y = all.get(b);
            boolean la = x.tier() > ClientShopCache.tier, lb = y.tier() > ClientShopCache.tier;
            if (la != lb) return la ? 1 : -1;
            if (x.tier() != y.tier()) return Integer.compare(x.tier(), y.tier());
            return Long.compare(x.price(), y.price());
        });
    }

    private static ItemStack stackOf(ShopSyncPayload.Entry e) {
        ResourceLocation id = ResourceLocation.tryParse(e.itemId());
        Item item = id == null ? Items.BARRIER : BuiltInRegistries.ITEM.get(id);
        return new ItemStack(item, Math.max(1, e.count()));
    }

    // ------------------------------------------------------------ input

    @Override
    public boolean mouseClicked(double mx, double my, int button) {
        for (int t = 0; t < TABS.length; t++) {
            int tx = left + GRID_X + t * 82, ty = top + 18;
            if (mx >= tx && mx < tx + 80 && my >= ty && my < ty + 13) {
                tab = TABS[t]; scroll = 0; selected = -1; refilter();
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

    // ------------------------------------------------------------ drawing

    @Override
    public void tick() {
        // Keep the list fresh after purchases / tier changes.
        if (visible.isEmpty() && !ClientShopCache.entries.isEmpty()) refilter();
        if (buy != null) {
            ShopSyncPayload.Entry e = selectedEntry();
            buy.active = e != null && e.tier() <= ClientShopCache.tier && ClientShopCache.balance >= e.price() * lots;
        }
    }

    private ShopSyncPayload.Entry selectedEntry() {
        return selected >= 0 && selected < ClientShopCache.entries.size() ? ClientShopCache.entries.get(selected) : null;
    }

    @Override
    public void render(GuiGraphics g, int mx, int my, float pt) {
        renderBackground(g, mx, my, pt);
        drawFrame(g);
        super.render(g, mx, my, pt);
        drawGrid(g, mx, my);
        drawPanel(g);
        drawTooltip(g, mx, my);
    }

    private void drawFrame(GuiGraphics g) {
        // Wooden frame, canvas body, striped awning across the top.
        g.fill(left - 4, top - 4, left + W + 4, top + H + 4, WOOD_DARK);
        g.fill(left - 2, top - 2, left + W + 2, top + H + 2, WOOD);
        g.fill(left, top, left + W, top + H, CANVAS);
        for (int x = 0; x < W; x += 20) {
            g.fill(left + x, top, left + Math.min(W, x + 10), top + 14, 0xFFB03A2E);
            g.fill(left + x + 10, top, left + Math.min(W, x + 20), top + 14, 0xFFF4EBD0);
        }
        for (int x = 0; x < W; x += 10) g.fill(left + x + 2, top + 14, left + x + 8, top + 16, (x / 10) % 2 == 0 ? 0xFFB03A2E : 0xFFF4EBD0);
        g.drawCenteredString(font, Component.translatable("gui.economy_core.shop_title").withStyle(ChatFormatting.BOLD), left + W / 2, top + 3, 0xFFFFFF);

        // Tabs.
        for (int t = 0; t < TABS.length; t++) {
            int tx = left + GRID_X + t * 82, ty = top + 18;
            boolean on = TABS[t].equals(tab);
            g.fill(tx, ty, tx + 80, ty + 13, on ? WOOD : CANVAS_DARK);
            g.drawCenteredString(font, Component.translatable("gui.economy_core.shop_tab_" + TABS[t]), tx + 40, ty + 3, on ? GOLD : INK);
        }
        // Grid well and detail panel.
        g.fill(left + GRID_X - 2, top + GRID_Y - 2, left + GRID_X + COLS * CELL + 2, top + GRID_Y + ROWS * CELL + 2, WOOD);
        g.fill(left + PANEL_X, top + 18, left + W - 8, top + H - 8, CANVAS_DARK);
    }

    private void drawGrid(GuiGraphics g, int mx, int my) {
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
                if (entry == selected) {
                    g.renderOutline(x, y, CELL - 1, CELL - 1, GOLD);
                }
            }
        }
        // Scroll hint.
        int rows = (visible.size() + COLS - 1) / COLS;
        if (rows > ROWS) {
            int barH = ROWS * CELL * ROWS / rows;
            int barY = gy + (ROWS * CELL - barH) * scroll / Math.max(1, rows - ROWS);
            g.fill(gx + COLS * CELL + 2, barY, gx + COLS * CELL + 5, barY + barH, GOLD);
        }
    }

    private void drawPanel(GuiGraphics g) {
        int px = left + PANEL_X + 8, py = top + 22;
        // Balance (always shown).
        g.renderItem(new ItemStack(coin("coin_gold")), px - 2, top + H - 26);
        g.drawString(font, fmt(ClientShopCache.balance), px + 16, top + H - 22, INK, false);

        ShopSyncPayload.Entry e = selectedEntry();
        if (e == null) {
            g.drawWordWrap(font, Component.translatable("gui.economy_core.shop_pick"), px, py + 4, 92, INK);
            return;
        }
        ItemStack stack = stackOf(e);
        var pose = g.pose();
        pose.pushPose();
        pose.translate(px + 30, py, 0);
        pose.scale(2f, 2f, 1f);
        g.renderItem(stack, 0, 0);
        pose.popPose();
        g.drawWordWrap(font, stack.getHoverName(), px, py + 36, 92, INK);

        boolean locked = e.tier() > ClientShopCache.tier;
        int y = py + 58;
        if (locked) {
            g.drawString(font, Component.translatable("gui.economy_core.shop_tier", e.tier()), px, y, RED, false);
        } else {
            long cost = e.price() * lots;
            g.drawString(font, Component.translatable("gui.economy_core.shop_price", fmt(cost)), px, y,
                    ClientShopCache.balance >= cost ? GREEN : RED, false);
            if (e.buyback() > 0) {
                g.drawString(font, Component.translatable("gui.economy_core.shop_buyback", fmt(e.buyback())), px, y + 11, INK, false);
            } else {
                g.drawString(font, Component.translatable("gui.economy_core.shop_no_buyback"), px, y + 11, 0xFF7A6A4A, false);
            }
        }
        // Quantity readout between the - and + buttons.
        g.drawCenteredString(font, "x" + lots + (e.count() > 1 ? " (" + e.count() * lots + ")" : ""), left + PANEL_X + 54, top + 140, 0xFFFFFF);
    }

    private void drawTooltip(GuiGraphics g, int mx, int my) {
        int cell = cellAt(mx, my);
        if (cell < 0) return;
        ShopSyncPayload.Entry e = ClientShopCache.entries.get(visible.get(cell));
        ItemStack stack = stackOf(e);
        List<Component> lines = new ArrayList<>();
        lines.add(stack.getHoverName());
        if (e.tier() > ClientShopCache.tier) {
            lines.add(Component.translatable("gui.economy_core.shop_tier", e.tier()).withStyle(ChatFormatting.RED));
        } else {
            lines.add(Component.translatable("gui.economy_core.shop_price", fmt(e.price())).withStyle(ChatFormatting.GOLD));
            if (e.buyback() > 0) lines.add(Component.translatable("gui.economy_core.shop_buyback", fmt(e.buyback())).withStyle(ChatFormatting.GRAY));
        }
        g.renderComponentTooltip(font, lines, mx, my);
    }

    private static Item coin(String path) {
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
