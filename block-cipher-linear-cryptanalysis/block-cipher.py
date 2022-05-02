#!/usr/bin/env python2

# Implementation of a variant of the block cipher described in "A Tutorial on Linear and Differential Cryptanalysis" by Howard M. Heys
# https://github.com/TartarusLabs/Crypto-Tricks/block-cipher-linear-cryptanalysis/
# james.fell@alumni.york.ac.uk


from bitstring import BitArray

###
# Configure subkeys and S-box

# Set the 5 subkeys 
subkey1 = BitArray(bin='0001000000100100') # 4132
subkey2 = BitArray(bin='0001111111100101') # 8165
subkey3 = BitArray(bin='0011011111001111') # 14287
subkey4 = BitArray(bin='1101010000110001') # 54321
subkey5 = BitArray(bin='1100111110000100') # 53124

# Hardcoded S box as per our modified cipher specification
sbox = [4,0,12,3,8,11,10,9,13,14,2,7,6,5,15,1]
###


# Function to apply the P Box to a bit array and return the result
def permutation(inputBlock):
	block_out = BitArray(length=16)
        block_out[0] = inputBlock[0]
        block_out[1] = inputBlock[4]
        block_out[2] = inputBlock[8]
        block_out[3] = inputBlock[12]
        block_out[4] = inputBlock[1]
        block_out[5] = inputBlock[5]
        block_out[6] = inputBlock[9]
        block_out[7] = inputBlock[13]
        block_out[8] = inputBlock[2]
        block_out[9] = inputBlock[6]
        block_out[10] = inputBlock[10]
        block_out[11] = inputBlock[14]
        block_out[12] = inputBlock[3]
        block_out[13] = inputBlock[7]
        block_out[14] = inputBlock[11]
        block_out[15] = inputBlock[15]
        return block_out


# Function to complete one round of encryption. Caller must pass in a 16 bit block to encrypt and specify which round it is.
def cipher_round(roundInputBlock, roundNumber):

	# Select the correct subkey for this round
	if roundNumber==1:
		subkey=subkey1
	elif roundNumber==2:
		subkey=subkey2
        elif roundNumber==3:
                subkey=subkey3
        elif roundNumber==4:
	        subkey=subkey4
	
	# XOR input block with appropriate subkey
	xorBlock = roundInputBlock ^ subkey

	# break result into 4 blocks of 4 bits
	block1 = xorBlock[0:4]
	block2 = xorBlock[4:8]
	block3 = xorBlock[8:12]
	block4 = xorBlock[12:16]

	# replace each 4 bit block with another using the S-box
	block1_s = sbox[block1.uint]
	block2_s = sbox[block2.uint]
	block3_s = sbox[block3.uint]
	block4_s = sbox[block4.uint]

	# combine each 4 bit block back into one 16 bit block
	block_s_str = "{0:b}".format(block1_s).zfill(4) + "{0:b}".format(block2_s).zfill(4) + "{0:b}".format(block3_s).zfill(4) + "{0:b}".format(block4_s).zfill(4)
	block_s = BitArray(bin=block_s_str)
	
	# If this is the fourth round we finish by XORing the 16 bit block with subkey5
	if roundNumber==4:
		return block_s ^ subkey5
	# For any other round we just apply the permutation 
	else:
		return permutation(block_s)


# Function to carry out four rounds of encryption and return the ciphertext
def encrypt(plaintext):
    return cipher_round(cipher_round(cipher_round(cipher_round(plaintext, 1), 2), 3), 4)



# Generate all 2^16 possible 16 bit plaintext blocks along with their ciphertext to use as a target for our linear cyptanalysis attack
print "Generating 65,536 plaintext/ciphertext pairs for linear cryptanalysis"
samples = open('plaintext-ciphertext-out.txt', 'w')
for num in range(0,65536):
	plain = BitArray('uint:16='+str(num))
	samples.write(str(plain.uint) + "  ")
    	samples.write(str(encrypt(plain).uint)+"\n")
samples.close()
print "plaintext-ciphertext-out.txt created"

