#!/usr/bin/env python2

# Compare the original PNG to the modified one in order to measure how well our stego.py script is working.
# https://github.com/TartarusLabs/Crypto-Tricks/steganography/
# james.fell@alumni.york.ac.uk

import png
import math

# Function to read in two PNG files and carry out statistical measurements
def getStats(coverImage, stegoImage):

	# Open the image file for reading
	cover = open(coverImage, 'rb')
	stego = open(stegoImage, 'rb')

	# Read in the contents of the cover image
	coverReader = png.Reader(file=cover)
	coverContent = coverReader.read()
	coverImageWidth = coverContent[0]
	coverImageHeight = coverContent[1]
	coverPixels = list(coverContent[2])
	coverInfo = coverContent[3]

	# Read in the contents of the stego image
        stegoReader = png.Reader(file=stego)
        stegoContent = stegoReader.read()
        stegoImageWidth = stegoContent[0]
        stegoImageHeight = stegoContent[1]
        stegoPixels = list(stegoContent[2])
        stegoInfo = stegoContent[3]

	# Flatten the arrays of RGB values
	coverValuesArray = []
	for row in coverPixels:
		for item in row:
			coverValuesArray.append(item)

        stegoValuesArray = []
        for row in stegoPixels:
                for item in row:
                        stegoValuesArray.append(item)

	# Remove the alpha values, leaving only RGB values
	coverRGBarray = []
	for i in xrange(0, (len(coverValuesArray)/4), 4):
		coverRGBarray.append(coverValuesArray[i])
		coverRGBarray.append(coverValuesArray[i+1])
		coverRGBarray.append(coverValuesArray[i+2])

        stegoRGBarray = []
        for i in xrange(0, (len(stegoValuesArray)/4), 4):
                stegoRGBarray.append(stegoValuesArray[i])
                stegoRGBarray.append(stegoValuesArray[i+1])
                stegoRGBarray.append(stegoValuesArray[i+2])

	# Calculate the MSE (Mean Square Error)
	diffSqrTotal = 0
	for i in range(0, len(coverValuesArray)):
		diff = coverValuesArray[i] - stegoValuesArray[i]
		diffSqr = diff * diff
		diffSqrTotal += diffSqr

	mse = float(diffSqrTotal) / float(len(coverValuesArray))
	print "Mean Square Error: " + str(mse)

	# Calculate the PSNR (Peak Signal to Noise Ratio)
	psnr = 10 * (math.log10((256 * 256) / mse))
	print "Peak Signal to Noise Ratio: " + str(psnr)

	# Close the files
	cover.close()
	stego.close()

# Run the tests on the cover image and the stego image
getStats("in.png", "out.png")
