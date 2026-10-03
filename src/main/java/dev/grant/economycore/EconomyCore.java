package dev.grant.economycore;

import dev.grant.economycore.client.ClientMarketCache;
import dev.grant.economycore.command.MarketCommand;
import dev.grant.economycore.market.MarketPrices;
import dev.grant.economycore.market.MarketService;
import dev.grant.economycore.network.MarketActionPayload;
import dev.grant.economycore.network.MarketSyncPayload;
import net.minecraft.world.item.CreativeModeTabs;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.ModContainer;
import net.neoforged.fml.common.Mod;
import net.neoforged.neoforge.capabilities.Capabilities;
import net.neoforged.neoforge.capabilities.RegisterCapabilitiesEvent;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.BuildCreativeModeTabContentsEvent;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.event.TagsUpdatedEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;
import net.neoforged.neoforge.network.event.RegisterPayloadHandlersEvent;
import net.neoforged.neoforge.network.registration.PayloadRegistrar;

/** Economy Core: the Market Crate and supporting economy systems for the Economy Pack. */
@Mod(EconomyCore.MODID)
public class EconomyCore {
    public static final String MODID = "economy_core";

    public EconomyCore(IEventBus modBus, ModContainer container) {
        ModRegistry.register(modBus);
        modBus.addListener(this::registerCapabilities);
        modBus.addListener(this::registerPayloads);
        modBus.addListener(this::addToCreativeTab);

        NeoForge.EVENT_BUS.addListener(this::onServerStarted);
        NeoForge.EVENT_BUS.addListener(this::onTagsUpdated);
        NeoForge.EVENT_BUS.addListener(this::onRegisterCommands);
    }

    private void registerCapabilities(RegisterCapabilitiesEvent event) {
        // Pipes and hoppers can insert into the crate from any side (insert only).
        event.registerBlockEntity(Capabilities.ItemHandler.BLOCK, ModRegistry.MARKET_CRATE_BE.get(),
                (be, side) -> be.getAutomationHandler());
    }

    private void registerPayloads(RegisterPayloadHandlersEvent event) {
        PayloadRegistrar r = event.registrar("1");
        r.playToServer(MarketActionPayload.TYPE, MarketActionPayload.CODEC, MarketActionPayload::handle);
        r.playToClient(MarketSyncPayload.TYPE, MarketSyncPayload.CODEC, ClientMarketCache::handle);
    }

    private void addToCreativeTab(BuildCreativeModeTabContentsEvent event) {
        if (event.getTabKey() == CreativeModeTabs.FUNCTIONAL_BLOCKS) event.accept(ModRegistry.MARKET_CRATE_ITEM);
    }

    private void onServerStarted(ServerStartedEvent event) {
        MarketPrices.reload();
        MarketService.ensureObjectives(event.getServer());
    }

    private void onTagsUpdated(TagsUpdatedEvent event) {
        // Tag-based price entries (e.g. #c:ingots/iron) need re-resolving whenever tags reload.
        if (event.getUpdateCause() == TagsUpdatedEvent.UpdateCause.SERVER_DATA_LOAD) MarketPrices.resolve();
    }

    private void onRegisterCommands(RegisterCommandsEvent event) {
        MarketCommand.register(event.getDispatcher(), event.getBuildContext());
    }
}
