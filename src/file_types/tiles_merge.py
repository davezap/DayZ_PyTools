from PIL import Image
from os import listdir, path
import math
im_dirs = ['output/']

# get sorted list of images
im_path_list = [[path.join(p, f) for f in sorted(listdir(p))] for p in im_dirs]

#print(im_path_list)

im = Image.open(im_path_list[0][0])
width = im.width
height = im.height
#print (len(im_path_list[0]))
out_width = width * int(math.sqrt(len(im_path_list[0])))
out_height = height * int(math.sqrt(len(im_path_list[0])))

print("tile size", width, height, "output size", out_width, out_height)

new_im = Image.new('RGB', (out_width, out_height))

x_offset = 0
y_offset = 0
nudge_x = 32 #32
nudge_y = 32  #31

for im_file in im_path_list[0]:
    print(x_offset, y_offset, x_offset, y_offset, im_file)
    im = Image.open(im_file)
    new_im.paste(im, (x_offset * (width-nudge_x), y_offset*(height-nudge_y)))
    y_offset +=1
    if y_offset==32:
        y_offset=0
        x_offset+=1
    

new_im.save('output.png')
    