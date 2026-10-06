package dev.grant.economycore.client;

import dev.grant.economycore.EconomyCore;
import dev.grant.economycore.ModRegistry;
import dev.grant.economycore.network.PricesPayload;
import net.minecraft.ChatFormatting;
import net.minecraft.client.Minecraft;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.ItemStack;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.EventPriority;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.ScreenEvent;
import net.neoforged.neoforge.event.entity.player.ItemTooltipEvent;

/** Keeps the balance counter visible while any in-game screen is open, and shows market prices in tooltips. */
@EventBusSubscriber(modid = EconomyCore.MODID, value = Dist.CLIENT)
public final class ClientGameEvents {
    private ClientGameEvents() {}

    /** Index = rarity level: common gray, uncommon green, rare aqua, legendary gold. */
    private static final ChatFormatting[] RARITY_COLORS =
            {ChatFormatting.GRAY, ChatFormatting.GRAY, ChatFormatting.GREEN, ChatFormatting.AQUA, ChatFormatting.GOLD};

    @SubscribeEvent
    public static void onScreenRender(ScreenEvent.Render.Post event) {
        BalanceHud.render(event.getGuiGraphics());
    }

    /**
     * Every sellable item shows what the Market Crate pays for it, wherever you hover it.
     * Shop-bought machines show their sell-back value instead. The Market screen has its own, longer lines.
     */
    // LOWEST so the price is added after ProgressiveStages rewrites a locked item's tooltip.
    @SubscribeEvent(priority = EventPriority.LOWEST)
    public static void onTooltip(ItemTooltipEvent event) {
        ItemStack stack = event.getItemStack();
        if (stack.isEmpty()) return;
        Long tag = stack.get(ModRegistry.PRICE_TAG.get());
        if (tag != null) {
            event.getToolTip().add(Component.translatable("tooltip.economy_core.price_tag",
                    String.format("%,d", tag)).withStyle(ChatFormatting.GOLD));
            return;
        }
        PricesPayload.Entry e = ClientPriceCache.get(BuiltInRegistries.ITEM.getKey(stack.getItem()).toString());
        if (e == null) return;
        if (e.rarity() > 0 && e.rarity() < RARITY_COLORS.length) {
            event.getToolTip().add(Component.translatable("tooltip.economy_core.rarity." + e.rarity())
                    .withStyle(RARITY_COLORS[e.rarity()]));
        }
        if (Minecraft.getInstance().screen instanceof MarketScreen) return;
        int pct = e.fair() > 0 ? (int) Math.round(100 * e.price() / e.fair()) : 100;
        Component line;
        if (pct >= 98) {
            line = Component.translatable("tooltip.economy_core.sells_for", fmt(e.fair())).withStyle(ChatFormatting.GOLD);
        } else {
            ChatFormatting color = pct >= 75 ? ChatFormatting.YELLOW : ChatFormatting.RED;
            line = Component.translatable("tooltip.economy_core.sells_for_now", fmt(e.price()), pct, fmt(e.fair()))
                    .withStyle(color);
        }
        event.getToolTip().add(line);
        if (stack.getCount() > 1) {
            event.getToolTip().add(Component.translatable("tooltip.economy_core.stack_about",
                    fmt(Math.floor(e.price() * stack.getCount()))).withStyle(ChatFormatting.DARK_GRAY));
        }
    }

    /** 0.5 -> "0.5", 4 -> "4", 1234.0 -> "1,234". */
    private static String fmt(double v) {
        if (v >= 100 || v == Math.rint(v)) return String.format("%,d", Math.round(v));
        String s = String.format("%.2f", v);
        return s.replaceAll("0+$", "").replaceAll("\\.$", "");
    }
}
