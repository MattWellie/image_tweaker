This is a quick app

Takes an image with a valid RGB pixel format (JPEG), and a directory of additional images with RGBa encoding (PNG)

The idea if to create an inflated blank image of the same proportions as the original image

The original image is blurred for a bit of smoothness (the logice that made this relevant has now been removed), and random sample pixels from it

Test the pixels using RMS logic to find the most similar image of the available PNGs, and stick that in a position similar to the original pixel

Eventually the idea is to have the original image vaguely recreated using PNG thumbnails as pixels



Concept shamelessly borrowed from https://github.com/STulling/ImageReconstructor and I've no doubt that this is a shitty implementation, I've never done anything with images before so this is a Social Distancing instigated hackaround 


Scripts:

Initial approach (covering first 2 scripts) used the approach of squashing the PNG images into one pixel as a mean value, and then comparing that against a select pixel from the input image. That average got some results, but everything trended towards brown.

colour_match_using_dict.py - uses a dictionary structure to store 'previously identified best match for this pixel colour' - that dictionary got well over a GB of JSON and affected runtime, especially when it comes to dumping to/reading from storage

no_dict_imager.py - dumps the dictionary store concept and runs each comparison fresh. Runtime is worse, sys resource usage is better

no_dict_dominant.py - no dictionary again, but tried something different to 'summarise' the input images. I've borrowed some code from https://github.com/fengsp/color-thief-py to generate a 'pallete' of colours present in the PNG images - for each colour in the pallete I compare to the selected pixel. The get_pallete function didn't seem to reliably return the 'best colour' first in the list. Might be worth revising this to generate a pallete, and explicitly see which of those colours is most prevalent in the images. Manyana
