package dev.grant.economycore.frontier;

import dev.grant.economycore.ModRegistry;
import dev.grant.economycore.market.MarketService;
import dev.grant.economycore.market.TeamHelper;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.BlockHitResult;
import org.jetbrains.annotations.Nullable;

import java.util.UUID;

/**
 * The Frontier Gateway. On an island (The Isles) it sends you to your team's landing spot in the Frontier
 * (the real overworld), once your team has bought tier 3. In the Frontier it sends you back to the gateway you
 * left from. Placing a gateway in the Frontier moves your team's landing spot there.
 */
public class FrontierGatewayBlock extends Block {
    public static final ResourceKey<Level> ISLES =
            ResourceKey.create(Registries.DIMENSION, ResourceLocation.fromNamespaceAndPath("economy_core", "isles"));
    public static final int FRONTIER_TIER = 3;
    private static final int MIN_DIST = 500, MAX_DIST = 1500;

    public FrontierGatewayBlock(Properties props) {
        super(props);
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (level.isClientSide) return InteractionResult.SUCCESS;
        if (!(player instanceof ServerPlayer sp) || !(level instanceof ServerLevel here)) return InteractionResult.CONSUME;
        MinecraftServer server = here.getServer();
        if (here.dimension() == Level.OVERWORLD) {
            goHome(sp, server);
        } else {
            goToFrontier(sp, server, here, pos);
        }
        return InteractionResult.CONSUME;
    }

    private static void goToFrontier(ServerPlayer player, MinecraftServer server, ServerLevel from, BlockPos gateway) {
        if (MarketService.getTier(server, player.getUUID()) < FRONTIER_TIER) {
            player.displayClientMessage(Component.translatable("message.economy_core.frontier_locked").withStyle(ChatFormatting.RED), true);
            return;
        }
        ServerLevel frontier = server.overworld();
        FrontierData data = FrontierData.get(server);
        UUID team = TeamHelper.accountId(player.getUUID());
        BlockPos landing = data.landing(team);
        boolean firstVisit = landing == null;
        if (firstVisit) {
            landing = findLanding(frontier, player.getRandom());
            data.setLanding(team, landing);
        }
        if (!frontier.getBlockState(landing).is(ModRegistry.FRONTIER_GATEWAY.get())) buildLanding(frontier, landing);
        data.setReturn(player.getUUID(), from.dimension(), gateway);
        teleport(player, frontier, landing.east());
        if (firstVisit) {
            player.displayClientMessage(Component.translatable("message.economy_core.frontier_first").withStyle(ChatFormatting.GREEN), false);
        }
    }

    private static void goHome(ServerPlayer player, MinecraftServer server) {
        FrontierData.Spot spot = FrontierData.get(server).returnSpot(player.getUUID());
        ServerLevel level = spot == null ? null : server.getLevel(spot.dimension());
        BlockPos target;
        if (level != null) {
            target = spot.pos().east();
        } else {
            // Never left through a gateway (e.g. came by portal): go to your bed/island, or the Isles spawn.
            level = server.getLevel(player.getRespawnDimension());
            BlockPos respawn = player.getRespawnPosition();
            if (level == null || respawn == null || level.dimension() == Level.OVERWORLD) {
                level = server.getLevel(ISLES);
                if (level == null) level = server.overworld();
                respawn = level.getSharedSpawnPos();
            }
            target = respawn;
        }
        teleport(player, level, target);
    }

    private static void teleport(ServerPlayer player, ServerLevel level, BlockPos feet) {
        level.getChunk(feet.getX() >> 4, feet.getZ() >> 4); // make sure it's generated and loaded
        player.teleportTo(level, feet.getX() + 0.5, feet.getY(), feet.getZ() + 0.5, player.getYRot(), player.getXRot());
        level.playSound(null, feet, SoundEvents.ENDERMAN_TELEPORT, SoundSource.PLAYERS, 1f, 0.8f);
    }

    /** A dry, solid surface spot 500-1,500 blocks from world spawn, so teams don't land on each other. */
    static BlockPos findLanding(ServerLevel level, RandomSource rng) {
        BlockPos spawn = level.getSharedSpawnPos();
        for (int i = 0; i < 64; i++) {
            float angle = rng.nextFloat() * Mth.TWO_PI;
            int dist = MIN_DIST + rng.nextInt(MAX_DIST - MIN_DIST);
            int x = spawn.getX() + (int) (Mth.cos(angle) * dist);
            int z = spawn.getZ() + (int) (Mth.sin(angle) * dist);
            level.getChunk(x >> 4, z >> 4);
            int y = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z);
            BlockPos ground = new BlockPos(x, y - 1, z);
            BlockState below = level.getBlockState(ground);
            if (below.getFluidState().isEmpty() && below.isSolid() && y > level.getSeaLevel()) {
                return new BlockPos(x, y, z);
            }
        }
        return level.getSharedSpawnPos();
    }

    /** 3x3 stone platform with the gateway in the middle and headroom above. */
    static void buildLanding(ServerLevel level, BlockPos center) {
        for (int dx = -1; dx <= 1; dx++) {
            for (int dz = -1; dz <= 1; dz++) {
                level.setBlockAndUpdate(center.offset(dx, -1, dz), Blocks.POLISHED_ANDESITE.defaultBlockState());
                for (int dy = 0; dy <= 2; dy++) {
                    if (dx == 0 && dz == 0 && dy == 0) continue;
                    level.setBlockAndUpdate(center.offset(dx, dy, dz), Blocks.AIR.defaultBlockState());
                }
            }
        }
        level.setBlockAndUpdate(center, ModRegistry.FRONTIER_GATEWAY.get().defaultBlockState());
    }

    @Override
    public void setPlacedBy(Level level, BlockPos pos, BlockState state, @Nullable LivingEntity placer, ItemStack stack) {
        super.setPlacedBy(level, pos, state, placer, stack);
        if (level instanceof ServerLevel sl && sl.dimension() == Level.OVERWORLD && placer instanceof ServerPlayer sp) {
            FrontierData.get(sl.getServer()).setLanding(TeamHelper.accountId(sp.getUUID()), pos);
            sp.displayClientMessage(Component.translatable("message.economy_core.frontier_moved").withStyle(ChatFormatting.GREEN), true);
        }
    }
}
