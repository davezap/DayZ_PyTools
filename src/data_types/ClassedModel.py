from src.data_types.Generic import XYZTriplet

class ClassedModel:
    def __init__(self, reader=None, class_name="", model_path="", position=XYZTriplet(0), unknown1=0, unknown2=0):
        if reader is not None: 
            self.consume(reader)
        else:
            self.class_name = class_name
            self.model_path = model_path
            self.Position = position
            self.unknown1 = unknown1
            self.unknown2 = unknown2
        
    def __str__(self):
        return f"{self.class_name}, {self.model_path}, {self.Position.x}, {self.Position.y}, {self.Position.z}, {self.unknown1}, {self.unknown2}"

    def consume(self, reader):
        self.class_name = reader.read_asciiz()
        self.model_path = reader.read_asciiz()
        self.Position:XYZTriplet = reader.read_xyz_triplet()
        self.unknown1 = reader.read_ulong()
        self.unknown2 = reader.read_ulong()