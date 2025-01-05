# Standard file handler template. 

from src.io.StreamReader import StreamReader

    
class Pbo:

    def __init__(self, reader = None):
        if reader is not None:
            self.consume(reader)


    def consume(self, reader: StreamReader):
        return True