package dev.grant.economycore.client;

import dev.grant.economycore.menu.MarketMenu;
import dev.grant.economycore.network.MarketActionPayload;
import dev.grant.economycore.network.MarketSyncPayload;
import net.minecraft.ChatFormatting;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.neoforged.neoforge.network.PacketDistributor;

import java.util.ArrayList;
import java.util.List;

/**
 * Large-chest style screen with a market panel on the right: balance with coin icon,
 * an "item to sell" slot with live price info, and the sell / auto-sell / withdraw buttons.
 */
public class MarketScreen extends AbstractContainerScreen<MarketMenu> {
    private static final ResourceLocation CHEST = ResourceLocation.withDefaultNamespace("textures/gui/container/generic_54.png");
    private static final int CHEST_W = 176;
    private static final int PANEL_X = 180, PANEL_W = 112;
    private static final int TEXT = 0x404040, MONEY = 0x7A5C00, GOOD = 0x1E7A1E, MID = 0x8A6A00, BAD = 0xA02020;

    private Button sellStack, sellAllOf, autoSell;

    public MarketScreen(MarketMenu menu, Inventory inv, Component title) {
        super(menu, inv, title);
        imageWidth = PANEL_X + PANEL_W;
        imageHeight = 114 + MarketMenu.ROWS * 18;
        inventoryLabelY = imageHeight - 94;
    }

    @Override
    protected void init() {
        super.init();
        int x = leftPos + PANEL_X + 4, w = PANEL_W - 8;
        sellStack = addRenderableWidget(Button.builder(Component.translatable("gui.economy_core.sell_stack"),
                b -> send(MarketActionPayload.SELL_STACK)).bounds(x, topPos + 120, w, 18).build());
        sellAllOf = addRenderableWidget(Button.builder(Component.translatable("gui.economy_core.sell_all_of"),
                b -> send(MarketActionPayload.SELL_ALL_OF_ITEM)).bounds(x, topPos + 140, w, 18).build());
        addRenderableWidget(Button.builder(Component.translatable("gui.economy_core.sell_everything"),
                b -> send(MarketActionPayload.SELL_EVERYTHING)).bounds(x, topPos + 162, w, 18).build());
        autoSell = addRenderableWidget(Button.builder(autoSellLabel(),
                b -> send(MarketActionPayload.TOGGLE_AUTOSELL)).bounds(x, topPos + 182, w, 18).build());
        addRenderableWidget(Button.builder(Component.translatable("gui.economy_core.withdraw"),
                b -> send(MarketActionPayload.WITHDRAW)).bounds(x, topPos + 200, w, 18).build());
    }

    private Component autoSellLabel() {
        return Component.translatable(menu.isAutoSell() ? "gui.economy_core.autosell_on" : "gui.economy_core.autosell_off");
    }

    private void send(int action) {
        PacketDistributor.sendToServer(new MarketActionPayload(action, -1));
    }

    @Override
    protected void containerTick() {
        super.containerTick();
        autoSell.setMessage(autoSellLabel());
        boolean hasItem = menu.sellSlot().hasItem();
        sellStack.active = hasItem;
        sellAllOf.active = hasItem;
    }

    // ------------------------------------------------------------ drawing

    @Override
    protected void renderBg(GuiGraphics g, float partialTick, int mouseX, int mouseY) {
        int rowsHeight = MarketMenu.ROWS * 18 + 17;
        g.blit(CHEST, leftPos, topPos, 0, 0, CHEST_W, rowsHeight);
        g.blit(CHEST, leftPos, topPos + rowsHeight, 0, 126, CHEST_W, 96);

        // Side panel in vanilla GUI colours.
        int px = leftPos + PANEL_X, py = topPos;
        bevel(g, px, py, PANEL_W, imageHeight, 0xFFC6C6C6, 0xFFFFFFFF, 0xFF555555);
        // Sell slot frame.
        int sx = leftPos + MarketMenu.SELL_SLOT_X - 1, sy = topPos + MarketMenu.SELL_SLOT_Y - 1;
        bevel(g, sx, sy, 18, 18, 0xFF8B8B8B, 0xFF373737, 0xFFFFFFFF);
    }

    private static void bevel(GuiGraphics g, int x, int y, int w, int h, int fill, int topLeft, int bottomRight) {
        g.fill(x, y, x + w, y + h, fill);
        g.fill(x, y, x + w - 1, y + 1, topLeft);
        g.fill(x, y, x + 1, y + h - 1, topLeft);
        g.fill(x + 1, y + h - 1, x + w, y + h, bottomRight);
        g.fill(x + w - 1, y + 1, x + w, y + h, bottomRight);
    }

