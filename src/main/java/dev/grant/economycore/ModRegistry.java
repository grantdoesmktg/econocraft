package dev.grant.economycore;

import dev.grant.economycore.block.MarketCrateBlock;
import dev.grant.economycore.block.MarketCrateBlockEntity;
import dev.grant.economycore.menu.MarketMenu;
import net.minecraft.core.registries.Registries;
import net.minecraft.world.inventory.MenuType;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.material.MapColor;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.common.extensions.IMenuTypeExtension;
import net.neoforged.neoforge.registries.DeferredBlock;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredItem;
import net.neoforged.neoforge.registries.DeferredRegister;

public final class ModRegistry {
    public static final DeferredRegister.Blocks BLOCKS = DeferredRegister.createBlocks(EconomyCore.MODID);
    public static final DeferredRegister.Items ITEMS = DeferredRegister.createItems(EconomyCore.MODID);
    public static final DeferredRegister<BlockEntityType<?>> BLOCK_ENTITIES =
            DeferredRegister.create(Registries.BLOCK_ENTITY_TYPE, EconomyCore.MODID);
    public static final DeferredRegister<MenuType<?>> MENUS = DeferredRegister.create(Registries.MENU, EconomyCore.MODID);

    public static final DeferredBlock<MarketCrateBlock> MARKET_CRATE = BLOCKS.register("market_crate",
            () -> new MarketCrateBlock(BlockBehaviour.Properties.of()
                    .mapColor(MapColor.WOOD).strength(2.5f).sound(SoundType.WOOD)));

    public static final DeferredItem<BlockItem> MARKET_CRATE_ITEM = ITEMS.registerSimpleBlockItem(MARKET_CRATE);

    @SuppressWarnings("DataFlowIssue")
    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<MarketCrateBlockEntity>> MARKET_CRATE_BE =
            BLOCK_ENTITIES.register("market_crate",
                    () -> BlockEntityType.Builder.of(MarketCrateBlockEntity::new, MARKET_CRATE.get()).build(null));

    public static final DeferredHolder<MenuType<?>, MenuType<MarketMenu>> MARKET_MENU =
            MENUS.register("market_crate", () -> IMenuTypeExtension.create(MarketMenu::new));

    private ModRegistry() {}

    public static void register(IEventBus bus) {
        BLOCKS.register(bus);
        ITEMS.register(bus);
        BLOCK_ENTITIES.register(bus);
        MENUS.register(bus);
    }
}
