#!/usr/bin/env python2

# LSB steganography using pseudorandom password-based embedding.
# https://github.com/TartarusLabs/Crypto-Tricks/steganography/
# james.fell@alumni.york.ac.uk

import png
import binascii
import random
import math
import sys
import argparse


# Read and process the command line arguments
parser = argparse.ArgumentParser(description='Hide text files inside PNG images using LSB steganography.')
parser.add_argument('-m','--mode', help='Set mode to embed or recover', required=True)
parser.add_argument('-i','--image', help='Image to read. If embedding this is the cover image, if recovering this is the stego image.', required=True)
parser.add_argument('-p','--password', help='Password.', required=True)
parser.add_argument('-t','--text', help='Text file to read. Only reuired if mode is embed.', required=False)
args = vars(parser.parse_args())


# Function to embed a hidden message into a cover image
def stego_embed(coverImageFile, hiddenMessageFile, password):

	# Open the cover image and hidden message files
	coverImage = open(coverImageFile, 'rb')
	hiddenMessage = open(hiddenMessageFile, 'r')

	# Read the text file and turn it into a string of 0s and 1s
	messageAscii = hiddenMessage.readlines()
	messageBinary = bin(int(binascii.hexlify(str(messageAscii)), 16))

	# Add a 24 bit header to the data to tell us its length when we want to extract it
	messageBinary = bin(len(messageBinary))[2:].zfill(24) + messageBinary

	# Read in and parse the contents of the cover image
	reader = png.Reader(file=coverImage)
	coverContent = reader.read()
	imageWidth = coverContent[0]
	imageHeight = coverContent[1]
	coverPixels = list(coverContent[2])
	coverInfo = coverContent[3]

	# Calculate the maximum number of bits we can hide in this cover image
	maxHideBits = imageWidth * imageHeight * 3

	# If the text file is too long to hide in this cover image, display an error and quit
	if len(messageBinary) > maxHideBits:
		print ("Sorry, this cover image can only hide up to " + str(maxHideBits) + " bits of data but you are trying to hide " + str(len(messageBinary)) + " bits (including 24 bit header we add). Please use a bigger cover image.")
		sys.exit()

	# Generate a pseudorandom permutation of all available LSBs in cover image based on the password as a seed
	ordering = range(maxHideBits)
	random.seed(password)
	random.shuffle(ordering)

	# Initialise a new counter
	bitCounter = 0

	# For every LSB in our pseudorandom permutation
	for lsb in ordering:

		# Stop when we reach the end of the message
		if bitCounter == len(messageBinary):
	        	break

		# Calculate the row and column in the image array that corresponds to the next LSB to manipulate
		row = int(math.floor(lsb / (imageWidth * 3)))
		col = lsb - (imageWidth * 3 * row)
		col = col + int(math.floor(col / 3))

		# Set the LSB value to the next bit of the message we are hiding
		if messageBinary[bitCounter] == '1':
			coverPixels[row][col] = coverPixels[row][col] | 1
		elif messageBinary[bitCounter] == '0':
			coverPixels[row][col] = coverPixels[row][col] & 254

		# Increment counter
		bitCounter += 1

	# Display some stats for the user
	print ("Data hidden (including 24 bit header we add): " + str(bitCounter) + " bits.")
	print ("Total capacity of cover image: " + str(maxHideBits) + " bits.")
	utilisation = (float(bitCounter) / float(maxHideBits)) * 100.00
	print ("Utilisation: " + str("%.2f" % utilisation) + "%")
	print ("Saving resulting stego image to out.png")

	# Write the stego image to disk
	png.from_array(coverPixels, 'RGBA', coverInfo).save('out.png')

	# Close the files
	coverImage.close()
	hiddenMessage.close()


# Function to recover a hidden message from a stego image
def stego_recover(stegoImageFile, password):

	# Open the stego image and a new text file to save the recovered message into
	stegoImage = open(stegoImageFile, 'rb')
	hiddenMessage = open('out.txt', 'w')

	# Read in and parse the contents of the stego image
	reader = png.Reader(file=stegoImage)
	coverContent = reader.read()
	imageWidth = coverContent[0]
	imageHeight = coverContent[1]
	coverPixels = list(coverContent[2])
	coverInfo = coverContent[3]

	# Calculate the maximum number of bits that can have been hidden in this stego image
	maxHideBits = imageWidth * imageHeight * 3

	# Generate a pseudorandom permutation of all available LSBs in cover image based on the password as a seed
	ordering = range(maxHideBits)
	random.seed(password)
	random.shuffle(ordering)

	# Initialise counters and empty string to store recovered message in
	messageSize = 0
	bitCounter = 0
	messageBinary = ''

	# For every LSB in our pseudorandom permutation
	for lsb in ordering:

		# Calculate the row and column in the image array that corresponds to the next LSB to read
		row = int(math.floor(lsb / (imageWidth * 3)))
		col = lsb - (imageWidth * 3 * row)
		col = col + int(math.floor(col / 3))

		# Read the LSB value to get the next bit of the message that was hidden
		messageBinary = messageBinary + str(coverPixels[row][col] & 1)

		# Once we have the first 24 bits, we know how much more data to extract
		if bitCounter == 23:
			messageSize = int(messageBinary, 2)

	               	# Discard first 24 bits now
			messageBinary = ''

		# Check if we have extracted all of the hidden message yet
		if bitCounter == (messageSize-1) + 24:
			break

		# Increment counter
		bitCounter += 1

	# Display some stats and progress for the user
	print ("Data extracted (excluding 24 bit header): " + str(bitCounter + 1 - 24) + " bits.")
	print ("Saving recovered hidden message to out.txt")

	# Convert the bits back to ASCII and write to out.txt
	n = int(messageBinary, 2)
	hiddenMessage.write(binascii.unhexlify('%x' % n))

        # Close the files
	stegoImage.close()
	hiddenMessage.close()



# Main entry point. Examine the command line arguments and act on them.
if args['mode'] == 'embed':
	stego_embed(args['image'], args['text'], args['password'])
elif args['mode'] == 'recover':
	stego_recover(args['image'], args['password'])
