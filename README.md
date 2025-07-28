# E-Paper Display Grayscale Tester

A Python application to generate test images for e-paper displays, specifically targeting the reMarkable 2 tablet. Tests different bit depths (1-bit, 2-bit, 3-bit, 4-bit) with various dithering and anti-aliasing options.

## Features

- Generates 4 equal-height sections, each simulating a different colorspace
- Each section includes:
  - 16-color grayscale strip (solid blocks, no dithering)
  - 16-color grayscale strip (gradient with dithering)
  - Text samples with different AA/dithering combinations
- Configurable display dimensions, DPI, and font size via environment variables
- Uses EB Garamond font for text rendering
- Docker containerized for consistent results

## Usage

### Using Docker Compose (Recommended)

```bash
# Build and run with default settings (reMarkable 2)
docker-compose up --build

# Run with custom settings
DISPLAY_WIDTH=1200 DISPLAY_HEIGHT=1600 DISPLAY_DPI=200 FONT_SIZE=12 docker-compose up --build
```

### Environment Variables

- `DISPLAY_WIDTH`: Display width in pixels (default: 1404)
- `DISPLAY_HEIGHT`: Display height in pixels (default: 1872)
- `DISPLAY_DPI`: Display DPI (default: 226)
- `FONT_SIZE`: Font size in points (default: 10) - automatically converted to pixels based on DPI

### Output

The generated test image will be saved to `./output/epd_grayscale_test.png`

## Technical Details

- **1-bit section**: Pure black/white with dithering for gradients
- **2-bit section**: 4 gray levels with dithering
- **3-bit section**: 8 gray levels with dithering  
- **4-bit section**: 16 gray levels (native, no dithering needed)

Each section demonstrates how content appears when rendered at different bit depths, helping optimize content for e-paper displays.