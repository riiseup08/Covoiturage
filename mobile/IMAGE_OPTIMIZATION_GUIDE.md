# Image Optimization Guide for Mobile APK

## Overview

This guide explains how to optimize images for the Covoiturage mobile app to reduce APK size and improve performance on low-bandwidth African networks.

## Why Optimize?

- **APK Size**: Uncompressed images can bloat APK from 50MB to 150MB+
- **Download Time**: Users on 3G/4G in Cameroon can wait 10+ minutes for large downloads
- **Battery**: Smaller app = faster installation = less battery drain
- **Storage**: Many African devices have limited storage space

## Quick Setup

```bash
cd mobile/
npm install --save-dev imagemin imagemin-mozjpeg imagemin-pngquant imagemin-webp sharp
```

Then run optimization:

```bash
# Check what can be optimized (no changes)
node scripts/optimize-images.js --check

# Optimize images
node scripts/optimize-images.js

# Resize + convert to WebP
node scripts/optimize-images.js --resize --webp
```

## Size Targets

| Image Type | Max Size | Max Width | Format |
|----------|----------|-----------|--------|
| Profile photos | 150KB | 400px | JPEG (75% quality) |
| Trip photos | 200KB | 800px | JPEG (75% quality) |
| Icons/UI | 50KB | 200px | PNG |
| Backgrounds | 100KB | 1920px | JPEG or WebP |

## Best Practices

### 1. Use Right Format

```bash
# Photos/Avatars → JPEG (75% quality)
convert photo.png -quality 75 photo.jpg  # 500KB → 80KB

# Icons/Graphics → PNG (with transparency)
# Use 8-bit PNG when possible

# Modern apps → WebP (better compression)
# JPEG: 80KB → WebP: 40KB
```

### 2. Image Sizes

**Profile Photos** (user avatars):
- Target: 200x200px @ 100KB max
- Show thumbnail (100x100px) in lists
- Show full-size (400x400px) in detail view

**Trip Photos** (car photos):
- Target: 800x600px @ 150KB max
- Compress to 80% quality

**Logo/UI Assets**:
- Target: 200x200px @ 30KB max
- Use PNG for transparency

### 3. React Native Specific Tips

```javascript
// In Images, specify size explicitly
<Image 
  source={require('./profile.jpg')}
  style={{ width: 100, height: 100 }}
  resizeMethod="scale"
  resizeMode="cover"
/>

// Lazy load large images
<Image
  source={{ uri: 'https://cdn.example.com/photo.jpg', cache: 'force-cache' }}
  style={{ width: 200, height: 200 }}
/>

// Use cached network images
const CachedImage = (props) => (
  <FastImage
    {...props}
    cache={FastImage.cacheControl.immutable}
  />
);
```

### 4. Using the Optimization Script

```bash
# Before building APK:
node scripts/optimize-images.js

# Check results:
node scripts/optimize-images.js --check

# Output example:
# 📊 SCAN SUMMARY
# Total image data: 12.45MB
# Oversized images: 3
#   ⚠️  car_photo.jpg (2.5MB, 4000x3000)
#   ⚠️  profile_banner.png (1.8MB, 2560x1440)
#   ⚠️  background.jpg (750KB, 3840x2160)
```

### 5. Network Image Optimization

For images loaded from server:

```bash
# Resize on backend before sending
# Provide multiple sizes via srcset (web) or URL parameters

# URL pattern: /api/images/{id}?size=thumbnail|medium|full
# thumbnail: 100x100px (10-15KB)
# medium: 400x400px (40-80KB)
# full: 800x800px (100-200KB)
```

## APK Optimization Steps

Before building APK:

```bash
# Step 1: Optimize all static images
node scripts/optimize-images.js --resize --webp

# Step 2: Check sizes
node scripts/optimize-images.js --check

# Step 3: Enable ProGuard/R8 (in android/app/build.gradle)
# minifyEnabled true
# shrinkResources true

# Step 4: Build APK (use release build)
cd android/
./gradlew assembleRelease

# Step 5: Check APK size
# Expected: 40-60MB (optimized) vs 100-150MB (unoptimized)
```

## Expected Results

| Metric | Before | After | Savings |
|--------|--------|-------|---------|
| Static images | 25MB | 3MB | 88% |
| APK size | 120MB | 45MB | 62% |
| Install time (3G) | 8 min | 3 min | 63% |
| App size on device | 260MB | 100MB | 62% |

## Recommended Dimensions

```
Profile Avatar:
  Thumbnail: 100x100 (5-8KB)
  Detail: 400x400 (40-60KB)

Trip/Car Photo:
  List thumbnail: 150x150 (8-12KB)
  Detail view: 600x450 (60-100KB)
  Full-screen: 1080x810 (120-180KB)

UI Icons:
  All sizes: 24x24 to 192x192 (2-15KB each)

Backgrounds:
  Mobile: 720x1280 (60-100KB)
  Tablet: 1920x2560 (150-200KB)
```

## Useful Commands

```bash
# Get image info
identify -verbose photo.jpg

# Convert to WebP
cwebp photo.jpg -o photo.webp -q 75

# Batch compress JPEGs
for f in *.jpg; do
  convert "$f" -quality 75 "$f"
done

# Find large images
find . -name "*.jpg" -o -name "*.png" | xargs ls -lh | awk '$5 > "500K" {print}'
```

## Monitoring Performance

After optimization, monitor:

```javascript
// In app code
import * as FileSystem from 'expo-file-system';

async function checkAppSize() {
  const info = await FileSystem.getInfoAsync(FileSystem.documentDirectory);
  console.log('App data size:', (info.size / 1024 / 1024).toFixed(2), 'MB');
}
```

## Further Reading

- [React Native Image Optimization](https://reactnative.dev/docs/images)
- [Expo Asset Optimization](https://docs.expo.dev/guides/optimizing-assets/)
- [ImageMin Documentation](https://github.com/imagemin/imagemin)
- [WebP Format Guide](https://developers.google.com/speed/webp)

---

**Question**: Should we enable automatic image optimization in CI/CD?
**Recommendation**: Yes, add to GitHub Actions to automatically optimize images on each commit.
