import json

def new_json(json_filename):
    province = {}


    for row in range(1, 409):
            
            # Build the dictionary entry
        province[row] = {
            "owner": "",
            "troops": "",
            "has_city": "",
            "is_fortified": ""
        }

    # Write out the JSON dictionary with indentation for readability
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(province, f, indent=4)
        

# Run the function on your file
new_json('gamestate.json')