#!/usr/bin/env python3
"""
E-Paper Display Grayscale Tester
Generates test images for different bit depths and dithering settings
"""

import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from wand.image import Image as WandImage
from wand.drawing import Drawing
from wand.color import Color
import tempfile

class EPDTester:
    def __init__(self):
        self.width = int(os.getenv('DISPLAY_WIDTH', 1404))
        self.height = int(os.getenv('DISPLAY_HEIGHT', 1872))
        self.dpi = int(os.getenv('DISPLAY_DPI', 226))
        self.font_size = int(os.getenv('FONT_SIZE', 10))
        
        # Calculate section height (4 equal sections)
        self.section_height = self.height // 4
        
        # Test text
        self.test_text = "The quick brown fox jumps over the lazy dog"
        
        # Bit depths to simulate
        self.bit_depths = [1, 2, 3, 4]  # 4-bit is native
        
    def quantize_to_bits(self, image, bits):
        """Quantize image to specified bit depth"""
        levels = 2 ** bits
        arr = np.array(image)
        
        # Quantize to exact levels (even for 4-bit to ensure clean blocks)
        # Scale to 0-1, quantize, then scale back
        normalized = arr / 255.0
        quantized = np.round(normalized * (levels - 1)) / (levels - 1)
        result = (quantized * 255).astype(np.uint8)
        
        return Image.fromarray(result, mode='L')
    
    def apply_dithering(self, image, target_bits, method='floyd-steinberg'):
        """Apply dithering using ImageMagick then ensure proper scaling"""
        levels = 2 ** target_bits
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_in:
            image.save(tmp_in.name)
            
            with WandImage(filename=tmp_in.name) as wand_img:
                wand_img.type = 'grayscale'
                if method == 'floyd-steinberg':
                    wand_img.dither = True
                    wand_img.quantize(levels, 'gray', 0, True, False)
                    # Ensure the result uses full 0-255 range
                    wand_img.normalize()
                
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_out:
                    wand_img.save(filename=tmp_out.name)
                    result = Image.open(tmp_out.name).convert('L')
                    
                    # Ensure the result spans 0-255 by remapping
                    arr = np.array(result)
                    if arr.max() > arr.min():
                        # Remap to 0-255 range preserving the quantized levels
                        unique_vals = np.unique(arr)
                        if len(unique_vals) == levels:
                            # Map unique values to proper quantized levels
                            for i, val in enumerate(sorted(unique_vals)):
                                target_val = int(255 * i / (levels - 1))
                                arr[arr == val] = target_val
                            result = Image.fromarray(arr.astype(np.uint8), mode='L')
                    
                    os.unlink(tmp_out.name)
            
            os.unlink(tmp_in.name)
            return result
    
    def create_grayscale_strip(self, width, height, mode="16_blocks", dithered=False, target_bits=4):
        """Create grayscale strip based on mode
        
        Args:
            mode: "native" (show target colorspace levels), "16_blocks" (16 levels), "gradient" (smooth)
            dithered: apply dithering when converting to target colorspace
            target_bits: target bit depth
        """
        strip = Image.new('L', (width, height), 255)
        draw = ImageDraw.Draw(strip)
        
        if mode == "native":
            # Show the actual levels available in the target colorspace
            levels = 2 ** target_bits
            block_width = width // levels
            for i in range(levels):
                gray_value = int(255 * (1 - i / (levels - 1)))
                x1 = i * block_width
                x2 = (i + 1) * block_width if i < levels - 1 else width
                draw.rectangle([x1, 0, x2-1, height-1], fill=gray_value)
            # No dithering - these are the native levels
            return self.quantize_to_bits(strip, target_bits)
            
        elif mode == "gradient":
            # Create smooth gradient from white (255) to black (0)
            for x in range(width):
                # Ensure we go from 255 at x=0 to 0 at x=width-1
                progress = x / (width - 1) if width > 1 else 0
                gray_value = int(255 * (1 - progress))
                draw.line([(x, 0), (x, height-1)], fill=gray_value)
        else:  # "16_blocks"
            # Create 16 distinct blocks (full 4-bit grayscale)
            block_width = width // 16
            for i in range(16):
                gray_value = int(255 * (1 - i / 15))
                x1 = i * block_width
                x2 = (i + 1) * block_width if i < 15 else width
                draw.rectangle([x1, 0, x2-1, height-1], fill=gray_value)
        
        # Apply processing based on whether we want dithering
        if target_bits < 4 and dithered:
            # Use ImageMagick dithering (includes quantization)
            strip = self.apply_dithering(strip, target_bits)
        elif target_bits < 4:
            # Use our quantization (no dithering)
            strip = self.quantize_to_bits(strip, target_bits)
        elif mode == "gradient" and target_bits == 4:
            # For 4-bit gradients, keep them smooth (no quantization)
            pass
        else:
            # For 4-bit blocks, quantize to show distinct levels
            strip = self.quantize_to_bits(strip, target_bits)
        
        return strip
    
    def create_text_sample(self, width, height, antialiased=False, dithered=False, target_bits=4):
        """Create text sample with specified settings, then simulate target bit depth"""
        # Create high-res image for better font rendering
        scale = 4 if antialiased else 1
        img = Image.new('L', (width * scale, height * scale), 255)
        draw = ImageDraw.Draw(img)
        
        try:
            # Try to load Liberation Serif font (similar to Times/Garamond)
            font_size_scaled = self.font_size * scale
            font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf", font_size_scaled)
        except:
            # Fallback to default font
            font = ImageFont.load_default()
        
        # Calculate text position (centered)
        bbox = draw.textbbox((0, 0), self.test_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (width * scale - text_width) // 2
        y = (height * scale - text_height) // 2
        
        # Draw text (always render with full grayscale range first)
        draw.text((x, y), self.test_text, fill=0, font=font)
        
        # Scale down if antialiased
        if antialiased:
            img = img.resize((width, height), Image.LANCZOS)
        
        # Now simulate how this looks on target bit depth display
        if target_bits < 4 and dithered:
            img = self.apply_dithering(img, target_bits)
        
        # Always quantize to show effect on target bit depth
        img = self.quantize_to_bits(img, target_bits)
        
        return img
    
    def create_section(self, bit_depth):
        """Create one complete section for a specific bit depth"""
        section = Image.new('L', (self.width, self.section_height), 255)
        
        # Calculate component heights - now 3 strips + 3 text samples
        strip_height = self.section_height // 10  # 3 strips
        text_height = self.section_height // 10   # 3 text samples
        spacing = (self.section_height - 3 * strip_height - 3 * text_height) // 7
        
        current_y = spacing
        
        # 1. Native colorspace levels (no dithering)
        strip1 = self.create_grayscale_strip(self.width, strip_height, mode="native", 
                                           dithered=False, target_bits=bit_depth)
        section.paste(strip1, (0, current_y))
        current_y += strip_height + spacing
        
        # 2. 16-level blocks dithered to colorspace
        strip2 = self.create_grayscale_strip(self.width, strip_height, mode="16_blocks", 
                                           dithered=(bit_depth < 4), target_bits=bit_depth)
        section.paste(strip2, (0, current_y))
        current_y += strip_height + spacing
        
        # 3. Smooth gradient dithered to colorspace
        strip3 = self.create_grayscale_strip(self.width, strip_height, mode="gradient", 
                                           dithered=(bit_depth < 4), target_bits=bit_depth)
        section.paste(strip3, (0, current_y))
        current_y += strip_height + spacing
        
        # 4. Text - no AA, no dithering
        text1 = self.create_text_sample(self.width, text_height, antialiased=False, 
                                       dithered=False, target_bits=bit_depth)
        section.paste(text1, (0, current_y))
        current_y += text_height + spacing
        
        # 5. Text - no AA, with dithering (if not native)
        text2 = self.create_text_sample(self.width, text_height, antialiased=False, 
                                       dithered=(bit_depth < 4), target_bits=bit_depth)
        section.paste(text2, (0, current_y))
        current_y += text_height + spacing
        
        # 6. Text - AA, no dithering
        text3 = self.create_text_sample(self.width, text_height, antialiased=True, 
                                       dithered=False, target_bits=bit_depth)
        section.paste(text3, (0, current_y))
        
        return section
    
    def generate_test_image(self):
        """Generate the complete test image"""
        print(f"Generating test image: {self.width}x{self.height} @ {self.dpi}dpi")
        
        # Create the main image
        test_image = Image.new('L', (self.width, self.height), 255)
        
        # Generate each section
        for i, bit_depth in enumerate(self.bit_depths):
            print(f"Creating {bit_depth}-bit section...")
            section = self.create_section(bit_depth)
            y_offset = i * self.section_height
            test_image.paste(section, (0, y_offset))
            
            # Add section label
            draw = ImageDraw.Draw(test_image)
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf", 20)
            except:
                font = ImageFont.load_default()
            
            label = f"{bit_depth}-bit grayscale"
            draw.text((10, y_offset + 10), label, fill=0, font=font)
        
        # Save the image
        output_path = "/app/output/epd_grayscale_test.png"
        test_image.save(output_path, dpi=(self.dpi, self.dpi))
        print(f"Test image saved to: {output_path}")
        
        return test_image

def main():
    tester = EPDTester()
    tester.generate_test_image()

if __name__ == "__main__":
    main()