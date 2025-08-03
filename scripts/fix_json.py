import glob
import json 

file_paths = glob.glob("*.json")

for file_path in file_paths:
    with open(file_path, "r") as f_in:
        data = json.load(f_in)

    try:
        del data["layout"]["template"]["data"]
    except (KeyError, TypeError):
        pass 

    with open(file_path, "w") as f_out:
        json.dump(data, f_out, indent=4)
