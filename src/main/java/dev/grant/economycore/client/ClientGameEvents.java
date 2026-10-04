package dev.grant.economycore.client;

import dev.grant.economycore.EconomyCore;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.ScreenEvent;

/** Keeps the balance counter visible while any in-game screen is open. */
@EventBusSubscriber(modid = EconomyCore.MODID, value = Dist.CLIENT)
public final class ClientGameEvents {
    private ClientGameEvents() {}

    @SubscribeEvent
    public static void onScreenRender(ScreenEvent.Render.Post event) {
        BalanceHud.render(event.getGuiGraphics());
    }
}
