import csv
import json

def convert_csv_to_json(csv_filename, json_filename):
    topology = {}

    with open(csv_filename, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        header = next(reader) # Skip the header row
        
        for row in reader:
            # Skip completely empty rows
            if not row:
                continue
            
            prov_id = str(row[0]).strip()
            if not prov_id:
                continue
            
            # Parse X and Y coordinates as integers
            try:
                x = int(row[1].strip())
            except ValueError:
                x = row[1].strip()
                
            try:
                y = int(row[2].strip())
            except ValueError:
                y = row[2].strip()
                
            # Parse Coastal as a boolean (true if "yes", false otherwise)
            coastal = True if str(row[3]).strip().lower() == 'yes' else False
            
            # Extract neighbors and filter out any empty string artifacts from CSV formatting
            neighbors = [str(n).strip() for n in row[4:] if str(n).strip()]
            
            # Build the dictionary entry
            topology[prov_id] = {
                "x": x,
                "y": y,
                "coastal": coastal,
                "neighbors": neighbors
            }

    # Write out the JSON dictionary with indentation for readability
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(topology, f, indent=4)
        
    print(f"Successfully converted {csv_filename} to {json_filename}!")

# Run the function on your file
convert_csv_to_json('LAMGsheet - IDs.csv', 'topology.json')