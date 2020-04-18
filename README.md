This is a quick app

Takes an image with a valid RGB pixel format (JPEG), and a directory of additional images with RGBa encoding (PNG)

The idea if to create an inflated blank image of the same proportions as the original image

The original image is blurred for a bit of smoothness (the logice that made this relevant has now been removed), and random sample pixels from it

Test the pixels using RMS logic to find the most similar image of the available PNGs, and stick that in a position similar to the original pixel

Eventually the idea is to have the original image vaguely recreated using PNG thumbnails as pixels



Concept shamelessly borrowed from https://github.com/STulling/ImageReconstructor and I've no doubt that this is a shitty implementation, I've never done anything with images before so this is a Social Distancing instigated hackaround 