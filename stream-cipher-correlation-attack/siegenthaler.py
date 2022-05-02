#!/usr/bin/python

# Implementation of a stream cipher
# https://github.com/TartarusLabs/Crypto-Tricks/stream-cipher-correlation-attack/
# james.fell@alumni.york.ac.uk


from bitstring import BitArray

# Set how many bits of keystream to generate
keybits = 2000

# Define the boolean function as simply an array of results which can be used for lookups
boolean_outputs = [1,1,0,1,0,1,1,0,1,0,0,0,1,1,0,0]


# Function to create a requested LFSR and clock it a requested number of times, returning the resulting bit stream in a BitArray
def register(tap_sequence, initial_bits, clock_cycles):

        # Initialise the LFSR
        lfsr = initial_bits

        # Initialise output_bits to be a BitArray of zeroes with length equal to the number of clock cycles requested
        output_bits = '0' * clock_cycles
        output_bits = BitArray(bin=output_bits)

        # Clock the LFSR the requested number of times
        for cycle in range(0, clock_cycles):

                # tapped is the result of XORing together all the bits specified by the tap sequence
                tapped = 0
                for tap in tap_sequence:
                        tapped = tapped ^ lfsr[tap-1]

                # Add the rightmost bit of the LFSR to the output
                output_bits[cycle] = lfsr[initial_bits.len-1]

                # Shift the LFSR right one bit, discarding the already saved rightmost bit
                lfsr >>= 1

                # Overwrite the leftmost bit of the LFSR with the result of the earlier tap operation
                lfsr[0] = tapped

        # Return the BitArray of all the output bits we saved from the LFSR
        return output_bits


# Function to implement the boolean function from our stream cipher specification
# This is really as simple as using the 4 bit input as an index into an array and looking up the output.
def boolean_function(bit1, bit2, bit3, bit4):
	input_num = BitArray('bin='+str(bit1)+str(bit2)+str(bit3)+str(bit4))
	return boolean_outputs[input_num.uint]



# Calculate a Linear Approximation Table for the boolean function
# This essentially gives us the same information as the Walsh-Hadamard spectrum although it is done with statistics instead of vectors

counter = [-8] * 16

# For all 16 possible input masks, ie for all 16 possible ways of combining input bits
for s_in_bits in range(0,16):

	# For all 16 possible 4 bit inputs to the combining function
	for s_in in range(0,16):

		# Do boolean function lookup on s_in and assign to s_out
                s_out = boolean_outputs[s_in]

                # XOR together the bits of s_in marked by the input mask
                s_in_bitarray = BitArray('uint:4='+str(s_in & s_in_bits))
                xor_in = s_in_bitarray[0] ^ s_in_bitarray[1] ^ s_in_bitarray[2] ^ s_in_bitarray[3]

                # If the output and the XORed inputs are the same value, increment counter[s_in_bits]
                if xor_in == s_out:
                	counter[s_in_bits] += 1

	# Print the table out so we can plan our divide and conquer attack
	print "Input Mask = " + str(s_in_bits) + " Bias = " +str(counter[s_in_bits])


# Read the target key stream from the text file
print "\nReading in target keystream from stream.txt"
samples = open('stream.txt', 'r')
sampleKeyStream = BitArray('bin='+samples.read())
samples.close()


# Generate 2000 bits of output from LFSR1 for all 128 possible initial states and check for correlation with the keystream
# All incorrect initial states should give about 4/8 agreement whereas correct one should give about 3/8

print "\nAttacking LFSR1 using first order correlation"

for key in range (0, 128):
	counter = 0
	lfsr1 = register([4,7], BitArray('uint:7='+str(key)), keybits)

	for cycle in range(0, keybits):
		if sampleKeyStream[cycle] == lfsr1[cycle]:
			counter += 1

	# As soon as we find an initial state that gives a correlation of less than 800 out of 2000 we stop
	if counter < 800:
		print "LFSR1 - Initial State: " + str(key) + " Counter: " + str(counter)
		break

