package dev.grant.economycore.power;

import dev.grant.economycore.ModRegistry;
import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientGamePacketListener;
import net.minecraft.network.protocol.game.ClientboundBlockEntityDataPacket;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.neoforge.energy.IEnergyStorage;
import org.jetbrains.annotations.Nullable;

import java.util.UUID;

/** Accepts any amount of FE from any side and hands it to {@link PowerExchangeService} for the owner's team. */
public class PowerExchangeBlockEntity extends BlockEntity {
    @Nullable private UUID owner;
    private String ownerName = "";
    /** Team-wide live numbers, synced to the client for the floating display. */
    private double fePerTick, coinsPerMinute;
    private int tickCounter;

    private final IEnergyStorage energy = new IEnergyStorage() {
        @Override
        public int receiveEnergy(int max, boolean simulate) {
            if (owner == null || max <= 0) return 0;
            if (!simulate) PowerExchangeService.receive(owner, max);
            return max;
        }
        @Override public int extractEnergy(int max, boolean simulate) { return 0; }
        @Override public int getEnergyStored() { return 0; }
        @Override public int getMaxEnergyStored() { return Integer.MAX_VALUE; }
        @Override public boolean canExtract() { return false; }
        @Override public boolean canReceive() { return owner != null; }
    };

    public PowerExchangeBlockEntity(BlockPos pos, BlockState state) {
        super(ModRegistry.POWER_EXCHANGE_BE.get(), pos, state);
    }

    public IEnergyStorage getEnergy() { return energy; }
    @Nullable public UUID getOwner() { return owner; }
    public String getOwnerName() { return ownerName; }
    public double getFePerTick() { return fePerTick; }
    public double getCoinsPerMinute() { return coinsPerMinute; }

    public void setOwner(Player player) {
        owner = player.getUUID();
        ownerName = player.getGameProfile().getName();
        setChanged();
    }

    public static void serverTick(Level level, BlockPos pos, BlockState state, PowerExchangeBlockEntity be) {
        if (be.owner == null || ++be.tickCounter < 20) return;
        be.tickCounter = 0;
        var r = PowerExchangeService.rateFor(be.owner);
        if (Math.abs(r.fePerTick() - be.fePerTick) > 0.5 || Math.abs(r.coinsPerMinute() - be.coinsPerMinute) > 0.05) {
            be.fePerTick = r.fePerTick();
            be.coinsPerMinute = r.coinsPerMinute();
            level.sendBlockUpdated(pos, state, state, Block.UPDATE_CLIENTS);
        }
    }

    @Override
    protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.saveAdditional(tag, registries);
        if (owner != null) tag.putUUID("Owner", owner);
        tag.putString("OwnerName", ownerName);
    }

    @Override
    protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        owner = tag.hasUUID("Owner") ? tag.getUUID("Owner") : null;
        ownerName = tag.getString("OwnerName");
        fePerTick = tag.getDouble("FePerTick");
        coinsPerMinute = tag.getDouble("CoinsPerMinute");
    }

    @Override
    public CompoundTag getUpdateTag(HolderLookup.Provider registries) {
        CompoundTag tag = new CompoundTag();
        tag.putDouble("FePerTick", fePerTick);
        tag.putDouble("CoinsPerMinute", coinsPerMinute);
        return tag;
    }

    @Override
    public Packet<ClientGamePacketListener> getUpdatePacket() {
        return ClientboundBlockEntityDataPacket.create(this);
    }
}