    @Override
    protected void renderLabels(GuiGraphics g, int mouseX, int mouseY) {
        super.renderLabels(g, mouseX, mouseY);
        int x = PANEL_X + 6;

        // Balance with a coin icon.
        drawCoin(g, x, 6, biggestCoinFor(ClientMarketCache.balance));
        g.drawString(font, fmt(ClientMarketCache.balance), x + 19, 10, MONEY, false);
        g.drawString(font, Component.translatable("gui.economy_core.tier", ClientMarketCache.tier), x, 28, TEXT, false);

        // Sell slot and its info.
        g.drawString(font, Component.translatable("gui.economy_core.sell_slot"), x, 42, TEXT, false);
        ItemStack sel = menu.sellSlot().getItem();
        int infoX = MarketMenu.SELL_SLOT_X + 20;
        if (sel.isEmpty()) {
            g.drawString(font, Component.translatable("gui.economy_core.sell_slot_hint"), x, 88, 0x707070, false);
            return;
        }
        MarketSyncPayload.Entry e = entryFor(sel.getItem());
        if (e == null) return;
        int pct = pct(e);
        g.drawString(font, fmtPrice(e.price()) + " ea", infoX, MarketMenu.SELL_SLOT_Y, MONEY, false);
        g.drawString(font, pct + "% of fair", infoX, MarketMenu.SELL_SLOT_Y + 9, pctColor(pct), false);

        drawCoin(g, x - 2, 84, biggestCoinFor(ClientMarketCache.sellStackValue));
        g.drawString(font, Component.translatable("gui.economy_core.preview_stack").getString() + " " + fmt(ClientMarketCache.sellStackValue), x + 16, 88, TEXT, false);
        if (ClientMarketCache.sellAllUnits > sel.getCount()) {
            g.drawString(font, Component.translatable("gui.economy_core.preview_all", ClientMarketCache.sellAllUnits).getString()
                    + " " + fmt(ClientMarketCache.sellAllValue), x + 16, 98, TEXT, false);
        }
        if (e.remaining() > 0) {
            g.drawString(font, Component.translatable("gui.economy_core.recover_short", e.remaining()), x, 109, 0x707070, false);
        }
    }

    @Override
    public void render(GuiGraphics g, int mouseX, int mouseY, float partialTick) {
        super.render(g, mouseX, mouseY, partialTick);
        renderTooltip(g, mouseX, mouseY);
        // Sale celebrations: small ones float up from the balance, big ones take over the screen.
        SaleCelebrations.render(g, leftPos + PANEL_X + 40, topPos + 2);
        // Balance tooltip: breakdown into coins.
        int bx = leftPos + PANEL_X + 4, by = topPos + 4;
        if (mouseX >= bx && mouseX < bx + PANEL_W - 8 && mouseY >= by && mouseY < by + 20) {
            g.renderComponentTooltip(font, balanceTooltip(), mouseX, mouseY);
        }
    }

    private List<Component> balanceTooltip() {
        List<Component> lines = new ArrayList<>();
        lines.add(Component.translatable("gui.economy_core.balance_tooltip").withStyle(ChatFormatting.GOLD));
        long rest = ClientMarketCache.balance;
        for (MarketSyncPayload.Coin c : ClientMarketCache.coins) {
            long n = rest / c.value();
            if (n <= 0) continue;
            rest -= n * c.value();
            lines.add(Component.literal(fmt(n) + " × ").append(coinItem(c).getDescription()).withStyle(ChatFormatting.GRAY));
        }
        lines.add(Component.translatable("gui.economy_core.earned", fmt(ClientMarketCache.earned)).withStyle(ChatFormatting.DARK_GRAY));
        return lines;
    }

    /** Add price lines to every sellable item's tooltip. */
    @Override
    protected List<Component> getTooltipFromContainerItem(ItemStack stack) {
        List<Component> lines = new ArrayList<>(super.getTooltipFromContainerItem(stack));
        MarketSyncPayload.Entry e = entryFor(stack.getItem());
        if (e == null) return lines;
        int pct = pct(e);
        ChatFormatting color = pct >= 95 ? ChatFormatting.GREEN : pct >= 75 ? ChatFormatting.YELLOW : ChatFormatting.RED;
        lines.add(Component.translatable("tooltip.economy_core.price", fmtPrice(e.price()), pct).withStyle(color));
        lines.add(Component.translatable("tooltip.economy_core.fair", fmtPrice(e.fair())).withStyle(ChatFormatting.GRAY));
        if (stack.getCount() > 1) {
            lines.add(Component.translatable("tooltip.economy_core.stack_hint").withStyle(ChatFormatting.DARK_GRAY));
        }
        if (e.remaining() > 0) {
            lines.add(Component.translatable("tooltip.economy_core.recovery", e.remaining()).withStyle(ChatFormatting.GRAY));
        }
        return lines;
    }

    // ------------------------------------------------------------ helpers

    private void drawCoin(GuiGraphics g, int x, int y, Item coin) {
        g.renderItem(new ItemStack(coin), x, y);
    }

    /** The largest coin worth no more than the amount (so 4,605 shows a gold coin). */
    private static Item biggestCoinFor(long amount) {
        Item fallback = Items.GOLD_NUGGET;
        for (MarketSyncPayload.Coin c : ClientMarketCache.coins) {
            Item item = coinItem(c);
            if (item == Items.AIR) continue;
            fallback = item; // ends on the smallest coin
            if (c.value() <= Math.max(1, amount)) return item;
        }
        return fallback;
    }

    private static Item coinItem(MarketSyncPayload.Coin c) {
        ResourceLocation id = ResourceLocation.tryParse(c.itemId());
        return id == null ? Items.AIR : BuiltInRegistries.ITEM.get(id);
    }

    private static MarketSyncPayload.Entry entryFor(Item item) {
        return ClientMarketCache.prices.get(BuiltInRegistries.ITEM.getKey(item).toString());
    }

    private static int pct(MarketSyncPayload.Entry e) {
        return (int) Math.round(100.0 * e.price() / Math.max(1e-9, e.fair()));
    }

    private static int pctColor(int pct) {
        return pct >= 95 ? GOOD : pct >= 75 ? MID : BAD;
    }

    private static String fmt(long v) {
        return String.format("%,d", v);
    }

    private static String fmtPrice(double v) {
        return v >= 100 ? String.format("%,.0f", v) : String.format("%.1f", v);
    }
}
