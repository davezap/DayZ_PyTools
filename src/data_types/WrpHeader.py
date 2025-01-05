from src.io.StreamReader import StreamReader
from src.data_types.Generic import XYPair

class WrpHeader:
    def __init__(self, reader = None):
        if reader is not None:
            self.consume(reader)
        else:
            self.Filetype = "OPWR"   # char   // "OPWR"
            self.version = 0         # ulong  // 0x12 = 18
            self.notsure = ""        # Undocumented bytes? 0x30464e4500000000
            self.LayerSize = None    # XYPair // 256 x 256 (SaraLite), 128 x 128 (Intro)
            self.MapSize = None      # XYPair // 1024 x 1024 (SaraLite), 512 x 512 (Intro)
            self.LayerCellSize = 0.0 # float  // Layer cell size in meters (40m)

    def header_recompute(self):
        self.MapCellSize = self.LayerCellSize * self.LayerSize.x / self.MapSize.x
        self.iMapSize = self.MapSize.x * self.MapSize.y
        self.iLayerSize = self.LayerSize.x * self.LayerSize.y

    def __str__(self):
        return (f"Filetype:{self.Filetype} "
        f"version:{self.version} "
        f"LayerSize:{self.LayerSize.x, self.LayerSize.y} "
        f"MapSize:{self.MapSize.x, self.MapSize.y} "
        f"LayerCellSize:{self.LayerCellSize} "
        f"fin MapCellSize:{self.MapCellSize} "
        )

    def consume(self, reader: StreamReader):
        self.Filetype = reader.read_string( 4)
        self.version = reader.meta("version", reader.read_ulong())
        if self.version == 28:
            self.notsure = reader.read_bytes( 8)
        self.LayerSize = XYPair (
            reader.read_ulong(),  #@0x10
            reader.read_ulong()   #@0x14
        )
        self.MapSize = XYPair (
            reader.read_ulong(),  #@0x18
            reader.read_ulong()   #@0x1C
        )
        self.LayerCellSize = reader.read_float() #@0x20
        self.header_recompute()