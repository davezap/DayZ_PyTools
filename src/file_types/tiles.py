from os import listdir
from os.path import isfile, join, isfile
from io import FileIO
import struct

import paa 

#111471 bytes
path = "P:/DZ/worlds/chernarusplus/data/layers"
file_name = "s_027_029_lco.paa"


files = [f for f in listdir(path) if isfile(join(path,f))]

for file_name in files:
    if file_name.startswith("s_"):
        output_file = 'output/' + file_name.replace(".paa", ".png")
        if not isfile(output_file):
            print(path + "/" + file_name + "...")
            p = paa.Paa(path + "/" + file_name)
            p.read_paa()
            p.writeImage(output_file, 0)

