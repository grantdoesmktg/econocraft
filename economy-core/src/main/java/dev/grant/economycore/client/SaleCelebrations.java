package dev.grant.economycore.client;

import com.mojang.blaze3d.vertex.PoseStack;
import dev.grant.economycore.network.MarketFxPayload;
import it.unimi.dsi.fastutil.ints.IntList;
import net.minecraft.Util;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.resources.sounds.SimpleSoundInstance;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ItemParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.FireworkExplosion;
import org.joml.Vector3f;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;

/**
 * Client-side sale celebrations. Eight tiers, from dull grey pocket change to a MEGA SALE with fireworks.
 * Overlay text and sparks are drawn on top of the Market screen (or the HUD when no screen is open);
 * world particles, fireworks and sounds play around the crate / player.
 */
public final class SaleCelebrations {
    private static final RandomSource RNG = RandomSource.create();
    private static final List<Effect> ACTIVE = new ArrayList<>();
    /** Big (tier 7-8) effects are limited to one every few seconds so auto-sell can't spam them. */
    private static final long BIG_COOLDOWN_MS = 4000;
    private static long lastBigMs;

    //                                    tier: 0(dep)  1     2     3     4     5     6     7     8
    private static final int[] DURATION_MS = {1400, 1000, 1300, 1500, 1800, 2200, 2600, 3200, 4500};
    private static final float[] SCALE =     {0.9f, 0.9f, 1.0f, 1.15f, 1.4f, 1.8f, 2.2f, 2.8f, 2.6f};
    private static final int[] SPARKS =      {0,    0,    0,    0,    4,    10,   18,   30,   60};

    private SaleCelebrations() {}

    private record Spark(float vx, float vy, int color, boolean coin, float size) {}

    private static final class Effect {
        final int tier;
        final boolean deposit;
        final long amount;
        final long start = Util.getMillis();
        final List<Spark> sparks = new ArrayList<>();

        Effect(int tier, boolean deposit, long amount) {
            this.tier = tier;
            this.deposit = deposit;
            this.amount = amount;
            for (int i = 0; i < SPARKS[tier]; i++) {
                float angle = RNG.nextFloat() * Mth.TWO_PI;
                float speed = 40 + RNG.nextFloat() * (40 + tier * 25);
                int color = tier >= 7 ? Mth.hsvToRgb(RNG.nextFloat(), 0.8f, 1f)
                        : tier == 6 ? (RNG.nextBoolean() ? 0xFFE066 : 0x7FFFEF) : 0xFFD24A;
                sparks.add(new Spark(Mth.cos(angle) * speed, Mth.sin(angle) * speed - 30,
                        color, tier <= 5 || RNG.nextFloat() < 0.35f, 2 + RNG.nextFloat() * 2));
            }
        }

        int duration() { return DURATION_MS[tier]; }
    }

    // ------------------------------------------------------------ incoming

    public static void onPayload(MarketFxPayload msg) {
        Minecraft mc = Minecraft.getInstance();
        if (msg.kind() == MarketFxPayload.KIND_DEPOSIT) {
            ACTIVE.add(new Effect(0, true, msg.amount()));
            play(mc, SoundEvents.UI_BUTTON_CLICK.value(), 1.6f, 0.25f);
            return;
        }
        int tier = Mth.clamp(msg.tier(), 0, 8);
        if (tier == 0) return; // celebrations disabled on the server
        long now = Util.getMillis();
        if (tier >= 7) {
            if (now - lastBigMs < BIG_COOLDOWN_MS) tier = 6;
            else lastBigMs = now;
        }
        ACTIVE.add(new Effect(tier, false, msg.amount()));
        if (ACTIVE.size() > 12) ACTIVE.remove(0);
        worldEffects(mc, tier, msg.pos());
    }

