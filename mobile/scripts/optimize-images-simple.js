#!/usr/bin/env node
/**
 * Simple Image Optimization Script for Mobile APK (using sharp)
 * Optimizes PNG/JPEG images for smaller APK size
 */

const fs = require('fs');
const path = require('path');
const sharp = require('sharp');

const DIRS_TO_OPTIMIZE = ['./assets', './src/assets', './static/images'];
const QUALITY_JPEG = 75;
const QUALITY_PNG = 8; // Number of colors for PNG
const MAX_WIDTH = 1920;

const args = process.argv.slice(2);
const checkOnly = args.includes('--check');
const resize = args.includes('--resize');
const convertWebp = args.includes('--webp');

function getDirectoryFiles(dir) {
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir, { recursive: true })
    .filter(f => /\.(jpg|jpeg|png|gif)$/i.test(f))
    .map(f => path.join(dir, f))
    .filter(f => fs.statSync(f).isFile());
}

async function optimizeImage(imagePath) {
  try {
    const stats = fs.statSync(imagePath);
    const sizeBefore = stats.size;
    const ext = path.extname(imagePath).toLowerCase();
    const metadata = await sharp(imagePath).metadata();

    // Determine output format
    let shouldConvert = false;
    let outputPath = imagePath;

    // Resize if needed
    let transform = sharp(imagePath);
    if (metadata.width > MAX_WIDTH) {
      const height = Math.round((metadata.height * MAX_WIDTH) / metadata.width);
      transform = transform.resize(MAX_WIDTH, height, { withoutEnlargement: true });
    }

    // Compress based on format
    if (ext === '.png') {
      if (convertWebp) {
        transform = transform.webp({ quality: 75 });
        outputPath = imagePath.replace(/\.png$/, '.webp');
        shouldConvert = true;
      } else {
        transform = transform.png({ colors: QUALITY_PNG, progressive: true });
      }
    } else if (['.jpg', '.jpeg'].includes(ext)) {
      if (convertWebp) {
        transform = transform.webp({ quality: 75 });
        outputPath = imagePath.replace(/\.(jpg|jpeg)$/i, '.webp');
        shouldConvert = true;
      } else {
        transform = transform.jpeg({ quality: QUALITY_JPEG, progressive: true });
      }
    }

    // Save optimized image
    await transform.toFile(outputPath);
    const sizeAfter = fs.statSync(outputPath).size;
    const saved = Math.round((1 - sizeAfter / sizeBefore) * 100);

    if (shouldConvert) {
      console.log(`  ✓ ${path.basename(imagePath)} → ${path.basename(outputPath)}`);
      console.log(`    ${(sizeBefore / 1024).toFixed(1)}KB → ${(sizeAfter / 1024).toFixed(1)}KB (saved ${saved}%)`);
      if (imagePath !== outputPath) {
        // Keep original for now, can be deleted later
      }
    } else {
      if (sizeBefore !== sizeAfter) {
        console.log(`  ✓ ${path.basename(imagePath)} (${(sizeBefore / 1024).toFixed(1)}KB → ${(sizeAfter / 1024).toFixed(1)}KB, saved ${saved}%)`);
      }
    }

    return { before: sizeBefore, after: sizeAfter };
  } catch (error) {
    console.error(`  ✗ Error optimizing ${path.basename(imagePath)}:`, error.message);
    return null;
  }
}

async function scanImages() {
  console.log('📊 IMAGE SIZES BEFORE OPTIMIZATION:\n');
  let totalSize = 0;

  for (const dir of DIRS_TO_OPTIMIZE) {
    const files = getDirectoryFiles(dir);
    if (files.length === 0) continue;

    console.log(`📁 ${dir}:`);
    for (const file of files) {
      const size = fs.statSync(file).size;
      console.log(`  ${path.basename(file)}: ${(size / 1024).toFixed(2)} KB`);
      totalSize += size;
    }
  }

  console.log(`\n  📦 Total: ${(totalSize / 1024).toFixed(2)} KB\n`);
  return totalSize;
}

async function main() {
  console.log('🖼️  Image Optimization Tool (Sharp-based)\n');
  console.log('Configuration:');
  console.log(`  JPEG quality: ${QUALITY_JPEG}%`);
  console.log(`  PNG colors: ${QUALITY_PNG}`);
  console.log(`  Max width: ${MAX_WIDTH}px`);
  console.log(`  Check only: ${checkOnly}`);
  console.log(`  Resize: ${resize}`);
  console.log(`  WebP: ${convertWebp}\n`);

  let sizeBefore = 0;
  let sizeAfter = 0;

  if (checkOnly) {
    sizeBefore = await scanImages();
    console.log('Use without --check to optimize images\n');
  } else {
    console.log('🔄 Optimizing images...\n');

    for (const dir of DIRS_TO_OPTIMIZE) {
      const files = getDirectoryFiles(dir);
      if (files.length === 0) continue;

      console.log(`📁 ${dir}:`);
      for (const file of files) {
        const result = await optimizeImage(file);
        if (result) {
          sizeBefore += result.before;
          sizeAfter += result.after;
        }
      }
      console.log('');
    }

    if (sizeBefore > 0) {
      const saved = Math.round((1 - sizeAfter / sizeBefore) * 100);
      console.log('📊 OPTIMIZATION SUMMARY');
      console.log('═════════════════════════════════════');
      console.log(`Before:  ${(sizeBefore / 1024).toFixed(2)} KB`);
      console.log(`After:   ${(sizeAfter / 1024).toFixed(2)} KB`);
      console.log(`Saved:   ${saved}% (${((sizeBefore - sizeAfter) / 1024).toFixed(2)} KB)\n`);
    }

    console.log('✅ Optimization complete!');
  }
}

main().catch(err => {
  console.error('❌ Error:', err.message);
  process.exit(1);
});
