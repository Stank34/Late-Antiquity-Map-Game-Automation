import json
import matplotlib.pyplot as plt

def draw_topology_map(json_filepath, output_image_path):
    # 1. Load the topology data
    with open(json_filepath, 'r', encoding='utf-8') as f:
        topology = json.load(f)

    # 2. Set up the canvas
    # figsize controls the width/height of the output image in inches
    fig, ax = plt.subplots(figsize=(16, 12)) 
    
    # We use a set to keep track of drawn lines so we don't draw
    # a line from 1 -> 2 and then redraw it from 2 -> 1
    drawn_connections = set()

    # 3. Iterate through the dictionary to draw the map
    for prov_id, data in topology.items():
        # Ensure coordinates are treated as integers
        try:
            x1 = int(data['x'])
            y1 = int(data['y'])
        except (ValueError, TypeError):
            continue # Skip territories with missing or broken coordinates

        # --- STEP A: Draw the connections (Thin Black Lines) ---
        for neighbor_id in data['neighbors']:
            if neighbor_id in topology:
                # Create a sorted tuple so (1,2) and (2,1) are treated as the same connection
                connection = tuple(sorted([prov_id, neighbor_id]))
                
                if connection not in drawn_connections:
                    try:
                        x2 = int(topology[neighbor_id]['x'])
                        y2 = int(topology[neighbor_id]['y'])
                        
                        # Plot the line between (x1, y1) and (x2, y2)
                        # zorder=1 ensures lines are drawn UNDER the nodes
                        ax.plot([x1, x2], [y1, y2], color='black', linewidth=0.5, zorder=1)
                        drawn_connections.add(connection)
                    except (ValueError, TypeError):
                        pass

        # --- STEP B: Draw the province centers (Red/Blue Nodes) ---
        # Blue if coastal, Red if not coastal
        node_color = 'blue' if data['coastal'] else 'red'
        
        # s=15 controls the size of the dot. zorder=2 ensures dots sit ON TOP of lines.
        ax.scatter(x1, y1, color=node_color, s=15, zorder=2)
        
        # Optional: Uncomment the next line if you want to see the ID numbers printed on the map
        ax.text(x1, y1 - 4, prov_id, fontsize=5, ha='center', color='black', zorder=3)

    # 4. Format the final image
    # IMPORTANT: Image coordinates usually have Y=0 at the top and increase going down. 
    # Matplotlib has Y=0 at the bottom. We must invert the Y-axis so your map isn't upside down!
    ax.invert_yaxis() 
    
    # 'equal' forces the X and Y axes to have the same scale so the map doesn't look stretched
    ax.set_aspect('equal') 
    
    # Hide the graph axis borders and numbers for a clean look
    plt.axis('off') 

    # 5. Save and display
    plt.savefig(output_image_path, dpi=300, bbox_inches='tight')
    print(f"Map successfully saved to {output_image_path}!")
    
    # Opens a window to show you the map immediately
    plt.show()

# Run the function using your topology file
draw_topology_map('topology.json', 'map_visual.png')