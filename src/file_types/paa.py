
from enum import Enum
import lzo
from io import FileIO
import numpy
import oiio
import tex2img
from src.io.StreamReader import StreamReader


class TypeOfPaX(Enum):
    
    DXT1 = 1
    DXT2 = 2
    DXT3 = 3
    DXT4 = 4
    DXT5 = 5
    RGBA4444 = 6
    RGBA5551 = 7
    RGBA8888 = 8
    GRAYwAlpha = 9

paa_magic_number_map = {
    0xff01: TypeOfPaX.DXT1,
    0xff02: TypeOfPaX.DXT2,
    0xff03: TypeOfPaX.DXT3,
    0xff04: TypeOfPaX.DXT4,
    0xff05: TypeOfPaX.DXT5,
    0x4444: TypeOfPaX.RGBA4444,
    0x1555: TypeOfPaX.RGBA5551,
    0x8888: TypeOfPaX.RGBA8888,
    0x8080: TypeOfPaX.GRAYwAlpha
}

def is_paa(b):
    return (b[1]<<8 | b[0]) in paa_magic_number_map

class Tagg:
    def __init__(self):
        
        self.signature = ""
        self.dataLength = 0
        self.data = b""

class Palette:
    def __init__(self):
        self.dataLength = 0
        self.data = b""

class MipMap:
    def __init__(self):
        self.width = 0
        self.height = 0
        self.dataLength = 0
        self.data = b""
        self.lzoCompressed = False
        self.dataOffset = 0

class Paa:

    def __init__(self, reader=None):
        self.magicNumber = 0
        self.typeOfPax = None
        self.taggs = []
        self.hasTransparency = False
        self.palette = Palette()
        self.mipMaps = []
        if reader is not None:
            self.consume(reader)


    def consume(self, reader: StreamReader):
        
        self.magicNumber = reader.read_ushort() #. struct.unpack('<H', self.read_bytes(self.is_, 2))[0]

   
        if self.magicNumber not in paa_magic_number_map:
            raise RuntimeError("Invalid file/magic number")
        
        self.typeOfPax = paa_magic_number_map[self.magicNumber]

        # Taggs

        
        while reader.peek_bytes(1)[0] != 0:
            tagg = Tagg()
            tagg.signature = reader.read_string(8)
            tagg.dataLength = reader.read_uint()
            tagg.data = reader.read_bytes(tagg.dataLength)
            self.taggs.append(tagg)
            #reader.print_offset(f"{tagg.signature} {str(reader.peek_bytes(1))}")

            if tagg.signature == "GGATGALF":
                self.hasTransparency = True
        #reader.print_offset(f"end tags")

        self.palette.dataLength = reader.read_ushort()
        #reader.print_offset(f"pal len {self.palette.dataLength}")
        if self.palette.dataLength > 0:
            #print("palette...")
            self.palette.data = reader.read_bytes(self.palette.dataLength)
        #reader.print_offset(f"pal end")
        #for tag in self.taggs:
            #print(tag.signature + ' ' + str(tag.dataLength) + ' ' + str(tag.data))

        #self.print_pos()
        # MipMaps
        while reader.peek_ushort() != 0:
            #reader.print_offset(f"loop start")
            #print("mippamp")
            mipmap = MipMap()
            mipmap.width = reader.read_ushort() 
            mipmap.height = reader.read_ushort()
            #reader.print_offset(f"{mipmap.width}, {mipmap.height}")

            mipmap.dataLength = reader.read_ushort_arma()
            mipmap.dataOffset = reader.get_offset()
            #print("Data Offset = " + hex(mipmap.dataOffset))
            mipmap.data = reader.read_bytes(mipmap.dataLength) 
            
            if mipmap.width & 0x8000:
                mipmap.width &= 0x7FFF
                mipmap.lzoCompressed = True
            else:
                mipmap.lzoCompressed = False
            
            #print(f"w={mipmap.width} h={mipmap.height} len={mipmap.dataLength}")
            
            if mipmap.lzoCompressed:
                #print("lzoCompressed")
                expectedSize = mipmap.width * mipmap.height
                mipmap.data = lzo.decompress(mipmap.data, False, expectedSize, algorithm="LZO1X")
                mipmap.dataLength = len(mipmap.data)

            # decompress
            if self.typeOfPax == TypeOfPaX.DXT1:
                # https://pypi.org/project/tex2img/
                #print(len(mipmap.data))
                #print(mipmap.width, mipmap.height)
                uncompressed_data = tex2img.basisu_decompress(bytes(mipmap.data),mipmap.width, mipmap.height, 5 )
                mipmap.dataLength = len(uncompressed_data)
                mipmap.data = bytearray(uncompressed_data)
            elif self.typeOfPax == TypeOfPaX.DXT5:
                # https://pypi.org/project/tex2img/
                uncompressed_data = tex2img.basisu_decompress(bytes(mipmap.data),mipmap.width, mipmap.height, 6 )
                mipmap.dataLength = len(uncompressed_data)
                mipmap.data = bytearray(uncompressed_data)
            # TODO: other pax types
            
            self.mipMaps.append(mipmap)

        reader.read_bytes(2) # Skip the final two null bytes
        

    def writeImage(self, filename, level=0):
        if level > len(self.mipMaps):
            print("Error")
            return 

        width = self.mipMaps[level].width
        height = self.mipMaps[level].height
        out = oiio.ImageOutput.create (filename)
        spec = oiio.ImageSpec(width, height, 4, 'uint8')
        out.open(filename, spec)    
        out.write_image(numpy.array(self.mipMaps[level].data))
        out.close ()
