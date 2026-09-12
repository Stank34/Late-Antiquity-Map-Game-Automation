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

    for prov_id, data in topology.items():
        p_id = str(prov_id)
        state = gamestate.get(p_id, {})
        owner = state.get("owner", "None")

        if owner in PLAYER_COLORS:
            fill_color = hex_to_rgb(PLAYER_COLORS[owner])
            seed_x, seed_y = int(data['x']), int(data['y'])
            ImageDraw.floodfill(base_map, (seed_x, seed_y), fill_color, thresh=0)

    base_map.save("base_layer.png")
    print("Map repaint complete -> base_layer.png")

if __name__ == "__main__":
    repaint_map()