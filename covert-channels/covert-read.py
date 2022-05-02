#!/usr/bin/env python2

# Proof-of-concept of a storage-based covert channel.
# https://github.com/TartarusLabs/Crypto-Tricks/covert-channels/
# james.fell@alumni.york.ac.uk

import binascii
import os.path
import time


#########################
# SETTINGS START

dummyFile = "/tmp/gconfd-05" 	# File whose metadata will act as our covert channel. Should be in /tmp and have non-suspicious filename!
delay = 0.005			# Number of seconds to pause between reading each 64 bit block of message data. Lower equals more bandwidth but less reliability.
outFile = "received.txt"	# File to store the received message in

# SETTINGS END 
########################


# Until dummy file appears do nothing
print "Waiting for message..."
while os.path.isfile(dummyFile) == False:
	pass

# Make a note of start time for calculating bandwidth
startTime = time.time()

# Let the user know there is an incoming message
print "Receiving data...."

# Small pause to let the writer process get a little bit ahead and write the first 64 bits into the metadata
time.sleep(delay/2)

# Initialise the empty message string
messageBinary = ''

# While dummy file still exists read the metadata
while os.path.isfile(dummyFile) == True:

	# Get accessed timestamp
	atime = bin(int(os.path.getatime(dummyFile)))
	atime = atime[2:]
	atime = atime.zfill(32)
        messageBinary = messageBinary + atime

	# Get modified timestamp
	mtime = bin(int(os.path.getmtime(dummyFile)))
	mtime = mtime[2:]
	mtime = mtime.zfill(32)
        messageBinary = messageBinary + mtime

        # Sleep for delay seconds
        time.sleep(delay)

# Make a note of end time for calculating bandwidth
endTime = time.time()

# Make a note of how much data we received in total
dataReceived = len(messageBinary)

# Read the first 24 bits of messageBinary to find the actual message length
messageLen = int(messageBinary[:24],2)

# Discard the first 24 bits and the zero padding from the end
messageBinary = messageBinary[24:messageLen+24]

# Convert the binary stream back into ASCII, display it and also save it to a file
n = int(messageBinary, 2)
print "\nMessage received (also saved to " + outFile + "):"
print binascii.unhexlify('%x' % n)
receivedFile = open(outFile, 'w')
receivedFile.write(binascii.unhexlify('%x' % n))

# Calculate the bandwidth of our covert channel
print "\nTime taken (seconds): " + str(endTime - startTime)
print "Data transfered (bits): " + str(dataReceived)
print "Bandwidth (bits per second): " + str(dataReceived / (endTime - startTime)) + "\n"

# Close the file we saved the message in
receivedFile.close()
