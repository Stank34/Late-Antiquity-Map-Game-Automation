import json
import os
from PIL import Image, ImageFilter
from pixel_font import PixelFontRenderer
from counter import get_civ_stats, calculate_civ_income

# --- CONFIGURATION ---
CANVAS_WIDTH = 1920
CANVAS_HEIGHT = 1080
DEFAULT_TEXT_COLOR = "#FFD800" 
OUTPUT_DIR = "board_outputs"

# Font Files
FONT_28_IMAGE = "board_font_28.png"
FONT_28_MAP = "board_font_28_map.json"

FONT_26_IMAGE = "board_font_26.png"
FONT_26_MAP = "board_font_26_map.json"

FONT_16_IMAGE = "board_font_16.png"
FONT_16_MAP = "board_font_16_map.json"
# Stats outline
OUTLINE_BOUNDS = (795, 376, 1142, 998)

PRIMARY_COORDS = {
    "Silver": (462, 129, "#FFFFFF", "left"),
    "Food": (780, 129, "#FFFFFF", "left"),
    "Gold": (1110, 129, "#FFFFFF", "left"),
    "Troops": (1370, 129, "#FFFFFF", "left"),
    "Sieges": (1635, 129, "#FFFFFF", "left"),
    "Ships": (1818, 129, "#FFFFFF", "left"),
    "Attack": (1654, 410, "#FF0000", "center"),
    "Defense": (1654, 473, "#0023F4", "center"),
    "Agriculture": (1654, 537, "#FD9400", "center"),
    "Economy": (1654, 599, "#02FF54", "center")
}

DELTA_KEYS = {
    "Food",
    "Silver",
    "Gold"
}

SECONDARY_COORDS = {
    "Troops_Recruited": (1017, 419),
    "Troops_Lost": (944, 459),
    "Battles_Won": (946, 499),
    "Battles_Lost": (944, 539),
    "Silver_Traded": (963, 579),
    "Food_Traded": (954, 619),
    "Gold_Traded": (952, 659),
    "Sieges_Traded": (958, 699),
    "Transport_Tradeds": (1033, 739),
    "Silver_Received": (991, 779),
    "Food_Received": (982, 819),
    "Gold_Recieved": (980, 859),
    "Sieges_Received": (986, 899),
    "Transports_Received": (1061, 939)
}

TERTIARY_COORDS = {
    "Attack": (1697, 396, "#FF0000"),
    "Defense": (1697, 462, "#0023F4"),
    "Agriculture": (1697, 521, "#FD9400"),
    "Economy": (1697, 586, "#02FF54")
}

def apply_bounded_outline(img, bbox):
    """
    Applies a 1-pixel solid black (#000000) outline to all colored pixels
    within the specified bounding box (including diagonal neighbors).
    """
    crop = img.crop(bbox)
    
    alpha = crop.split()[3]
    dilated_alpha = alpha.filter(ImageFilter.MaxFilter(3))
    
    black_fill = Image.new("RGBA", crop.size, (0, 0, 0, 255))
    outline_bg = Image.new("RGBA", crop.size, (0, 0, 0, 0))
    outline_bg.paste(black_fill, (0, 0), mask=dilated_alpha)
    
    composited_crop = Image.alpha_composite(outline_bg, crop)
    
    img.paste(composited_crop, bbox)

def generate_civ_stats_layer(target_civ, output_file):
    with open("civ_stats.json", "r", encoding="utf-8") as f:
        stats_data = json.load(f)

    civ_object = stats_data.get(target_civ)
    if not civ_object:
        print(f"Error: Civilization '{target_civ}' not found in civ_stats.json.")
        return
    counter_stats = get_civ_stats(target_civ)
    income_stats = calculate_civ_income(counter_stats, agriculture=civ_object.get("Agriculture", 0), economy=civ_object.get("Economy", 0)) 
    civ_object["Troops"] = counter_stats.get("troops")
    with open("civ_stats.json", "w", encoding="utf-8") as f:
        json.dump(stats_data, f, indent=4)

    layer = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 0))

    font_28 = PixelFontRenderer(FONT_28_IMAGE, map_path=FONT_28_MAP)
    font_26 = PixelFontRenderer(FONT_26_IMAGE, map_path=FONT_26_MAP)
    font_16 = PixelFontRenderer(FONT_16_IMAGE, map_path=FONT_16_MAP)

    # Convert primary keys to lower-case set for flexible matching
    primary_keys_lower = {k.lower() for k in PRIMARY_COORDS.keys()}

    for stat_key, stat_value in civ_object.items():
        text_to_draw = str(stat_value)
        key_lower = stat_key.lower()

        if key_lower in primary_keys_lower:
            # Case-insensitive lookup for primary coords
            matched_key = next(k for k in PRIMARY_COORDS if k.lower() == key_lower)
            x, y, color, align = PRIMARY_COORDS[matched_key]
            
            extra_w, extra_h = font_28.draw_text(
                layer, 
                text_str=text_to_draw, 
                x=x, 
                y=y, 
                color=color, 
                align=align  
            )
            x += extra_w + 10
            if matched_key in DELTA_KEYS:
                if income_stats.get(matched_key, 0) > 0:
                    text_to_draw_2 = (f"(+{income_stats.get(matched_key)})")
                    color = "#00FF21"
                else:
                    text_to_draw_2 = (f"({income_stats.get(matched_key)})")
                    color = "#FF0000"
                
                font_28.draw_text(
                    layer,
                    text_str=text_to_draw_2,
                    x=x,
                    y=y,
                    color=color,
                    align="left"
                )
        else:
            x, y = SECONDARY_COORDS.get(stat_key, (0, 0))
            
            font_26.draw_text(
                layer, 
                text_str=text_to_draw, 
                x=x, 
                y=y, 
                color=DEFAULT_TEXT_COLOR, 
                align="left"
            )
    techs = ["Attack", "Defense", "Agriculture", "Economy"]
    for tech in techs:
        text_to_draw = civ_object.get(tech, 0)
        if tech == "Agriculture":
            text_to_draw *= 10
        elif tech == "Economy":
            text_to_draw *= 7
        x, y, color = TERTIARY_COORDS.get(tech)

        font_16.draw_text(
            layer,
            text_str=text_to_draw,
            x=x,
            y=y,
            color=color,
            align="left"
        )

    apply_bounded_outline(layer, OUTLINE_BOUNDS)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    full_output_path = os.path.join(OUTPUT_DIR, output_file)

    layer.save(full_output_path)
    print(f"Stats layer successfully rendered for '{target_civ}' -> {output_file}")

if __name__ == "__main__":
    generate_civ_stats_layer("Rome", "rome_board_changable.png")
    generate_civ_stats_layer("Persia", "persia_board_changable.png")
    generate_civ_stats_layer("Vandals", "vandals_board_changable.png")
    generate_civ_stats_layer("Visigoths", "visigoths_board_changable.png")
    generate_civ_stats_layer("Suebi", "suebi_board_changable.png")
    generate_civ_stats_layer("Franks", "franks_board_changable.png")
    generate_civ_stats_layer("Saxons", "saxons_board_changable.png")
    generate_civ_stats_layer("Arabs", "arabs_board_changable.png")
    generate_civ_stats_layer("Ostrogoths", "ostrogoths_board_changable.png")
    generate_civ_stats_layer("Lombards", "lombards_board_changable.png")