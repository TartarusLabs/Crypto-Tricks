#!/usr/bin/env python2

# Proof-of-concept of a storage-based covert channel.
# https://github.com/TartarusLabs/Crypto-Tricks/covert-channels/
# james.fell@alumni.york.ac.uk

import binascii
import os
import time


#########################
# SETTINGS START

dummyFile = "/tmp/gconfd-05"		# File whose metadata will act as our covert channel. Should be in /tmp and have non-suspicious filename!
delay = 0.005 				# Number of seconds to pause between sending each 64 bit block of message data. Lower equals more bandwidth but less reliability.
messageFile = "secret.txt"		# Text file containing message to send through the covert channel

# SETTINGS END 
########################


# Open the hidden message file
hiddenMessage = open(messageFile, 'r')

# Read the text file and turn it into a string of 0s and 1s
messageAscii = hiddenMessage.readlines()
messageBinary = bin(int(binascii.hexlify(str(messageAscii)), 16))

# Remove the '0b' from the start
messageBinary = messageBinary[2:]

# Add a 24 bit header to the data to tell us its length when we want to extract it
messageBinary = bin(len(messageBinary))[2:].zfill(24) + messageBinary

# Pad out end of message with 0 bits to make it an exact multiple of 64
messageBinary = messageBinary + (64 - (len(messageBinary) % 64)) * '0'

# Create the empty dummy file to signal that we are starting to send a message
print "Creating dummy file: " + dummyFile
dummy = open(dummyFile, 'w')
dummy.close()

# Initialise bit counter
bitCounter = 0

# Until we have sent the entire message
print "Sending message file: " + messageFile
while bitCounter < len(messageBinary):

	# Set the accessed and modified timestamps on the dummy file so as to communicate another 64 bit block of the message
	os.utime(dummyFile,(int(messageBinary[bitCounter:bitCounter+32], 2), int(messageBinary[bitCounter+32:bitCounter+64], 2)))

        # Sleep for delay seconds
        time.sleep(delay)

	# Move onto the next 64 bit block
	bitCounter += 64

# Signal that we have finished by deleting the dummy file
print "Message sent. Deleting dummy file."
os.remove(dummyFile)

# Close the message text file
hiddenMessage.close()
