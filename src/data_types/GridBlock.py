import math
import numpy as np
from src.data_types.Generic import XYPair

class GridBlock:
    def __init__(self, size = 0, typesize = 0, CorrectSize=0, reader=None, debug=False):
        self.size = size.x * size.y
        self.CellDimensions = size
        self.typesize = typesize
        self.data = None
        self.debug = debug
        self.ForceCorrectSize = CorrectSize
        self._wipe()
        if reader is not None: self.consume(reader)

    def _wipe(self):
        if self.typesize == 2:
            self.data = np.empty([self.size], dtype=np.uint16)
        elif self.typesize == 1:
            self.data = np.empty([self.size], dtype=np.uint16)
        else:
            print(f"unsupported typesize {self.typesize}")
            exit()

    def push(self, num):
        np.append(self.data, values=np.uint16(num))   # short	16 bit signed short (2 bytes)

    def gettype(self, num):
        return num >> 13
    def gettype2(self, num):
        return (num & 0x0007)
    
    def road(self, num):
        return (num & 8) >> 3

    def print(self):
        for a in range(0,100):
            v = self.data[a].item()
            print(a, "\t", "{:04x}".format(self.data[a]), "\t", self.gettype(v), "\t", self.gettype2(v), "\t", self.road(v))
    

    def consume(self, reader): # byte or ushort

        #sys.setrecursionlimit(5000)
        if self.debug: print("ReadPackedGrid...")

        IsPresent = reader.read_byte()
        #print(hex(IsPresent))
        if IsPresent==0x00:
            return 0 == reader.read_ulong()
        #elif IsPresent != 0x01:
            #return False

        BlockSize = XYPair(self.CorrectSize(self.CellDimensions)) # 
        print("CellDimentions, BlockSize", self.CellDimensions.x, self.CellDimensions.y, BlockSize.x, BlockSize.y)
        #exit()
        BlockOffset = XYPair(0)
        
        SnapOffset = reader.get_offset() # in case 1st Blocksize is too large
        
        try:
            if not self.RecursePacketRead(reader, BlockSize, BlockOffset):
                
                self._wipe()
                reader.set_offset(SnapOffset)
                reader.print_offset("")
                BlockSize = XYPair(BlockSize.x / 4, BlockSize.y / 4)

                if not self.RecursePacketRead(reader, BlockSize, BlockOffset):
                    return False
                
        except Exception as e:
            reader.print_offset("")
            print("Error", e)

        return True

    def CorrectSize(self, xy):
        print(f"CorrectSize {xy.x}")
        #if xy.x == 1024: return 2048
        if self.ForceCorrectSize != 0: return self.ForceCorrectSize

        #if xy.x == 2048: return 2048
        #print("I don't get this CorrectSize thing?")
        #exit()
        x = int(math.ceil( (math.log10(xy.x) / math.log10(2)) / 2 ))
        return int(math.pow(2, 2 * x ))


    def RecursePacketRead(self, reader, BlockSize, BlockOffset):


        #if Grid.debug: print(BlockSize.x, BlockSize.y)
        ThisBlockSize = XYPair(BlockSize.x / 4, BlockSize.y / 4) # 256..64..16..1
        #if Grid.debug: print(ThisBlockSize.x, ThisBlockSize.y)
        if ThisBlockSize.x == 0: return True
        ThisBlockOffset = XYPair(0)
        PacketFlag = reader.read_ushort()
        #if Grid.debug: 
            #print(PacketFlag)
            #exit()
        for BitCount in range(0,16):
            #if Grid.debug:
                #print(Grid.typesize)
                #exit()
            ThisBlockOffset.x = (BlockOffset.x +  (BitCount % 4) * ThisBlockSize.x * 2) # 0,1,2,3
            ThisBlockOffset.y = (BlockOffset.y + ((BitCount >> 2) * ThisBlockSize.y)) # 0,1,2,3
            #if Grid.debug: print(ThisBlockOffset.x, ThisBlockOffset.y)
            if isinstance(ThisBlockOffset.x, float) or isinstance(ThisBlockOffset.y, float):
                exit()
            if PacketFlag & 0x0001:
                if not self.RecursePacketRead(reader, ThisBlockSize, ThisBlockOffset): return False
            else:
                #if Grid.typesize == 1:
                #    A =  struct.unpack('<B', reader.read_bytes( 1))[0]
                #    B =  struct.unpack('<B', reader.read_bytes( 1))[0]
                    #if A > 0x00 and A < 0x83: A=0xF0
                    #if B > 0x00 and B < 0x83: B=0xF0
                #else:
                A =  reader.read_ushort()
                B =  reader.read_ushort()
                #print("AB", hex(A),hex(B))
                #exit()
                if A==0 and B==0:	
                    PacketFlag >>= 1
                    continue  # filler

                if ThisBlockOffset.x >= self.CellDimensions.x or ThisBlockOffset.y >= self.CellDimensions.y: 
                    print("CellDimensions, BlockOffset", self.CellDimensions.x, self.CellDimensions.y, ThisBlockOffset.x,ThisBlockOffset.y)
                    #exit()
                    return False
                
                #A1	A5	A9	A13	B1  ..........B13...................................
                #.................. b2 b3 b4
                #A4	A8	A12	A16	B4 ...........B16...............................


                for iy in range(0, ThisBlockSize.y):
                    for ix in range(0, ThisBlockSize.x):
                        OffsetAB=(((ThisBlockOffset.y + iy)*self.CellDimensions.x)+ThisBlockOffset.x + ix)
                        #print(ThisBlockOffset.y)
                        if OffsetAB >= self.data.size:
                            print(f"A overflow @ {OffsetAB}")
                            continue
                        
                        if OffsetAB+ThisBlockSize.x >= self.data.size:
                            print(f"blocksize {ThisBlockSize.x}, {ThisBlockSize.y}")
                            print(f"B overflow @ {OffsetAB}", self.data.size, ThisBlockOffset.y, iy, self.CellDimensions.x,ThisBlockOffset.x, ix)
                            continue

                        self.data[OffsetAB] = A
                        self.data[OffsetAB+ThisBlockSize.x] = B
                        #if this.debug: print(OffsetAB, A, B)
            PacketFlag >>= 1
    
        return True