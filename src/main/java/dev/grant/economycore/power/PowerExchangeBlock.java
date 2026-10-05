package dev.grant.economycore.power;

import com.mojang.serialization.MapCodec;
import dev.grant.economycore.ModRegistry;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;
import org.jetbrains.annotations.Nullable;

/** Pipe power in, get coins for your team. See {@link PowerExchangeService} for the payout curve. */
public class PowerExchangeBlock extends BaseEntityBlock {
    public static final MapCodec<PowerExchangeBlock> CODEC = simpleCodec(PowerExchangeBlock::new);

    public PowerExchangeBlock(Properties props) {
        super(props);
    }

    @Override
    protected MapCodec<? extends BaseEntityBlock> codec() {
        return CODEC;
    }

    @Override
    protected RenderShape getRenderShape(BlockState state) {
        return RenderShape.MODEL;
    }

    @Nullable
    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new PowerExchangeBlockEntity(pos, state);
    }

    @Nullable
    @Override
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
        return level.isClientSide ? null
                : createTickerHelper(type, ModRegistry.POWER_EXCHANGE_BE.get(), PowerExchangeBlockEntity::serverTick);
    }

    @Override
    public void setPlacedBy(Level level, BlockPos pos, BlockState state, @Nullable LivingEntity placer, ItemStack stack) {
        super.setPlacedBy(level, pos, state, placer, stack);
        if (!level.isClientSide && placer instanceof Player player
                && level.getBlockEntity(pos) instanceof PowerExchangeBlockEntity be) {
            be.setOwner(player);
        }
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (level.isClientSide) return InteractionResult.SUCCESS;
        if (level.getBlockEntity(pos) instanceof PowerExchangeBlockEntity be) {
            if (be.getOwner() == null) be.setOwner(player); // e.g. placed by a machine
            var r = PowerExchangeService.rateFor(be.getOwner());
            player.displayClientMessage(Component.translatable("message.economy_core.power_exchange",
                    String.format("%,.0f", r.fePerTick()), String.format("%,.1f", r.coinsPerMinute()), be.getOwnerName()), true);
        }
        return InteractionResult.CONSUME;
    }
}
