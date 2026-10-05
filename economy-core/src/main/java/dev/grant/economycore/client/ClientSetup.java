package dev.grant.economycore.client;

import dev.grant.economycore.EconomyCore;
import dev.grant.economycore.ModRegistry;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.RegisterGuiLayersEvent;
import net.neoforged.neoforge.client.event.RegisterMenuScreensEvent;
import net.minecraft.client.Minecraft;
import net.minecraft.resources.ResourceLocation;

@EventBusSubscriber(modid = EconomyCore.MODID, value = Dist.CLIENT)
public final class ClientSetup {
    private ClientSetup() {}

    /** Celebrations also show on the HUD (e.g. auto-sell while you're not looking at the crate). */
    @SubscribeEvent
    public static void registerLayers(RegisterGuiLayersEvent event) {
        event.registerAboveAll(ResourceLocation.fromNamespaceAndPath(EconomyCore.MODID, "sale_celebrations"), (g, delta) -> {
            if (!(Minecraft.getInstance().screen instanceof MarketScreen)) SaleCelebrations.render(g, -1, -1);
        });
        event.registerAboveAll(ResourceLocation.fromNamespaceAndPath(EconomyCore.MODID, "balance"), (g, delta) -> {
            if (Minecraft.getInstance().screen == null) BalanceHud.render(g);
        });
    }

    @SubscribeEvent
    public static void registerRenderers(net.neoforged.neoforge.client.event.EntityRenderersEvent.RegisterRenderers event) {
        event.registerBlockEntityRenderer(ModRegistry.POWER_EXCHANGE_BE.get(), PowerExchangeRenderer::new);
    }

    @SubscribeEvent
    public static void registerScreens(RegisterMenuScreensEvent event) {
        event.register(ModRegistry.MARKET_MENU.get(), MarketScreen::new);
    }
}
