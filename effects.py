from PIL import Image
from django.conf import settings
import os
import math



# /home/rob/djangosites/filemanager/test/house.jpg
# e = Effects('/home/rob/djangosites/filemanager/test/house.jpg', '/home/rob/djangosites/filemanager/test/out.jpg')
# http://pillow.readthedocs.io/en/3.0.x/reference/Image.html
class ImageEffects():
    '''
    Files should be pre-tested for suitability before applying this 
    class.
    If sucessful, save() overwrites an existing file
    
    @param src path-like to source
    @param dst path-like to destination dir
    PNG TIFF also acceptable
    '''
    def __init__(self, src, dst, img_format='JPEG'):
        self.src = src
        self.dst = dst
        self.img_format = img_format
        self.image = Image.open(src)
        # if not RGB, convert
        if (self.image.mode) not in ('L', 'RGB'):
            self.image = self.image.convert('RGB')
        
        #(root, ext) = os.path.splitext(self.src)
        #fileName = os.path.basename(root) + '.jpg'
        #newPath = os.path.join(dstDir, fileName)

    def grayscale(self):
        if (self.image.mode != 'L'):
            self.image = self.image.convert('L')

    def centre_crop(self, size):
        '''
        Crop to a size.
        The size is assumed on the longest side, and the crop taken 
        from each side (centered).
        '''
        assert size > 0, 'size to crop must be > 0'
        width_is_short_side = self.image.size[0] < self.image.size[1]
        if (not width_is_short_side):
            assert size <  self.image.size[0], 'size to crop is larger than image size'
            left_offset = math.floor((self.image.size[0] - size) / 2)
            self.image = self.image.crop((left_offset, 0, left_offset + size, self.image.size[1]))
        else:
            assert size <  self.image.size[1], 'size to crop is larger than image size'
            top_offset = math.floor((self.image.size[1] - size) / 2)
            self.image = self.image.crop((0, top_offset, self.image.size[0], top_offset + size))

    def aspect_centre_crop(self, ratio):
        '''
        Crop to an aspect ratio.
        Centre crop.
        @param ratio width / height
        '''
        current_ar = self.image.size[0] / self.image.size[1]
        if (current_ar < ratio):
            # height crop
            new_height = math.floor(self.image.size[0] / ratio)
            top_offset = math.floor((self.image.size[1] - new_height) / 2)
            self.image = self.image.crop((0, top_offset, self.image.size[0], top_offset + new_height))
        else:
            # width crop
            new_width = math.floor(self.image.size[1] * ratio)
            left_offset = math.floor((self.image.size[0] - new_width) / 2)
            self.image = self.image.crop((left_offset, 0, left_offset + new_width, self.image.size[1]))


    def aspect_resize(self, size, on_y_side=True):
        '''
        Resize an image.
        Preserves aspect ratio. BILINEAR up, LANCZOS down.

        @param size size to resize to. In pixels.
        @param on_y_side which side defines the size. boolean, True = y, False = x
        '''
        ## create pillow Image instance
        ##! set warning?
        ##warnings.simplefilter('error', Image.DecompressionBombWarning)
        #imagefile  = StringIO.StringIO(image_str)
        ##image = Image.fromString(imagefile)

        # resize dims
        if (not on_y_side):
            downscale = size < self.image.size[0]
            x = size
            y = math.floor((self.image.size[1] * size)/self.image.size[0])
        else:
            downscale = size < self.image.size[1]
            y = size
            x = math.floor((self.image.size[0] * size)/self.image.size[1])        
        # resize
        if (downscale):
          self.image = self.image.resize((x, y), Image.LANCZOS)
        else:
          self.image = self.image.resize((x, y), Image.BILINEAR)
         

    def resize(self, x_size, y_size):
        '''
        Resize to given dimentions.
        The image is cropped to centre to maintain given aspect ratio.
        Can upscale(BILINEAR) or downscale(LANCZOS).  
        '''
        self.aspect_centre_crop(x_size / y_size)
        # resize
        # side doesn't matter, the aspect is right, needs resizing
        # dont use aspect_resize(), it will introduce cumulative errors---
        # accept some distortion for honouring exact size request.
        sampler = Image.LANCZOS if (x_size < self.image.size[0]) else Image.BILINEAR
        self.image = self.image.resize((x_size, y_size), sampler)

    def turn(self, clockwise=True):
        ''' 90 degrees left or right '''
        angle = 270 if (clockwise) else 90
        self.image = self.image.rotate(angle, resample=Image.NEAREST, expand=True)
        
    def updown(self):
        ''' 180 degrees turn '''
        self.image = self.image.rotate(180, resample=Image.NEAREST, expand=False)

        
    def save(self, **args):
        '''
        Overwrites existing files.
        
        @args anything from Pillow for the format.
        The most interesting are,
        for JPEG: 
            quality: 0--95 (75 default)
            optimize: encoder guesswork
        PNG:
            compress_level : 0--9
            optimize: encoder guesswork
            
        @return path to the new image
        '''
        self.image.save(self.dst, self.img_format, **args)
        return self.dst