    private static void worldEffects(Minecraft mc, int tier, BlockPos crate) {
        ClientLevel level = mc.level;
        Player player = mc.player;
        if (level == null || player == null) return;
        double cx = crate.getX() + 0.5, cy = crate.getY() + 1.0, cz = crate.getZ() + 0.5;
        switch (tier) {
            case 2 -> play(mc, SoundEvents.UI_BUTTON_CLICK.value(), 1.4f, 0.3f);
            case 3 -> play(mc, SoundEvents.EXPERIENCE_ORB_PICKUP, 1.2f, 0.35f);
            case 4 -> {
                play(mc, SoundEvents.EXPERIENCE_ORB_PICKUP, 1.0f, 0.6f);
                DustParticleOptions gold = new DustParticleOptions(new Vector3f(1f, 0.84f, 0.1f), 1.0f);
                for (int i = 0; i < 10; i++) level.addParticle(gold, cx + rnd(0.7), cy + RNG.nextDouble() * 0.6, cz + rnd(0.7), 0, 0.02, 0);
            }
            case 5 -> {
                play(mc, SoundEvents.NOTE_BLOCK_BELL.value(), 1.2f, 0.8f);
                play(mc, SoundEvents.EXPERIENCE_ORB_PICKUP, 0.8f, 0.6f);
                ItemParticleOption coin = new ItemParticleOption(ParticleTypes.ITEM, new ItemStack(coinItem("coin_gold")));
                for (int i = 0; i < 24; i++) level.addParticle(coin, cx + rnd(0.8), cy + 1.2 + RNG.nextDouble(), cz + rnd(0.8), rnd(0.08), 0.05, rnd(0.08));
            }
            case 6 -> {
                play(mc, SoundEvents.PLAYER_LEVELUP, 1.3f, 0.7f);
                play(mc, SoundEvents.AMETHYST_BLOCK_CHIME, 1.0f, 1.0f);
                for (int i = 0; i < 30; i++) {
                    level.addParticle(i % 2 == 0 ? ParticleTypes.END_ROD : ParticleTypes.ELECTRIC_SPARK,
                            cx + rnd(1.0), cy + RNG.nextDouble() * 1.5, cz + rnd(1.0), rnd(0.05), 0.05, rnd(0.05));
                }
            }
            case 7 -> {
                play(mc, SoundEvents.PLAYER_LEVELUP, 1.0f, 0.9f);
                fireworks(level, player.getX(), player.getY() + 3, player.getZ(), 2, FireworkExplosion.Shape.LARGE_BALL);
            }
            case 8 -> {
                play(mc, SoundEvents.UI_TOAST_CHALLENGE_COMPLETE, 1.0f, 1.0f);
                play(mc, SoundEvents.PLAYER_LEVELUP, 0.8f, 1.0f);
                play(mc, SoundEvents.FIREWORK_ROCKET_LARGE_BLAST, 1.0f, 1.0f);
                fireworks(level, player.getX(), player.getY() + 3, player.getZ(), 4, FireworkExplosion.Shape.STAR);
                fireworks(level, player.getX() + 3, player.getY() + 5, player.getZ() - 2, 1, FireworkExplosion.Shape.LARGE_BALL);
                fireworks(level, player.getX() - 3, player.getY() + 4, player.getZ() + 2, 1, FireworkExplosion.Shape.BURST);
                // Totem-style item pop-up, with a coin instead of a totem.
                mc.gameRenderer.displayItemActivation(new ItemStack(coinItem("coin_netherite")));
            }
            default -> { }
        }
    }

    /** Visual-only firework explosions (no entity, no damage). */
    private static void fireworks(ClientLevel level, double x, double y, double z, int count, FireworkExplosion.Shape shape) {
        List<FireworkExplosion> list = new ArrayList<>();
        for (int i = 0; i < count; i++) {
            int a = Mth.hsvToRgb(RNG.nextFloat(), 0.9f, 1f), b = Mth.hsvToRgb(RNG.nextFloat(), 0.9f, 1f);
            list.add(new FireworkExplosion(shape, IntList.of(a, b), IntList.of(0xFFFFFF), true, true));
        }
        level.createFireworks(x, y, z, 0, 0, 0, list);
    }

