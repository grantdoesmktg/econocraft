package dev.grant.economycore.block;

import dev.grant.economycore.ModRegistry;
import dev.grant.economycore.market.MarketPrices;
import dev.grant.economycore.market.MarketService;
import dev.grant.economycore.menu.MarketMenu;
import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.MenuProvider;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.neoforge.items.IItemHandler;
import net.neoforged.neoforge.items.ItemStackHandler;
import org.jetbrains.annotations.Nullable;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.UUID;

/**
 * The Market Crate: 54 slots of storage (like a large double chest) that only accepts sellable goods.
 * Pipes and hoppers can insert from any side. With auto-sell on, the contents are sold every
 * autosell_interval_ticks; otherwise goods accumulate until the owner sells them from the screen.
 */
public class MarketCrateBlockEntity extends BlockEntity implements MenuProvider {
    public static final int SLOTS = 54;

    private final ItemStackHandler items = new ItemStackHandler(SLOTS) {
        @Override
        protected void onContentsChanged(int slot) {
            setChanged();
        }

        @Override
        public boolean isItemValid(int slot, ItemStack stack) {
            // Prices are only known on the server; the client trusts the server's decision.
            if (level != null && level.isClientSide) return true;
            return MarketPrices.isSellable(stack);
        }
    };

    /** The "item to sell" slot in the side panel. Not reachable by automation. */
    private final ItemStackHandler sellSlot = new ItemStackHandler(1) {
        @Override
        protected void onContentsChanged(int slot) {
            setChanged();
        }

        @Override
        public boolean isItemValid(int slot, ItemStack stack) {
            if (level != null && level.isClientSide) return true;
            return MarketPrices.isSellable(stack);
        }
    };

    /** What pipes/hoppers see: insert only, so automation can't pull goods back out. */
    private final IItemHandler automationHandler = new IItemHandler() {
        @Override public int getSlots() { return items.getSlots(); }
        @Override public ItemStack getStackInSlot(int slot) { return items.getStackInSlot(slot); }
        @Override public ItemStack insertItem(int slot, ItemStack stack, boolean simulate) { return items.insertItem(slot, stack, simulate); }
        @Override public ItemStack extractItem(int slot, int amount, boolean simulate) { return ItemStack.EMPTY; }
        @Override public int getSlotLimit(int slot) { return items.getSlotLimit(slot); }
        @Override public boolean isItemValid(int slot, ItemStack stack) { return items.isItemValid(slot, stack); }
    };

    @Nullable private UUID owner;
    private String ownerName = "";
    private boolean autoSell;
    private int tickCounter;

    public MarketCrateBlockEntity(BlockPos pos, BlockState state) {
        super(ModRegistry.MARKET_CRATE_BE.get(), pos, state);
    }

    public ItemStackHandler getItems() { return items; }
    public ItemStackHandler getSellSlot() { return sellSlot; }
    public IItemHandler getAutomationHandler() { return automationHandler; }
    public boolean isAutoSell() { return autoSell; }
    @Nullable public UUID getOwner() { return owner; }
    public String getOwnerName() { return ownerName; }

    public void setOwner(Player player) {
        owner = player.getUUID();
        ownerName = player.getGameProfile().getName();
        setChanged();
    }

    public boolean isOwner(Player player) {
        return owner == null || owner.equals(player.getUUID());
    }

    public void setAutoSell(boolean value) {
        autoSell = value;
        tickCounter = 0;
        setChanged();
    }

    // ------------------------------------------------------------ selling

    /** Sell just the stack in the panel's "item to sell" slot. */
    public MarketService.Sale sellSelectedStack(ServerLevel level) {
        if (owner == null) return null;
        ItemStack stack = sellSlot.getStackInSlot(0);
        if (!MarketPrices.isSellable(stack)) return null;
        Item item = stack.getItem();
        int count = stack.getCount();
        sellSlot.setStackInSlot(0, ItemStack.EMPTY);
        return MarketService.sell(level.getServer(), owner, ownerName, item, count);
    }

    /** Sell the panel stack plus every matching unit in the crate, as one action. */
    public MarketService.Sale sellAllOfSelected(ServerLevel level) {
        ItemStack stack = sellSlot.getStackInSlot(0);
        if (stack.isEmpty()) return null;
        return sellAllOf(level, stack.getItem());
    }

    /** Sell every unit of one item in the crate as a single action. */
    public MarketService.Sale sellAllOf(ServerLevel level, Item item) {
        if (owner == null) return null;
        int count = 0;
        ItemStack sel = sellSlot.getStackInSlot(0);
        if (!sel.isEmpty() && sel.getItem() == item && MarketPrices.isSellable(sel)) {
            count += sel.getCount();
            sellSlot.setStackInSlot(0, ItemStack.EMPTY);
        }
        for (int i = 0; i < SLOTS; i++) {
            ItemStack s = items.getStackInSlot(i);
            if (!s.isEmpty() && s.getItem() == item && MarketPrices.isSellable(s)) {
                count += s.getCount();
                items.setStackInSlot(i, ItemStack.EMPTY);
            }
        }
        return count == 0 ? null : MarketService.sell(level.getServer(), owner, ownerName, item, count);
    }

    /** Sell everything: one sell action per distinct item. Returns total coins. */
    public long sellEverything(ServerLevel level) {
        if (owner == null) return 0;
        Map<Item, Integer> counts = new LinkedHashMap<>();
        for (int i = 0; i < SLOTS; i++) {
            ItemStack s = items.getStackInSlot(i);
            if (MarketPrices.isSellable(s)) {
                counts.merge(s.getItem(), s.getCount(), Integer::sum);
                items.setStackInSlot(i, ItemStack.EMPTY);
            }
        }
        long total = 0;
        for (var e : counts.entrySet()) {
            total += MarketService.sell(level.getServer(), owner, ownerName, e.getKey(), e.getValue()).coins();
        }
        return total;
    }

    public static void serverTick(Level level, BlockPos pos, BlockState state, MarketCrateBlockEntity be) {
        if (!be.autoSell || !(level instanceof ServerLevel server)) return;
        int interval = Math.max(20, MarketPrices.config().autosellIntervalTicks);
        if (++be.tickCounter < interval) return;
        be.tickCounter = 0;
        be.sellEverything(server);
    }

    // ------------------------------------------------------------ menu

    @Override
    public Component getDisplayName() {
        return Component.translatable("block.economy_core.market_crate");
    }

    @Nullable
    @Override
    public AbstractContainerMenu createMenu(int id, Inventory inv, Player player) {
        return new MarketMenu(id, inv, this);
    }

    public void openFor(ServerPlayer player) {
        player.openMenu(this, buf -> buf.writeBlockPos(worldPosition));
    }

    // ------------------------------------------------------------ save/load

    @Override
    protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.saveAdditional(tag, registries);
        tag.put("Items", items.serializeNBT(registries));
        tag.put("SellSlot", sellSlot.serializeNBT(registries));
        if (owner != null) tag.putUUID("Owner", owner);
        tag.putString("OwnerName", ownerName);
        tag.putBoolean("AutoSell", autoSell);
    }

    @Override
    protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        items.deserializeNBT(registries, tag.getCompound("Items"));
        if (tag.contains("SellSlot")) sellSlot.deserializeNBT(registries, tag.getCompound("SellSlot"));
        owner = tag.hasUUID("Owner") ? tag.getUUID("Owner") : null;
        ownerName = tag.getString("OwnerName");
        autoSell = tag.getBoolean("AutoSell");
    }
}
