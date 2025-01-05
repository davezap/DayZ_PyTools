class MapInfo:
    def __init__(self, infoType=None, reader=None):
        self.infoType = -1
        self.MapType = 0
        self.MapData = None
        if infoType is not None:
            self.infoType = infoType    # ulong
        elif reader is not None:
            try:
                self.infoType = reader.read_ulong()
                #reader.print_offset(self.infoType, d=-4)
            except Exception as ex:
                self.infoType = -1
                self.MapType = -1
                return
        else:
            return
        
        self.MapType = self.infoType_to_MapType(self.infoType)

        if self.MapType is None:
            raise Exception("Invalid infoType " + str(self.infoType) + " ??!")
 
        if self.MapType == 1: self.MapData = MapType1(reader = reader)
        elif self.MapType == 2: self.MapData = MapType2(reader = reader)
        elif self.MapType == 3: self.MapData = MapType3(reader = reader)
        elif self.MapType == 4: self.MapData = MapType4(reader = reader)
        elif self.MapType == 5: self.MapData = MapType5(reader = reader)
        elif self.MapType == 35: self.MapData = MapType35(reader = reader)
        else: raise Exception(f"Unsupported MapType {self.MapType}")
        #if self.MapType == 1: self.MapData = MapType1(fp := fp)


    def infoType_to_MapType(self, infoType):
        # found 36, 38, 39, 40 to be same other MapType1
        # found 41, 42, 43 to be same other MapType4
        if infoType in [0,1,2,10,11,13,14,15,16,17,22,23,26,27,30,  36, 38, 39, 40]: return 1 # MapType1
        elif infoType in [24,31,32]: return 2 # MapType2
        elif infoType in [25,33]: return 3 # MapType3;
        elif infoType in [3,4,8,9,18,19,20,21,28,29,  41, 42, 43]: return 4 # MapType4;
        elif infoType in [34]: return 5 # MapType5;
        elif infoType in [35]: return 35 # MapType35; 
        return None

class MapType1: # 12 bytes
    def __init__(self, reader=None):
        self.ObjectId = 0   # ulong
        self.x = 0.0    # float
        self.y = 0.0    # float
        if reader is not None: self.consume(reader)

    def consume(self, reader):
        self.ObjectId = reader.read_ulong()
        self.x = reader.read_float()
        self.z = reader.read_float()

class MapType2: # 36 bytes
    def __init__(self, reader=None):
        self.ObjectId = 0   # ulong
        self.bounds = None    # float[4][2]
        if reader is not None: self.consume(reader)

    def consume(self, reader):
        self.ObjectId = reader.read_ulong()
        self.bounds = reader.read_ndarray(4 * 2 * 4, dtype='<f', shape=(4,2))

class MapType3: # 24 bytes
    def __init__(self, reader=None):
        self.color = 0   # ulong // maybe. or default ind of 0xFFFFFFF generally
        self.indicator = 0    # ulong  // typically 0x01010000
        self.floaters = [0,0,0,0]  #float[4] // typically 0.5,1.0.1,5.3.0 always 'integers'
        if reader is not None: self.consume(reader)

    def consume(self, reader):
        self.color = reader.read_ulong()
        self.indicator = reader.read_ulong()
        self.floaters = reader.read_ndarray(( 4 * 4 ), dtype='<f', shape=(4,))

class MapType4: # 40 bytes
    def __init__(self, reader=None):
        self.ObjectId = 0   # ulong
        self.bounds = None    # float[4][2]
        self.color = 0  # byte[4] // rgba
        if reader is not None: self.consume(reader)

    def consume(self, reader):
        self.ObjectId = reader.read_ulong()
        self.bounds = reader.read_ndarray(( 4 * 2 * 4 ), dtype='<f', shape=(4,2))
        self.color = reader.read_bytes(4)

class MapType5: # 20 bytes
    def __init__(self, reader=None):
        self.ObjectId = 0   # ulong
        self.line = None    # float[3][2]
        if reader is not None: self.consume(reader)

    def consume(self, reader):
        self.ObjectId = reader.read_ulong()
        self.line = reader.read_ndarray(( 2 * 2 * 4 ), dtype='<f', shape=(2,2))


class MapType35: # 29 bytes // found in chernarus
    def __init__(self, reader=None):
        self.ObjectId = 0   # ulong
        self.line = None    # float[3][2]
        self.unknown = 0  #byte
        if reader is not None: self.consume(reader)

    def consume(self, reader):
        self.ObjectId = reader.read_ulong()
        self.line = reader.read_ndarray(( 3 * 2 * 4 ), dtype='<f', shape=(3,2))
        self.unknown = reader.read_byte()
