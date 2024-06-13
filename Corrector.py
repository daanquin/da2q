from PIL import Image
from multiprocessing import Pool, cpu_count
import time
import math
import os
import numpy as np

class Corrector:
    def __init__(self):

        """Add a comment here!"""

        self.input_image_path = input("Enter the relative path to the image (default is ...):")
        if self.input_image_path == "":
            self.input_image_path = "./images/test_simple_400x300.png"
        _, input_filename = os.path.split(self.input_image_path)

        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.abspath(__file__))

        # Construct the full path to the input image
        if not os.path.isabs(self.input_image_path):
            full_input_path = os.path.join(script_dir, self.input_image_path)
        else:
            full_input_path = self.input_image_path

        try:
            self.img = Image.open(full_input_path)
        except Exception as e:
            print(f"Error opening image: {e}")
            raise e

        self.img = self.img.convert('L')
        self.width, self.height = self.img.size
        self.BLACK_THRESHOLD = input("Enter the darkness threshold (default is 1):")
        if self.BLACK_THRESHOLD == "":
            self.BLACK_THRESHOLD = 1
        self.WHITE_THRESHOLD = input("Enter the brightness threshold (default is 254):")
        if self.WHITE_THRESHOLD == "":
            self.WHITE_THRESHOLD = 254

        # Construct the output path
        output_filename, ext = os.path.splitext(input_filename)
        output_filename = f'{output_filename}_corrected{ext}'
        output_dir = os.path.join(script_dir, 'results')
        self.output_path = os.path.join(output_dir, output_filename)

        # Create the 'results' directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

    def _compute_average(self, pos_x, pos_y, kernel_size=1):

        """The original version of the correct_pixel function.
        It traverses all valid pixels inside the kernel to collect their
        brightness value, then returns the average value of all valid pixels.
        A pixel inside the kernel is "valid" if :
            a. It is not too dark or too bright
            b. Its coordinates are inside the image dimensions
            c. It is not the center of the kernel
        Name changed to indicate it should not be called by the user."""

        if kernel_size < 0:
            raise ValueError("Kernel size must be a non-negative integer")

        correction = 0
        count = 0

        for x in range(pos_x - kernel_size, pos_x + kernel_size + 1):
            for y in range(pos_y - kernel_size, pos_y + kernel_size + 1):
                # To filter the exact pixel on which the kernel is based
                if x != pos_x or y != pos_y: 
                    # To filter pixels outside the image
                    if x >= 0 and x < self.width and y >= 0 and y < self.height:
                        # To filter pixels inside the kernel also being too dark or too bright
                        if self.img.getpixel((x, y)) > self.BLACK_THRESHOLD and self.img.getpixel((x, y)) < self.WHITE_THRESHOLD:
                            correction += self.img.getpixel((x, y))
                            count += 1

        if count > 0:
            correction = correction / count
        return correction

    def _replace_pixel_on_image(self, coords):
        x, y = coords

        """Function to actually implement the computed corrected pixel
        on the image indicated coordinates if the are too dark or too bright.
        This method should not be called by the user."""

        pixel = self.img.getpixel((x, y))
        
        # If the pixel on the passed coordinates is too dark or bright,
        # We correct it, and then we replace it on the image.

        if pixel <= self.BLACK_THRESHOLD:
            new_pixel = self._compute_average(x, y)
            self.img.putpixel((x, y), int(new_pixel))
            print('>> Black pixel found @ x=%d\t y=%d\t codes=%d\t correction=%d' % (x, y, pixel, new_pixel))
        elif pixel >= self.WHITE_THRESHOLD:
            new_pixel = self._compute_average(x, y)
            self.img.putpixel((x, y), int(new_pixel))
            print('>> White pixel found @ x=%d\t y=%d\t codes=%d\t correction=%d' % (x, y, pixel, new_pixel))

    def correct_image_og(self):
        """The previous main the original defect_pixel.py used to correct an image.
        This method does a simple traversal of all possible x,y pixel combinations 
        and calls the correction on the image.
        The method uses a single process, different to the correct_image_mp method."""

        start = time.time()

        # Simple two-dimensional traversal
        for y in range(self.height):
            for x in range(self.width):
                self._replace_pixel_on_image((x, y))  # Pass a tuple of coordinates

        print('processing done in %.3f secs' % (time.time() - start))
        print('image corrected is available at: %s' % self.output_path)
        self.img.show()
        self.img.save(self.output_path, 'png')

    def correct_image_mp(self):

        """New proposed way of correcting an image: using multiprocessing.
        The method retrieves the number of cores available, say n cores, then
        splits the image pixels in n parts mostly equal, and assigns every process/core
        a part of the image to correct, the same way correct_image_og does."""

        start = time.time()

        # Create a pool of processes
        with Pool(cpu_count()) as p:
            # Create a list of all pixel coordinates
            all_pixels = [(x, y) for y in range(self.height) for x in range(self.width)]
            # Use map to apply the _replace_pixel_on_image function to all pixel coordinates
            p.map(self._replace_pixel_on_image, all_pixels)

        print('processing done in %.3f secs' % (time.time() - start))
        print('image corrected is available at: %s' % self.output_path)
        self.img.show()
        self.img.save(self.output_path, 'png')

    def check_golden(self, golden_path):
        
        # Get current directory to construct the full path to golden image
        script_dir = os.path.dirname(os.path.abspath(__file__))
        if not os.path.isabs(golden_path):
            full_golden_path = os.path.join(script_dir, golden_path)
        else:
            full_golden_path = golden_path
        try:
            img_golden = Image.open(full_golden_path).convert('L')
        except Exception as e:
            print(f"Error opening golden image: {e}")
            raise e

        for y in range(self.height):
            for x in range(self.width):
                if self.img.getpixel((x, y)) != img_golden.getpixel((x, y)):
                    print(f"Pixel @ x={x}, y={y} does not match with golden. corrected={self.img.getpixel((x, y))}, golden={img_golden.getpixel((x, y))}")
        
        print("Done checking golden image!")
        
if __name__ == "__main__":
    corrector = Corrector()
    corrector.correct_image_mp()
    corrector.check_golden("./golden/test_simple_400x300_golden.png")