from datetime import datetime
from PIL import Image, ImageDraw
import numpy as np

def Layers2Img(MapSizeULONG, width, height):
    shift = 0
    while shift < 16:
        i = 0
        new_im = Image.new('RGB', (width, height))
        pixel_map = new_im.load()
        new_im
        print(shift)
        for y in range(0, height):
            for x in range(0,width):
                #p = cdata[i] # MapSizeULONG.data[i].item()
                #q = cdata[i+1]
                p = MapSizeULONG.data[i].item()
                val = (p >> shift) & 0x01
                i += 1
                #if shift < 8:
                #    val = (p >> shift) & 0x01
                #else:
                #    val = (q >> (shift-8)) & 0x01
                pixel_map[x,y] = (val*200 , val*200, val*200)
        flip_im = new_im.transpose(method=Image.FLIP_TOP_BOTTOM)
        flip_im.save(f'CellEnv_{shift}.png')
        shift+=1

def SaveImg(img, filename):
    time = datetime.now().strftime("%Y%m%d%H%M%S")
    flip_im = img.transpose(method=Image.FLIP_TOP_BOTTOM)
    flip_im.save(f'{filename}_{time}.png')

def Grid2Imgxy(data, width, height, filename, colour=""):
    new_im = Image.new('RGB', (width, height))
    
    pixel_map = new_im.load()
    
    print("img", new_im.width, new_im.height)
    i = 0
    print("wh", height, width)
    p = 0
    q = 0
    try:
        for y in range(0, height):
            for x in range(0, width):
                p = data[i].item()
                if np.isnan(p):
                    p = 0
                i += 1
                if colour=="gs":
                    pixel_map[x,y] = (p*5 , p*5, p*5)
                else:
                    q = int(((p + 400) / 1000) * 255)
                    if p < 0: 
                        pixel_map[x,y] = (0 , 0, q)
                    elif p >= 400:
                        pixel_map[x,y] = (q , q, q)
                    elif p >= 200:
                        pixel_map[x,y] = (q , q, 0)
                    elif p >= 0:
                        pixel_map[x,y] = (0 , q, 0)


    except Exception as ex:
        print(str(ex))
        print(i)
        print(x,y, p, q)
        exit()

    time = datetime.now().strftime("%Y%m%d%H%M%S")
    flip_im = new_im.transpose(method=Image.FLIP_TOP_BOTTOM)
    flip_im.save(f'{filename}_{time}.png')
    return True

def Grid2Img(grid, filename, flipaxis=False):
    new_im = Image.new('RGB', (grid.CellDimensions.x, grid.CellDimensions.y))
    pixel_map = new_im.load()
    i = 0
    for y in range(0, grid.CellDimensions.y):
        for x in range(0,grid.CellDimensions.x):
            #p = cdata[i] # cellenv.data[i].item()
            #q = cdata[i+1]
            p = grid.data[i].item()
            valA = (p >> 8) & 0xFF
            valB = p & 0xFF
            i += 1
            #if shift < 8:
            #    val = (p >> shift) & 0x01
            #else:
            #    val = (q >> (shift-8)) & 0x01
            if flipaxis:
                pixel_map[y,x] = (0 , valA, valB)
            else:
                pixel_map[x,y] = (0 , valA, valB)

    time = datetime.now().strftime("%Y%m%d%H%M%S")
    flip_im = new_im.transpose(method=Image.FLIP_TOP_BOTTOM)
    flip_im.save(f'{filename}_{time}.png')
    return True