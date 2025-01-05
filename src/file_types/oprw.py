
# https://community.bistudio.com/wiki/BIS_File_Formats#Island_File_Formats

# OFP WRP File Formats
#   4WVR File Format
#   https://community.bistudio.com/wiki/Wrp_File_Format_-_4WVR
#
#   OPRW v2 & v3 File Format
#   https://community.bistudio.com/wiki/Wrp_File_Format_-_OPRW2_%26_3

# ArmA WRP File Formats
#   8WVR File Format Editable 
#   https://community.bistudio.com/wiki/Wrp_File_Format_-_8WVR
#
#   OPRW v17,18,20 File Format Binarised output
#   https://community.bistudio.com/wiki/Wrp_File_Format_-_OPRWv17_to_24

# https://community.bistudio.com/wiki/Generic_FileFormat_Data_Types
# https://docs.python.org/3/library/struct.html

import numpy as np
import math
from src.io.Raster import *
from src.data_types.MapInfo import MapInfo
from src.data_types.RoadNet import RoadNets, RoadNet
from src.data_types.GridBlock import GridBlock
from src.data_types.Object import Object
from src.data_types.ClassedModel import ClassedModel
from src.data_types.WrpHeader import WrpHeader


class OPRW:


    def __init__(self, img_dump=False, reader=None):
        self.Header = ""
        self.img_dump = img_dump
        if reader is not None:
            self.consume(reader)
        

 
    
    def write(self):
        #todo.
        #lol
        return


    def consume(self, reader):

        #reader.set_offset(0x1127A32)
        #a = reader.read_asciiz_array(100)
        #print(a)
        #exit()

        print("decoding ...")
        
        #self.magicNumber = struct.unpack('<H', reader.read_bytes( 2))[0]
        
        ########################################################
        # @0x00 WrpHeader     Header;
        reader.print_offset("WrpHeader Header ...", type="heading")
        
        header = WrpHeader(reader = reader)
        print(header)
        self.header = header
        

        # Bits 0-2 are ground (0x0), coast (0x1), beach (0x2) and sea (0x3). Bit 4 indicates road/airstrip.
        # Chernarus = 225 km²
        # heightmap 2048x2048 
        # 2048 heightmap grid
        # 7.5 meter cell size
        # = 15360x15360 meters

        ########################################################
        # @ 0x24 -  ushort GridBlock_CellEnv[MapSize]
        reader.print_offset("ushort GridBlock_CellEnv[MapSize] ...", type="heading")
        self.cellenv = GridBlock(header.MapSize, 2, CorrectSize=2048, reader = reader)
        if self.img_dump: Grid2Img(self.cellenv, "output/oprw/CellEnv")

        ########################################################
        # @ 0x1afbd -  byte GridBlock_CfgEnvSounds[MapSize]
        reader.print_offset("byte GridBlock_CfgEnvSounds[MapSize] ...", type="heading")
        self.CfgEnvSounds = GridBlock(header.MapSize, 1, debug=True, reader=reader)
        if self.img_dump: Grid2Img(self.CfgEnvSounds, "output/oprw/CfgEnvSounds")
        
        
        ########################################################
        # @0x2859c - ulong       nPeaks;
        # @0x285A0 - XYZTriplet    PeakPositions[nPeaks];
        #reader.set_offset(0x2859c)
        reader.print_offset("XYZTriplet PeakPositions[nPeaks] ...", type="heading")
        self.nPeaks = reader.read_ulong()
        print("nPeaks=", self.nPeaks)
        self.Peeks = reader.read_float_array(self.nPeaks * 3, 3)
        print("first", self.Peeks[0][0], self.Peeks[0][1], self.Peeks[0][2])
        print("last", self.Peeks[-1][0], self.Peeks[-1][1], self.Peeks[-1][2])
        

        ########################################################
        # @ 0x35BC0 - ushort        GridBlock_RvmatLayerIndex[LayerSize];
        reader.print_offset("ushort GridBlock_RvmatLayerIndex[LayerSize] ...", type="heading")
        self.RvmatLayerIndex = GridBlock(header.LayerSize, 2, reader=reader) # , CorrectSize=2048
        if self.img_dump: Grid2Img(self.RvmatLayerIndex, "output/oprw/RvmatLayerIndex")
        

        ########################################################
        # @0x50a61 - if !Elite
        #   if ArmaOne
        #       ushort      RandomClutter[LayerSize];   //compressed.
        # else
        #       bytes       RandomClutter[MapSize];    //compressed
        #reader.set_offset(0x50A61)  
        reader.print_offset("bytes RandomClutter[MapSize];  //compressed", type="heading")
        #LZO blocks seem to consitantly start with "\x02\x00\x00\x00\x00\x00\x20\x00\x00\x00\x00\x00"
        # end finish with 11 00 00
        #self.lzo_search(self.header.iMapSize, 0x50A61, 0x50A61, range(0, 1), range(1,1000000))
        #Algo LZO1X @0x50a61 - 0x54aad length 16461 bytes  (si 0 ei 16461).
        #Out data length = 4194304 OK
        data2 = reader.read_lzo_decompress(16461, self.header.iMapSize)
        self.RandomClutter = np.ndarray(buffer=data2, dtype='<B', shape=(2048*2048,))
        if self.img_dump: Grid2Imgxy(self.RandomClutter, 2048, 2048, "output/oprw/RandomClutter", colour="gs")


        ########################################################
        # @0x1C177D - bytes         CompressedBytes1[MapSize];    //compressed
        reader.print_offset("bytes CompressedBytes1[MapSize];    //compressed ...", type="heading")
        #self.lzo_search(self.header.iMapSize, 0x54aae, 0x1C1770, range(0, 1), range(1,1000000))
        #Algo LZO1X @0x54aae - 0x1c177d length 1494224 bytes  (si 0 ei 14).
        #Out data length = 4194304 OK
        data2 = reader.read_lzo_decompress(1494224, self.header.iMapSize)
        self.CompressedBytes1 = np.ndarray(buffer=data2, dtype='<B', shape=(2048*2048,))
        if self.img_dump: Grid2Imgxy(self.CompressedBytes1, 2048, 2048, "output/oprw/CompressedBytes1", colour="gs")
        

        ########################################################
        # @ 0x1C177E -  float       Elevation[MapSize];     //compressed
        #self.lzo_search(self.header.iMapSize*4, 0x1C177E, 0x1127A2B, range(-5, 5), range(0,100))
        #reader.set_offset(0x1C177E)   
        reader.print_offset("float Elevation[MapSize]; //compressed ...", type="heading")
        #def read_lzo(self, ):
        data2 = reader.read_lzo_decompress(16147120, self.header.iMapSize*4)
        self.Elevation = np.ndarray(buffer=data2, dtype='<f', shape=(2048*2048,))
        if self.img_dump: Grid2Imgxy(self.Elevation, 2048, 2048, "output/oprw/Elevation")


        ########################################################
        # @0x1127A30 - ulong         nRvmats;     == This is 0x0000 in my file.
        # @0x1127A34 - Texture       Textures[nRvmats];  == "dz\worlds\chernarusplus\data\layers\p_000-000_l01_l03_l04_n_l10.rvmat" 0x0000 "..." 0x0000
        reader.print_offset("ulong nRvmats; ...", type="heading")
        self.nRvmats = reader.read_ulong()
        reader.print_offset("Texture Textures[nRvmats]; ...", type="heading")
        print("nRvmats=", self.nRvmats)
        #data = reader.read_bytes( self.nPeaks * 3 * 4) #8388608
        self.Textures = reader.read_asciiz_array(self.nRvmats)

        #self.Textures = []
        #for i in range(0,self.nRvmats):
        #    self.Textures.append(reader.read_asciiz(self.nRvmats))
        #print(self.Textures[0])
        #print(self.Textures[-2])
        #print(self.Textures[-1])
        reader.print_offset(f"read rvmats = {len(self.Textures)}")
        #exit()

        ########################################################
        # @0x11A6AB0 - ulong         nModels;
        # @0x11A6AB3 - asciiz        modelPaths[nModels]; == "dz\plants\tree\t_betulapendula_1fb.p3d" 0x00 "..." 0x00
        reader.print_offset("ulong nModels; ...", type="heading")
        self.nModels = reader.read_ulong()
        reader.print_offset("asciiz modelPaths[nModels]; ...", type="heading")
        print("nModels=", self.nModels)
        self.modelPaths = reader.read_asciiz_array(self.nModels, cdn=False)
        print(self.modelPaths[-1])
        reader.print_offset(f"read modelPaths = {len(self.modelPaths)}")


        ########################################################
        # @0x11C254D - ulong         nClassedModels;
        # @0x11C2551 - ClassedModel  Models[nClassedModels];          //"Land_Hangar\0" : "ca\buildings\Hangar.p3d\0"
        reader.print_offset("ulong nClassedModels; ...", type="heading")
        self.nClassedModels = reader.read_ulong()
        print("nClassedModels=", self.nClassedModels)
        reader.print_offset("ClassedModel Models[nClassedModels]; ...", type="heading")
        self.Models = []
        for a in range(0,self.nClassedModels):
            self.Models.append(ClassedModel(reader=reader))

        #print("read modelPaths = ", len(self.modelPaths))
        #reader.print_offset("ulong nClassedModels; ...")
        #print(self.Models[0])
        #print("")
        #print(self.Models[-1])

        ########################################################
        # @0x135F205 - ushort        GridBlock_UnknownGrid3[MapSize];
        reader.print_offset("ushort GridBlock_UnknownGrid3[MapSize]; ...", type="heading")
        self.UnknownGrid3 = GridBlock(header.MapSize, 2, reader=reader) # , CorrectSize=2048
        if self.img_dump: Grid2Img(self.UnknownGrid3, "output/oprw/GridBlock_UnknownGrid3")
        reader.print_offset("ushort GridBlock_UnknownGrid3[MapSize]; ...")

        ########################################################
        # @0x01393a30 - ulong         SizeOfObjects;                   //in bytes
        reader.print_offset("ulong SizeOfObjects; ...", type="heading")
        self.SizeOfObjects = reader.read_ulong()
        print("SizeOfObjects=", self.SizeOfObjects)


        ########################################################
        # @0x01393a34 -  ushort         GridBlock_UnknownGrid4[MapSize]
        reader.print_offset("ushort GridBlock_UnknownGrid4[MapSize]; ...", type="heading")
        self.UnknownGrid4 = GridBlock(header.MapSize, 2, reader=reader) # , CorrectSize=2048
        if self.img_dump: Grid2Img(self.UnknownGrid4, "output/oprw/UnknownGrid4")
        reader.print_offset("ushort UnknownGrid4[MapSize]; ...")

        
        ########################################################
        # @0x013c825f - ulong         SizeOfMapInfo;                   //in bytes
        reader.print_offset("ulong SizeOfMapInfo; ...", type="heading")
        self.SizeOfMapInfo = reader.read_ulong()
        print("SizeOfMapInfo=", self.SizeOfMapInfo)

            
        ########################################################
        # @0x13C8263 - byte          CompressedBytes2[LayerSize];     // seems to be connected to roads, runways and special grounds
        #reader.set_offset(0x13C8263)  
        reader.print_offset("byte CompressedBytes2[LayerSize]; ...", type="heading")
        data2 = reader.read_lzo_decompress(24154, self.header.iMapSize)
        self.CompressedBytes2 = np.ndarray(buffer=data2, dtype='<b', shape=(256*256,))
        if self.img_dump: Grid2Imgxy(self.CompressedBytes2, 256, 256, "output/oprw/CompressedBytes2", colour="gs")
        
        ########################################################
        # @0x13ce0bd - byte          CompressedBytes3[LayerSize];     // seems to be connected to roads, runways and special grounds
        # Algo LZO1X @0x13ce0bd - 0x13d2109 length 16461 bytes  (si 0 ei 16461).
        #reader.set_offset(0x13ce0bd)
        reader.print_offset("byte CompressedBytes3[LayerSize]; ...", type="heading")      
        data2 = reader.read_lzo_decompress(16461, self.header.iMapSize)     
        self.CompressedBytes3 = np.ndarray(buffer=data2, dtype='<b', shape=(2048*2048,))
        if self.img_dump: Grid2Imgxy(self.CompressedBytes3, 2048, 2048, "output/oprw/CompressedBytes3", colour="gs")
        reader.print_offset("byte CompressedBytes3[LayerSize]; ...")
        
        
        ########################################################
        # @0x13d210a -  ulong         maxObjectID;
        reader.print_offset("ulong maxObjectID; ...", type="heading")
        self.maxObjectID = reader.read_ulong()
        print("maxObjectID=", self.maxObjectID)
        

        ########################################################
        # @0x13D210E - ulong         SizeOfRoadNets;                  //in bytes
        # @0x13D2112 - RoadNet       RoadNets[SizeOfRoadNets];
        reader.print_offset("ulong SizeOfRoadNets; ...", type="heading")
        self.SizeOfRoadNets = reader.read_ulong()
        print("SizeOfRoadNets=", self.SizeOfRoadNets)

        reader.print_offset("RoadNet RoadNets[SizeOfRoadNets]; ...", type="heading")
        #data = reader.read_bytes( self.nPeaks * 3 * 4) #8388608
        self.RoadNets = RoadNets(self.header.LayerSize, self.SizeOfRoadNets, reader)
        print(f"RoadNets - size={self.RoadNets.size()}, nets={self.RoadNets.count_road_nets()}, parts={self.RoadNets.count_road_parts()}")
        exit()
        #for rn in range(0,256*256):
        #    self.RoadNets.append(RoadNet(reader = reader))


        ########################################################
        # @0x01A4AD11 - Object        Objects[SizeOfObjects/SizeOfObject]; // SizeOfObject ==60
        reader.print_offset("Object Objects[SizeOfObjects/SizeOfObject]; ...", type="heading")
        SizeOfObject = 60
        self.nObjects = self.SizeOfObjects / SizeOfObject
        if math.floor(self.nObjects) != self.nObjects:
            raise Exception("That's not right? self.SizeOfObjects / SizeOfObject = ", self.SizeOfObjects, SizeOfObject)

        self.nObjects = int(self.nObjects)
        print("Objects =", self.nObjects)
        self.Objects = []
        for a in range(0,self.nObjects):
            self.Objects.append(Object(reader = reader))


        ########################################################
        # @0x0C44AEA1 -  MapInfo       MapInfos[...];
        # // Mapinfo, when it exists, extends to end of file
        #reader.set_offset(0x0C44AEA1)
        reader.print_offset("MapInfo MapInfos[...]; ...", type="heading")
        self.MapInfos = []

        while(1):
            mapinfo = MapInfo(reader = reader)
            if mapinfo.MapType==-1: 
                break #EOF
            self.MapInfos.append(mapinfo)



        reader.print_offset(f"FIN.", type="heading")
        


 
    

