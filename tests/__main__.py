from src.io.StreamReader import StreamReader
from src.file_types.oprw import OPRW
from src.file_types.paa import Paa
from src.file_types.pbo import Pbo
from src.file_types.P3d import P3d
import math
import time
start = time.time()

if 0:
    #path = "C:/Users/David/Documents/DayZ_MyTools/input/OFP Resistance/Red Hammer/redhammer.pbo"
    #path = "C:/Users/David/Documents/DayZ_MyTools/input/OFP Resistance/Red Hammer/VoiceRH.pbo"
    path = 'C:/Program Files (x86)/Steam/steamapps/common/DayZ/Addons/characters_belts.pbo'
    sr = StreamReader(path)
    pbo = Pbo(reader=sr)
    pbo.extract(destination = "output/pbo/")
    pbo.get_files()

if 0:   
    path = "P:/DZ/worlds/chernarusplus/data/layers"
    file_name = "s_005_029_lco.paa"
    #file_name = "s_005_028_lco.paa"
    paa = Paa(reader=StreamReader(path + "/" + file_name))
    paa.writeImage("test.png",1)
    exit()


if 0:
    file = "P:/DZ/worlds/chernarusplus/world/chernarusplus.wrp"
    o = OPRW(reader=StreamReader(file), img_dump=False)

if 1:
    file = "P:/DZ/structures/roads/parts/asf1_6_crosswalk.p3d"
    o = P3d(reader=StreamReader(file))

t = "{:.8f}".format(time.time()-start)
print(f"Time: { t }" )