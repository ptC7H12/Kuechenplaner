#!/usr/bin/env python3
"""
Icon Generator für Freizeit Rezepturverwaltung
Erstellt Icons in verschiedenen Formaten (.ico, .png, .icns)
"""

import os
import sys
from pathlib import Path

# Try to import PIL, install if not available
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Pillow is not installed. Installing now...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    from PIL import Image, ImageDraw, ImageFont

def create_icon(size=256):
    """Create a simple but nice icon for the application"""

    # Create a new image with transparent background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw a gradient-like background (blue circle)
    margin = int(size * 0.05)
    circle_bbox = [margin, margin, size - margin, size - margin]

    # Main circle background (blue gradient simulation with multiple circles)
    for i in range(10):
        alpha = int(255 - (i * 20))
        offset = i * 3
        if margin + offset < size - margin - offset:  # Ensure valid coordinates
            color = (59 + min(i * 5, 60), 130 + min(i * 5, 60), 246, alpha)  # Blue gradient
            draw.ellipse(
                [margin + offset, margin + offset, size - margin - offset, size - margin - offset],
                fill=color
            )

    # Draw the main emoji/symbol
    # We'll use a simple geometric design representing food/cooking
    center = size // 2

    # Draw a cooking pot symbol
    pot_width = int(size * 0.5)
    pot_height = int(size * 0.4)
    pot_x = center - pot_width // 2
    pot_y = center - pot_height // 4

    # Pot body (trapezoid shape)
    pot_top_width = int(pot_width * 0.8)
    pot_points = [
        (center - pot_top_width // 2, pot_y),  # Top left
        (center + pot_top_width // 2, pot_y),  # Top right
        (center + pot_width // 2, pot_y + pot_height),  # Bottom right
        (center - pot_width // 2, pot_y + pot_height),  # Bottom left
    ]
    draw.polygon(pot_points, fill=(255, 255, 255, 255))

    # Pot handles
    handle_width = int(size * 0.08)
    handle_height = int(size * 0.15)
    # Left handle
    draw.arc(
        [pot_x - handle_width, pot_y + handle_height // 2, pot_x, pot_y + handle_height * 2],
        start=90, end=270, fill=(255, 255, 255, 255), width=int(size * 0.04)
    )
    # Right handle
    draw.arc(
        [pot_x + pot_width, pot_y + handle_height // 2, pot_x + pot_width + handle_width, pot_y + handle_height * 2],
        start=270, end=90, fill=(255, 255, 255, 255), width=int(size * 0.04)
    )

    # Steam lines above pot
    steam_y = pot_y - int(size * 0.15)
    steam_spacing = int(size * 0.08)
    for i in range(3):
        x = center - steam_spacing + (i * steam_spacing)
        draw.arc(
            [x - 10, steam_y, x + 10, steam_y + 30],
            start=0, end=180, fill=(255, 255, 255, 200), width=int(size * 0.02)
        )

    # Add a small spoon or utensil
    spoon_x = center + int(pot_width * 0.3)
    spoon_y = pot_y + int(pot_height * 0.3)
    spoon_length = int(size * 0.25)
    # Spoon handle
    draw.line(
        [(spoon_x, spoon_y), (spoon_x + spoon_length * 0.7, spoon_y - spoon_length * 0.7)],
        fill=(255, 255, 255, 255), width=int(size * 0.03)
    )
    # Spoon bowl
    draw.ellipse(
        [spoon_x - 12, spoon_y - 12, spoon_x + 12, spoon_y + 12],
        fill=(255, 255, 255, 255)
    )

    return img

def save_icons():
    """Save icons in different formats"""

    # Create static directory if it doesn't exist
    static_dir = Path(__file__).parent / "app" / "static"
    static_dir.mkdir(parents=True, exist_ok=True)

    print("Generating icons...")

    # Create main icon
    icon_256 = create_icon(256)

    # Save as PNG (for Linux)
    png_path = static_dir / "icon.png"
    icon_256.save(png_path, "PNG")
    print(f"✓ Created {png_path}")

    # Create multiple sizes for .ico (Windows)
    sizes = [16, 32, 48, 64, 128, 256]
    icons = [create_icon(size) for size in sizes]

    # Save as .ico
    ico_path = static_dir / "icon.ico"
    icons[0].save(
        ico_path,
        format='ICO',
        sizes=[(size, size) for size in sizes],
        append_images=icons[1:]
    )
    print(f"✓ Created {ico_path}")

    # For macOS .icns, we need to use a different approach
    # Save individual PNGs that can be converted to .icns using iconutil on macOS
    if os.name != 'nt':  # Not Windows
        try:
            # Create iconset directory
            iconset_dir = static_dir / "icon.iconset"
            iconset_dir.mkdir(exist_ok=True)

            # macOS icon sizes
            mac_sizes = {
                16: "16x16",
                32: "16x16@2x",
                32: "32x32",
                64: "32x32@2x",
                128: "128x128",
                256: "128x128@2x",
                256: "256x256",
                512: "256x256@2x",
                512: "512x512",
                1024: "512x512@2x"
            }

            for size, name in mac_sizes.items():
                icon = create_icon(size)
                icon.save(iconset_dir / f"icon_{name}.png", "PNG")

            print(f"✓ Created iconset at {iconset_dir}")
            print("  To create .icns on macOS, run:")
            print(f"  iconutil -c icns {iconset_dir}")

        except Exception as e:
            print(f"Note: macOS iconset creation requires macOS and iconutil: {e}")

    print("\n" + "=" * 50)
    print("✓ Icon generation complete!")
    print("=" * 50)

if __name__ == "__main__":
    save_icons()
