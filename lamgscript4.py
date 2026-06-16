import json
import tkinter as tk
from tkinter import messagebox

class MapGameEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Late Antiquity Map Editor")
        
        # Load the files
        self.topology = self.load_json('topology.json', default={})
        self.gamestate = self.load_json('gamestate.json', default={})
        
        # Ensure all territories in topology exist in the gamestate
        self.sync_gamestate()

        # Set up a scrollable canvas in case the map is larger than the screen
        self.canvas = tk.Canvas(root, width=1200, height=800, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.node_radius = 5
        self.item_to_prov_id = {} # Dictionary to map drawn circles to their Province IDs

        self.draw_map()

    def load_json(self, filepath, default):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return default

    def save_gamestate(self):
        with open('gamestate.json', 'w', encoding='utf-8') as f:
            json.dump(self.gamestate, f, indent=4)
        print("Gamestate saved!")

    def sync_gamestate(self):
        """Creates default gamestate entries for new provinces."""
        changed = False
        for prov_id in self.topology:
            if prov_id not in self.gamestate:
                self.gamestate[prov_id] = {
                    "owner": "None",
                    "troops": 0,
                    "has_city": False,
                    "is_fortified": False
                }
                changed = True
        if changed:
            self.save_gamestate()

    def draw_map(self):
        drawn_lines = set()

        # 1. Draw connections (Lines)
        for prov_id, data in self.topology.items():
            x1, y1 = int(data['x']), int(data['y'])
            
            for neighbor in data['neighbors']:
                if neighbor in self.topology:
                    connection = tuple(sorted([prov_id, neighbor]))
                    if connection not in drawn_lines:
                        x2, y2 = int(self.topology[neighbor]['x']), int(self.topology[neighbor]['y'])
                        self.canvas.create_line(x1, y1, x2, y2, fill="gray", width=1)
                        drawn_lines.add(connection)

        # 2. Draw nodes and text
        for prov_id, data in self.topology.items():
            x, y = int(data['x']), int(data['y'])
            node_color = "red" if data.get('coastal') else "blue"
            
            # Draw the circle and tag it as a 'node'
            circle_id = self.canvas.create_oval(
                x - self.node_radius, y - self.node_radius,
                x + self.node_radius, y + self.node_radius,
                fill=node_color, outline="black", tags=("node", f"prov_{prov_id}")
            )
            
            # Map this specific drawn circle to its province ID
            self.item_to_prov_id[circle_id] = prov_id
            
            # Add text slightly above the node
            self.canvas.create_text(x, y - 12, text=prov_id, font=("Arial", 7))

        # 3. Bind Left-Click (<Button-1>) on anything tagged "node" to the click handler
        self.canvas.tag_bind("node", "<Button-1>", self.on_node_click)

    def on_node_click(self, event):
        # Identify which circle was clicked
        clicked_item = self.canvas.find_withtag("current")[0]
        prov_id = self.item_to_prov_id[clicked_item]
        
        # Open the editor window
        self.open_editor_popup(prov_id)

    def open_editor_popup(self, prov_id):
        state = self.gamestate.get(prov_id, {})

        # Create a new mini-window
        popup = tk.Toplevel(self.root)
        popup.title(f"Edit Province {prov_id}")
        popup.geometry("300x200")
        
        # --- SAFE PARSING: Convert "" to actual types so Tkinter doesn't crash ---
        raw_owner = state.get("owner", "None")
        raw_troops = state.get("troops", 0)
        raw_city = state.get("has_city", False)
        raw_fort = state.get("is_fortified", False)

        owner_val = raw_owner if raw_owner != "" else "None"
        
        try:
            troops_val = int(raw_troops) if raw_troops != "" else 0
        except ValueError:
            troops_val = 0
            
        city_val = True if raw_city == True or raw_city == "true" or raw_city == "True" else False
        fort_val = True if raw_fort == True or raw_fort == "true" or raw_fort == "True" else False

        # --- Variables to hold form data ---
        owner_var = tk.StringVar(value=owner_val)
        troops_var = tk.IntVar(value=troops_val)
        city_var = tk.BooleanVar(value=city_val)
        fort_var = tk.BooleanVar(value=fort_val)

        # --- Form UI ---
        tk.Label(popup, text=f"Province {prov_id}", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, pady=5)

        tk.Label(popup, text="Owner:").grid(row=1, column=0, sticky="e", padx=5)
        tk.Entry(popup, textvariable=owner_var).grid(row=1, column=1, sticky="w")

        tk.Label(popup, text="Troops:").grid(row=2, column=0, sticky="e", padx=5)
        tk.Entry(popup, textvariable=troops_var).grid(row=2, column=1, sticky="w")

        tk.Checkbutton(popup, text="Has City", variable=city_var).grid(row=3, column=1, sticky="w")
        tk.Checkbutton(popup, text="Is Fortified", variable=fort_var).grid(row=4, column=1, sticky="w")

        # --- Save Function inside popup ---
        def save_changes():
            try:
                # Update the dictionary with PROPER data types
                self.gamestate[prov_id]["owner"] = owner_var.get()
                self.gamestate[prov_id]["troops"] = troops_var.get()  # Saves as Int
                self.gamestate[prov_id]["has_city"] = city_var.get()  # Saves as Bool
                self.gamestate[prov_id]["is_fortified"] = fort_var.get() # Saves as Bool
                
                # Write to the JSON file
                self.save_gamestate()
                popup.destroy() # Close the popup
            except tk.TclError:
                messagebox.showerror("Input Error", "Troops must be a valid number!")

        # Save Button
        tk.Button(popup, text="Save Changes", command=save_changes, bg="lightgreen").grid(row=5, column=0, columnspan=2, pady=10)


# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = MapGameEditor(root)
    root.mainloop()