# This found that the correct initial state for LFSR1 is 27


# Generate 2000 bits of output from LFSR3 for all 8192 possible initial states and check for correlation with the keystream
# All incorrect initial states should give about 4/8 agreement whereas correct one should give about 2/8

print "\nAttacking LFSR3 using first order correlation"

for key in range (0, 8192):
        counter = 0
        lfsr3 = register([8,11,12,13], BitArray('uint:13='+str(key)), keybits)

        for cycle in range(0, keybits):
                if sampleKeyStream[cycle] == lfsr3[cycle]:
                        counter += 1

	# As soon as we find an initial state that gives a correlation of less than 600 out of 2000 we stop
        if counter < 600:
                print "LFSR3 - Key: " + str(key) + " Counter: " + str(counter)
		break

# This found that the correct initial state for LFSR3 is 991


# Generate 2000 bits of output from LFSR4 for all 32768 possible initial states, XOR it with the output of LFSR1 and check for correlation with the keystream
# All incorrect initial states should give about 4/8 agreement whereas correct one should give about 5/8

print "\nAttacking LFSR4 using second order correlation with LFSR1"

# Set up LFSR1 using already recovered initial state
lfsr1 = register([4,7], BitArray(bin='0011011'), keybits)    	# Correct initial state is 27

# For each possible initial value of LFSR4
for key in range (0, 32768):
	
	# Generate 2000 bits from LFSR4
	lfsr4 = register([14,15], BitArray('uint:15='+str(key)), keybits)

	# XOR together the 2000 bits from LFSR1 with the 2000 bits from LFSR4
	lfsr1_xor_lfsr4 = lfsr1 ^ lfsr4
	
	# Compare the resulting bitstream with the keystream we are attacking
	counter = 0
	for cycle in range(0, keybits):
		if sampleKeyStream.bin[cycle] == lfsr1_xor_lfsr4.bin[cycle]:
			counter += 1

	# If more than 1200 of the 2000 bits agree we have found the correct initial value of LFSR4
	if counter > 1200:
		print "LFSR4 - Key: " + str(key) + " Counter: " + str(counter)
		break

# This found that the correct initial state for LFSR4 is 3254


# Generate 2000 bits of output from LFSR2 for all 2048 possible initial states and see if the resulting keystream is identical to that under attack
# All incorrect initial states should give about 50% agreement whereas correct one should give 100%

print "\nAttacking LFSR2 using brute force"

# Set up LFSRs 1, 3 and 4 using recovered initial states
lfsr1 = register([4,7], BitArray('uint:7=27'), keybits)
lfsr3 = register([8,11,12,13], BitArray('uint:13=991'), keybits)
lfsr4 = register([14,15], BitArray('uint:15=3254'), keybits)

# Set up BitArray to hold the generated keystream
stream_key = '0' * keybits
stream_key = BitArray(bin=stream_key)

# For each possible initial value of LFSR2
for key in range (0, 2048):

        # Generate 2000 bits from LFSR2
        lfsr2 = register([3,8,9,11], BitArray('uint:11='+str(key)), keybits)
       
        # Compare the resulting keystream with the keystream we are attacking
        counter = 0
        for cycle in range(0, keybits):

        	# Generate 1 bit of keystream based on the current guess for the initial state of LFSR2
        	stream_key[cycle] = boolean_function(lfsr1.bin[cycle], lfsr2.bin[cycle], lfsr3.bin[cycle], lfsr4.bin[cycle])

		# Compare it to the corresponding bit of the keystream under attack, increment a counter whenever they match
                if sampleKeyStream.bin[cycle] == stream_key.bin[cycle]:
                        counter += 1

        # If all of the 2000 bits agree we have found the correct initial value of LFSR2
        if counter == 2000:
                print "LFSR2 - Key: " + str(key) + " Counter: " + str(counter) 
                break

# This found that the correct initial state for LFSR2 is 474
