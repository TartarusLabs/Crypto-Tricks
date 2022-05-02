#!/usr/bin/env python2

# Generating an improved combining function for our stream cipher
# https://github.com/TartarusLabs/Crypto-Tricks/stream-cipher-correlation-attack/
# james.fell@alumni.york.ac.uk


from bitstring import BitArray

print "Checking all possible 16 bit vectors to find balanced, order 1 correlation immune combining functions."

# A counter to keep track of how many candidate functions we have identified
candidate_function_counter = 0

for combiner in range(0,65536):

	# If combiner is not balanced we don't even need to check it, so move onto next one if Hamming weight is not 8
	if bin(combiner).count("1") != 8:
		continue

	# Convert the combiner into a BitArray we can work with
	combining_func = BitArray('uint:16='+str(combiner))

	# Calculate a Linear Approximation Table for the boolean function
	counter = [-8] * 16

	for s_in_bits in range(0,16):
		for s_in in range(0,16):

			# Do boolean function lookup on s_in and assign to s_out
	                s_out = combining_func[s_in]
	
	                # XOR together the bits of s_in marked by s_in_bits
	                s_in_bitarray = BitArray('uint:4='+str(s_in & s_in_bits))
	                xor_in = s_in_bitarray[0] ^ s_in_bitarray[1] ^ s_in_bitarray[2] ^ s_in_bitarray[3]

	                # If they are the same, increment counter[s_in_bits]
	                if xor_in == s_out:
        	        	counter[s_in_bits] += 1
	

	# Bias must be 0 for input sums 1,2,4,8 in order to be correlation immune of order 1
	if (counter[1] == 0) and (counter[2] == 0) and (counter[4] == 0) and (counter[8] == 0):

		# this function is balanced and correlation immune order 1 so increment our counter
		candidate_function_counter += 1

		# convert all the counters into absolute values
		for j in range(0, len(counter)):
			counter[j] = abs(counter[j])

		# Non-linearity is 1/2(2^n - max_{w}|F(w)|)
		non_linearity = 0.5 * (16 - (2 * max(counter)))

		# print out the function as a vector along with its non-linearity score
		print str(candidate_function_counter) + " - " + combining_func.bin + " - Non-linearity: " + str(non_linearity)

		# Check if the function is also correlation immune of order 2 and alert the user if it is
		if (counter[3] == 0) and (counter[5] == 0) and (counter[6] == 0) and (counter[9] == 0) and (counter[10] == 0) and (counter[12] == 0):
			print "The above function is also correlation immune order 2"
