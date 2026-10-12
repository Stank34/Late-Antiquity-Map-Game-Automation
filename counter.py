import json

# Civ alias mapping for factions with split tags (e.g., Western Rome)
CIV_ALIASES = {
    "Rome": ["Rome", "RomeW"]
}

SPECIAL_TERRITORY_BONUSES = {
    "11": {"gold": 4},  # Britain gold mine
    "71": {"silver": 240}, # Gaul silver
    "104": {"gold": 4}, # Iberia gold
    "142": {"silver": 240}, # Illyria training
    "349": {"territories": 4}, # Lower Egypt
    "350": {"territories": 2}, # Upper Egypt
    "351": {"territories": 2}, # Libya Inferior
    "401": {"gold": 1}, # North Cyprus
    "403": {"gold": 4}, # Syracuse
    "411": {"gold": 1}, # South Cyprus
}

ROME_TERRITORY_BONUSES = {
    "128": {"gold": 4, "silver": 50}, # Rome
    "180": {"gold": 4, "silver": 50}, # Constantinople
    "210": {"gold": 2, "silver": 100}, # Antioch
    "248": {"silver": 150}, # Dara
    "275": {"gold": 2, "silver": 100}, # Jerusalem
    "349": {"gold": 2, "silver": 100}, # Alexandria
}

# Change when these things happen!
DARA_BLOWN = False
PENTARCHY_ACTIVE = False
PERSIA_ECO = 1
FRANKS_BOOST = True

# IS THE TRIBE A TRIBE?
TRIBES = {
    "Vandals": True,
    "Visigoths": True,
    "Suebi": True,
    "Franks": True, 
    "Saxons": True,
    "Ostrogoths": True,
    "Arabs": True,
    "Lombards": True,
}

def get_civ_stats(civ_name):
    """
    Calculates statistics for a given civilization from gamestate data.
    
    :param civ_name: Name of the civilization (e.g., "Rome", "Persia")
    :return: dict containing territories, cities, fortified_cities, and troops count
    """
    with open("gamestate.json", 'r', encoding='utf-8') as f:
        gamestate = json.load(f)

    # Resolve civilization ownership tags/aliases
    target_owners = CIV_ALIASES.get(civ_name, [civ_name])

    territories = 0
    cities = 0
    fortified_cities = 0
    troops = 0

    for state in gamestate.values():
        owner = state.get("owner", "None")
        if owner in target_owners:
            territories += 1
            troops += state.get("troops", 0)

            has_city = state.get("has_city", False)
            is_fortified = state.get("is_fortified", False)

            if has_city:
                cities += 1
                if is_fortified:
                    fortified_cities += 1
    return {
        "civ": civ_name,
        "territories": territories,
        "cities": cities,
        "fortified_cities": fortified_cities,
        "troops": troops
    }


def calculate_civ_income(civ_stats, agriculture=1, economy=1):
    """
    Calculates Food, Silver, and Gold income based on civilization stats and technology levels.
    
    :param civ_stats: Dictionary returned by get_civ_stats()
    :param agriculture: Civilization's Agriculture technology level
    :param economy: Civilization's Economy technology level
    :return: dict containing 'food', 'silver', and 'gold' income
    """
    civ = civ_stats.get("civ", "None")
    territories = civ_stats.get("territories", 0)
    cities = civ_stats.get("cities", 0)
    troops = civ_stats.get("troops", 0)

    target_owners = CIV_ALIASES.get(civ, [civ])

    with open("gamestate.json", 'r', encoding='utf-8') as f:
        gamestate = json.load(f)
    if civ == "Persia":
        economy += PERSIA_ECO
    # Formula calculations
    food_per_territory = 100 + (agriculture * 10)
    # Food income has to be calculated AFTER the bonuses are added.

    silver_per_city = 10 + (economy * 7)
    silver_income = cities * silver_per_city

    gold_income = cities

    for prov_id, state in gamestate.items():
        owner = state.get("owner", "None")
        if owner in target_owners:
            if prov_id in SPECIAL_TERRITORY_BONUSES:
                bonuses = SPECIAL_TERRITORY_BONUSES[prov_id]
                territories += bonuses.get("territories", 0)
                silver_income += bonuses.get("silver", 0)
                gold_income += bonuses.get("gold", 0)
            if civ == "Rome":
                if prov_id in ROME_TERRITORY_BONUSES:
                    bonuses = ROME_TERRITORY_BONUSES[prov_id]
                    if (prov_id == "248" and DARA_BLOWN == False) or (prov_id != "248" and PENTARCHY_ACTIVE == True):
                        silver_income += bonuses.get("silver", 0)
                        gold_income += bonuses.get("gold", 0)

    
    
    food_income = (territories * food_per_territory) - troops

    if civ == "Suebi":
        food_income = (territories * food_per_territory * 2) - troops
    if civ == "Franks" and FRANKS_BOOST:
        silver_income *= 3
        gold_income *= 3
    elif civ == "Franks":
        silver_income *= 2
    if civ in TRIBES and TRIBES[civ]:
        food_income = 0 - troops
        silver_income = 0
        gold_income = 0
    return {
        "civ": civ,
        "Food": food_income,
        "Silver": silver_income,
        "Gold": gold_income
    }


if __name__ == "__main__":
    civ = "Rome"
    stats = get_civ_stats(civ)
    income = calculate_civ_income(stats, agriculture=3, economy=4)

    print(f"--- {civ} Stats ---")
    print(json.dumps(stats, indent=4))
    
    print(f"\n--- {civ} Income ---")
    print(json.dumps(income, indent=4))