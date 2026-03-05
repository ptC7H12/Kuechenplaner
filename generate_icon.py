#!/usr/bin/env python3
"""
Icon Generator für Freizeit Rezepturverwaltung
Erstellt Icons in verschiedenen Formaten (.ico, .png, .icns)
Minimalistisches, modernes Design: Kochtopf mit Dampf auf rundem Hintergrund
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
    """Create a modern, minimalistic kitchen icon"""

    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    s = size / 256  # Scale factor

    # Rounded square background with indigo gradient
    margin = int(12 * s)
    radius = int(48 * s)
    bg_rect = [margin, margin, size - margin, size - margin]

    # Draw rounded rectangle background layers for gradient effect
    # Dark indigo base
    draw.rounded_rectangle(bg_rect, radius=radius, fill=(67, 56, 202, 255))
    # Lighter overlay at top for gradient
    overlay_rect = [margin, margin, size - margin, int(size * 0.55)]
    draw.rounded_rectangle(overlay_rect, radius=radius, fill=(99, 102, 241, 255))
    # Mid section blend
    mid_rect = [margin, int(size * 0.35), size - margin, int(size * 0.55)]
    draw.rectangle(mid_rect, fill=(79, 70, 229, 255))

    cx = size // 2  # Center x

    # === POT LID (flat bar on top) ===
    lid_y = int(88 * s)
    lid_w = int(90 * s)
    lid_h = int(8 * s)
    draw.rounded_rectangle(
        [cx - lid_w // 2, lid_y, cx + lid_w // 2, lid_y + lid_h],
        radius=int(4 * s),
        fill=(255, 255, 255, 255)
    )

    # Lid knob (small rectangle on top center)
    knob_w = int(20 * s)
    knob_h = int(6 * s)
    knob_y = lid_y - knob_h - int(2 * s)
    draw.rounded_rectangle(
        [cx - knob_w // 2, knob_y, cx + knob_w // 2, knob_y + knob_h],
        radius=int(3 * s),
        fill=(255, 255, 255, 240)
    )

    # === POT BODY ===
    pot_top = lid_y + lid_h
    pot_bottom = int(185 * s)
    pot_left = int(60 * s)
    pot_right = int(196 * s)
    pot_radius = int(16 * s)

    draw.rounded_rectangle(
        [pot_left, pot_top, pot_right, pot_bottom],
        radius=pot_radius,
        fill=(255, 255, 255, 255)
    )

    # === HANDLES ===
    handle_w = int(12 * s)
    handle_h = int(28 * s)
    handle_y = pot_top + int(20 * s)
    handle_thickness = max(int(5 * s), 2)

    # Left handle
    draw.arc(
        [pot_left - handle_w - int(4 * s), handle_y,
         pot_left + int(2 * s), handle_y + handle_h],
        start=90, end=270,
        fill=(255, 255, 255, 255),
        width=handle_thickness
    )
    # Right handle
    draw.arc(
        [pot_right - int(2 * s), handle_y,
         pot_right + handle_w + int(4 * s), handle_y + handle_h],
        start=270, end=90,
        fill=(255, 255, 255, 255),
        width=handle_thickness
    )

    # === STEAM LINES (three elegant curved lines) ===
    steam_base_y = knob_y - int(6 * s)
    steam_color = (255, 255, 255, 180)
    steam_w = max(int(3 * s), 1)

    offsets = [-int(22 * s), 0, int(22 * s)]
    heights = [int(24 * s), int(30 * s), int(24 * s)]

    for i, (ox, h) in enumerate(zip(offsets, heights)):
        x = cx + ox
        y_top = steam_base_y - h
        curve = int(6 * s)

        # S-curve steam
        draw.arc(
            [x - curve, y_top, x + curve, y_top + h // 2],
            start=180, end=0,
            fill=steam_color,
            width=steam_w
        )
        draw.arc(
            [x - curve, y_top + h // 2 - int(2 * s), x + curve, steam_base_y],
            start=0, end=180,
            fill=steam_color,
            width=steam_w
        )

    # === ACCENT: small colored dots on pot (food items peeking out) ===
    dot_y = pot_top + int(18 * s)
    dot_r = int(5 * s)

    # Orange dot
    draw.ellipse(
        [cx - int(20 * s) - dot_r, dot_y - dot_r,
         cx - int(20 * s) + dot_r, dot_y + dot_r],
        fill=(251, 191, 36, 220)
    )
    # Red dot
    draw.ellipse(
        [cx - dot_r, dot_y - dot_r + int(2 * s),
         cx + dot_r, dot_y + dot_r + int(2 * s)],
        fill=(248, 113, 113, 220)
    )
    # Green dot
    draw.ellipse(
        [cx + int(20 * s) - dot_r, dot_y - dot_r,
         cx + int(20 * s) + dot_r, dot_y + dot_r],
        fill=(52, 211, 153, 220)
    )

    # === BOTTOM TEXT AREA: Recipe lines (abstract text lines) ===
    line_y = pot_bottom + int(14 * s)
    line_h = max(int(3 * s), 1)
    line_color = (255, 255, 255, 120)

    draw.rounded_rectangle(
        [int(75 * s), line_y, int(181 * s), line_y + line_h],
        radius=max(int(1.5 * s), 1),
        fill=line_color
    )
    line_y += int(8 * s)
    draw.rounded_rectangle(
        [int(85 * s), line_y, int(171 * s), line_y + line_h],
        radius=max(int(1.5 * s), 1),
        fill=line_color
    )
    line_y += int(8 * s)
    draw.rounded_rectangle(
        [int(95 * s), line_y, int(161 * s), line_y + line_h],
        radius=max(int(1.5 * s), 1),
        fill=line_color
    )

    return img


def save_icons():
    """Save icons in different formats"""

    static_dir = Path(__file__).parent / "app" / "static"
    static_dir.mkdir(parents=True, exist_ok=True)

    print("Generating icons...")

    # Create main icon
    icon_256 = create_icon(256)

    # Save as PNG (for Linux)
    png_path = static_dir / "icon.png"
    icon_256.save(png_path, "PNG")
    print(f"  Created {png_path}")

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
    print(f"  Created {ico_path}")

    # For macOS .icns: save individual PNGs for iconutil
    if os.name != 'nt':
        try:
            iconset_dir = static_dir / "icon.iconset"
            iconset_dir.mkdir(exist_ok=True)

            mac_sizes = [
                (16, "16x16"),
                (32, "16x16@2x"),
                (32, "32x32"),
                (64, "32x32@2x"),
                (128, "128x128"),
                (256, "128x128@2x"),
                (256, "256x256"),
                (512, "256x256@2x"),
                (512, "512x512"),
                (1024, "512x512@2x"),
            ]

            for icon_size, name in mac_sizes:
                icon = create_icon(icon_size)
                icon.save(iconset_dir / f"icon_{name}.png", "PNG")

            print(f"  Created iconset at {iconset_dir}")
            print("  To create .icns on macOS, run:")
            print(f"  iconutil -c icns {iconset_dir}")

        except Exception as e:
            print(f"Note: macOS iconset creation requires macOS and iconutil: {e}")

    print("\n" + "=" * 50)
    print("Icon generation complete!")
    print("=" * 50)

if __name__ == "__main__":
    save_icons()
