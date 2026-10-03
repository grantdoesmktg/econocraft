package dev.grant.economycore.client;

import dev.grant.economycore.EconomyCore;
import dev.grant.economycore.ModRegistry;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.RegisterMenuScreensEvent;

@EventBusSubscriber(modid = EconomyCore.MODID, value = Dist.CLIENT)
public final class ClientSetup {
    private ClientSetup() {}

    @SubscribeEvent
    public static void registerScreens(RegisterMenuScreensEvent event) {
        event.register(ModRegistry.MARKET_MENU.get(), MarketScreen::new);
    }
}
