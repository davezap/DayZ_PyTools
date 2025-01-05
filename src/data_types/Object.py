
class Object:
    def __init__(self, reader=None):
        if reader is not None:
            self.consume(reader)
        else:
            self.ObjectID = 0   # ulong 
            self.modelIndex = 0 # ulong  // into the [[#Models|models path name list]] (1 based)
            self.TransformMatrix = None # float   // standard directX RowFormat transform matrix
            # ulong 0x02   # That we will discard.

    def __str__(self):
        return f"ObjectID={self.ObjectID} modelIndex={self.modelIndex} TransformMatrix={self.TransformMatrix}"

    def consume(self, reader):
        self.ObjectID = reader.read_ulong()
        self.modelIndex = reader.read_ulong()
        self.TransformMatrix = reader.read_ndarray(( 4 * 3 * 4), dtype='<f', shape=(4,3))
        term = reader.read_ulong()
        if  term!= 0x02:
            raise Exception(f"{reader.get_offset_hex()} Unexpected object termination {hex(term[0])}??!" )
