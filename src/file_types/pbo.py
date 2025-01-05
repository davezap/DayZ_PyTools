# URL https://community.bistudio.com/wiki/PBO_File_Format?useskin=darkvector
# ifa: A World War2 mod hard wired to only accept ifa files.
# ebo: initially used by VBS, then by Arma, to encrypt the contents of a pbo and call it a different extension.
# xbo: Used by vbsLite encrypt with a different algorithm to above.
# the encryption method used for vbslite UK and vbslite US is different.
import os
from src.io.StreamReader import *
from src.file_types.Rap import *
from src.file_types.paa import *

PBO_DEBUG = False

class Pbo_Header_Entry:
    def __init__(self, reader = None, type = 0):
        if reader is not None:
            self.consume(reader)
        else:
            self.file_name = ""
            # Asciiz // a zero terminated string defining the path and file_name,
            #		 // ''relative to the name of this .pbo'' or it is prefix.
            #		 // Zero length filenames ('\0') indicate the first (optional), or last (non optional) entry in header.
            #		 // Other fields in the last entry are filled by zero bytes.
            if type == 0:
                self.values: Pbo_Header_Entry = {}
                self.mime_type = [0,0,0,0]
                # char[4] // 0x56657273 'Vers' properties entry (only first entry if at all)
                #         // 0x43707273 'Cprs' compressed entry
                #         // 0x456e6372 'Enco' comressed (vbs)
                #         // 0x00000000 dummy last header entry
            else:
                self.packing_method = 0

            self.original_size = 0
            # ulong // Uncompressed: 0 or same value as the DataSize
            #       // compressed: Size of file after unpacking. 
            #       // This value is needed for byte boundary unpacking
            #       // since unpacking itself can lead to bleeding of up
            #       // to 7 extra bytes.

            self.reserved = 0
            # ulong		// not actually used, always zeros (but vbs = encryption data)

            self.offset = 0
            ## this is for our computed offset not part of the PBO.

            self.timestamp = 0
            # ulong	// meant to be the unix filetime of Jan 1 1970 +, but often 0

            self.data_size = 0
            # ulong    // The size in the data block. 
            #          // This is also the file size when '''not''' packed

    def __str__(self):
        if self.type == 0:
            return (f"Header {self.type} file_name={str(self.file_name)}, "
                f"mime_type={hex(self.mime_type)}, "
                f"original_size={str(self.original_size)}, "
                f"offset={hex(self.offset)}, "
                f"timestamp={str(self.timestamp)}, "
                f"data_size={str(self.data_size)}")
        else:
            return (f"Header {self.type} file_name={str(self.file_name)}, "
                f"mime_type={hex(self.packing_method)}, "
                f"original_size={str(self.original_size)}, "
                f"offset={hex(self.offset)}, "
                f"timestamp={str(self.timestamp)}, "
                f"data_size={str(self.data_size)}")

    def consume(self, reader: StreamReader):
        self.file_name = reader.read_asciiz(cdn = False)
        if self.file_name == '':
            self.type = 0 #PboProperties
            self.mime_type = reader.read_ulong()
            self.original_size = reader.read_ulong()
            self.reserved = reader.read_ulong()
            self.offset = 0
            self.timestamp = reader.read_ulong()
            self.data_size = reader.read_ulong()
            self.values = {}
        else:
            self.type = 1 # FileEntry
            self.packing_method = reader.read_ulong()
            self.original_size = reader.read_ulong()
            self.reserved = reader.read_ulong()
            self.offset = 0
            self.timestamp = reader.read_ulong()
            self.data_size = reader.read_ulong()         

        return True

class Pbo:

    def __init__(self, reader = None):
        self.properties: Pbo_Header_Entry = None
        self.file_list = []
        if reader is not None:
            self.consume(reader)
            


    def consume(self, reader: StreamReader):
        offset_count = 0
        self.data_start = 0
        self.stream_reader = reader
        m = 0

        while 1:
            #reader.print_offset("reads")
            header = Pbo_Header_Entry(reader = reader)
            reader.print_offset(header.file_name)
            
            
            if header.file_name == '':
                if header.mime_type == 0x56657273: # // 'Vers' properties entry (only first entry if at all)
                    if self.properties is not None:
                        reader.print_offset(self.properties)
                        reader.print_offset("Properties already defined?!", type="exception")
                            
                    pairs = reader.read_asciiz_tonull()
                    if (len(pairs) % 2):
                        reader.print_offset(f"Uneven properties length={len(pairs)}!", type="error")
                    for a in range(0,len(pairs),2):
                        header.values[pairs[a].decode("utf-8")] = pairs[a+1].decode("utf-8")
                        
                        self.properties = header
                    
                    reader.print_offset(f"Properties {header.values}")
                elif header.mime_type == 0x43707273: # // 'Cprs' compressed entry
                    reader.print_offset("Cprs")

                elif header.mime_type == 0x456e6372: # // 'Enco' comressed (vbs)
                    reader.print_offset("Enco")
                elif header.mime_type == 0x00000000:
                    reader.print_offset("Data.Start")
                    self.data_start = reader.get_offset()
                    break
            else: # // dummy last header entry

                header.offset = offset_count
                self.file_list.append(header)
                offset_count += header.data_size
                #if "stringtable.csv" == header.file_name: 
                #    print(len(self.file_list)-1)
                #    print(self.file_list[len(self.file_list)-1])
                #    exit()
            #print(header)
            m += 1
        
        #reader.print_offset("end")
        print(hex(self.file_list[-1].offset) , hex(self.file_list[-1].data_size))
        self.check_offset = self.data_start + self.file_list[-1].offset + self.file_list[-1].data_size
        reader.set_offset(self.check_offset)
        self.check_data = reader.read_bytes(100)
        self.check_len = len(self.check_data)
        #reader.print_offset(f"{hex(self.check_offset)}, {self.check_data}, {self.check_len}")

        return True
    
    def get_files(self):
            for n in range(0, len(self.file_list)):
                file:Pbo_Header_Entry = self.file_list[n]
                print(file.original_size, file.packing_method, datetime.fromtimestamp(file.timestamp), file.file_name)


    def extract(self, destination = "output/pbo/"):
        reader = self.stream_reader
        base_path = [destination, reader.path.stem]
        if self.properties is not None:
            if "prefix" in self.properties.values:
                base_path.append(self.properties.values["prefix"])

        file:Pbo_Header_Entry = None

        n = 0
        for n in range(0, len(self.file_list)):
            file = self.file_list[n]


            offset = self.data_start + file.offset

            #print(file.file_name)
            if PBO_DEBUG: reader.print_offset(f"@hex(offset) len={file.data_size} {file.file_name}")
            #if file.data_size == 0: exit()
            sr = StreamReader(
                reader.mm[offset:offset+file.data_size],
                file_name=file.file_name,
                file_mtime=file.timestamp # reader.file_mtime
            )

            file_name = sr.file_name
            if is_raP(sr):
                #print("Its a raP") # https://www.youtube.com/watch?v=aR8qtxts1jY
                rap: Rap = Rap(sr)
                cpp_file = rap.to_cpp()
                cpp_file.save(base_path + [cpp_file.file_name])
                file_name = cpp_file.file_name
            elif ".paa" in file.file_name:
                if is_paa(sr):
                    paa: Paa = Paa(sr)
                    paa.writeImage(str(sr.fqn_to_path(base_path + [file.file_name.replace(".paa", ".png")])))

            elif file.packing_method !=0:
                reader.print_offset(f"A Strange new packing type? {file.packing_method}!", type="exception")
            else:
                sr.save(base_path + [file.file_name])
            
            print(f"{file_name}")
