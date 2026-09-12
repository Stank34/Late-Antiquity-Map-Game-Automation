import json
from PIL import Image, ImageDraw

PLAYER_COLORS = {
    "RomeW": "#A80048",
    "Rome": "#7F0037",
    "Persia": "#FF6A00",
    "Franks": "#00137F",
    "Suebi": "#B5009C",
    "Visigoths": "#B2CC41",
    "Ostrogoths": "#0094B6",
    "Saxons": "#FF8C77",
    "Vandals": "#FF3A00",
    "Lombards": "#777092",
    "ArabAI": "#4BBC4B",
    "Arabs": "#004000",
    "AI": "#AFAFAF",
    "Gepids": "#7F3300",
    "Slavs": "#75A0C9",
    "Avars": "#A3B2AC"
}

def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

def repaint_map():
    with open('topology.json', 'r', encoding='utf-8') as f:
        topology = json.load(f)
    with open('gamestate.json', 'r', encoding='utf-8') as f:
        gamestate = json.load(f)

    base_map = Image.open('base_layer.png').convert("RGB")
    width, height = base_map.size
    for prov_id, data in topology.items():
        p_id = str(prov_id)
        state = gamestate.get(p_id, {})
        owner = state.get("owner", "None")

        if owner in PLAYER_COLORS:
            fill_color = hex_to_rgb(PLAYER_COLORS[owner])
            seed_x, seed_y = int(data['x']), int(data['y'])
            ImageDraw.floodfill(base_map, (seed_x, seed_y), fill_color, thresh=0)


    # --- Generate Troop Text Layer ---
    text_layer = create_pixelated_text_layer(width, height, topology, gamestate)
    
    # Save standalone layer (Ready to import as a Paint.NET / PDN layer)
    text_layer.save("troop_text_layer.png")
    print("Saved standalone layer -> troop_text_layer.png")

    base_map.save("base_layer.png")
    print("Map repaint complete -> base_layer.png")

def create_pixelated_text_layer(width, height, topology, gamestate):
    # 1. Create a single transparent RGBA canvas
    text_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    
    # 2. Initialize your sprite font renderer
    pixel_font = PixelFontRenderer("troop_font_medium.png", char_width=6, char_height=9)

    # 3. Draw troop counts onto the canvas
    for prov_id, data in topology.items():
        p_id = str(prov_id)
        state = gamestate.get(p_id, {})
        troops = state.get("troops", 0)

        # Get coordinates
        tx = int(data.get("text_x", data["x"]))
        ty = int(data.get("text_y", data["y"]))

        # Draw character sprites directly onto text_layer
        pixel_font.draw_number(text_layer, str(troops), tx, ty)

    return text_layer

class PixelFontRenderer:
    def __init__(self, template_path, char_width=6, char_height=9):
        self.char_width = char_width
        self.char_height = char_height
        
        # Load your pixelated font template (assumes digits 0-9 arranged left to right)
        template = Image.open(template_path).convert("RGBA")
        
        # Slice the template into individual digit sprites
        self.digits = {}
        for i in range(10):
            left = i * char_width
            box = (left, 0, left + char_width, char_height)
            self.digits[str(i)] = template.crop(box)

    def draw_number(self, target_img, number_str, center_x, center_y):
        # Calculate total width of the rendered number to center it over (x, y)
        total_width = len(number_str) * self.char_width
        start_x = center_x - (total_width // 2)
        start_y = center_y - (self.char_height // 2)

        # Paste each character sprite onto the layer
        for i, char in enumerate(number_str):
            if char in self.digits:
                sprite = self.digits[char]
                px = start_x + (i * self.char_width)
                target_img.paste(sprite, (px, start_y), mask=sprite)

if __name__ == "__main__":
    repaint_map()