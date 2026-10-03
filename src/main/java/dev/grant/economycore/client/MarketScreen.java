package dev.grant.economycore.client;

import dev.grant.economycore.block.MarketCrateBlockEntity;
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
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;
import net.neoforged.neoforge.network.PacketDistributor;

import java.util.ArrayList;
import java.util.List;

/**
 * Large-chest style screen with a button panel on the right.
 * Cmd-click (Ctrl-click on Windows/Linux) a crate slot to select it for "Sell stack" / "Sell all of this item".
 */
public class MarketScreen extends AbstractContainerScreen<MarketMenu> {
    private static final ResourceLocation CHEST = ResourceLocation.withDefaultNamespace("textures/gui/container/generic_54.png");
    private static final int PANEL_W = 112;
    private static final int PANEL_GAP = 4;

    private int selectedSlot = -1;
    private Button sellStack, sellAllOf, autoSell;

    public MarketScreen(MarketMenu menu, Inventory inv, Component title) {
        super(menu, inv, title);
        imageWidth = 176;
        imageHeight = 114 + MarketMenu.ROWS * 18;
        inventoryLabelY = imageHeight - 94;
    }

    @Override
    protected void init() {
        super.init();
        // Center the chest + side panel together.
        leftPos = (width - (imageWidth + PANEL_GAP + PANEL_W)) / 2;
        int x = leftPos + imageWidth + PANEL_GAP;
        int y = topPos + 40;
        sellStack = addRenderableWidget(Button.builder(Component.translatable("gui.economy_core.sell_stack"),
                b -> send(MarketActionPayload.SELL_STACK)).bounds(x, y, PANEL_W, 20).build());
        sellAllOf = addRenderableWidget(Button.builder(Component.translatable("gui.economy_core.sell_all_of"),
                b -> send(MarketActionPayload.SELL_ALL_OF_ITEM)).bounds(x, y + 22, PANEL_W, 20).build());
        addRenderableWidget(Button.builder(Component.translatable("gui.economy_core.sell_everything"),
                b -> send(MarketActionPayload.SELL_EVERYTHING)).bounds(x, y + 44, PANEL_W, 20).build());
        autoSell = addRenderableWidget(Button.builder(autoSellLabel(),
                b -> send(MarketActionPayload.TOGGLE_AUTOSELL)).bounds(x, y + 72, PANEL_W, 20).build());
        addRenderableWidget(Button.builder(Component.translatable("gui.economy_core.withdraw"),
                b -> send(MarketActionPayload.WITHDRAW)).bounds(x, y + 100, PANEL_W, 20).build());
    }

    private Component autoSellLabel() {
        return Component.translatable(menu.isAutoSell() ? "gui.economy_core.autosell_on" : "gui.economy_core.autosell_off");
    }

    private void send(int action) {
        PacketDistributor.sendToServer(new MarketActionPayload(action, selectedSlot));
    }

    @Override
    protected void containerTick() {
        super.containerTick();
        autoSell.setMessage(autoSellLabel());
        // Clear the selection when the selected slot empties (e.g. after selling it).
        if (selectedSlot >= 0 && menu.slots.get(selectedSlot).getItem().isEmpty()) selectedSlot = -1;
        sellStack.active = selectedSlot >= 0;
        sellAllOf.active = selectedSlot >= 0;
    }

    @Override
    public boolean mouseClicked(double mouseX, double mouseY, int button) {
        if (hasControlDown() && hoveredSlot != null && menu.isCrateSlot(hoveredSlot) && hoveredSlot.hasItem()) {
            selectedSlot = hoveredSlot.index == selectedSlot ? -1 : hoveredSlot.index;
            return true;
        }
        return super.mouseClicked(mouseX, mouseY, button);
    }

    @Override
    protected void renderBg(GuiGraphics g, float partialTick, int mouseX, int mouseY) {
        int rowsHeight = MarketMenu.ROWS * 18 + 17;
        g.blit(CHEST, leftPos, topPos, 0, 0, imageWidth, rowsHeight);
        g.blit(CHEST, leftPos, topPos + rowsHeight, 0, 126, imageWidth, 96);
        if (selectedSlot >= 0) {
            Slot s = menu.slots.get(selectedSlot);
            int sx = leftPos + s.x, sy = topPos + s.y;
            g.fill(sx - 1, sy - 1, sx + 17, sy + 17, 0x80FFD700);
        }
    }

    @Override
    public void render(GuiGraphics g, int mouseX, int mouseY, float partialTick) {
        super.render(g, mouseX, mouseY, partialTick);
        int x = leftPos + imageWidth + PANEL_GAP;
        g.drawString(font, Component.translatable("gui.economy_core.balance", fmt(ClientMarketCache.balance)), x, topPos + 6, 0xFFD700);
        g.drawString(font, Component.translatable("gui.economy_core.tier", ClientMarketCache.tier), x, topPos + 18, 0xFFFFFF);
        g.drawString(font, Component.translatable("gui.economy_core.hint"), x, topPos + 28, 0xA0A0A0);
        renderTooltip(g, mouseX, mouseY);
    }

    /** Add price lines to every sellable item's tooltip. */
    @Override
    protected List<Component> getTooltipFromContainerItem(ItemStack stack) {
        List<Component> lines = new ArrayList<>(super.getTooltipFromContainerItem(stack));
        String id = BuiltInRegistries.ITEM.getKey(stack.getItem()).toString();
        MarketSyncPayload.Entry e = ClientMarketCache.prices.get(id);
        if (e == null) return lines;
        int pct = (int) Math.round(100.0 * e.price() / Math.max(1e-9, e.fair()));
        ChatFormatting color = pct >= 95 ? ChatFormatting.GREEN : pct >= 75 ? ChatFormatting.YELLOW : ChatFormatting.RED;
        lines.add(Component.translatable("tooltip.economy_core.price", fmtD(e.price()), pct).withStyle(color));
        lines.add(Component.translatable("tooltip.economy_core.fair", fmtD(e.fair())).withStyle(ChatFormatting.GRAY));
        if (stack.getCount() > 1) {
            lines.add(Component.translatable("tooltip.economy_core.stack_hint").withStyle(ChatFormatting.DARK_GRAY));
        }
        if (e.remaining() > 0) {
            lines.add(Component.translatable("tooltip.economy_core.recovery", e.remaining()).withStyle(ChatFormatting.GRAY));
        }
        return lines;
    }

    private static String fmt(long v) {
        return String.format("%,d", v);
    }

    private static String fmtD(double v) {
        return v >= 100 ? String.format("%,.0f", v) : String.format("%.1f", v);
    }
}
