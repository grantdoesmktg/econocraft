package dev.grant.economycore.block;

import dev.grant.economycore.ModRegistry;
import dev.grant.economycore.market.MarketPrices;
import dev.grant.economycore.market.MarketService;
import dev.grant.economycore.market.TeamHelper;
import dev.grant.economycore.menu.MarketMenu;
import dev.grant.economycore.network.MarketFxPayload;
import net.neoforged.neoforge.network.PacketDistributor;
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
            depositPending = true;
        }

        @Override
        public boolean isItemValid(int slot, ItemStack stack) {
            // Prices are only known on the server; the client trusts the server's decision.
            if (level != null && level.isClientSide) return true;
            return MarketPrices.isAccepted(stack) || MarketService.priceTag(stack) > 0;
        }
    };

    /** The "item to sell" slot in the side panel. Not reachable by automation. */
    private final ItemStackHandler sellSlot = new ItemStackHandler(1) {
        @Override
        protected void onContentsChanged(int slot) {
            setChanged();
            depositPending = true;
        }

        @Override
        public boolean isItemValid(int slot, ItemStack stack) {
            if (level != null && level.isClientSide) return true;
            return MarketPrices.isAccepted(stack) || MarketService.priceTag(stack) > 0;
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
    /** Set when contents change; the next tick turns any coin items into balance. */
    private boolean depositPending;

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

    /** The placer and anyone on their FTB team can use the crate; proceeds go to the shared team account. */
    public boolean isOwner(Player player) {
        return owner == null || owner.equals(player.getUUID()) || TeamHelper.sameTeam(owner, player.getUUID());
    }

    public void setAutoSell(boolean value) {
        autoSell = value;
        tickCounter = AUTOSELL_PERIOD; // start selling right away
        autosellRun.clear();
        setChanged();
    }

    // ------------------------------------------------------------ selling

    /** Sell just the stack in the panel's "item to sell" slot. */
    public MarketService.Sale sellSelectedStack(ServerLevel level) {
        if (owner == null) return null;
        ItemStack stack = sellSlot.getStackInSlot(0);
        if (MarketService.priceTag(stack) > 0) {
            sellSlot.setStackInSlot(0, ItemStack.EMPTY);
            return MarketService.sellBack(level.getServer(), owner, stack);
        }
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
        if (MarketService.priceTag(sel) > 0) return sellSelectedStack(level);
        if (!sel.isEmpty() && sel.getItem() == item && MarketPrices.isSellable(sel)) {
            count += sel.getCount();
            sellSlot.setStackInSlot(0, ItemStack.EMPTY);
        }
        for (int i = 0; i < SLOTS; i++) {
            ItemStack s = items.getStackInSlot(i);
            if (!s.isEmpty() && s.getItem() == item && MarketPrices.isSellable(s) && MarketService.priceTag(s) == 0) {
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
        long backTotal = 0;
        for (int i = 0; i < SLOTS; i++) {
            ItemStack s = items.getStackInSlot(i);
            if (MarketService.priceTag(s) > 0) {
                backTotal += MarketService.sellBack(level.getServer(), owner, s).coins();
                items.setStackInSlot(i, ItemStack.EMPTY);
                continue;
            }
            if (MarketPrices.isSellable(s)) {
                counts.merge(s.getItem(), s.getCount(), Integer::sum);
                items.setStackInSlot(i, ItemStack.EMPTY);
            }
        }
        long total = backTotal;
        for (var e : counts.entrySet()) {
            total += MarketService.sell(level.getServer(), owner, ownerName, e.getKey(), e.getValue()).coins();
        }
        return total;
    }

    /** Ticks between auto-sell chunks (10 ticks = half a second). */
    public static final int AUTOSELL_PERIOD = 10;
    /** Celebrations for auto-sell are pooled and shown at most this often, so chunks don't spam effects. */
    private static final int FX_PERIOD = 100;

    private long pendingFxCoins;
    private int fxCounter;
    private int nextSlot;
    /** Units of each item auto-sold in the current run, so small chunks still count toward price recovery. */
    private final java.util.Map<Item, Integer> autosellRun = new java.util.HashMap<>();

    public static void serverTick(Level level, BlockPos pos, BlockState state, MarketCrateBlockEntity be) {
        if (!(level instanceof ServerLevel server)) return;
        if (be.depositPending) {
            be.depositPending = false;
            be.depositCoins(server);
        }
        if (!be.autoSell || be.owner == null) {
            be.flushFx(server);
            return;
        }
        if (++be.tickCounter >= AUTOSELL_PERIOD) {
            be.tickCounter = 0;
            be.sellChunk(server);
        }
        if (++be.fxCounter >= FX_PERIOD) {
            be.fxCounter = 0;
            be.flushFx(server);
        }
    }

    /**
     * Sell one chunk: up to N units of the next item in the crate, round-robin across slots so a mix of goods
     * gets sold (and recovers prices) instead of draining one item first. N = 2 at tier 0, x2 per tier, max 64.
     */
    private void sellChunk(ServerLevel level) {
        int tier = MarketService.getTier(level.getServer(), owner);
        int chunk = MarketService.autosellChunk(tier);
        for (int tries = 0; tries < SLOTS; tries++) {
            int slot = (nextSlot + tries) % SLOTS;
            ItemStack s = items.getStackInSlot(slot);
            if (MarketService.priceTag(s) > 0) {
                ItemStack taken = items.extractItem(slot, s.getCount(), false);
                pendingFxCoins += MarketService.sellBack(level.getServer(), owner, taken).coins();
                nextSlot = slot + 1;
                return;
            }
            if (!MarketPrices.isSellable(s)) continue;
            Item item = s.getItem();
            int units = Math.min(chunk, s.getCount());
            items.extractItem(slot, units, false);
            int run = autosellRun.merge(item, units, Integer::sum);
            MarketService.Sale sale = MarketService.sell(level.getServer(), owner, ownerName, item, units, run);
            if (run >= 64) autosellRun.remove(item);
            pendingFxCoins += sale.coins();
            nextSlot = items.getStackInSlot(slot).isEmpty() ? slot + 1 : slot + 1;
            for (UUID member : TeamHelper.members(owner)) {
                ServerPlayer p = level.getServer().getPlayerList().getPlayer(member);
                if (p != null) MarketService.award(p, "autosell");
            }
            ServerPlayer ownerOnline = level.getServer().getPlayerList().getPlayer(owner);
            if (ownerOnline != null) MarketService.firstSale(ownerOnline, sale.coins(), getBlockPos());
            return;
        }
        autosellRun.clear(); // crate empty: the next delivery starts a fresh run
    }

    private void flushFx(ServerLevel level) {
        if (pendingFxCoins > 0) {
            notifyOwner(level, MarketFxPayload.KIND_AUTOSELL, pendingFxCoins);
            pendingFxCoins = 0;
        }
    }

    /** Remove coin items from storage and the sell slot and add their value to the owner's balance. */
    private void depositCoins(ServerLevel level) {
        if (owner == null) return;
        long total = 0;
        total += takeCoins(items);
        total += takeCoins(sellSlot);
        if (total <= 0) return;
        MarketService.deposit(level.getServer(), owner, total);
        notifyOwner(level, MarketFxPayload.KIND_DEPOSIT, total);
    }

    private static long takeCoins(ItemStackHandler handler) {
        long total = 0;
        for (int i = 0; i < handler.getSlots(); i++) {
            ItemStack s = handler.getStackInSlot(i);
            long value = MarketPrices.coinValue(s);
            if (value > 0) {
                total += value * s.getCount();
                handler.setStackInSlot(i, ItemStack.EMPTY);
            }
        }
        return total;
    }

    /** Tell the owner (if online and nearby, or viewing this crate) about a sale or deposit. */
    public void notifyOwner(ServerLevel level, int kind, long coins) {
        if (owner == null) return;
        int tier = kind == MarketFxPayload.KIND_DEPOSIT ? 0 : MarketService.celebrationTier(coins);
        for (UUID member : TeamHelper.members(owner)) {
            ServerPlayer p = level.getServer().getPlayerList().getPlayer(member);
            if (p == null) continue;
            boolean viewing = p.containerMenu instanceof MarketMenu m && m.getCrate() == this;
            boolean nearby = p.level() == level && p.blockPosition().closerThan(worldPosition, 32);
            if (viewing || nearby) PacketDistributor.sendToPlayer(p, new MarketFxPayload(kind, coins, tier, worldPosition));
        }
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
