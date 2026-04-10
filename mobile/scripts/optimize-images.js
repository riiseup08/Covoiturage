#!/usr/bin/env node
/**
 * Image Optimization Script for Mobile APK
 * 
 * This script optimizes all images in the project for mobile distribution.
 * Reduces APK size by compressing and resizing images.
 * 
 * Requirements:
 *   npm install --save-dev imagemin imagemin-mozjpeg imagemin-pngquant imagemin-webp sharp
 * 
 * Usage:
 *   node optimize-images.js [--check] [--resize] [--webp]
 * 
 * Options:
 *   --check    Only report sizes, don't modify
 *   --resize   Resize large images to max 1920px width
 *   --webp     Convert to WebP format (better compression)
 */

const fs = require('fs');
const path = require('path');
const imagemin = require('imagemin');
const imageminMozjpeg = require('imagemin-mozjpeg').default;
const imageminPngquant = require('imagemin-pngquant').default;
const imageminWebp = require('imagemin-webp').default;
const sharp = require('sharp');

const DIRS_TO_OPTIMIZE = [
  './assets',
  './src/assets',
  './static/images',
];

const MAX_IMAGE_SIZE = 100 * 1024; // 100KB per image
const MAX_WIDTH = 1920; // Max 1920px width
const QUALITY_COMPRESSION = 75; // JPEG quality

const args = process.argv.slice(2);
const checkOnly = args.includes('--check');
const resize = args.includes('--resize');
const convertWebp = args.includes('--webp');

async function getImageStats(imagePath) {
  try {
    const stats = fs.statSync(imagePath);
    const meta = await sharp(imagePath).metadata();
    return {
      path: imagePath,
      size: stats.size,
      width: meta.width,
      height: meta.height,
      format: meta.format,
      oversized: stats.size > MAX_IMAGE_SIZE,
    };
  } catch (error) {
    return null;
  }
}

async function resizeImage(imagePath) {
  try {
    const metadata = await sharp(imagePath).metadata();
    if (metadata.width > MAX_WIDTH) {
      const height = Math.round((metadata.height * MAX_WIDTH) / metadata.width);
      await sharp(imagePath)
        .resize(MAX_WIDTH, height, { fit: 'contain', withoutEnlargement: true })
        .toFile(imagePath.replace(/\.\w+$/, '-resized.$&'));
      console.log(`  ✓ Resized: ${path.basename(imagePath)} (${metadata.width}x${metadata.height} → ${MAX_WIDTH}x${height})`);
    }
  } catch (error) {
    console.error(`  ✗ Failed to resize ${imagePath}:`, error.message);
  }
}

async function compressImages() {
  console.log('🖼️  Image Optimization Scanner\n');
  console.log('Configuration:');
  console.log(`  Max image size: ${MAX_IMAGE_SIZE / 1024}KB`);
  console.log(`  Max width: ${MAX_WIDTH}px`);
  console.log(`  JPEG quality: ${QUALITY_COMPRESSION}%`);
  console.log(`  Check only: ${checkOnly}`);
  console.log(`  Resize: ${resize}`);
  console.log(`  WebP conversion: ${convertWebp}\n`);

  let totalSize = 0;
  let totalCompressed = 0;
  let oversizedCount = 0;

  // Scan all directories
  for (const dir of DIRS_TO_OPTIMIZE) {
    if (!fs.existsSync(dir)) continue;

    console.log(`📁 Scanning ${dir}...`);
    const files = fs.readdirSync(dir, { recursive: true });
    const imageFiles = files.filter((f) => /\.(jpg|jpeg|png|webp)$/i.test(f));

    if (imageFiles.length === 0) {
      console.log('  (no images found)\n');
      continue;
    }

    for (const file of imageFiles) {
      const fullPath = path.join(dir, file);
      const stats = await getImageStats(fullPath);

      if (!stats) continue;

      totalSize += stats.size;
      const isOversized = stats.size > MAX_IMAGE_SIZE;

      if (isOversized) {
        oversizedCount++;
        console.log(
          `  ⚠️  ${path.basename(fullPath)} (${(stats.size / 1024).toFixed(1)}KB, ${stats.width}x${stats.height})`
        );
      } else {
        console.log(
          `  ✓ ${path.basename(fullPath)} (${(stats.size / 1024).toFixed(1)}KB, ${stats.width}x${stats.height})`
        );
      }

      if (!checkOnly && resize && stats.width > MAX_WIDTH) {
        await resizeImage(fullPath);
      }
    }
    console.log('');
  }

  // Summary
  console.log('═════════════════════════════════════════');
  console.log('📊 SCAN SUMMARY');
  console.log('═════════════════════════════════════════');
  console.log(`Total image data: ${(totalSize / 1024 / 1024).toFixed(2)}MB`);
  console.log(`Oversized images: ${oversizedCount}`);

  if (oversizedCount > 0) {
    console.log(`\n⚠️  Recommendations:`);
    console.log(`  1. Run with --resize to auto-shrink images > ${MAX_WIDTH}px`);
    console.log(`  2. Manually compress images > ${MAX_IMAGE_SIZE / 1024}KB`);
    console.log(`  3. Use PNG for images with transparency, JPEG for photos`);
    console.log(`  4. Consider WebP format (run with --webp)`);
  } else {
    console.log(`\n✅ All images are optimized!`);
  }
}

async function runOptimization() {
  if (checkOnly) {
    await compressImages();
    return;
  }

  console.log('🖼️  Starting image optimization...\n');

  try {
    const options = [
      imageminMozjpeg({ quality: QUALITY_COMPRESSION }),
      imageminPngquant({
        quality: [0.6, 0.8],
      }),
    ];

    if (convertWebp) {
      options.push(imageminWebp({ quality: 75 }));
    }

    for (const dir of DIRS_TO_OPTIMIZE) {
      if (!fs.existsSync(dir)) continue;

      console.log(`📁 Optimizing ${dir}...`);
      const files = await imagemin([`${dir}/**/*.{jpg,jpeg,png}`], {
        destination: dir,
        plugins: options,
      });

      if (files.length === 0) {
        console.log('  (no images to optimize)\n');
      } else {
        console.log(`  ✓ Optimized ${files.length} image(s)\n`);
      }
    }

    console.log('✅ Image optimization complete!');

    // Show scan after optimization
    await compressImages();
  } catch (error) {
    console.error('❌ Optimization failed:', error);
    process.exit(1);
  }
}

// Run
runOptimization().catch((error) => {
  console.error('Error:', error);
  process.exit(1);
});
