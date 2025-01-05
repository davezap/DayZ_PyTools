################################################################################
# BI raP file type with support for
# OFP   https://community.bistudio.com/wiki/raP_File_Format_-_OFP?useskin=darkvector
# Elite https://community.bistudio.com/wiki/raP_File_Format_-_Elite?useskin=darkvector
# ArmA  https://community.bistudio.com/wiki/raP_File_Format_-_ArmA?useskin=darkvector
# 
# NOTE AuthenticationSignature (if available) is read but not checked, or generated.

# Standard file handler template. 
from datetime import datetime
import numpy as np

from src.io.StreamReader import StreamReader
from src.data_types.Generic import IndexedString

RAP_SIGNATURE = b'\0raP'
RAP_OFP_SIGNATURE = b'\x04\x00\x00'
RAP_DEBUG = False


def is_raP(b):
    return b[0:4] == RAP_SIGNATURE

def fmt_float(num):
    # More, probably meaningless, formatting only to make the output match Mikero's
    if abs(num) >  19000000:
        return np.format_float_scientific(num).replace(".e", "e")
    return str(np.float32(num))
    
class ClassBody:
    def __init__(self, reader:StreamReader = None, offset:int = -1):

        self.offset = offset
        self.inherited_classname:bytes = b''   # Asciiz // can be zero
        self.n_entries:int = 0                #CompressedInteger  // can be zero.
        self.class_entries:list[ClassEntry] = []
        
        if reader is not None:
            self.consume(reader)

    def to_cpp(self, srout, level):

        if srout.meta('version') == "ofp":
            if len(self.inherited_classname) > 0:
                srout += f": {self.inherited_classname}"

            #if self.n_entries > 0:
            tabs = ('\t'*level)
            if self.n_entries:       
                if level>=0: 
                    srout += f"{tabs}class {self.class_name}"
                    if self.inherited_classname:
                        srout += f": self.inherited_classname"
                    srout += f" {{\r\n"
                else:
                    srout += "\r\n"
            
                for a in range(self.n_entries):    
                    self.class_entries[a].to_cpp(srout, level+1)
                
                if level>=0: 
                    srout += f"{tabs}}};\r\n"
            else:
                srout += f"{tabs}class {self.class_name}"
                if self.inherited_classname:
                    srout += f": self.inherited_classname"
                srout += f" {{}};\r\n"
        else:

            if len(self.inherited_classname) > 0:
                srout += f": {self.inherited_classname}"

            if self.n_entries > 0:
                tabs = ('\t'*level)            
                if level>=0: 
                    srout += f"\r\n{tabs}{{\r\n"
                else:
                    srout += "\r\n"
            
                for a in range(self.n_entries):    
                    self.class_entries[a].to_cpp(srout, level+1)
                
                if level>=0: 
                    srout += f"{tabs}}};\r\n"
                
            else:
                srout += "{};\r\n"
        

        
        

    def consume(self, reader: StreamReader):
        if self.offset == -1:
            self.offset = reader.get_offset()
        else:
            reader.set_offset(self.offset)

        version = reader.meta("version")
        if version is None: reader.print_offset("P3d P3dModelInfo requires reader.meta('version')!", type="exception")

        if version == "ofp":
            self.class_name = reader.read_string_indexed()

        self.inherited_classname = reader.read_asciiz(cdn=False)
        self.n_entries = reader.read_uint_compressed()

        #p = reader.get_offset()
        for a in range(self.n_entries):
            
            type = reader.read_byte()
            if type == 0:
                if version == "ofp":
                    self.class_entries.append(ClassBody(reader))
                else:
                    self.class_entries.append(ClassEntry_RapClass(reader))
            elif type == 1:
                self.class_entries.append(ClassEntry_ValueEq(reader))
            elif type == 2:
                self.class_entries.append(ClassEntry_Array(reader))
            elif type == 3:
                self.class_entries.append(ClassEntry_ExternClass(reader))
            elif type == 4:
                self.class_entries.append(ClassEntry_DeleteClass(reader))
            elif type == 5:
                self.class_entries.append(ClassEntry_ArrayFlags(reader))
            else:
                reader.print_offset(f"Invalid entry type {type}!", type="exception")
        #reader.set_offset(p)

