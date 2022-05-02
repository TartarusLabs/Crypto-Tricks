#!/usr/bin/env python2

# Linear cryptanalysis attack against our block cipher implementation in block-cipher.py
# https://github.com/TartarusLabs/Crypto-Tricks/block-cipher-linear-cryptanalysis/
# james.fell@alumni.york.ac.uk


from bitstring import BitArray

# Hardcoded S box as per the specification
sbox_encrypt = [4,0,12,3,8,11,10,9,13,14,2,7,6,5,15,1]
sbox_decrypt = [1,15,10,3,0,13,12,11,4,7,6,5,2,8,9,14]

# Calculate the Linear Approximation Table

# Initialise every entry in the 16 by 16 table to -8
counter = [[-8 for x in range(16)] for x in range(16)]

# For every combination of input sum and ouput sum
for s_in_bits in range(0,16):
	for s_out_bits in range(0,16):
		# For every possible input to the S-box
		for s_in in range(0,16):

			# Do S box lookup on s_in and assign to s_out
			s_out = sbox_encrypt[s_in]

			# XOR together the bits of s_in marked by the mask s_in_bits
			s_in_bitarray = BitArray('uint:4='+str(s_in & s_in_bits))
			xor_in = s_in_bitarray[0] ^ s_in_bitarray[1] ^ s_in_bitarray[2] ^ s_in_bitarray[3]

			# XOR together the bits of s_out marked by the mask s_out_bits
                        s_out_bitarray = BitArray('uint:4='+str(s_out & s_out_bits))
                        xor_out = s_out_bitarray[0] ^ s_out_bitarray[1] ^ s_out_bitarray[2] ^ s_out_bitarray[3]

			# If they are the same, increment the relevant entry in the LAT
			if xor_in == xor_out:
				counter[s_in_bits][s_out_bits] += 1

		# Print out the table as we go
		print "Input Sum: " + str(s_in_bits) + "  Output Sum: " + str(s_out_bits) + "  Bias: " +str(counter[s_in_bits][s_out_bits])


# Read our target 64k plaintext/ciphertext pairs into an array
with open('plaintext-ciphertext.txt') as f:
        samples = f.readlines()

print "Initiating linear cryptanalysis attack...."

# First we attack the first and second 4 bit blocks of subkey5
# P1 + U4,2 + U4,6 = 0 with bias 1/16

# For each of the 256 possible values for the bits of partial subkey5
counter = [0] * 256
for subkey5_bits in range(0,256):

        # Turn the int into an 8 bit BitArray
        subkey5_bits_array = BitArray('uint:8='+str(subkey5_bits))

        # For each of the 64k plaintext/ciphertext pairs
        for i in range(0,65536):
                plaintext = BitArray('uint:16='+str(i))
                ciphertext = BitArray('uint:16='+str(samples[i].split()[1]))

                # XOR this partial subkey5 guess with relevant bits of ciphertext to get back to V4 bits
                V4_1 = ciphertext[0:4] ^ subkey5_bits_array[0:4]
                V4_2 = ciphertext[4:8] ^ subkey5_bits_array[4:8]

                # Then put that backwards through sbox to get back to U4 bits
                U4_1 = sbox_decrypt[V4_1.uint]
                U4_2 = sbox_decrypt[V4_2.uint]
                U4_str = "{0:b}".format(U4_1).zfill(4) + "{0:b}".format(U4_2).zfill(4)
                U4 = BitArray(bin=U4_str)

                # XOR the relevant U4 bits and plaintext bits as per our 3 round approximation, increment counter if result is zero
                result = plaintext[0] ^ U4[1] ^ U4[5]
                if result == 0:
                        counter[subkey5_bits] += 1

        # Whichever 8 bit guess for partial subkey5 gave the biggest deviation from 32,768 is the correct one. Expected deviation is approx 4096.
        print "Partial Subkey: " + str(subkey5_bits) + " Deviation: " + str(counter[subkey5_bits]-32768)
        if abs(counter[subkey5_bits]-32768) > 3900:
                print "Partial Subkey " + str(subkey5_bits) + " is a candidate key!"

# This identified 8 bits of subkey5. The partial subkey is 1101 1101 XXXX XXXX.


