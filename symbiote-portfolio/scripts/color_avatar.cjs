/**
 * Color avatar frames using precise SVG regions based on pixel analysis.
 * Character centered ~x=510, left=389, right=878
 * 
 * Key landmarks from pixel scan:
 * - Hair top: y=0-140 (ellipse around x=505)
 * - Face: y=140-240 (x=477-539 at y=200, so face center ~508)
 * - Neck: y=240-280
 * - Necklace: y=270-295
 * - Shoulders/shirt top: y=280-310
 * - Shirt body: y=310-510
 * - Arms: left arm x=389-430, right arm extends to x=878 at y=250
 * - Belt: y=510-530
 * - Pants: y=530-880
 * - Shoes: y=880-1000
 */

const sharp = require('sharp');
const fs = require('fs');
const path = require('path');

const COLORS = {
    hair: '#000000',
    skin: '#E8B89A',
    glasses: '#7C3AED',
    shirt: '#0EA5E9',
    necklace: '#A78BFA',
    pants: '#4C1D95',
    shoes: '#1E40AF',
    belt: '#1E3A8A',
};

function hexToRgb(hex) {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return [r, g, b];
}

async function colorFrame(inputPath, outputPath) {
    const { data, info } = await sharp(inputPath)
        .raw()
        .toBuffer({ resolveWithObject: true });

    const { width, height, channels } = info;
    // Create output buffer (copy of original)
    const out = Buffer.from(data);

    // For each pixel: if it's white/near-white and has alpha > threshold,
    // color it based on its y,x position
    for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
            const idx = (y * width + x) * channels;
            const r = out[idx], g = out[idx + 1], b = out[idx + 2], a = out[idx + 3];

            // Skip transparent pixels
            if (a < 30) continue;

            // Skip dark pixels (black outlines) — keep them as-is
            if (r < 100 && g < 100 && b < 100) continue;

            // Skip medium-grey pixels (shading lines in shoes/hands)
            if (r < 160 && g < 160 && b < 160) continue;

            // This pixel is light (white or near-white fill area)
            // Determine which body part based on position
            let color = null;
            const cx = 510; // character center x

            // HAIR region: top of head
            if (y < 155 && x > 400 && x < 620) {
                // Upper hair dome
                const dx = x - 505;
                const dy = y - 90;
                if (dx * dx / (115 * 115) + dy * dy / (105 * 105) < 1.1) {
                    color = COLORS.hair;
                }
            }

            // FACE/SKIN region
            if (!color && y >= 130 && y < 265 && x > 430 && x < 590) {
                const dx = x - 508;
                const dy = y - 195;
                if (dx * dx / (75 * 75) + dy * dy / (70 * 70) < 1) {
                    color = COLORS.skin;
                }
            }

            // NECK skin
            if (!color && y >= 245 && y < 290 && x > 460 && x < 555) {
                color = COLORS.skin;
            }

            // Upper chest / collarbone — skin beside necklace
            if (!color && y >= 250 && y < 270 && x > 440 && x < 480) {
                color = COLORS.skin;
            }
            if (!color && y >= 250 && y < 270 && x > 520 && x < 560) {
                color = COLORS.skin;
            }
            // Shoulder fill — bridge gap between neck and shirt around necklace
            if (!color && y >= 265 && y < 300 && x > 420 && x < 475) {
                color = COLORS.shirt;
            }
            if (!color && y >= 265 && y < 300 && x > 525 && x < 600) {
                color = COLORS.shirt;
            }

            // HANDS — skin color
            // Left hand and forearm (near body, lower arm area)
            if (!color && y >= 380 && y < 500 && x >= 380 && x < 430) {
                color = COLORS.skin;
            }
            // Right hand and forearm (waving, extends far right)
            if (!color && y >= 200 && y < 320 && x > 680) {
                color = COLORS.skin;
            }
            // Right wrist area
            if (!color && y >= 240 && y < 300 && x > 650 && x < 700) {
                color = COLORS.skin;
            }

            // SHIRT region — expanded to fill shoulder gaps
            if (!color && y >= 280 && y < 520 && x > 395 && x < 600) {
                color = COLORS.shirt;
            }
            // Left sleeve — wider coverage
            if (!color && y >= 280 && y < 420 && x >= 380 && x <= 440) {
                color = COLORS.shirt;
            }
            // Right sleeve — wider coverage
            if (!color && y >= 260 && y < 370 && x >= 555 && x < 700) {
                color = COLORS.shirt;
            }
            // Right upper arm (shirt visible on shoulder)
            if (!color && y >= 240 && y < 320 && x >= 570 && x < 730) {
                color = COLORS.shirt;
            }

            // BELT region
            if (!color && y >= 515 && y < 545 && x > 420 && x < 590) {
                color = COLORS.belt;
            }

            // PANTS region
            if (!color && y >= 540 && y < 890 && x > 420 && x < 590) {
                color = COLORS.pants;
            }

            // SHOES region
            if (!color && y >= 890 && y < 1010 && x > 410 && x < 600) {
                color = COLORS.shoes;
            }

            // Apply color (strong fill, minimal blending)
            if (color) {
                const [cr, cg, cb] = hexToRgb(color);
                // 90% brand color for solid fill, 10% original for subtle shading
                const mix = 0.92;
                out[idx] = Math.round(cr * mix + r * (1 - mix));
                out[idx + 1] = Math.round(cg * mix + g * (1 - mix));
                out[idx + 2] = Math.round(cb * mix + b * (1 - mix));
                // Ensure full opacity
                out[idx + 3] = 255;
            }
        }
    }

    await sharp(out, { raw: { width, height, channels } })
        .webp({ quality: 92 })
        .toFile(outputPath);
}

async function main() {
    const dir = path.join(__dirname, '..', 'public', 'textures', 'corridor', 'avatar_anim');
    const backupDir = path.join(dir, 'originals');

    for (let i = 1; i <= 9; i++) {
        const filename = `${i}.webp`;
        const inputPath = path.join(backupDir, filename); // Read from originals
        const outputPath = path.join(dir, filename);

        if (!fs.existsSync(inputPath)) {
            console.log(`Backup not found for ${filename}, skipping`);
            continue;
        }

        await colorFrame(inputPath, outputPath);
        console.log(`Colored: ${filename}`);
    }

    console.log('\nAll frames colored!');
}

main().catch(console.error);