class ClassBodyOFP:
    def __init__(self, reader:StreamReader = None, offset:int = -1):

        self.offset = offset
        self.class_name = ""
        self.inherited_classname:bytes = ""
        self.n_entries:int = 0                #CompressedInteger  // can be zero.
        self.class_entries:list[ClassEntry] = []
        
        if reader is not None:
            self.consume(reader)

    def to_cpp(self, srout, level):

        if len(self.inherited_classname) > 0:
            srout += f": {self.inherited_classname}"

        #if self.n_entries > 0:
        tabs = ('\t'*level)
        if self.n_entries:       
            if level>=0: 
                srout += f"{tabs}class {self.class_name}"
                if self.inherited_classname:
                    srout += f": self.inherited_classname"
                srout += f" {{\r\n"
            else:
                srout += "\r\n"
        
            for a in range(self.n_entries):    
                self.class_entries[a].to_cpp(srout, level+1)
            
            if level>=0: 
                srout += f"{tabs}}};\r\n"
        else:
            srout += f"{tabs}class {self.class_name}"
            if self.inherited_classname:
                srout += f": self.inherited_classname"
            srout += f" {{}};\r\n"
              

    def consume(self, reader: StreamReader):
        if self.offset == -1:
            self.offset = reader.get_offset()
        else:
            reader.set_offset(self.offset)

        self.class_name = reader.read_string_indexed()
        self.inherited_classname = reader.read_asciiz(cdn=False)
        self.n_entries = reader.read_uint_compressed()
        if RAP_DEBUG: reader.print_offset(f"Class {self.class_name} Entries={self.n_entries}")
        #if self.n_entries > 300: exit()
        type = 0
        for a in range(self.n_entries):
            type = reader.read_byte()

            if type == 0:
                self.class_entries.append(ClassBodyOFP(reader))
            elif type == 1:
                self.class_entries.append(ClassEntry_ValueEq(reader))
            elif type == 2:
                self.class_entries.append(ClassEntry_Array(reader))
            else:
                reader.print_offset(f"Invalid entry type {type}!", type="exception")
        

class ClassEntry:
    def __init__(self, reader:StreamReader = None, offset:int = -1):
        self.type = -1   
        self.offset = offset
        self.name = b''
        if reader is not None:
             if self.offset == -1:
                self.offset = reader.get_offset()
        return        



class ClassEntry_RapClass(ClassEntry):  # EntryType 0: RapClass
    def __init__(self, reader:StreamReader = None, offset:int = -1):
        super().__init__(reader, offset)
        self.type = 0
        self.name = b''
        self.offset_to_classbody = -1
        self.class_body:ClassBody = None

        if reader is not None:
            self.consume(reader)

    def __str__(self):
        return(
            f"type = {self.type} "
            f"name = {self.name} "
            f"offset_to_classbody = {self.offset_to_classbody} "
            f"class_body = {self.class_body} "
        )
    
    def to_cpp(self, srout, level):
        tabs = ('\t'*level)
        srout += f"{tabs}class {self.name}"
        self.class_body.to_cpp(srout, level)
        #srout += f"{tabs}}};\r\n"
    
    def consume(self, reader: StreamReader):

        self.name = reader.read_asciiz(cdn=False)
        self.offset_to_classbody = reader.read_ulong()
        p = reader.get_offset()
        self.class_body = ClassBody(reader, offset=self.offset_to_classbody)
        reader.set_offset(p)

        


class ClassEntry_ValueEq(ClassEntry):   # EntryType 1: Value Eq
    def __init__(self, reader:StreamReader = None, offset:int = -1):
        super().__init__(reader, offset)
        self.type = 1
        self.sub_type = 0
        self.name = b''
        self.value = None

        if reader is not None:
            self.consume(reader)

    def __str__(self):
        return(
            f"type = {self.type} "
            f"sub_type = {self.sub_type} "
            f"name = {self.name} "
            f"value = {self.value} "
        )

    def to_cpp(self, srout, level):
        tabs = ('\t'*level)
        if self.sub_type==0:
            v = self.value.replace('"', '""') # escape quotes.
            srout += f"{tabs}{self.name} = \"{v}\";\r\n"
        elif self.sub_type==1:
            srout += f"{tabs}{self.name} = {fmt_float(self.value)};\r\n"            
        elif self.sub_type==2:
            srout += f"{tabs}{self.name} = {self.value};\r\n"
        else:
            Exception(f"Unsupported subtype {self.sub_type}", type="exception")


    def consume(self, reader: StreamReader):
        version = reader.meta('version')
        self.sub_type = reader.read_byte()
        if version == "ofp":
            self.name = reader.read_string_indexed()
        else:
            self.name = reader.read_asciiz(cdn=False)
        if self.sub_type==0: 
            if version == "ofp":
                self.value = reader.read_string_indexed()
            else:
                self.value = reader.read_asciiz(cdn=False)
        elif self.sub_type==1: self.value = reader.read_float()
        elif self.sub_type==2: self.value = reader.read_ulong()
        else:
            reader.print_offset(f"Unsupported subtype {self.sub_type}", type="exception")
        
        if RAP_DEBUG: reader.print_offset(f"  {self.name}={self.value}")