# Next we attack the fourth 4 bit block of subkey5
# P6 + P7 + P8 + U4,5 + U4,13 = 0 with bias 1/64

# For each of the 16 possible values for the bits of partial subkey5
counter = [0] * 16
for subkey5_bits in range(0,16):

	# Turn the int into a 4 bit BitArray
	subkey5_bits_array = BitArray('uint:4='+str(subkey5_bits))

	# For each of the 64k plaintext/ciphertext pairs
	for i in range(0,65536):
		plaintext = BitArray('uint:16='+str(i))
		ciphertext = BitArray('uint:16='+str(samples[i].split()[1]))

		# XOR this subkey bits guess with relevant bits of ciphertext to get V4 bits
		V4_1 = ciphertext[4:8] ^ BitArray('bin=1101')	# Hardcode the value for the second 4 bit block as we already cracked it
		V4_2 = ciphertext[12:16] ^ subkey5_bits_array

		# Then put that backwards through sbox to get back to U4 bits
		U4_1 = sbox_decrypt[V4_1.uint]
		U4_2 = sbox_decrypt[V4_2.uint]
	        U4_str = "{0:b}".format(U4_1).zfill(4) + "{0:b}".format(U4_2).zfill(4)
        	U4 = BitArray(bin=U4_str)

		# XOR U4 bits together with plaintext bits, increment counter if result is zero
		result = plaintext[5] ^ plaintext[6] ^ plaintext[7] ^ U4[0] ^ U4[4]
		if result == 0:
			counter[subkey5_bits] += 1

	# Whichever 4 bit guess for partial subkey5 gave the biggest deviation from 32,768 is the correct one. Expected deviation is approx 1024.
	print "Partial Subkey: " + str(subkey5_bits) + " Deviation: " + str(counter[subkey5_bits]-32768)
	if abs(counter[subkey5_bits]-32768) > 900:
		print "Partial Subkey " + str(subkey5_bits) + " is a candidate key!"

# This identified 4 more bits of subkey5. The partial subkey is now 1101 1101 XXXX 1101.



# Finally we attack the third 4 bit block of subkey5
# P13 + P15 + U4,4 + U4,12 = 0 with bias 1/32

# For each of the 16 possible values for the bits of partial subkey5
counter = [0] * 16
for subkey5_bits in range(0,16):

	# Turn the int into a 4 bit BitArray
        subkey5_bits_array = BitArray('uint:4='+str(subkey5_bits))

        # For each of the 64k plaintext/ciphertext pairs
        for i in range(0,65536):
                plaintext = BitArray('uint:16='+str(i))
                ciphertext = BitArray('uint:16='+str(samples[i].split()[1]))

                # XOR this partial subkey5 guess with relevant bits of ciphertext to get back to V4 bits
                V4_1 = ciphertext[0:4] ^ BitArray('bin=1101')	# Hardcode the value for the first 4 bit block as we already cracked it
                V4_2 = ciphertext[8:12] ^ subkey5_bits_array

                # Then put that backwards through sbox to get back to U4 bits
                U4_1 = sbox_decrypt[V4_1.uint]
                U4_2 = sbox_decrypt[V4_2.uint]
                U4_str = "{0:b}".format(U4_1).zfill(4) + "{0:b}".format(U4_2).zfill(4)
                U4 = BitArray(bin=U4_str)

                # XOR the relevant U4 bits and plaintext bits as per our 3 round approximation, increment counter if result is zero
               	result = plaintext[12] ^ plaintext[14] ^ U4[3] ^ U4[7]
                if result == 0:
                        counter[subkey5_bits] += 1

        # Whichever 4 bit guess for partial subkey5 gave the biggest deviation from 32,768 is the correct one. Expected deviation is approx 2048.
        print "Partial Subkey: " + str(subkey5_bits) + " Deviation: " + str(counter[subkey5_bits]-32768)
        if abs(counter[subkey5_bits]-32768) > 1800:
                print "Partial Subkey " + str(subkey5_bits) + " is a candidate key!"
                                                                                      
# This identified the final 4 bits of subkey5. The entire subkey5 is 1101 1101 1101 1101 = 56797

