package dev.grant.economycore.client;

import com.mojang.blaze3d.vertex.PoseStack;
import dev.grant.economycore.power.PowerExchangeBlockEntity;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.blockentity.BlockEntityRenderer;
import net.minecraft.client.renderer.blockentity.BlockEntityRendererProvider;
import net.minecraft.network.chat.Component;

/** Floating "coins per minute" over the Power Exchange, facing the camera. */
public class PowerExchangeRenderer implements BlockEntityRenderer<PowerExchangeBlockEntity> {
    private final Font font;

    public PowerExchangeRenderer(BlockEntityRendererProvider.Context ctx) {
        this.font = ctx.getFont();
    }

    @Override
    public void render(PowerExchangeBlockEntity be, float partialTick, PoseStack pose, MultiBufferSource buffers,
                       int light, int overlay) {
        double cpm = be.getCoinsPerMinute();
        Component top = Component.translatable("display.economy_core.power_exchange.coins", String.format("%,.1f", cpm));
        Component bottom = Component.translatable("display.economy_core.power_exchange.fe", String.format("%,.0f", be.getFePerTick()));
        pose.pushPose();
        pose.translate(0.5, 1.45, 0.5);
        pose.mulPose(Minecraft.getInstance().getEntityRenderDispatcher().cameraOrientation());
        pose.scale(-0.025f, -0.025f, 0.025f);
        int color = cpm > 0 ? 0xFFFFD34D : 0xFFAAAAAA;
        font.drawInBatch(top, -font.width(top) / 2f, 0, color, false, pose.last().pose(), buffers,
                Font.DisplayMode.NORMAL, 0x40000000, 0xF000F0);
        font.drawInBatch(bottom, -font.width(bottom) / 2f, 10, 0xFFCCCCCC, false, pose.last().pose(), buffers,
                Font.DisplayMode.NORMAL, 0x40000000, 0xF000F0);
        pose.popPose();
    }
}