    private static void play(Minecraft mc, SoundEvent sound, float pitch, float volume) {
        mc.getSoundManager().play(SimpleSoundInstance.forUI(sound, pitch, volume));
    }

    private static double rnd(double r) {
        return (RNG.nextDouble() * 2 - 1) * r;
    }

    private static Item coinItem(String path) {
        Item item = BuiltInRegistries.ITEM.get(ResourceLocation.fromNamespaceAndPath("lightmanscurrency", path));
        return item == Items.AIR ? Items.GOLD_NUGGET : item;
    }

    // ------------------------------------------------------------ overlay

    /**
     * Draw active effects. Small ones (and deposits) float up from (anchorX, anchorY);
     * tier 5+ celebrations play in the middle of the screen. Pass anchor -1 to use the HUD default.
     */
    public static void render(GuiGraphics g, int anchorX, int anchorY) {
        if (ACTIVE.isEmpty()) return;
        Font font = Minecraft.getInstance().font;
        int w = g.guiWidth(), h = g.guiHeight();
        if (anchorX < 0) { anchorX = w / 2; anchorY = h - 72; }
        long now = Util.getMillis();

        Iterator<Effect> it = ACTIVE.iterator();
        while (it.hasNext()) {
            Effect e = it.next();
            float age = (now - e.start) / 1000f;
            float t = (now - e.start) / (float) e.duration();
            if (t >= 1f) { it.remove(); continue; }

            boolean big = e.tier >= 5;
            float cx = big ? w / 2f : anchorX;
            float cy = big ? h * 0.33f : anchorY - t * (8 + e.tier * 3);
            float alpha = t < 0.7f ? 1f : 1f - (t - 0.7f) / 0.3f;

            // Pop-in bounce for tier 4+.
            float pop = 1f;
            if (e.tier >= 4) {
                float p = Math.min(1f, (now - e.start) / 280f);
                pop = 0.3f + 0.7f * easeOutBack(p);
                if (e.tier >= 8) pop *= 1f + 0.06f * Mth.sin(age * 9f); // MEGA keeps pulsing
            }
            // Shake for the top tiers.
            if (e.tier >= 7 && t < 0.4f) {
                float s = (e.tier == 8 ? 3f : 1.5f) * (1f - t / 0.4f);
                cx += rnd(s);
                cy += rnd(s);
            }

            // Screen flash.
            if (e.tier == 8 && now - e.start < 450) {
                int a = (int) (170 * (1f - (now - e.start) / 450f));
                g.fill(0, 0, w, h, (a << 24) | 0xFFFFFF);
            } else if (e.tier == 7 && now - e.start < 250) {
                int a = (int) (70 * (1f - (now - e.start) / 250f));
                g.fill(0, 0, w, h, (a << 24) | 0xFFFFFF);
            }

            drawSparks(g, e, cx, cy, age, alpha);

            String amount = (e.deposit ? "Deposited " : "+") + String.format("%,d", e.amount);
            if (e.tier == 8) {
                drawText(g, font, "MEGA SALE!", cx, cy - 26 * pop, 4.0f * pop, e.tier, age, alpha, true);
                drawText(g, font, amount, cx, cy + 14 * pop, SCALE[8] * pop, e.tier, age, alpha, true);
            } else if (e.tier == 7) {
                drawText(g, font, "BIG SALE!", cx, cy - 20 * pop, 2.0f * pop, e.tier, age, alpha, true);
                drawText(g, font, amount, cx, cy + 6 * pop, SCALE[7] * pop, e.tier, age, alpha, true);
            } else {
                drawText(g, font, amount, cx, cy, SCALE[e.tier] * pop, e.tier, age, alpha, e.tier >= 5);
            }
        }
    }