class ClassEntry_Array(ClassEntry): # EntryType 2: array[]
    def __init__(self, reader:StreamReader = None, offset:int = -1, recursive_array = False):
        super().__init__(reader, offset)

        if recursive_array:
             # Not a valid Entry type but I wanted to reuse this class for the
             # array element "3 recursive array  ArrayStruct;" given the only
             # difference is it has no name.
            self.type = 33
        else:
            self.type = 2
            self.name = b''

        self.n_elements:int = 0
        self.array_elements:list[ClassEntry] = []

        if reader is not None:
            self.consume(reader)
    
    def __str__(self):
        return(
            f"type = {self.type} "
            f"name = {self.name} "
            f"n_elements = {self.n_elements} "
        )
    
    def to_cpp(self, srout, level):
        tabs = ('\t'*level)
        if self.type ==2:
            srout += f"{tabs}{self.name}[] = {{"
        else:
            srout += f"{{"
        for a in range(self.n_elements):
            type,value = self.array_elements[a]
            if a>0: srout += ","
            if type==0: 
                if value.isnumeric():
                    srout += f'{value}'
                else:
                    srout += f'"{value}"'
            elif type==1: srout += f'{fmt_float(value)}'
            elif type==2: srout += f'{value}'
            elif type==3: value.to_cpp(srout, level)
            elif type==4: srout += f'{value}'
            else:
                srout.print_offset(f"Unsupported type {type}", type="exception")
        
        if self.type ==2:
            srout += f"}};\r\n"
        else:
            srout += f"}}"

    def consume(self, reader: StreamReader):
        version = reader.meta('version')
        if self.type==2:
            if version == "ofp":
                self.name = reader.read_string_indexed()
            else:    
                self.name = reader.read_asciiz(cdn=False)

        self.n_elements = reader.read_uint_compressed()
        #reader.print_offset(f"{self.type} {self.name} {self.offset} {self.n_elements}")
        
        for a in range(self.n_elements):
            type = reader.read_byte()
            if type==0: 
                if version == "ofp":
                    self.array_elements.append((0, reader.read_string_indexed()))
                else:
                    self.array_elements.append((0, reader.read_asciiz(cdn=False)))
            elif type==1: self.array_elements.append((1, reader.read_float()))
            elif type==2: self.array_elements.append((2, reader.read_long()))
            elif type==3: self.array_elements.append((3, ClassEntry_Array(reader, recursive_array=True)))
            elif type==4: self.array_elements.append((4, reader.read_asciiz(cdn=False)))
            else:
                reader.print_offset(f"Unsupported type {type}", type="exception")
        
        if RAP_DEBUG: reader.print_offset(self.array_elements)


class ClassEntry_ExternClass(ClassEntry):   # EntryType 3: ExternClass
    def __init__(self, reader:StreamReader = None, offset:int = -1):
        super().__init__(reader, offset)
        self.type = 3
        self.name = b''

        if reader is not None:
            self.consume(reader)

    def __str__(self):
        return(
            f"type = {self.type} "
            f"name = {self.name} "
        )

    def to_cpp(self, srout, level):
        tabs = ('\t'*level)
        srout += f"{tabs}class {self.name};\r\n"

    def consume(self, reader: StreamReader):

        self.name = reader.read_asciiz(cdn=False)
        if RAP_DEBUG: reader.print_offset(self.offset)


class ClassEntry_DeleteClass(ClassEntry):   # EntryType 4: Delete Class
    def __init__(self, reader:StreamReader = None, offset:int = -1):
        super().__init__(reader, offset)
        self.type = 4
        self.name = b''

        if reader is not None:
            self.consume(reader)

    def __str__(self):
        return(
            f"type = {self.type} "
            f"name = {self.name} "
        )
    
    def to_cpp(self, srout, level):
        tabs = ('\t'*level)
        srout += f"{tabs}DELETE?? class {self.name};\r\n"

    def consume(self, reader: StreamReader):

        self.name = reader.read_asciiz(cdn=False)
        if RAP_DEBUG: reader.print_offset(self.offset)


class ClassEntry_ArrayFlags(ClassEntry):   # Entry type 5: Array with flags
    def __init__(self, reader:StreamReader = None, offset:int = -1):
        super().__init__(reader, offset)
        self.type = 4
        self.name = b''

        if reader is not None:
            self.consume(reader)

    def __str__(self):
        return(
            f"type = {self.type} "
            f"name = {self.name} "
        )

    def to_cpp(self, srout, level):
        tabs = ('\t'*level)
        srout += f"{tabs}ArrayFlags?? {self.name};\r\n"
    
    def consume(self, reader: StreamReader):

        reader.print_offset("ClassEntry_ArrayFlags I DONT KNOW!", type="exception")
        self.name = reader.read_asciiz(cdn=False)
        if RAP_DEBUG: reader.print_offset(self.offset)

