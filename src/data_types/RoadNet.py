from src.io.StreamReader import StreamReader
from src.data_types.Generic import *
from src.io.Raster import *

class RoadNets():
    def __init__(self, size:XYPair, SizeOfRoadNets, reader=None):
        self._size = size
        self.inets = size.x * size.y
        self.SizeOfRoadNets = SizeOfRoadNets       
                
        if reader is not None: 
            self.nets = []
            self.consume(reader)
        else:
            self.nets = [RoadNet()]*self.inets

    def size(self):
        return self._size

    def count_road_nets(self):
        cnt = 0
        for rn in range(0,self.inets):
            if self.nets[rn].nRoadParts > 0: cnt+=1
        return cnt

    def count_road_parts(self):
        cnt = 0
        for rn in range(0,self.inets):
            cnt+=self.nets[rn].nRoadParts
        return cnt


    def to_csv(self):
        sr = StreamReader()
        mx = 0
        my = 0
        from PIL import Image, ImageDraw
        img = Image.new("RGB", (15360, 15360)) 
        img1 = ImageDraw.Draw(img)   

        flags = {}

        for rn in range(0,self.inets):
            if self.nets[rn].nRoadParts > 0:
                
                for rp in self.nets[rn].RoadParts:
                    ln = f"{rn}, {self.nets[rn].nRoadParts}, "
                    ln += " rp=("
                    ln += f"{(int.from_bytes(rp.Flags)):#0{22}x}, "
                    ln += f"{(int.from_bytes(rp.MoreFlags)):#0{(4 * rp.nRoadPositions)+2}x}, "
                    ln += rp.P3DModel + ", "
                    ln += str(rp.nRoadPositions) + ", "

                    key = f"{(int.from_bytes(rp.Flags)):#0{22}x},{(int.from_bytes(rp.MoreFlags)):#0{(4 * rp.nRoadPositions)+2}x},{rp.P3DModel}"
                    if key in flags: 
                        flags[key]+=1
                    else:
                        flags[key]=1
                    cords = []
                    for p in rp.RoadPositions:
                        #ln += f"{fmt_float(p[0])},{fmt_float(p[1])},{fmt_float(p[2])}, "
                        if p[0].item() > mx: mx = p[0].item()
                        if p[2].item() > my: my = p[2].item()
                        cords.append((p[0].item(), p[2].item()))
                    #print(cords)
                    if len(cords)==1:
                        img1.point(cords[0], fill ="green", width = 20)
                    elif len(cords)>1:
                        n = 0
                        r=0xa0
                        g=0xa0
                        b=0xa0
                        #if n < 2 * rp.nRoadPositions: r = int(rp.MoreFlags[n])
                        #if n+1 < 2 * rp.nRoadPositions: g = int(rp.MoreFlags[n+1])
                        #if n+2 < 2 * rp.nRoadPositions: b = int(rp.MoreFlags[n+2])
                        img1.line(cords, fill =(r,g,b), width = 5)
                    ln += ")"
                #ln += "\n\r"
                    #print(ln)

        if 0:
            #print(flags)
            print(len(flags))
            f = open("output/oprw/road_flags.csv", "wt")
            for k,v in flags.items():
                f.write(k + ','+ str(v) +'\n')
                #print(k,v)
            f.close()

        SaveImg(img, "output/oprw/RoadNetPreview")
        print(mx,my)
                #sr.write(f"\n\r")
            
        return sr
    
    def consume(self, reader):
        for rn in range(0,self.inets):
            self.nets.append(RoadNet(reader = reader))
        self.to_csv()

class RoadNet:
    def __init__(self, reader = None, nRoadParts=0):
        if reader is not None: 
            self.consume(reader)
        else:
            self.nRoadParts = nRoadParts #ulong // Zero or More... 
            self.RoadParts = []  #RoadPart
        

    def __str__(self):
        return f"nRoadParts={self.nRoadParts} len(RoadParts)={len(self.RoadParts)}"

    def consume(self, reader):
        self.nRoadParts = reader.read_ulong()
        self.RoadParts =[]
        for rnp in range(0,self.nRoadParts):
            self.RoadParts.append(RoadPart(reader = reader))

class RoadPart:
    def __init__(self, reader = None, nRoadPositions = 0):
        if reader is not None: 
            self.consume(reader)
        else:
            self.nRoadPositions = nRoadPositions # ushort// at least 1? sometimes 0
            self.RoadPositions = []   #	XYZTriplet RoadPositions[nRoadPositions];
            self.Flags = []  # byte
            # if WrpType==24
            self.MoreFlags = []  # byte      MoreFlags[nRoadPositions];
            self.P3DModel = ""   #	Asciiz     P3DModel;
            self.XYZTransform = [] # We reuse XYZTriplet, but was writen as	XYZTransform Transform[4]; // t
    def __str__(self):
        return f"nRoadPositions={self.nRoadPositions} len(RoadPositions)={len(self.RoadPositions)} P3DModel={self.P3DModel}"

    def dump(self):
        print(self.nRoadPositions)
        print(self.RoadPositions[0])
        print(self.RoadPositions[1])
        print(self.Flags)
        print(self.MoreFlags)
        print(self.P3DModel)
        print(self.XYZTransform)

    def consume(self, reader):
        self.RoadPositions = []
        #reader.print_offset("roadpart")
        self.nRoadPositions = reader.read_ushort()
        for rps in range(0,self.nRoadPositions):
            self.RoadPositions.append(reader.read_ndarray(( 3 * 4), dtype='<f', shape=(3,)))
            
        #reader.print_offset("")
        self.Flags = reader.read_bytes(10)
        self.MoreFlags = reader.read_bytes( 2 * self.nRoadPositions)
        self.P3DModel = reader.read_asciiz(cdn=False)
        self.XYZTransform = reader.read_ndarray(( 4 * 3 * 4), dtype='<f', shape=(3,4))

        if self.nRoadPositions > 4:
            # this would be new.
            roadpart.dump()
            roadpart = self.RoadParts[-2]
            roadpart.dump()
            raise Exception(f"That's too many RoadPositions {self.nRoadPositions}")
