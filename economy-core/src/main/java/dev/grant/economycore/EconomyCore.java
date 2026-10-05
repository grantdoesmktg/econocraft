package dev.grant.economycore;

import dev.grant.economycore.client.ClientMarketCache;
import dev.grant.economycore.command.MarketCommand;
import dev.grant.economycore.market.MarketPrices;
import dev.grant.economycore.market.MarketService;
import dev.grant.economycore.network.MarketActionPayload;
import dev.grant.economycore.network.MarketFxPayload;
import dev.grant.economycore.network.MarketSyncPayload;
import dev.grant.economycore.network.ShopBuyPayload;
import dev.grant.economycore.network.BalancePayload;
import net.neoforged.neoforge.event.tick.PlayerTickEvent;
import net.neoforged.neoforge.network.PacketDistributor;
import dev.grant.economycore.network.ShopSyncPayload;
import dev.grant.economycore.shop.ShopCatalog;
import net.neoforged.neoforge.event.entity.player.ItemTooltipEvent;
import dev.grant.economycore.market.MarketData;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.CreativeModeTabs;
import net.neoforged.neoforge.event.entity.player.PlayerEvent;
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
        NeoForge.EVENT_BUS.addListener(this::onPlayerLogin);
        NeoForge.EVENT_BUS.addListener(this::onTooltip);
        NeoForge.EVENT_BUS.addListener(this::onPlayerTick);
        NeoForge.EVENT_BUS.addListener((net.neoforged.neoforge.event.tick.ServerTickEvent.Post e) ->
                dev.grant.economycore.market.IslandPartyLink.tick(e.getServer()));
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
        // Lambda body keeps client-only classes from loading on a dedicated server.
        r.playToServer(ShopBuyPayload.TYPE, ShopBuyPayload.CODEC, ShopBuyPayload::handle);
        r.playToClient(BalancePayload.TYPE, BalancePayload.CODEC,
                (msg, ctx) -> dev.grant.economycore.client.BalanceHud.set(msg.balance()));
        r.playToClient(ShopSyncPayload.TYPE, ShopSyncPayload.CODEC,
                (msg, ctx) -> dev.grant.economycore.client.ClientShopCache.handle(msg, ctx));
        r.playToClient(MarketFxPayload.TYPE, MarketFxPayload.CODEC,
                (msg, ctx) -> dev.grant.economycore.client.SaleCelebrations.onPayload(msg));
    }

    private void addToCreativeTab(BuildCreativeModeTabContentsEvent event) {
        if (event.getTabKey() == CreativeModeTabs.FUNCTIONAL_BLOCKS) {
            event.accept(ModRegistry.MARKET_CRATE_ITEM);
            event.accept(ModRegistry.FRONTIER_GATEWAY_ITEM);
            event.accept(ModRegistry.SUPPLY_MARKET_ITEM);
        }
    }

    private void onServerStarted(ServerStartedEvent event) {
        MarketPrices.reload();
        ShopCatalog.reload();
        MarketService.ensureObjectives(event.getServer());
    }

    private void onTagsUpdated(TagsUpdatedEvent event) {
        // Tag-based price entries (e.g. #c:ingots/iron) need re-resolving whenever tags reload.
        if (event.getUpdateCause() == TagsUpdatedEvent.UpdateCause.SERVER_DATA_LOAD) MarketPrices.resolve();
    }

    /** Catch up on earnings milestones reached while offline (auto-sell keeps earning). */
    private void onPlayerLogin(PlayerEvent.PlayerLoggedInEvent event) {
        if (event.getEntity() instanceof ServerPlayer sp) {
            lastBalanceSent.remove(sp.getUUID()); // resend on next tick
            MarketService.awardMilestones(sp, MarketData.get(sp.server).accountFor(sp.getUUID()).earned, 0);
        }
    }

    private final java.util.Map<java.util.UUID, Long> lastBalanceSent = new java.util.HashMap<>();

    /** Push the team balance to each player's balance counter once a second, when it has changed. */
    private void onPlayerTick(PlayerTickEvent.Post event) {
        if (!(event.getEntity() instanceof ServerPlayer sp) || sp.tickCount % 20 != 0) return;
        long bal = MarketData.get(sp.server).accountFor(sp.getUUID()).balance;
        Long last = lastBalanceSent.put(sp.getUUID(), bal);
        if (last == null || last != bal) PacketDistributor.sendToPlayer(sp, new BalancePayload(bal));
    }

    /** Shop-bought machines show what they sell back for. */
    private void onTooltip(ItemTooltipEvent event) {
        Long tag = event.getItemStack().get(ModRegistry.PRICE_TAG.get());
        if (tag != null) {
            event.getToolTip().add(net.minecraft.network.chat.Component.translatable("tooltip.economy_core.price_tag",
                    String.format("%,d", tag)).withStyle(net.minecraft.ChatFormatting.GOLD));
        }
    }

    private void onRegisterCommands(RegisterCommandsEvent event) {
        MarketCommand.register(event.getDispatcher(), event.getBuildContext());
    }
}
