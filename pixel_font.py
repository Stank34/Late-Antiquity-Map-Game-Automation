# pixel_font.py
import json
from PIL import Image

class PixelFontRenderer:
    """Proportional pixel font renderer supporting digits, letters, and symbols with custom colors."""
    
    def __init__(self, template_path, map_path=None, char_sequence=None, spacing=1, space_width=3):
        self.spacing = spacing
        self.space_width = space_width
        self.glyphs = {}

        template = Image.open(template_path).convert("RGBA")

        if map_path:
            # --- Method A: Load from JSON metadata ---
            with open(map_path, 'r', encoding='utf-8') as f:
                font_data = json.load(f)

            self.spacing = font_data.get("spacing", self.spacing)
            self.space_width = font_data.get("space_width", self.space_width)
            default_h = font_data.get("default_height", template.height)

            for char, bbox in font_data.get("glyphs", {}).items():
                if len(bbox) == 2:  # Single row: [x, width]
                    x, w = bbox
                    y, h = 0, default_h
                elif len(bbox) == 4:  # Multi-row: [x, y, width, height]
                    x, y, w, h = bbox

                sprite = template.crop((x, y, x + w, y + h))
                self.glyphs[char] = {"sprite": sprite, "width": w, "height": h}

        elif char_sequence:
            # --- Method B: Auto-slice based on transparent column gaps ---
            self._auto_slice_template(template, char_sequence)

    def _auto_slice_template(self, template, char_sequence):
        """Scans the image left-to-right and slices glyphs wherever transparent column gaps occur."""
        width, height = template.size
        char_idx = 0
        in_glyph = False
        start_x = 0

        # Scan alpha values across image columns
        alpha_data = template.split()[-1]

        for x in range(width):
            col_has_pixel = any(alpha_data.getpixel((x, y)) > 0 for y in range(height))

            if col_has_pixel and not in_glyph:
                in_glyph = True
                start_x = x
            elif not col_has_pixel and in_glyph:
                in_glyph = False
                w = x - start_x
                if char_idx < len(char_sequence):
                    char = char_sequence[char_idx]
                    sprite = template.crop((start_x, 0, x, height))
                    self.glyphs[char] = {"sprite": sprite, "width": w, "height": height}
                    char_idx += 1

    @staticmethod
    def _hex_to_rgba(hex_str):
        """Converts '#RRGGBB' string to an (R, G, B, 255) tuple."""
        hex_str = hex_str.lstrip('#')
        rgb = tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))
        return rgb + (255,)

    def measure_text(self, text_str):
        """Calculates total pixel width and max height of a formatted string."""
        total_width = 0
        max_height = 0

        chars = list(str(text_str))
        for i, char in enumerate(chars):
            if char in self.glyphs:
                w = self.glyphs[char]["width"]
                h = self.glyphs[char]["height"]
            elif char == ' ':
                w = self.space_width
                h = max_height or 1
            else:
                continue

            total_width += w
            if i < len(chars) - 1:
                total_width += self.spacing
            if h > max_height:
                max_height = h

        return total_width, max_height

    def draw_text(self, target_img, text_str, x, y, color="#000000", align="center"):
        """
        Renders variable-width text onto target_img at (x, y).
        align options: 'center', 'left', 'right'
        """
        text_str = str(text_str)
        total_w, total_h = self.measure_text(text_str)

        if align == "center":
            start_x = x - (total_w // 2)
            start_y = y - (total_h // 2)
        elif align == "left":
            start_x = x
            start_y = y - (total_h // 2)
        elif align == "right":
            start_x = x - total_w
            start_y = y - (total_h // 2)

        fill_color = self._hex_to_rgba(color) if isinstance(color, str) else color
        curr_x = start_x

        for char in text_str:
            if char == ' ':
                curr_x += self.space_width + self.spacing
                continue

            if char in self.glyphs:
                glyph = self.glyphs[char]
                sprite = glyph["sprite"]
                w = glyph["width"]

                target_img.paste(fill_color, (curr_x, start_y), mask=sprite)
                curr_x += w + self.spacing
        return total_w, total_h