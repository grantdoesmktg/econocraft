package dev.grant.economycore.menu;

import dev.grant.economycore.ModRegistry;
import dev.grant.economycore.block.MarketCrateBlockEntity;
import dev.grant.economycore.network.MarketSyncPayload;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ContainerLevelAccess;
import net.minecraft.world.inventory.DataSlot;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;
import net.neoforged.neoforge.items.ItemStackHandler;
import net.neoforged.neoforge.items.SlotItemHandler;
import net.neoforged.neoforge.network.PacketDistributor;

/**
 * 6x9 crate slots on top, player inventory below (same layout as a large chest), plus one
 * "item to sell" slot in the side panel. Slot order: 0-53 crate, 54 sell slot, 55-90 player.
 */
public class MarketMenu extends AbstractContainerMenu {
    public static final int ROWS = 6;
    public static final int SELL_SLOT_INDEX = MarketCrateBlockEntity.SLOTS;
    /** Position of the sell slot inside the (widened) screen. */
    public static final int SELL_SLOT_X = 188, SELL_SLOT_Y = 66;

    private final MarketCrateBlockEntity crate;
    private final Player player;
    private final DataSlot autoSell = DataSlot.standalone();
    private int syncCounter;

    /** Client side: the block position comes from the open-menu packet. */
    public MarketMenu(int id, Inventory inv, RegistryFriendlyByteBuf buf) {
        this(id, inv, (MarketCrateBlockEntity) inv.player.level().getBlockEntity(buf.readBlockPos()));
    }

    public MarketMenu(int id, Inventory inv, MarketCrateBlockEntity crate) {
        super(ModRegistry.MARKET_MENU.get(), id);
        this.crate = crate;
        this.player = inv.player;

        ItemStackHandler items = crate != null ? crate.getItems() : new ItemStackHandler(MarketCrateBlockEntity.SLOTS);
        for (int row = 0; row < ROWS; row++)
            for (int col = 0; col < 9; col++)
                addSlot(new SlotItemHandler(items, col + row * 9, 8 + col * 18, 18 + row * 18));

        ItemStackHandler sell = crate != null ? crate.getSellSlot() : new ItemStackHandler(1);
        addSlot(new SlotItemHandler(sell, 0, SELL_SLOT_X, SELL_SLOT_Y));

        int yOffset = (ROWS - 4) * 18;
        for (int row = 0; row < 3; row++)
            for (int col = 0; col < 9; col++)
                addSlot(new Slot(inv, col + row * 9 + 9, 8 + col * 18, 103 + row * 18 + yOffset));
        for (int col = 0; col < 9; col++)
            addSlot(new Slot(inv, col, 8 + col * 18, 161 + yOffset));

        if (crate != null) autoSell.set(crate.isAutoSell() ? 1 : 0);
        addDataSlot(autoSell);
    }

    public MarketCrateBlockEntity getCrate() { return crate; }
    public boolean isAutoSell() { return autoSell.get() != 0; }
    public boolean isCrateSlot(Slot slot) { return slot.index < MarketCrateBlockEntity.SLOTS; }
    public Slot sellSlot() { return slots.get(SELL_SLOT_INDEX); }

    @Override
    public void broadcastChanges() {
        if (crate != null) autoSell.set(crate.isAutoSell() ? 1 : 0);
        super.broadcastChanges();
        // Push fresh prices/balance to the viewer twice a second.
        if (player instanceof ServerPlayer sp && crate != null && ++syncCounter >= 10) {
            syncCounter = 0;
            sendSync(sp);
        }
    }

    public void sendSync(ServerPlayer sp) {
        PacketDistributor.sendToPlayer(sp, MarketSyncPayload.build(sp, crate));
    }

    @Override
    public ItemStack quickMoveStack(Player player, int index) {
        Slot slot = slots.get(index);
        if (!slot.hasItem()) return ItemStack.EMPTY;
        ItemStack stack = slot.getItem();
        ItemStack copy = stack.copy();
        int crateEnd = MarketCrateBlockEntity.SLOTS;
        int playerStart = SELL_SLOT_INDEX + 1;
        if (index <= SELL_SLOT_INDEX) {
            // Crate or sell slot -> player inventory.
            if (!moveItemStackTo(stack, playerStart, slots.size(), true)) return ItemStack.EMPTY;
        } else if (!moveItemStackTo(stack, 0, crateEnd, false)) {
            // Player -> crate storage (never auto-filled into the sell slot).
            return ItemStack.EMPTY;
        }
        if (stack.isEmpty()) slot.set(ItemStack.EMPTY);
        else slot.setChanged();
        return copy;
    }

    @Override
    public boolean stillValid(Player player) {
        return crate != null && !crate.isRemoved()
                && stillValid(ContainerLevelAccess.create(crate.getLevel(), crate.getBlockPos()), player, ModRegistry.MARKET_CRATE.get());
    }
}
