# encoding=utf-8
import random
# import matplotlib.pyplot as plt
import string
import sys
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter


class PictureMaker(object):
    def __init__(self, filepath):
        self.filename = filepath
        self.font_path = './static/Mono.ttf'
        self.size = (229, 53)
        self.bgcolor = (255, 255, 255)
        self.fontcolor = (0, 0, 0)
        self.linecolor = (0, 0, 0)
        self.draw_line = True
        self.line_number = (1, 5)


    def gene_text(self, number, cmd):
        source1 = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
        source2 = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R',
                   'S', 'T', 'U', 'V', 'W', 'Z', 'X', 'Y']
        source3 = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J',
                   'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R',
                   'S', 'T', 'U', 'V', 'W', 'Z', 'X', 'Y']
        if (cmd == 1):
            return ''.join(random.sample(source1, number))
        if (cmd == 2):
            return ''.join(random.sample(source2, number))
        if (cmd == 3):
            return ''.join(random.sample(source3, number))

    def gene_line(self, draw, width, height):
        # begin = (random.randint(0, width), random.randint(0, height))
        # end = (random.randint(0, width), random.randint(0, height))
        begin = (0, random.randint(0, height))
        end = (74, random.randint(0, height))
        draw.line([begin, end], fill=self.linecolor, width=3)

    def gene_code(self, input_text):
        number = len(input_text)
        width, height = self.size
        image = Image.new('RGBA', (width, height), self.bgcolor)
        font = ImageFont.truetype(self.font_path, 40)
        draw = ImageDraw.Draw(image)
        text = input_text
        font_width, font_height = font.getsize(text)
        draw.text(((width - font_width) / number, (height - font_height) / number), text, font=font, fill=self.fontcolor)
        if self.draw_line:
            self.gene_line(draw, width, height)
        image = image.transform((width + 30, height + 10), Image.AFFINE, (1, -0.3, 0, -0.1, 1, 0),
                                Image.BILINEAR)
        image = image.filter(ImageFilter.EDGE_ENHANCE_MORE)
        aa = str(".png")
        path = self.filename + text + aa

        image.save(path)


if __name__ == "__main__":
    photo = PictureMaker('./static/')
    str1 = photo.gene_text(9, 3)
    print(str1)
    photo.gene_code(str1)