class Rap: # raP

    def __init__(self, reader = None):
        self.class_body = None
        self.n_enums = 0
        self.enums = {}
        self.version = "ARMA"
        self.signature = RAP_SIGNATURE
        self.authentication_signature = [0]*20   # byte[20] // XBOX ONLY NOT ARMA
        self.always_0 = 0   # ulong
        self.always_8 = 0   # ulong
        self.offset_to_enums = 0    #ulong
        if reader is not None:
            self.consume(reader)



    def save(self, file_fqn):
        return True
    
    def __str__(self):
        return(
            f"signature = {self.signature} "
            f"authentication_signature = {self.authentication_signature} "
            f"always_0 = {self.always_0} "
            f"always_8 = {self.always_8} "
            f"offset_to_enums = {self.offset_to_enums} "
            f"class_body = {self.class_body}"
        )
    
    def consume(self, reader: StreamReader):
        self.file_name = reader.file_name
        self.file_mtime = reader.file_mtime
        self.signature = reader.read_bytes(4)
        
        self.version = ""

        if not is_raP(self.signature):
            reader.print_offset(f"Nope, it's not a raP! {reader.file_name}", type="exception")
        
        reader.print_offset(f"It's a raP! {reader.file_name}")
        
        #Test if OFP
        if reader.peek_bytes(3) == RAP_OFP_SIGNATURE:
            self.version = reader.meta('version', 'ofp')
            reader.read_bytes(3)   # dispose.
            reader.print_offset("ofp")
            
            type = reader.read_byte()
            if type == 0:
                self.class_body = ClassBody(reader)
            else:
                reader.print_offset(f"First ofp packet type must be class but we got type={type}", type="exception")
                exit()
        else:
            self.always_0 = reader.read_ulong()
            self.always_8 = reader.read_ulong()
            if self.always_0 != 0 or self.always_8 != 8:
                reader.set_offset(len(RAP_SIGNATURE))
                self.authentication_signature = reader.read_bytes(20)
                self.always_0 = reader.read_ulong()
                self.always_8 = reader.read_ulong()
                self.version = reader.meta('version', 'elite')
            else:
                self.authentication_signature = b''
                self.version = reader.meta('version', 'arma')
            
                self.offset_to_enums = reader.read_ulong()
            if RAP_DEBUG: reader.print_offset(self)
            
            self.class_body = ClassBody(reader)
        
        # Read enums.
        self.enums = {}
        if self.version != "ofp": reader.set_offset(self.offset_to_enums)
        if RAP_DEBUG: reader.print_offset("ENUMS be here.")
        nenums = reader.read_ulong()
        while nenums:            
            for a in range(nenums):
                key = reader.read_asciiz(cdn=False)
                value = reader.read_int()
                self.enums[key] = value
            self.n_enums += nenums
            if reader.eof(): break
            nenums = reader.read_ulong()
            #print(reader.mm.size(), reader.mm.tell())
        if RAP_DEBUG: reader.print_offset(self.enums)

        return True
    
    def to_cpp(self)->StreamReader:
        # Make it a cpp already!
        srout = StreamReader(
            file_name=self.file_name.replace(".bin", ".cpp"),
            version=self.version
        )
        # we do enums first. 
        out = "////////////////////////////////////////////////////////////////////\r\n"
        out+= f"//DeRap: {self.file_name}\r\n"
        out+= f"//Produced from DaveZ's Python Tools 0.1\r\n"
        out+= f"//Special thanks to mikero\r\n"
        out+= f"//https://mikero.bytex.digital/Downloads\r\n"
        out+= f"//https://community.bistudio.com/wiki/raP_File_Format_-_Elite\r\n"
        out+= f"//'now' is {datetime.now().strftime('%a %b %d %H:%M:%S %Y')} : 'file' last modified on {self.file_mtime.strftime('%a %b %d %H:%M:%S %Y')}\r\n"
        out+= f"////////////////////////////////////////////////////////////////////\r\n"
        out += f"\r\n#define _{self.version}_\r\n"
        if self.version == "ofp": out += "\r\n//class  {"
        if self.n_enums:
            out += f"\r\n//({self.n_enums} Enums)\r\nenum {{"
            for k,v in self.enums.items():
                out+=f"\r\n\t{k} = {v},"
            out = out[:-1] + "\r\n};\r\n"

        srout += out
        self.class_body.to_cpp(srout,-1)
        if self.version == "ofp": srout += "//};\r\n"
        srout.set_offset(0)
        return srout