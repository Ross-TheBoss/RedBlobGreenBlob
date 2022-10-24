import json

from pprint import pprint

def with_key(key, iterable,
             key_func = lambda x: x,
             value_func = lambda x: x):
    for item in iterable:
        yield key_func(item[key]), value_func(dict([*item.items()][1:]))
    

FILENAME = "level1.json"

with open(FILENAME, "r") as file:
    level_map = json.load(file)

width, height = level_map["width"], level_map["height"]

data = level_map["layers"][0]["data"]

tileset_src = level_map["tilesets"][0]["source"]
with open(tileset_src, "r") as file:
    tileset = json.load(file)

tiles = tileset["tiles"]

tile_mapping = dict(with_key("id", tiles, lambda x: x + 1))

output_file = open("parsed_map.txt", "w")

for row in range(height):
    for column in range(width):
        tile = data[column + (row * width)]
        if tile in tile_mapping:
            properties = tile_mapping[tile]["properties"]
            properties_mapping = dict(with_key("name", properties,
                                               value_func=lambda d: d["value"]))
            char = properties_mapping["ASCII"]
        else:
            char = " "
        print(char, file=output_file, end="")
    print(file=output_file)

output_file.close()
