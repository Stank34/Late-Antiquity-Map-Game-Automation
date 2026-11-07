import copy
import json
import random
import tkinter as tk
from tkinter import ttk, messagebox

CIVILIZATIONS = [
    "Arabs", "Suebi", "Saxons", "Lombards", "Vandals",
    "Ostrogoths", "Visigoths", "Persia", "Franks", "Rome"
]
TRIBES = [
    "Lombards", "Ostrogoths", "Arabs"
]


class MoveGameEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Late Antiquity Move & Simulation Editor")
        self.root.geometry("1400x900")

        # Load JSON Data Files
        self.topology = self.load_json('topology.json', default={})
        self.gamestate = self.load_json('gamestate.json', default={})
        self.gamestate_temp = copy.deepcopy(self.gamestate)
        self.civ_stats = self.load_json('civ_stats.json', default={})
        self.moves_data = self.load_json('moves.json', default={})

        self.player_colors = {
            "RomeW": "#A80048", "Rome": "#7F0037", "Persia": "#FF6A00",
            "Franks": "#00137F", "Suebi": "#B5009C", "Visigoths": "#B2CC41",
            "Ostrogoths": "#0094B6", "Saxons": "#FF8C77", "Vandals": "#FF3A00",
            "Lombards": "#777092", "ArabAI": "#4BBC4B", "Arabs": "#004000",
            "AI": "#AFAFAF", "Gepids": "#7F3300", "Slavs": "#75A0C9",
            "Avars": "#A3B2AC", "Bulgars": "#43285D"
        }

        self.node_radius = 5
        self.item_to_prov_id = {}

        # Mode State: "input" or "simulate"
        self.mode = "input"

        # Simulation Settings Variables
        self.no_random_var = tk.BooleanVar(value=False)
        self.seed_var = tk.StringVar(value=str(random.randint(100000, 999999)))

        # Selection Trackers
        self.selected_source_prov = None
        self.selected_dest_prov = None

        # Sync structure
        self.sync_moves_data()

        # --- Main Layout ---
        main_frame = tk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. RIGHT SIDE: Civilization Notebook Panel
        panel_frame = tk.Frame(main_frame, width=440, bg="#f0f0f0")
        panel_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        panel_frame.pack_propagate(False)

        # Mode Switcher Header
        header_frame = tk.Frame(panel_frame, bg="#f0f0f0")
        header_frame.pack(fill=tk.X, pady=5)

        self.mode_title_lbl = tk.Label(header_frame, text="Move Orders (Input Mode)", font=("Arial", 11, "bold"), bg="#f0f0f0")
        self.mode_title_lbl.pack(side=tk.LEFT, padx=5)

        self.mode_btn = tk.Button(header_frame, text="Switch to Simulation", bg="#E0E0E0", command=self.toggle_mode)
        self.mode_btn.pack(side=tk.RIGHT, padx=5)

        # Tabbed Notebook
        self.notebook = ttk.Notebook(panel_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        self.tab_widgets = {}
        self.build_civ_tabs()

        # 2. LEFT SIDE: Map Canvas Frame
        map_frame = tk.Frame(main_frame)
        map_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        v_scroll = tk.Scrollbar(map_frame, orient=tk.VERTICAL)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        h_scroll = tk.Scrollbar(map_frame, orient=tk.HORIZONTAL)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        self.canvas = tk.Canvas(
            map_frame,
            width=2400,
            height=1600,
            bg="white",
            xscrollcommand=h_scroll.set,
            yscrollcommand=v_scroll.set
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        v_scroll.config(command=self.canvas.yview)
        h_scroll.config(command=self.canvas.xview)

        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        self.canvas.bind_all("<Shift-MouseWheel>", lambda e: self.canvas.xview_scroll(int(-1*(e.delta/120)), "units"))

        self.draw_map()

    def load_json(self, filepath, default):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return default

    def normalize_civ(self, civ_name):
        """Maps civilization aliases (e.g. RomeW -> Rome)."""
        if civ_name == "RomeW":
            return "Rome"
        return civ_name

    def record_civ_stats(self, civ_name, units_moved=0, losses=0, won=False, lost=False):
        """Updates battle and unit statistics for tracked civilizations."""
        norm_civ = self.normalize_civ(civ_name)
        if norm_civ in CIVILIZATIONS and norm_civ in self.moves_data:
            civ_entry = self.moves_data[norm_civ]
            civ_entry["total_units_moved"] = civ_entry.get("total_units_moved", 0) + units_moved
            civ_entry["troops_lost"] = civ_entry.get("troops_lost", 0) + losses
            if won:
                civ_entry["battles_won"] = civ_entry.get("battles_won", 0) + 1
            if lost:
                civ_entry["battles_lost"] = civ_entry.get("battles_lost", 0) + 1

    def get_active_gamestate(self):
        """Returns temporary gamestate during simulation mode, or main gamestate during input mode."""
        return self.gamestate_temp if self.mode == "simulate" else self.gamestate

    def save_moves(self):
        """Saves current moves hierarchy to moves.json."""
        with open('moves.json', 'w', encoding='utf-8') as f:
            json.dump(self.moves_data, f, indent=4)

    def save_gamestate(self):
        """Saves current primary gamestate to gamestate.json."""
        with open('gamestate.json', 'w', encoding='utf-8') as f:
            json.dump(self.gamestate, f, indent=4)

    def save_gamestate_temp(self):
        """Saves current temporary gamestate to gamestate_temp.json."""
        with open('gamestate_temp.json', 'w', encoding='utf-8') as f:
            json.dump(self.gamestate_temp, f, indent=4)

    def sync_moves_data(self):
        """Ensures all 10 civilizations + Sieges exist in moves.json and syncs stats."""
        for civ in CIVILIZATIONS:
            if civ not in self.moves_data:
                self.moves_data[civ] = {
                    "attack": 1,
                    "defense": 1,
                    "total_units_moved": 0,
                    "troops_lost": 0,
                    "battles_won": 0,
                    "battles_lost": 0,
                    "moves": []
                }

            lookup_civ = self.normalize_civ(civ)
            civ_info = self.civ_stats.get(lookup_civ, {})
            
            atk_val = civ_info.get("Attack", 1)
            def_val = civ_info.get("Defense", 1)

            self.moves_data[civ]["attack"] = max(0, atk_val if atk_val is not None else 1)
            self.moves_data[civ]["defense"] = max(0, def_val if def_val is not None else 1)

            if "troops_lost" not in self.moves_data[civ]:
                self.moves_data[civ]["troops_lost"] = 0
            if "battles_won" not in self.moves_data[civ]:
                self.moves_data[civ]["battles_won"] = 0
            if "battles_lost" not in self.moves_data[civ]:
                self.moves_data[civ]["battles_lost"] = 0

            moves = self.moves_data[civ].get("moves", [])
            self.moves_data[civ]["total_units_moved"] = sum(int(m.get("units", 0)) for m in moves)

        if "Sieges" not in self.moves_data:
            self.moves_data["Sieges"] = {"moves": []}

        self.save_moves()

    def generate_new_seed(self):
        """Generates a new random seed integer."""
        new_seed = str(random.randint(100000, 999999))
        self.seed_var.set(new_seed)

    def toggle_mode(self):
        """Switches UI between Move Input Mode and Simulation Mode."""
        if self.mode == "input":
            self.mode = "simulate"
            self.mode_title_lbl.config(text="Simulation Mode")
            self.mode_btn.config(text="Switch to Move Input")
            
            # Reset statistics for all civilizations on entering simulation mode
            for civ in CIVILIZATIONS:
                if civ in self.moves_data:
                    self.moves_data[civ]["total_units_moved"] = 0
                    self.moves_data[civ]["troops_lost"] = 0
                    self.moves_data[civ]["battles_won"] = 0
                    self.moves_data[civ]["battles_lost"] = 0

            self.gamestate_temp = copy.deepcopy(self.gamestate)
            self.save_gamestate_temp()
            self.save_moves()

            if "Sieges" in self.tab_widgets:
                self.notebook.add(self.tab_widgets["Sieges"]["tab"], text="Sieges")
        else:
            self.mode = "input"
            self.mode_title_lbl.config(text="Move Orders (Input Mode)")
            self.mode_btn.config(text="Switch to Simulation")
            
            self.gamestate_temp = copy.deepcopy(self.gamestate)
            self.save_gamestate_temp()

            # Clear all pending sieges when exiting simulation mode
            if "Sieges" in self.moves_data:
                self.moves_data["Sieges"]["moves"] = []
            self.save_moves()

            if "Sieges" in self.tab_widgets:
                self.notebook.forget(self.tab_widgets["Sieges"]["tab"])
                self.refresh_civ_tab("Sieges")

        for key, w in self.tab_widgets.items():
            if self.mode == "simulate":
                w["form_frame"].pack_forget()
                w["settings_frame"].pack(fill=tk.X, padx=5, pady=5)
                w["input_btn_frame"].pack_forget()
                w["sim_btn_frame"].pack(fill=tk.X, padx=5, pady=5)
            else:
                w["settings_frame"].pack_forget()
                w["form_frame"].pack(fill=tk.X, padx=5, pady=5)
                w["sim_btn_frame"].pack_forget()
                w["input_btn_frame"].pack(fill=tk.X, padx=5, pady=5)

            self.refresh_civ_tab(key)

        self.draw_map()

    def get_next_priority(self, civ):
        moves = self.moves_data.get(civ, {}).get("moves", [])
        if not moves:
            return 1
        return max(int(m.get("priority", 0)) for m in moves) + 1

    def build_civ_tabs(self):
        """Constructs tab UI for all 10 civilizations and the Sieges turn."""
        all_tabs = CIVILIZATIONS + ["Sieges"]

        for civ in all_tabs:
            tab = tk.Frame(self.notebook)
            if civ != "Sieges":
                self.notebook.add(tab, text=civ)

            civ_data = self.moves_data.get(civ, {
                "attack": 1, "defense": 1, "total_units_moved": 0,
                "troops_lost": 0, "battles_won": 0, "battles_lost": 0, "moves": []
            })

            # Dynamic Top Stats Banner
            stats_frame = tk.LabelFrame(tab, text="Turn / Civ Overview", padx=5, pady=5)
            stats_frame.pack(fill=tk.X, padx=5, pady=5)

            if civ != "Sieges":
                attack_lbl = tk.Label(stats_frame, text=f"Attack: {civ_data.get('attack', 1)}", fg="red", font=("Arial", 9, "bold"))
                attack_lbl.grid(row=0, column=0, padx=10, sticky="w")

                defense_lbl = tk.Label(stats_frame, text=f"Defense: {civ_data.get('defense', 1)}", fg="blue", font=("Arial", 9, "bold"))
                defense_lbl.grid(row=0, column=1, padx=10, sticky="w")

                total_lbl = tk.Label(stats_frame, text=f"Units Moved: {civ_data.get('total_units_moved', 0)}", font=("Arial", 9, "bold"))
                total_lbl.grid(row=1, column=0, padx=10, pady=2, sticky="w")

                lost_lbl = tk.Label(stats_frame, text=f"Troops Lost: {civ_data.get('troops_lost', 0)}", fg="#B22222", font=("Arial", 9, "bold"))
                lost_lbl.grid(row=1, column=1, padx=10, pady=2, sticky="w")

                won_lbl = tk.Label(stats_frame, text=f"Battles Won: {civ_data.get('battles_won', 0)}", fg="#228B22", font=("Arial", 9, "bold"))
                won_lbl.grid(row=2, column=0, padx=10, pady=2, sticky="w")

                lost_battles_lbl = tk.Label(stats_frame, text=f"Battles Lost: {civ_data.get('battles_lost', 0)}", fg="#CD5C5C", font=("Arial", 9, "bold"))
                lost_battles_lbl.grid(row=2, column=1, padx=10, pady=2, sticky="w")
            else:
                attack_lbl, defense_lbl, lost_lbl, won_lbl, lost_battles_lbl = None, None, None, None, None
                total_lbl = tk.Label(stats_frame, text="Active Sieges Pending Resolution", font=("Arial", 9, "bold"))
                total_lbl.pack(pady=2)

            # Moves Treeview Table
            tree_frame = tk.Frame(tab)
            tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

            if civ != "Sieges":
                cols = ("Priority", "Source", "Destination", "Units")
                tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=7)
                tree.heading("Priority", text="Prio")
                tree.heading("Source", text="From")
                tree.heading("Destination", text="To")
                tree.heading("Units", text="Units")
                tree.column("Priority", width=45, anchor="center")
                tree.column("Source", width=80, anchor="center")
                tree.column("Destination", width=80, anchor="center")
                tree.column("Units", width=80, anchor="center")
            else:
                cols = ("Attacker", "Source", "Destination", "Units")
                tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=7)
                tree.heading("Attacker", text="Attacker")
                tree.heading("Source", text="From")
                tree.heading("Destination", text="To")
                tree.heading("Units", text="Units")
                tree.column("Attacker", width=80, anchor="center")
                tree.column("Source", width=80, anchor="center")
                tree.column("Destination", width=80, anchor="center")
                tree.column("Units", width=80, anchor="center")

            tree.pack(fill=tk.BOTH, expand=True)
            tree.bind("<Double-1>", lambda event, c=civ: self.on_move_double_click(event, c))

            # --- MODE 1: Add New Move Section ---
            form_frame = tk.LabelFrame(tab, text="Add New Move", padx=5, pady=5)
            form_frame.pack(fill=tk.X, padx=5, pady=5)

            src_var = tk.StringVar()
            dst_var = tk.StringVar()
            units_var = tk.StringVar(value="0")
            prio_var = tk.StringVar(value=str(self.get_next_priority(civ)))

            tk.Label(form_frame, text="Source:").grid(row=0, column=0, sticky="e")
            tk.Entry(form_frame, textvariable=src_var, width=8).grid(row=0, column=1, padx=2, pady=2)

            tk.Label(form_frame, text="Dest:").grid(row=0, column=2, sticky="e")
            tk.Entry(form_frame, textvariable=dst_var, width=8).grid(row=0, column=3, padx=2, pady=2)

            tk.Label(form_frame, text="Units:").grid(row=1, column=0, sticky="e")
            tk.Entry(form_frame, textvariable=units_var, width=8).grid(row=1, column=1, padx=2, pady=2)

            tk.Label(form_frame, text="Priority:").grid(row=1, column=2, sticky="e")
            tk.Entry(form_frame, textvariable=prio_var, width=8).grid(row=1, column=3, padx=2, pady=2)

            # --- MODE 2: Settings Section ---
            settings_frame = tk.LabelFrame(tab, text="Simulation Settings", padx=5, pady=5)

            tk.Checkbutton(settings_frame, text="No Random", variable=self.no_random_var).grid(row=0, column=0, columnspan=2, sticky="w", padx=5)

            tk.Label(settings_frame, text="Seed:").grid(row=1, column=0, sticky="e", padx=2)
            tk.Entry(settings_frame, textvariable=self.seed_var, width=10).grid(row=1, column=1, sticky="w", padx=2)
            tk.Button(settings_frame, text="New Seed", command=self.generate_new_seed).grid(row=1, column=2, padx=5)

            # --- MODE 1 Buttons ---
            input_btn_frame = tk.Frame(tab)
            input_btn_frame.pack(fill=tk.X, padx=5, pady=5)

            add_btn = tk.Button(
                input_btn_frame, text="Add Move", bg="lightgreen",
                command=lambda c=civ, s=src_var, d=dst_var, u=units_var, p=prio_var: self.add_move(c, s, d, u, p)
            )
            add_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

            del_btn = tk.Button(
                input_btn_frame, text="Delete Selected", bg="#FF8888",
                command=lambda c=civ: self.delete_selected_move(c)
            )
            del_btn.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=2)

            # --- MODE 2 Buttons ---
            sim_btn_frame = tk.Frame(tab)

            exec_btn = tk.Button(sim_btn_frame, text="Execute Turn", bg="#88CCFF", font=("Arial", 9, "bold"), command=self.execute_turn)
            exec_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

            save_st_btn = tk.Button(sim_btn_frame, text="Save State", bg="#A3E4D7", font=("Arial", 9, "bold"), command=self.save_full_state)
            save_st_btn.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=2)

            self.tab_widgets[civ] = {
                "tab": tab,
                "tree": tree,
                "total_lbl": total_lbl,
                "lost_lbl": lost_lbl,
                "won_lbl": won_lbl,
                "lost_battles_lbl": lost_battles_lbl,
                "src_var": src_var,
                "dst_var": dst_var,
                "units_var": units_var,
                "prio_var": prio_var,
                "form_frame": form_frame,
                "settings_frame": settings_frame,
                "input_btn_frame": input_btn_frame,
                "sim_btn_frame": sim_btn_frame
            }

            self.refresh_civ_tab(civ)

    def refresh_civ_tab(self, civ):
        """Refreshes treeview items, Overview statistics, and autofills next priority for a civ."""
        widgets = self.tab_widgets[civ]
        tree = widgets["tree"]
        
        for item in tree.get_children():
            tree.delete(item)

        moves = self.moves_data.get(civ, {}).get("moves", [])

        if civ != "Sieges":
            moves.sort(key=lambda m: int(m.get("priority", 1)))
            total_units = 0
            for idx, m in enumerate(moves):
                units = int(m.get("units", 0))
                total_units += units
                tree.insert("", "end", iid=str(idx), values=(m.get("priority"), m.get("source"), m.get("destination"), units))

            if self.mode == "input":
                self.moves_data[civ]["total_units_moved"] = total_units

            civ_data = self.moves_data.get(civ, {})
            widgets["total_lbl"].config(text=f"Units Moved: {civ_data.get('total_units_moved', 0)}")
            if widgets["lost_lbl"]:
                widgets["lost_lbl"].config(text=f"Troops Lost: {civ_data.get('troops_lost', 0)}")
            if widgets["won_lbl"]:
                widgets["won_lbl"].config(text=f"Battles Won: {civ_data.get('battles_won', 0)}")
            if widgets["lost_battles_lbl"]:
                widgets["lost_battles_lbl"].config(text=f"Battles Lost: {civ_data.get('battles_lost', 0)}")

            widgets["prio_var"].set(str(self.get_next_priority(civ)))
        else:
            for idx, m in enumerate(moves):
                tree.insert("", "end", iid=str(idx), values=(m.get("attacker"), m.get("source"), m.get("destination"), m.get("units")))

        try:
            current_tab_idx = self.notebook.index(self.notebook.select())
            active_tab_name = (CIVILIZATIONS + ["Sieges"])[current_tab_idx]
            if active_tab_name == civ:
                self.draw_move_lines()
        except Exception:
            pass

    # --- BATTLE RESOLUTION CALCULATOR ---
    def calculate_battle(self, attacker_civ, attacker_troops, defender_civ, defender_troops, has_city, is_fortified, is_naval):
        """Executes battle calculation between attacker and defender."""
        atk_lookup = self.normalize_civ(attacker_civ)
        def_lookup = self.normalize_civ(defender_civ)

        atk_stat = self.moves_data.get(atk_lookup, {}).get("attack")
        if atk_stat is None or int(atk_stat) <= 0:
            atk_stat = self.civ_stats.get(atk_lookup, {}).get("Attack", 1)
        atk_stat = max(0, int(atk_stat) if atk_stat else 1)

        def_stat = self.moves_data.get(def_lookup, {}).get("defense")
        if def_stat is None or int(def_stat) <= 0:
            def_stat = self.civ_stats.get(def_lookup, {}).get("Defense", 1)
        def_stat = max(0, int(def_stat) if def_stat else 1)
        if atk_lookup in TRIBES and not is_fortified:
            if def_lookup == "Franks":
                def_stat = min(2, int(def_stat) if def_stat else 1)
            else:
                def_stat = min(1, int(def_stat) if def_stat else 1)
        if is_fortified:
            if def_lookup == "Rome":
                def_stat += 3
            else:
                def_stat += 1
        if has_city and atk_lookup == "Persia":
            atk_stat += 2
        if atk_lookup == "Visigoths":
            atk_stat += 2
        if is_naval:
            if atk_lookup == "Rome":
                atk_stat += 2
            if atk_lookup in ["Vandals", "Saxons"]:
                atk_stat += 3
            if atk_lookup == "Persia":
                atk_stat -= 3
            if def_lookup == "Rome":
                def_stat += 2
            if def_lookup in ["Vandals", "Saxons"]:
                def_stat += 8
        if atk_lookup == "Arabs": # REMOVE AFTER 600-625
            atk_stat += 2
        p_atk = attacker_troops * atk_stat
        p_def = defender_troops * def_stat

        if p_atk > p_def:
            winner = "attacker"
            winner_troops = attacker_troops
            loser_bp = p_def
        else:
            winner = "defender"
            winner_troops = defender_troops
            loser_bp = p_atk

        if winner == "attacker" and attacker_troops >= 7 * max(1, defender_troops):
            return "attacker", 0, defender_troops

        b_total = p_atk + p_def
        if b_total <= 0:
            b_total = 1

        r_factor = 1.0 if self.no_random_var.get() else random.uniform(0.8, 1.2)
        raw_losses = 3.0 * winner_troops * ((loser_bp / b_total) ** 2) * r_factor
        winner_losses = min(winner_troops, int(round(raw_losses)))

        if winner == "attacker":
            return "attacker", winner_losses, defender_troops
        else:
            return "defender", attacker_troops, winner_losses

    # --- EXECUTE TURN SIMULATION PROCESSOR ---
    def execute_turn(self):
        """Executes moves for ONLY the currently selected civilization tab (or Sieges tab) on gamestate_temp."""
        try:
            seed_val = int(self.seed_var.get().strip())
        except ValueError:
            seed_val = hash(self.seed_var.get().strip())
        random.seed(seed_val)

        try:
            current_tab_idx = self.notebook.index(self.notebook.select())
            active_civ = (CIVILIZATIONS + ["Sieges"])[current_tab_idx]
        except Exception:
            return

        log_events = []

        if active_civ != "Sieges":
            moves = self.moves_data.get(active_civ, {}).get("moves", [])
            sorted_moves = sorted(moves, key=lambda m: int(m.get("priority", 1)))

            for m in sorted_moves:
                src = str(m.get("source"))
                dst = str(m.get("destination"))
                req_units = int(m.get("units", 0))

                # Step 1: Check origin territory ownership on gamestate_temp
                if self.gamestate_temp.get(src, {}).get("owner") != active_civ:
                    log_events.append(f"[{active_civ}] Move {src}->{dst} cancelled (Origin not owned).")
                    continue

                # Step 1.5: CITY MOVE LOCK CHECK
                raw_src_city = self.gamestate_temp.get(src, {}).get("has_city", False)
                src_has_city = raw_src_city in [True, "true", "True", 1]

                if src_has_city:
                    current_src_troops = int(self.gamestate_temp.get(src, {}).get("troops", 0))
                    pending_siege_troops = sum(
                        int(sm.get("units", 0))
                        for sm in self.moves_data.get("Sieges", {}).get("moves", [])
                        if str(sm.get("destination")) == src
                    )
                    if pending_siege_troops > 0.5 * current_src_troops:
                        log_events.append(
                            f"[{active_civ}] Move {src}->{dst} cancelled "
                            f"(City moves locked: {pending_siege_troops} pending siege troops > 50% of {current_src_troops} defenders)."
                        )
                        continue

                # Step 2 & 3: Insufficient troops handling
                avail_troops = int(self.gamestate_temp[src].get("troops", 0))
                units_moved = min(req_units, avail_troops)

                if units_moved <= 0:
                    continue

                self.gamestate_temp[src]["troops"] -= units_moved

                # Track units moved
                self.record_civ_stats(active_civ, units_moved=units_moved)

                dst_owner = self.gamestate_temp.get(dst, {}).get("owner", "None")
                neighbors = self.topology.get(src, {}).get("neighbors", [])
                is_naval = False
                # Double counting for naval move
                if dst not in neighbors:
                    if dst_owner != active_civ:
                        if active_civ not in ["Vandals", "Saxons"]:
                            self.record_civ_stats(active_civ, units_moved=units_moved)
                            log_events.append(f"[{active_civ}] Naval movement detected {src}->{dst} (Double food cost).")
                        else:
                            log_events.append(f"[{active_civ}] Naval movement detected {src}->{dst} (Standard food cost, naval attack civ).")
                    else:
                        if active_civ == "Vandals":
                            self.record_civ_stats(active_civ, units_moved=-units_moved)
                            log_events.append(f"[{active_civ}] Naval movement detected {src}->{dst} (No food cost, Vandal naval move).")
                    is_naval = True
                
                if dst_owner == active_civ:
                    self.gamestate_temp[dst]["troops"] += units_moved
                    log_events.append(f"[{active_civ}] Reinforced {dst} with {units_moved} troops.")
                    continue

                raw_city = self.gamestate_temp.get(dst, {}).get("has_city", False)
                raw_fortified = self.gamestate_temp.get(dst, {}).get("is_fortified", False)
                has_city = raw_city in [True, "true", "True", 1]
                is_fortified = raw_fortified in [True, "true", "True", 1]

                if (has_city and (is_fortified or (active_civ not in TRIBES))):
                    # Check for an existing siege order from the active civ targeting this destination
                    existing_siege = next(
                        (
                            sm for sm in self.moves_data["Sieges"]["moves"]
                            if sm.get("attacker") == active_civ and str(sm.get("destination")) == str(dst)
                        ),
                        None
                    )

                    if existing_siege:
                        existing_siege["units"] += units_moved
                        log_events.append(
                            f"[{active_civ}] Reinforced siege at {dst} with {units_moved} troops "
                            f"(Total siege force: {existing_siege['units']})."
                        )
                    else:
                        siege_entry = {
                            "attacker": active_civ,
                            "source": src,
                            "destination": dst,
                            "units": units_moved,
                            "priority": m.get("priority", 1),
                            "is_fortified": is_fortified,
                            "is_naval": is_naval
                        }
                        self.moves_data["Sieges"]["moves"].append(siege_entry)
                        log_events.append(f"[{active_civ}] Commenced siege against city at {dst} with {units_moved} troops.")

                    continue

                def_troops = int(self.gamestate_temp.get(dst, {}).get("troops", 0))

                if def_troops == 0:
                    self.gamestate_temp[dst]["owner"] = active_civ
                    self.gamestate_temp[dst]["troops"] = units_moved
                    log_events.append(f"[{active_civ}] Claimed undefended territory at {dst} with {units_moved} troops.")
                    continue

                # Immediate Battle resolution
                def_owner = dst_owner
                winner, atk_loss, def_loss = self.calculate_battle(active_civ, units_moved, def_owner, def_troops, has_city, is_fortified, is_naval)

                # Record casualty and win/loss statistics
                if winner == "attacker":
                    self.record_civ_stats(active_civ, losses=atk_loss, won=True)
                    self.record_civ_stats(def_owner, losses=def_loss, lost=True)
                    surviving = units_moved - atk_loss
                    self.gamestate_temp[dst]["owner"] = active_civ
                    self.gamestate_temp[dst]["troops"] = surviving
                    log_events.append(f"[{active_civ}] BATTLE WIN at {dst}! Captured territory with {surviving} troops remaining.")
                else:
                    self.record_civ_stats(active_civ, losses=atk_loss, lost=True)
                    self.record_civ_stats(def_owner, losses=def_loss, won=True)
                    surviving = max(0, def_troops - def_loss)
                    self.gamestate_temp[dst]["troops"] = surviving
                    log_events.append(f"[{active_civ}] BATTLE LOSS at {dst}! Defender ({def_owner}) holds with {surviving} troops.")

        else:
            # EXECUTE SIEGES TURN
            siege_moves = list(self.moves_data.get("Sieges", {}).get("moves", []))
            self.moves_data["Sieges"]["moves"] = []

            if not siege_moves:
                log_events.append("No active sieges to execute.")
            for s_move in siege_moves:
                atk_civ = s_move["attacker"]
                dst = str(s_move["destination"])
                is_fortified = s_move["is_fortified"]
                is_naval = s_move["is_naval"]
                print("Executing a siege move " + str(is_fortified))
                units_moved = int(s_move["units"])
                def_owner = self.gamestate_temp.get(dst, {}).get("owner", "None")
                def_troops = int(self.gamestate_temp.get(dst, {}).get("troops", 0))

                if def_troops == 0:
                    self.gamestate_temp[dst]["owner"] = atk_civ
                    self.gamestate_temp[dst]["troops"] = units_moved
                    log_events.append(f"[SIEGE WIN] {atk_civ} captured undefended city at {dst} with {units_moved} troops.")
                    continue

                winner, atk_loss, def_loss = self.calculate_battle(atk_civ, units_moved, def_owner, def_troops, True, is_fortified, is_naval)

                if winner == "attacker":
                    self.record_civ_stats(atk_civ, losses=atk_loss, won=True)
                    self.record_civ_stats(def_owner, losses=def_loss, lost=True)
                    surviving = units_moved - atk_loss
                    self.gamestate_temp[dst]["owner"] = atk_civ
                    self.gamestate_temp[dst]["troops"] = surviving
                    self.gamestate_temp[dst]["is_fortified"] = False
                    log_events.append(f"[SIEGE WIN] {atk_civ} breached {dst}! City conquered with {surviving} troops.")
                else:
                    self.record_civ_stats(atk_civ, losses=atk_loss, lost=True)
                    self.record_civ_stats(def_owner, losses=def_loss, won=True)
                    surviving = max(0, def_troops - def_loss)
                    self.gamestate_temp[dst]["troops"] = surviving
                    log_events.append(f"[SIEGE FAIL] {atk_civ} repelled at {dst}! Defender ({def_owner}) retains city with {surviving} troops.")

        self.save_gamestate_temp()
        self.save_moves()

        for c in CIVILIZATIONS + ["Sieges"]:
            self.refresh_civ_tab(c)

        self.draw_map()

        msg = "\n".join(log_events[:15]) + (f"\n...and {len(log_events)-15} more events." if len(log_events)>15 else "")
        messagebox.showinfo(f"{active_civ} Turn Complete", msg if log_events else f"No moves executed for {active_civ}.")

    def save_full_state(self):
        """Overwrites main gamestate with gamestate_temp and saves files."""
        self.gamestate = copy.deepcopy(self.gamestate_temp)
        self.save_gamestate()
        self.save_gamestate_temp()
        self.save_moves()
        messagebox.showinfo("State Saved", "Temporary gamestate written to primary gamestate.json successfully!")

    def draw_move_lines(self):
        """Draws priority-colored directional move vectors and outlined unit labels on the canvas."""
        self.canvas.delete("move_line")

        try:
            current_tab_idx = self.notebook.index(self.notebook.select())
            active_civ = (CIVILIZATIONS + ["Sieges"])[current_tab_idx]
        except Exception:
            return

        moves = self.moves_data.get(active_civ, {}).get("moves", [])
        if not moves:
            return

        priorities = [int(m.get("priority", 1)) for m in moves]
        max_prio = max(priorities) if priorities else 1

        for m in moves:
            src_id = str(m.get("source"))
            dst_id = str(m.get("destination"))
            prio = int(m.get("priority", 1))
            units = int(m.get("units", 0))

            if src_id in self.topology and dst_id in self.topology:
                x1 = int(self.topology[src_id]['x']) * 3 / 2
                y1 = int(self.topology[src_id]['y']) * 3 / 2
                x2 = int(self.topology[dst_id]['x']) * 3 / 2
                y2 = int(self.topology[dst_id]['y']) * 3 / 2

                if max_prio <= 1:
                    t = 0.0
                else:
                    t = max(0.0, min(1.0, (prio - 1) / (max_prio - 1)))

                if t <= 0.5:
                    f = t * 2.0
                    r = int(255 * f)
                    g = 255
                    b = 0
                else:
                    f = (t - 0.5) * 2.0
                    r = 255
                    g = int(255 * (1.0 - f))
                    b = 0

                raw_color_hex = f"#{r:02X}{g:02X}{b:02X}"

                self.canvas.create_line(
                    x1, y1, x2, y2,
                    fill=raw_color_hex,
                    width=3,
                    arrow=tk.LAST,
                    arrowshape=(12, 15, 6),
                    tags="move_line"
                )

                mid_x = (x1 + x2) / 2
                mid_y = (y1 + y2) / 2

                outline_offsets = [
                    (-1, -1), (0, -1), (1, -1),
                    (-1,  0),          (1,  0),
                    (-1,  1), (0,  1), (1,  1)
                ]
                for dx, dy in outline_offsets:
                    self.canvas.create_text(
                        mid_x + dx, mid_y - 8 + dy,
                        text=f"{units}",
                        font=("Arial", 9, "bold"),
                        fill="#000000",
                        tags="move_line"
                    )

                self.canvas.create_text(
                    mid_x, mid_y - 8,
                    text=f"{units}",
                    font=("Arial", 9, "bold"),
                    fill=raw_color_hex,
                    tags="move_line"
                )

        self.canvas.tag_raise("node")
        self.canvas.tag_raise("text")

    def update_node_visual(self, prov_id):
        p_id = str(prov_id)
        if p_id not in self.topology:
            return

        active_state = self.get_active_gamestate()
        state = active_state.get(p_id, {})
        owner = state.get("owner", "None")
        node_color = self.player_colors.get(owner, "white")
        has_city = state.get("has_city", False)
        is_fortified = state.get("is_fortified", False)

        if p_id == self.selected_source_prov:
            outline_color = "#FFD700"  # Gold
            thickness = 5
        elif p_id == self.selected_dest_prov:
            outline_color = "#E0E0E0"  # Lighter Silver
            thickness = 5
        elif has_city:
            thickness = 3
            outline_color = "#606060" if is_fortified else "#7F3300"
        else:
            thickness = 1
            outline_color = "#000000"

        self.canvas.itemconfig(
            f"prov_{p_id}",
            fill=node_color,
            outline=outline_color,
            width=thickness
        )

    def clear_node_selections(self):
        old_src = self.selected_source_prov
        old_dst = self.selected_dest_prov

        self.selected_source_prov = None
        self.selected_dest_prov = None

        if old_src:
            self.update_node_visual(old_src)
        if old_dst:
            self.update_node_visual(old_dst)

    def on_tab_changed(self, event):
        self.clear_node_selections()

        current_tab_idx = self.notebook.index(self.notebook.select())
        active_civ = (CIVILIZATIONS + ["Sieges"])[current_tab_idx]
        widgets = self.tab_widgets[active_civ]

        src_val = widgets["src_var"].get().strip()
        dst_val = widgets["dst_var"].get().strip()

        if src_val:
            self.selected_source_prov = src_val
            self.update_node_visual(src_val)

        if dst_val:
            self.selected_dest_prov = dst_val
            self.update_node_visual(dst_val)

        self.draw_move_lines()

    def on_node_click(self, event):
        if self.mode == "simulate":
            return

        clicked_item = self.canvas.find_withtag("current")[0]
        prov_id = str(self.item_to_prov_id[clicked_item])

        current_tab_idx = self.notebook.index(self.notebook.select())
        active_civ = (CIVILIZATIONS + ["Sieges"])[current_tab_idx]

        widgets = self.tab_widgets[active_civ]
        src_var = widgets["src_var"]
        dst_var = widgets["dst_var"]

        if self.selected_source_prov == prov_id:
            src_var.set("")
            dst_var.set("")
            self.clear_node_selections()

        elif self.selected_source_prov is None:
            self.selected_source_prov = prov_id
            src_var.set(prov_id)
            self.update_node_visual(prov_id)

        elif self.selected_dest_prov is None:
            self.selected_dest_prov = prov_id
            dst_var.set(prov_id)
            self.update_node_visual(prov_id)

        else:
            self.clear_node_selections()
            self.selected_source_prov = prov_id
            src_var.set(prov_id)
            dst_var.set("")
            self.update_node_visual(prov_id)

    def on_move_double_click(self, event, civ):
        if self.mode == "simulate" or civ == "Sieges":
            return

        widgets = self.tab_widgets[civ]
        tree = widgets["tree"]
        selected = tree.selection()

        if not selected:
            return

        move_idx = int(selected[0])
        self.open_move_edit_popup(civ, move_idx)

    def open_move_edit_popup(self, civ, move_idx):
        moves = self.moves_data[civ].get("moves", [])
        if move_idx >= len(moves):
            return

        move = moves[move_idx]

        popup = tk.Toplevel(self.root)
        popup.title(f"Edit Move - {civ}")
        popup.geometry("320x220")
        popup.resizable(False, False)
        popup.grab_set()

        src_var = tk.StringVar(value=str(move.get("source", "")))
        dst_var = tk.StringVar(value=str(move.get("destination", "")))
        units_var = tk.StringVar(value=str(move.get("units", 0)))
        prio_var = tk.StringVar(value=str(move.get("priority", 1)))

        tk.Label(popup, text=f"Edit Order #{move_idx + 1} ({civ})", font=("Arial", 11, "bold")).grid(row=0, column=0, columnspan=2, pady=10)

        tk.Label(popup, text="Source Province:").grid(row=1, column=0, sticky="e", padx=5, pady=2)
        tk.Entry(popup, textvariable=src_var, width=12).grid(row=1, column=1, sticky="w", padx=5, pady=2)

        tk.Label(popup, text="Destination Province:").grid(row=2, column=0, sticky="e", padx=5, pady=2)
        tk.Entry(popup, textvariable=dst_var, width=12).grid(row=2, column=1, sticky="w", padx=5, pady=2)

        tk.Label(popup, text="Troop Count:").grid(row=3, column=0, sticky="e", padx=5, pady=2)
        tk.Entry(popup, textvariable=units_var, width=12).grid(row=3, column=1, sticky="w", padx=5, pady=2)

        tk.Label(popup, text="Priority Level:").grid(row=4, column=0, sticky="e", padx=5, pady=2)
        tk.Entry(popup, textvariable=prio_var, width=12).grid(row=4, column=1, sticky="w", padx=5, pady=2)

        def save_edits():
            try:
                u_val = int(units_var.get().strip())
                p_val = int(prio_var.get().strip())
            except ValueError:
                messagebox.showerror("Input Error", "Units and Priority must be valid integers.", parent=popup)
                return

            s_val = src_var.get().strip()
            d_val = dst_var.get().strip()

            if not s_val or not d_val:
                messagebox.showerror("Input Error", "Source and Destination are required.", parent=popup)
                return

            existing_prios = [
                int(m.get("priority", 1)) 
                for i, m in enumerate(moves) 
                if i != move_idx
            ]
            if p_val in existing_prios:
                messagebox.showerror(
                    "Priority Conflict", 
                    f"Priority {p_val} already exists for {civ}.\nPlease choose a unique priority.", 
                    parent=popup
                )
                return

            move["source"] = s_val
            move["destination"] = d_val
            move["units"] = u_val
            move["priority"] = p_val

            self.save_moves()
            self.refresh_civ_tab(civ)
            popup.destroy()

        def delete_move():
            if messagebox.askyesno("Confirm Delete", f"Delete move order from {move.get('source')} to {move.get('destination')}?", parent=popup):
                self.moves_data[civ]["moves"].pop(move_idx)
                self.save_moves()
                self.refresh_civ_tab(civ)
                popup.destroy()

        btn_frame = tk.Frame(popup)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=15)

        tk.Button(btn_frame, text="Save", bg="lightgreen", width=8, command=save_edits).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Delete", bg="#FF8888", width=8, command=delete_move).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Cancel", width=8, command=popup.destroy).pack(side=tk.LEFT, padx=5)

    def add_move(self, civ, src_var, dst_var, units_var, prio_var):
        src = src_var.get().strip()
        dst = dst_var.get().strip()

        try:
            units = int(units_var.get().strip())
            prio = int(prio_var.get().strip())
        except ValueError:
            messagebox.showerror("Input Error", "Units and Priority must be valid integers.")
            return

        if not src or not dst:
            messagebox.showerror("Input Error", "Source and Destination province IDs are required.")
            return

        existing_prios = [int(m.get("priority", 1)) for m in self.moves_data[civ].get("moves", [])]
        if prio in existing_prios:
            messagebox.showerror(
                "Priority Conflict", 
                f"Priority {prio} already exists for {civ}.\nPlease choose a unique priority."
            )
            return

        new_move = {
            "source": src,
            "destination": dst,
            "units": units,
            "priority": prio
        }

        self.moves_data[civ]["moves"].append(new_move)
        self.save_moves()
        self.refresh_civ_tab(civ)
        self.clear_node_selections()

        src_var.set("")
        dst_var.set("")
        units_var.set("0")

    def delete_selected_move(self, civ):
        widgets = self.tab_widgets[civ]
        tree = widgets["tree"]
        selected = tree.selection()

        if not selected:
            return

        selected_idx = int(selected[0])
        self.moves_data[civ]["moves"].pop(selected_idx)

        self.save_moves()
        self.refresh_civ_tab(civ)

    def draw_map(self):
        """Renders topology connections, province nodes, and active move vectors using active gamestate."""
        self.canvas.delete("all")
        self.item_to_prov_id.clear()

        drawn_lines = set()
        active_state = self.get_active_gamestate()

        for prov_id, data in self.topology.items():
            x1, y1 = int(data['x']) * 3 / 2, int(data['y']) * 3 / 2
            
            for neighbor in data['neighbors']:
                if neighbor in self.topology:
                    connection = tuple(sorted([prov_id, neighbor]))
                    if connection not in drawn_lines:
                        x2, y2 = int(self.topology[neighbor]['x']) * 3 / 2, int(self.topology[neighbor]['y']) * 3 / 2
                        self.canvas.create_line(x1, y1, x2, y2, fill="gray", width=1)
                        drawn_lines.add(connection)

        for prov_id, data in self.topology.items():
            x, y = int(data['x']) * 3 / 2, int(data['y']) * 3 / 2
            state = active_state.get(str(prov_id), {})
            owner = state.get("owner", "None")

            node_color = self.player_colors.get(owner, "white")
            has_city = state.get("has_city", False)
            radius = 8 if has_city else 5

            circle_id = self.canvas.create_oval(
                x - radius, y - radius,
                x + radius, y + radius,
                fill=node_color,
                tags=("node", f"prov_{prov_id}")
            )
            self.item_to_prov_id[circle_id] = str(prov_id)
            self.update_node_visual(prov_id)

            troops = state.get("troops", 0)
            self.canvas.create_text(x, y - 12, text=troops, font=("Arial", 7), tags=f"text_{prov_id}")

        self.canvas.tag_bind("node", "<Button-1>", self.on_node_click)
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

        self.draw_move_lines()

if __name__ == "__main__":
    root = tk.Tk()
    app = MoveGameEditor(root)
    root.mainloop()