    private static void drawSparks(GuiGraphics g, Effect e, float cx, float cy, float age, float alpha) {
        if (e.sparks.isEmpty()) return;
        PoseStack pose = g.pose();
        ItemStack coin = new ItemStack(coinItem("coin_gold"));
        for (Spark s : e.sparks) {
            float x = cx + s.vx() * age;
            float y = cy + s.vy() * age + 90 * age * age; // gravity
            if (s.coin()) {
                pose.pushPose();
                pose.translate(x - 4, y - 4, 300);
                pose.scale(0.5f, 0.5f, 1f);
                g.renderItem(coin, 0, 0);
                pose.popPose();
            } else {
                int a = Math.max(5, (int) (alpha * 255));
                int size = (int) s.size();
                pose.pushPose();
                pose.translate(0, 0, 300);
                g.fill((int) x, (int) y, (int) x + size, (int) y + size, (a << 24) | s.color());
                pose.popPose();
            }
        }
    }

    /** Centered, scaled text with per-tier colouring (grey, white, greens, gold, shimmer, rainbow). */
    private static void drawText(GuiGraphics g, Font font, String text, float cx, float cy, float scale,
                                 int tier, float age, float alpha, boolean bold) {
        int a = (int) (alpha * 255);
        if (a < 6) return; // the font treats near-zero alpha as opaque
        Component full = bold ? Component.literal(text).withStyle(s -> s.withBold(true)) : Component.literal(text);
        int width = font.width(full);

        PoseStack pose = g.pose();
        pose.pushPose();
        pose.translate(cx, cy, 400);
        pose.scale(scale, scale, 1f);
        float x = -width / 2f;
        float y = -font.lineHeight / 2f;

        if (tier <= 5) {
            int rgb = switch (tier) {
                case 0 -> 0x9FB4C8;   // deposit: calm blue-grey
                case 1 -> 0x8A8A8A;   // pocket change: dull grey
                case 2 -> 0xFFFFFF;
                case 3 -> 0xA6F5A6;
                case 4 -> 0x3EDB3E;
                default -> 0xFFC400;  // 5: bold gold
            };
            g.drawString(font, full, (int) x, (int) y, (a << 24) | rgb, tier >= 2);
        } else {
            // Per-character colours: tier 6 shimmers gold<->aqua, tier 7-8 run a rainbow.
            float cursor = x;
            for (int i = 0; i < text.length(); i++) {
                String ch = String.valueOf(text.charAt(i));
                Component c = bold ? Component.literal(ch).withStyle(s -> s.withBold(true)) : Component.literal(ch);
                int rgb;
                if (tier == 6) {
                    float k = 0.5f + 0.5f * Mth.sin(age * 4f + i * 0.5f);
                    rgb = lerpColor(0xFFD700, 0x40E0D0, k);
                } else {
                    float hue = (age * (tier == 8 ? 0.9f : 0.6f) + i * 0.07f) % 1f;
                    rgb = Mth.hsvToRgb(hue, 0.85f, 1f);
                }
                float bob = tier >= 7 ? Mth.sin(age * 8f + i * 0.6f) * 1.2f : 0f;
                g.drawString(font, c, (int) cursor, (int) (y + bob), (a << 24) | rgb, true);
                cursor += font.width(c);
            }
        }
        pose.popPose();
    }

    private static int lerpColor(int c1, int c2, float k) {
        int r = (int) Mth.lerp(k, (c1 >> 16) & 255, (c2 >> 16) & 255);
        int gr = (int) Mth.lerp(k, (c1 >> 8) & 255, (c2 >> 8) & 255);
        int b = (int) Mth.lerp(k, c1 & 255, c2 & 255);
        return (r << 16) | (gr << 8) | b;
    }

    private static float easeOutBack(float x) {
        float c1 = 1.70158f, c3 = c1 + 1f;
        return 1f + c3 * (float) Math.pow(x - 1, 3) + c1 * (float) Math.pow(x - 1, 2);
    }
}
