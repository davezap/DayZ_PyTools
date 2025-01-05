import struct
import numpy as np
import lzo
import mmap 
import time 
from pathlib import Path
from enum import Enum
import math
import os
from datetime import datetime

from src.data_types.Generic import *

SR_MM_EXPAND_SIZE = 4000

class StreamReaderAccess(Enum):
    # COPY is READ/WRITE - But does not change the file, use must call 
    # StreamReader.save() to flush to file. 
    ACCESS_COPY = mmap.ACCESS_COPY  
    ACCESS_READ = mmap.ACCESS_READ  
    ACCESS_WRITE = mmap.ACCESS_WRITE

    def get(self, idx):
        return list(self)[idx].value

class StreamReader:
    # StreamReader provides file mapping via MMap, and a variety of 
    # convinence/life enhancing functions for navigating around binarry files, reading 
    # various basic data types read_bytes, read_ulong, reat_float, read_asciiz...
    # https://community.bistudio.com/wiki/Generic_FileFormat_Data_Types?useskin=darkvector
    # there are also decompresion algos like LZO and LZSS, and some methods
    # to assist in finding compressed blocks in a file.
    # A StreamReader is generally passed to vadious file_types classes for consumption.

    # Here are the various combinations and outcomes for the constructor.
    # #   file  file_data ACCESS file_exists  
    # 1.   Y               READ     yes       File is opened 'rb' and fully mapped ACCESS_READ or ACCESS_COPY
    # 2.   Y               READ     no        EXCEPTION: file not found error is raised. 
    # 3.   Y        Y      READ     yes       The file is first replaced with file_data, then as 1
    # 4.   Y        Y      READ     no        as 2
    # 5.            Y       dc      n/a       anonymous mmap of size len(file_data) populated with file_data with ACCESS_WRITE
    # 6.                    dc      n/a       map anonymous memory of size 0 with ACCESS_WRITE
    # 7.   Y        Y      WRITE    dc        file_data is writen to file then mmapped with ACCESS_WRITE
    # 8.   Y               WRITE    yes       File is opened 'r+b' and fully mapped ACCESS_WRITE
    # 9.   Y               WRITE    no        file is touched and then as 8

    # NOTE that the ACCESS method applies to the mmap and not nescisarrly the underlying file, as can be seen in 3.
    # NOTE For anontmous streas (where file was not given) user must manually call StreamReader.save() to flush to file.
    #      The mmap will then be attached to the file. 
    # Attempting to write to streams opened in READ mode will raise TypeError: mmap can't modify a readonly memory map.

    def __init__(self, file:str=None, file_data=None, access:StreamReaderAccess=StreamReaderAccess.ACCESS_READ, file_name="", file_mtime=None, version=""):
        self.data_len = 0
        self.allows_resize = (access == StreamReaderAccess.ACCESS_WRITE)
        self.fp = None            # File pointer
        self.fileno:int = -1
        self.mm:mmap.mmap = None    # mmap or bytearray 
        self.path:Path = None
        self.file_name = file_name  # This is virtual for anonymous mmaps to indicate the souce.
        self._meta = {
            version:version
        }
        if file_mtime is not None:
            if isinstance(file_mtime, int):
                self.file_mtime = datetime.fromtimestamp(file_mtime)
            else:
                self.file_mtime = file_mtime
        else:
            self.file_mtime = None
        self._access = access
        self.indexed_strings = {}   # if any, probably only relevent for raP'd OFP files.

        # This just allows user to pass file_date as single non-kw argument.
        if not isinstance(file, str) and file_data is None:
            file_data = file
            file = None

        if file is not None:
            self.path = self.fqn_to_path(file)
            fp = None
            if not self.path.exists():

                if access in [StreamReaderAccess.ACCESS_COPY, StreamReaderAccess.ACCESS_READ]:
                    # raises exception
                    self.print_offset(f"File not found '{file}'", type="exception", offset=0)

                # touch the file if it does not exist.
                fp = open(file, mode='wb')
                # sort of duplicate considering we raised exception for the other two access types above.
                # but this is probably safer if that ever changes.
                if self.allows_resize: fp.truncate(SR_MM_EXPAND_SIZE)              
                
            if file_data is not None:
                if fp is None: fp = open(file, mode='wb')
                fp.write(file_data)
                fp.flush()

            if fp is not None: fp.close()

            if self.file_mtime is None:
                self.file_mtime = datetime.fromtimestamp(self.path.stat().st_mtime)
            
            if access == StreamReaderAccess.ACCESS_WRITE:
                self.fp = open(file, mode='r+b')
            else:
                self.fp = open(file, mode='rb')           

            self.mm: mmap.mmap = mmap.mmap(self.fp.fileno(), 0, access=access.value)
            self.data_len = self.mm.size()
            self.mm.flush() # See note https://docs.python.org/3/library/mmap.html

        else:
            if file_data is not None and len(file_data):
                self.data_len = len(file_data)
                self.mm: mmap.mmap = mmap.mmap(-1, self.data_len, access=StreamReaderAccess.ACCESS_WRITE.value)
                self.mm.write(file_data)
                
            else:
                self.data_len = 0
                self.mm: mmap.mmap = mmap.mmap(-1, SR_MM_EXPAND_SIZE, access=StreamReaderAccess.ACCESS_WRITE.value)

            self._access = StreamReaderAccess.ACCESS_WRITE
            self.allows_resize = True
            self.mm.seek(0)
            if self.file_mtime is None:
                self.file_mtime = datetime.now()
        

    def __del__(self):
        self.close()

    def close(self):
        if self.mm is not None: 
            if not self.mm.closed:
                if self.data_len < self.mm.size() and self.allows_resize:
                    try:
                        self.mm.flush()
                        if self.data_len>0:
                            self.mm.resize(self.data_len)
                            self.mm.flush()
                    except Exception as ex:
                        print(ex)
                        print(self.mm, self.data_len, self.file_name, self.mm.size)
                self.mm.close()
        if self.fp is not None:
            self.fp.close()


    def __getitem__(self, x):
        return self.mm[x]

    

    def __str__(self):
        return self.mm[:self.data_len].decode()

    def fqn_to_path(self, file):
        
        if file is None: return None

        if isinstance(file, list):
            return Path(*file)
        else:
            return Path(file)

    def path_same(self, path):
        if self.path is not None and path is not None:
            if path.absolute() == self.path.absolute(): return True
        elif self.path is None and path is None:
            return True
        return False

    # if no file_fqn is given save will just call MMap.flush()
    # if file_fqn is given the MMap data is saved to that file
    # NOTE that StreamReader will remain mapped to the origional file if any.
    #       to remap you will need to create a new StreamReader instance. 
    def save(self, file_fqn=None):
    
        new_path = self.fqn_to_path(file_fqn)
        same = self.path_same(new_path)
        if self.path is None and new_path is None:
            # raise exception
            self.print_offset("StreamReader, you must provide a filename to save to.", type="exception")
        elif same and self._access != StreamReaderAccess.ACCESS_WRITE:
            # raise exception
            self.print_offset("StreamReader, cannot overwrite file unless it was mapped with ACCESS_WRITE!", type="exception")
        elif new_path is None:
            new_path = self.path

        if same:
            self.mm.flush()
        else:
            if not Path.exists(Path(new_path.parent)):
                Path.mkdir(new_path.parent, parents=True, exist_ok=True)
            with open(new_path, "wb") as bf:
                bf.write(self.mm[:self.data_len])

    def eof(self):
        return self.mm.size() == self.mm.tell()

    def meta(self, key, value=None):
        if value is not None:
            self._meta[key] = value
        if key in self._meta:
            return self._meta[key]
        return None


    def write(self, string: str):
        self.write_bytes(string.encode(encoding="utf-8"))

    def __add__(self, string):
        return self.__iadd__(string)

    def __iadd__(self, string):
        if isinstance(string, str):
            self.write_bytes(string.encode(encoding="utf-8"))
            return self
        elif isinstance(string, bytes) or isinstance(string, bytearray):
            self.write_bytes(string)
            return self
    
        raise NotImplemented

    def write_bytes(self, b):
        if not self.allows_resize:
            # exception
            self.print_offset("StreamReader, you cannot write to this stream.", type="exception")
        overflow = (len(b) + self.mm.tell()) - self.mm.size()
        if  overflow > 0:
            self.mm.resize(self.mm.size() + (math.ceil(overflow/SR_MM_EXPAND_SIZE)*SR_MM_EXPAND_SIZE))
        self.mm.write(b)
        self.data_len += len(b)


    def read_bytes(self, count):
        return self.mm.read(count)
        

    def npsize(self, dtype='B', shape=(1,)):
        size = 1
        for i in shape:
            size *= i
        return size * np.dtype(dtype).itemsize

    def read_ndarray(self, size, dtype, shape):
        return np.ndarray(buffer=self.mm.read(size), dtype=dtype, shape=shape)

    def read_asciiz_tonull(self):
        start = self.mm.tell()
        strings = []
        while -1 != (end := self.mm.find(b'\x00', start)):
            s = self.mm[start:end]
            if s == b'':
                break
            strings.append(s)
            start = end+1
        self.mm.seek(start+1)
        return strings
    
    def read_asciiz_array(self, n, chunks=3000, cdn = True):
        self.mm.size()
        strings = []
        buffer = b''
        step =  2 if cdn else 1
        st = 0
        en = 0
        while n:
            #print("readblock")
            buffer += self.mm.read(chunks)
            try:
                while n:
                    en = buffer.index(0, en+1)
                    if en == st: 
                        en += 1
                    else:
                        #print(st, en, buffer[st:en])
                        strings.append(buffer[st:en])
                        st = en + step
                        en = st
                        n -= 1
            except Exception as ex:
                buffer = buffer[st:]
                st = 0
                en = 0
                #print("cont " + str(ex))
                #print(traceback.print_exc())
                continue
        
        self.mm.seek(self.mm.tell() - len(buffer) + en)

        return strings

    def read_asciiz(self, chunks=33, maxchunks=10, cdn = True, debug=False):
        # Read chunks at a time, find null termination
        # reset position to next and return string.
        int_pos = self.mm.tell()
        buffer = []
        chunkcount = 0

        while maxchunks:
            buffer += self.mm.read(chunks)
            maxchunks -=1
            try:
                p = buffer.index(0, chunkcount*chunks)
                # read next byte to see if we're double null terminated.
                if cdn:
                    if p < len(buffer) - 1:
                        if buffer[p+1]==0:
                                self.mm.seek(int_pos+p+2)
                        else:
                                self.mm.seek(int_pos+p+1)
                    else:
                        b = self.mm.read(1)
                        if b[0] != 0:
                            self.mm.seek(int_pos+p+2)
                else:
                    self.mm.seek(int_pos+p+1)

                #if debug:
                #    reader.print_offset("")
                    #exit()

                return ''.join(chr(x) for x in buffer[:p])
            except Exception as ex:
                chunkcount +=1

        self.mm.seek(int_pos)
        return None

    def read_string_indexed(self)->IndexedString:
        index = self.read_uint_compressed()
        if index not in self.indexed_strings:
            string = self.read_asciiz(cdn=False)
            self.indexed_strings[index] = IndexedString(string, index=index)
        return self.indexed_strings[index]


    def read_string(self, count):
        return self.mm.read(count).decode('ascii')

    def peek_bytes(self, count):
        #return self.mm.peek(count)
        pos = self.mm.tell()
        data = self.mm.read(count)
        self.mm.seek(pos)
        return data
    
    def read_tbool(self):
        return 0!=struct.unpack('<B', self.mm.read(1))[0]
    
    def read_byte(self):
        return struct.unpack('<B', self.mm.read(1))[0]

    def read_int(self):
        return struct.unpack('<i', self.mm.read(4))[0]
    
    def read_uint(self):
        return struct.unpack('<I', self.mm.read(4))[0]

    def read_uint_compressed(self):
        # https://community.bistudio.com/wiki/raP_File_Format_-_OFP?useskin=darkvector#CompressedInteger
        # ok, I'll use a loop then.
        val = self.read_byte()
        if val & 0x80:
            for n in range(1,3):
                b = self.read_byte()
                val += (b-1)<< (n*7)

                if not b & 0x80: return val

            raise Exception("Compressed uint did not finish")
        return val
       

    def read_long(self):
        return struct.unpack('<l', self.mm.read(4))[0]
    
    def read_ulong(self):
        return struct.unpack('<L', self.mm.read(4))[0]

    def read_ushort(self):
        return struct.unpack('<H', self.mm.read(2))[0]

    def peek_ushort(self):
        b = self.peek_bytes(2)
        if len(b) == 2: return struct.unpack('<H', b)[0]
        return 0

    def read_ushort_arma(self): # 24bit
        return struct.unpack('<I', self.mm.read(3) + b'\x00' )[0]

    def read_float(self):
        return struct.unpack('<f', self.mm.read(4))[0]

    def read_xyz_triplet(self, n=1):
        if n == 1:
            return XYZTriplet(self.read_ndarray(( 3 * 4), dtype='<f', shape=(3,)))
        l = []
        while n:
            l.append(XYZTriplet(self.read_ndarray(( 3 * 4), dtype='<f', shape=(3,))))
            n-=1
        return l
        
    
    #TODO This is wanting to be a flat list of XYZTriplet's but this was fast,
    #      and I got lazy.
    def read_float_array(self, n=1, m=0):
        #return read_ndarray((self.nPeaks * 3 * 4), dtype='<f', shape=(self.nPeaks,3))
        if m<2:
            s = (n,)
        else:
            s = (n,m)
        return self.read_ndarray((n * 4), dtype='<f', shape=s)

    def read_rgba(self):
        return RGBA(self.read_ndarray(4, dtype='<B', shape=(4,)))
    


    def set_offset(self, pos, wence=os.SEEK_SET):
        return self.mm.seek(pos, wence)
    
    def get_offset(self):
        return self.mm.tell()
    
    def get_offset_hex(self, delta=0, offset = -1):
        if offset == -1: offset = self.mm.tell()
        return f"{(offset+delta):#0{10}x}"
    
    def print_offset(self, text="", delta=0, type="normal", offset = -1):
        if type=="error" or type=="exception":
            pref = "\033[91m"
        elif type=="heading":
            pref = "\033[94m"
        else:
            pref = ""

        post = ""
        if pref: post = "\033[0m" 
        
        #if "Class" in text:
        #    print(f"Delta={delta}, Offset={offset}")

        text = f"@{self.get_offset_hex(delta=delta, offset=offset)} {text}"
        print(f"{pref}{text}{post}")

        if type=="exception":
            raise Exception(text)

    def _find_lzo_ends(self, maxlen, base_address):
        pattern = b'\x11\x00\x00'
        found_address = base_address
        found_address = self.mm.find(pattern, found_address)
        hits = []
        while -1 != (found_address := self.mm.find(pattern, found_address + 1)):
            hits.append(found_address + 3)
        return hits

    def _find_lzo_end(self, maxlen, base_address, offset):
        pattern = b'\x11\x00\x00'
        #self.print_offset("a")
        found_address = self.mm.find(pattern, base_address+offset)
        #mm.seek(base_address)
        #self.print_offset(base_address)
        #time.sleep(1)
        self.set_offset(base_address)
        #self.print_offset(base_address)
        if found_address !=-1:    
            #self.print_offset("b")
            if found_address > (base_address + maxlen): return -1
            return (found_address-base_address) + 3
        
        return -1

    def read_lzo_decompress_old(self, count_guess, unsize=0):
        data = self.mm.read(count_guess)
        print(data[:3], data[-3:])
        print(len(data))

        return lzo.decompress(data, False, unsize, algorithm="LZO1X")
        
    
    def read_lzo_decompress(self, length_guess=0, unsize=0):

        base_address = self.get_offset()
        if length_guess >= 3:
            end_address = length_guess - 3
        else:
            end_address = 0
        max_try = 1000
        while (end_address+1) and max_try:
            end_address = self._find_lzo_end(unsize, base_address, end_address)
            #self.print_offset(str(hex(end_address)))
            if end_address == -1: 
                raise Exception("read_lzo_decompress() failed to find end of block!")
            #self.set_offset(base_address)
            data = self.mm.read(end_address)
            #print(data[:3], data[-3:])
            #print(len(data))
            try:
                decomp = lzo.decompress(data, False, unsize, algorithm="LZO1X")
                tries = {1000-max_try+1}
                if tries == 1:
                    self.print_offset(f"Found block, 1st try", type="error")
                else:
                    self.print_offset(f"Found block in {tries} tries", type="error")
                return decomp
            except Exception as ex:
                if length_guess >=3:
                    # the guess was wrong so start at the beginning.
                    self.print_offset("read_lzo_decompress() - You guessed wrong.", type="error")
                    end_address = 0
                    length_guess = 0
                #print(ex)
                #self.print_offset(f"Failed to decompress block ending at {hex(end_address)}")
                
                max_try -=1
        exit()
        return None
    

    def lzo_search(self, unsize, start, end, start_range, end_range):
        # the pattern searching read_lzo_decompress() uses is much faster.
        # but this byte for byte search method may still be useful?
        # self.lzo_search(self.header.iMapSize*4, 0x001C1780, 0x1127A2B, range(-3, 0), range(0,100)):
        from datetime import datetime
        size = end - start
        print("Searching for LZ block...")
        print(f"Expected decomp size = {unsize}")
        algos = ["LZO1X"] #, "LZO1B", "LZO1C", "LZO1F", "LZO1Y", "LZO1Z", "LZO2A"]
        t = datetime.now().timestamp()
        catch = 0
        for algo in algos:
            print("Algo " + algo)
            for si in start_range: #range(-3, 0):
                #print(f"si {si}")
                for ei in end_range: #range(0,100):
                    if t + 5 <= datetime.now().timestamp():
                        print(f"... {si} {ei} catches={catch}")
                        catch = 0
                        t = datetime.now().timestamp()
                    if size - si + ei <=0: 
                        continue

                    
                    self.reader.set_offset(start + si)
                    data = self.reader.read_bytes(size - si + ei) #8388608
                    #print(data[:10])
                    
                    try:
                        #LZO1, LZO1A, LZO1B, LZO1C, LZO1F, LZO1X, LZO1Y, LZO1Z, LZO2A.(default: LZO1X
                        #data2 = lzo.decompress(data)
                        data2 = lzo.decompress(data, False, unsize, algorithm=algo)
                        print("************************")
                        print(f"Algo {algo} @{hex(start + si)} - {hex(self.reader.get_offset()-1)} length {len(data)} bytes  (si {si} ei {ei}).")
                        if len(data2) == unsize:
                            print(f"Out data length = {len(data2)} OK")
                        else:
                            print(f"Out data length = {len(data2)} MISMATCH")
                        print("************************")
                    except Exception as ex:
                        catch +=1
                        #print(algo, si, ei, hex(reader.get_offset()), str(ex), start + si, size - si + ei)
