from PIL import Image, ImageFilter
import sys
import os
from collections import defaultdict
import random
from argparse import ArgumentParser
import logging
import numpy as np


"""
takes an input image (RGB - JPEG) and a directory of images with png images (RGBA)
"""

class Uknown_pokemon(Exception):
    pass


def get_dominant_colour_from_image(image_path):
    """
    manual implementation, nothing else worked well enough
    parse the image as a numpy array
    ignore pixels if the alpha mask is 0, or if the RGB is equal (shades of grey)
    return the RGB that is most common
    :param image_path:
    :return:
    """

    image_array = np.asarray(Image.open(image_path))

    pixel_dict = defaultdict(int)

    for row in image_array:
        for r, g, b, a in row:
            if (r == g == b) or a == 0:
                continue

            pixel_dict[(r, g, b)] += 1

    try:
        return max(pixel_dict, key=pixel_dict.get)
    except ValueError:
        raise Uknown_pokemon(image_path)


class PictureRejigger:
    """
    Talk me through it:

    Get a picture from a file, blur the image based on the blurring factor to reduce the pixel colour search space

    parse the directory of images, reducing each image to a pixel and saving the RGB values of the image in a dict

    optional shortcut - parse in the previous dictionary as JSON. This is likely to be slower overall if the current
    image has a significantly different palette to previous images

    Create a new image (black, blank canvas), some x the size of the original

    Randomly select pixels from the blurred image (<input> number of times), and compare the colour to all small images

    Save the contrast as a value in the image dictionary (image_path: (rgb): contrast, (rgb2): contrast2) to reduce
    future lookups

    take the image that matched the best, and paste that into the new image at position x*4,y*4

    """

    def __init__(
        self,
        input_image,
        input_pixels="pokemans",
        blurring_factor=2,
        output_filename="result.jpg",
        num_samples=10000,
        expansion_rate=4,
        logger=None,
    ):
        """

        :param input_image:
        :param input_pixels:
        :param blurring_factor:
        :param output_filename:
        :param num_samples:
        """
        self.logger = logger
        self.input_image = input_image
        self.blurring_factor = blurring_factor

        self.blurred_image = self.read_in_and_blur_image()

        self.expansion = expansion_rate
        self.new_base = self.create_new_blank_background(self.blurred_image)
        self.input_pixels = input_pixels

        self.logger.info('importing the dictionary of values')
        self.pixel_rgb = self.get_rgb_dict_from_new_pixels()
        self.input_pixels = f"parsed_to_json_{self.input_pixels}.json"

        self.logger.info('dictionary load complete')

        self.output_filename = output_filename
        self.num_samples = num_samples

    def get_colour_difference(self, pixel_rbg, image_rbg):
        """
        dictionaries can use tuples as arguments, so we should save this result
        image has been smoothed to reduce number of unique pixel colours

        calculate the mean square per colour, sum across RGB, and obtain root
        an approximation of contrast between the two colours

        e.g. 0 difference if colours are same

        Experimental condition, double the difference squared for the most intense colour. Hopefully this might overcome
        some of the red-green swaps

        :param pixel_rbg:
        :param image_rbg:
        :return:
        """

        self.logger.debug(f"input_pixel: {pixel_rbg}")
        self.logger.debug(f"image_avg_pixel: {image_rbg}")

        pr, pg, pb = pixel_rbg[:3]
        ir, ig, ib = image_rbg

        distances = [((pr - ir)*0.3)**2, ((pg - ig)*0.59)**2, ((pb - ib)*0.11)**2]

        self.logger.debug(
            f"r_dist={distances[0]}, g_dist={distances[1]}, b_dist={distances[2]}"
        )

        rgb_rms_distance = sum(distances)

        return rgb_rms_distance

    def get_rgb_dict_from_new_pixels(self):
        """
        for each image, squash into one pixel and get that value
        create an entry in the dictionary with filepath: { rgb: value, checked: defaultdict(float)}

        that second layer default dict can take a tuple of RGB as a key, and point to the pre-calculated RMS difference
        :return:
        """

        self.logger.debug(f"generating new dictionary from {self.input_pixels}")
        picture_dict = dict()
        for image in os.listdir(self.input_pixels):
            select_image_path = os.path.join(self.input_pixels, image)

            self.logger.debug(f"selected image: {select_image_path}")

            # 4 number returned: Alpha (transparency) + RGB. A used in mask, not other values
            try:
                picture_dict[select_image_path] = get_dominant_colour_from_image(select_image_path)
            except Uknown_pokemon:
                print('probably a uknown, fuck those guys')
                continue

        return picture_dict

    def read_in_and_blur_image(self):
        """
        reads external image, blurs as appropriate, returns new blurred image
        this is done to reduce the differences between adjacent pixels, smoothing the source image
        :return: new image object
        """

        self.logger.info(
            f"reading in {self.input_image} and using blurring factor {self.blurring_factor}"
        )

        # read in the image - creative name
        input_as_image_object = Image.open(self.input_image)

        # create a method instance with the blurring factor
        blur_with_set_radius = ImageFilter.BoxBlur(radius=self.blurring_factor)

        # apply this level of blurring to the image
        blurred_input = input_as_image_object.filter(blur_with_set_radius)

        return blurred_input

    def create_new_blank_background(self, input_image_for_size):
        """

        :param input_image_for_size:
        :return:
        """

        self.logger.debug("creating a new blank background")

        original_x, original_y = map(int, input_image_for_size.size)

        self.logger.debug(f"Original image size: {original_x}, {original_y}")

        new_x = original_x * self.expansion
        new_y = original_y * self.expansion

        self.logger.debug(f"New image size: {new_x}, {new_y}")

        # use RGBA to enable transparency of outlines (Alpha)
        new_img = Image.new("RGBA", (new_x, new_y), (0, 0, 0, 0),)

        return new_img

    def get_all_images_from_input_dir(self):
        """
        reads directory and returns all files as full filehandles
        :return:
        """
        self.logger.info(f"pulling all filepaths from {self.input_pixels}")
        new_pixels = [
            os.path.join(self.input_pixels, new_pixel)
            for new_pixel in os.listdir(self.input_pixels)
            if os.path.isfile(
                os.path.join(self.input_pixels, new_pixel)
                and new_pixel is not ".DS_Store"
            )
        ]

        return new_pixels

    def run_process(self):
        """

        :return:
        """

        range_x, range_y = map(range, self.blurred_image.size)

        iterations = 0

        self.logger.debug(f"rounds: {self.num_samples}")

        while self.num_samples > iterations:

            random_x, random_y = random.choice(range_x), random.choice(range_y)

            self.logger.debug(f"random x is '{random_x}', random y is '{random_y}'")

            select_pixel_rgb = self.blurred_image.getpixel((random_x, random_y))

            self.logger.debug("obtaining best fit")
            
            try:
                best_fit = self.compare_pixel_to_input_images(select_pixel_rgb)
            except:
                iterations += 1
                continue

            self.logger.debug(f"obtained best fit: {best_fit}")
            self.add_best_image_to_new_image(
                best_fit, input_x=random_x, input_y=random_y
            )

            iterations += 1

        new_small_image = self.resize_new_image_back_to_normal()

        self.save_new_things_to_file(self.new_base)

        self.output_filename = f"resized_{self.output_filename}"
        self.save_new_things_to_file(new_small_image)

    def add_best_image_to_new_image(self, best_fit, input_x, input_y):
        """
        text_img = Image.new('RGBA', (600,320), (0, 0, 0, 0))
        text_img.paste(bg, (0,0))
        text_img.paste(ironman, (0,0), mask=ironman)
        text_img.save("ball.png", format="png")
        :param best_fit:
        :param input_x:
        :param input_y:
        :return:
        """

        new_img = Image.open(best_fit, "r")

        # add the new image to the background with the expanded pixels, using the transparency mask
        self.new_base.paste(
            new_img, (input_x * self.expansion, input_y * self.expansion), mask=new_img
        )

    def resize_new_image_back_to_normal(self):
        """

        :return:
        """
        current_x, current_y = self.new_base.size
        resized_output = self.new_base.resize(
            (current_x // self.expansion, current_y // self.expansion)
        )

        return resized_output

    def save_new_things_to_file(self, new_image):
        """

        :param new_image:
        :return:
        """

        new_image.save(self.output_filename, "PNG")

    def compare_pixel_to_input_images(self, input_rgb):
        """
        takes input RGB values
        for each input image, checks to see if they have already been seen, otherwise runs a check against input images
        updates the dictionary if check was run

        :return:
        """

        self.logger.debug(f"comparing {input_rgb} to all images")

        image_path_keys = self.pixel_rgb.keys()

        this_pixel_check = {image_path: self.get_colour_difference(input_rgb, self.pixel_rgb[image_path]) for image_path in image_path_keys}

        # intially just assume there are no ties - find the best fitting key
        best_image = min(
            image_path_keys,
            key=(lambda k: this_pixel_check[k]),
        )
        return best_image

if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)

    logging.debug("creating argParser and parsing CMDLINE arguments")
    logging.debug(f"commandline input: {sys.argv}")
    parser = ArgumentParser()
    parser.add_argument("-i", required=True, help="input image to rejig")
    parser.add_argument(
        "-p",
        default="pokemans",
        help="path to the folder containing replacement images, "
    )
    parser.add_argument(
        "-b", default=3, type=int, help="blurring factor, number of adjacent pixels"
    )
    parser.add_argument(
        "-o", default="rejigged_result.png", help="filename for output PNG"
    )
    parser.add_argument(
        "-c", default=10000, help="number of selection cycles", type=int
    )
    parser.add_argument("-e", default=4, help="ratio of input to output size", type=int)
    args = parser.parse_args()
    logging.info("Argument parsing complete")

    image_logger = logging.getLogger("image_transform_logger")
    image_logger.setLevel(logging.INFO)

    # create file handler which logs even debug messages
    image_log_handle = logging.FileHandler(f"{args.i}__image_debug_log.log")
    image_log_handle.setLevel(logging.DEBUG)

    image_logger.addHandler(image_log_handle)

    image_logger.debug(f"cycles: {args.c}")
    image_logger.debug(f"input_image: {args.i}")
    image_logger.debug(f"blurring: {args.b}")
    image_logger.debug(f"output_path: {args.o}")
    image_logger.debug(f"expansion: {args.e}")
    image_logger.debug(f"input_stencils: {args.p}")

    image_logger.debug("creating a rejigger instance")
    rejigger = PictureRejigger(
        input_image=args.i,
        input_pixels=args.p,
        blurring_factor=args.b,
        output_filename=args.o,
        num_samples=args.c,
        expansion_rate=args.e,
        logger=image_logger,
    )
    rejigger.run_process()
