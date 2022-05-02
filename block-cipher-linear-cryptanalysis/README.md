# Linear Cryptanalysis Attack PoC

If you are new to linear cryptanalysis I recommend at least reading [1] from the References section at the bottom of this page before trying to follow any of this. It can be found online as a PDF if you copy and paste the paper's title into a search engine.


### The Block Cipher (block-cipher.py)

This walkthrough is concerned with the implementation, cryptanalysis and then improvement of a variant of the 2002 Heys block cipher [1]. The variant is identical to the Heys cipher but uses a different substitution box (S-Box) given below (using hex representation):

{0x4, 0x0, 0xC, 0x3, 0x8, 0xB, 0xA, 0x9, 0xD, 0xE, 0x2, 0x7, 0x6, 0x5, 0xF, 0x1}

Thus, the S-Box maps binary inputs 0000 to 0100, 0001 to 0000, 0010 to 1100, 0011 to 0011, 0100 to 1000, and so on.

My implementation of the cipher is in the block-cipher.py file.

I implemented the S-box as a simple python list such that the input can be treated as an index and the output is whatever value is stored at that index. The permutation was implemented as a function that takes a 16 bit BitArray as input and simply changes the order of the bits appropriately and returns the rearranged BitArray.

Based on this I was then able to create a function to carry out a single round of encryption. The round number (1 to 4) is passed in as an argument along with a block to encrypt in the form of a 16 bit BitArray. The input block is XORed with the appropriate round key and then split up into 4 blocks of 4 bits. Each one is passed through the S-box and the result is then recombined into a single 16 bit block. The block is then put through the permutation function and returned, unless the current round is number 4 in which case it is XORed with the fifth subkey instead.

The full four rounds of encryption are applied by simply calling the above function four times with the round number argument being incremented each time and the output of each call being used as the input for the next.

When executed the script generates a file called plaintext-ciphertext-out.txt which contains the encryption of all 65,536 possible 16-bit plaintext blocks based on the 5 subkeys currently configured.


### Linear Cryptanalysis Attack (linear-cryptanalysis.py)

The file plaintext-ciphertext.txt contains all 64K (2^16) possible plaintext-ciphertext pairs generated using block-cipher.py and five subkey values that are not known to us as the attacker. This file will be used as the target of our attack with the goal being to retrieve the value of the fifth subkey. The attack could (and obviously would) be continued to recover all five subkeys but recovering just one will suffice to demonstrate it.

Every possible 16 bit plaintext block has been encrypted. Encryption has been performed with the full 4 rounds. Plaintexts and ciphertexts are 16 bits and are represented in plaintext-ciphertext.txt by their natural non-negative integer interpretations. For example, the integer 13 represents the 16-bit text 0000000000001101, and the integer 65 represents the 16-bit text 0000000001000001.

My implementation of the attack is in the linear-cryptanalysis.py file.

The first task was to generate a linear approximation table [1] for the S-box. Again the S-box was implemented simply as a list. The linear approximation table itself was implemented as a 16 by 16 two dimensional list with all values initialised to -8. Three nested for loops were then used to iterate through all 16 possible input sums, all 16 possible output sums, and all 16 possible inputs to the S-box. This gave a total of 16 ^ 3 = 4096 total executions of the code in the inner for loop to generate the table.

The code in the innermost for loop starts by doing a lookup on the current input value to obtain the corresponding output value from the S-box. The input to the S-box is then bitwise ANDed with the input sum and all 4 bits of the result are XORed together. The output from the S-box is bitwise ANDed with the output sum and all 4 bits of the result are XORed together. Whenever those two operations generate the same result the number in the linear approximation table is incremented for that combination of input sum and output sum. Once the nested for loops have finished executing, the linear approximation table is complete.

The resulting Linear Approximation Table for the S-box is below. This is a tabulated form of the output from linear-cryptanalysis.py. The rows are the input sums and the columns are the output sums.

![Linear Approximation Table](https://github.com/TartarusLabs/Crypto-Tricks/blob/main/block-cipher-linear-cryptanalysis/linear-approximation-table.jpg?raw=true)

After generating the linear approximation table, I manually calculated three different three round approximations for use in the linear cryptanalysis attack [1]. The specific approximations used at each round along with the specific S-boxes involved are shown in the table below. The numbers in parentheses after each S box are the input sum followed by the output sum, both given in decimal.

![Approximations](https://github.com/TartarusLabs/Crypto-Tricks/blob/main/block-cipher-linear-cryptanalysis/approximations.jpg?raw=true)

I will now detail the derivation of the final three round approximations based on the table above. This also includes the calculation of the final biases based on the piling up lemma [1].

Approximation1 allows us to discover the 8 key bits K5,1 to K5,8 inclusive.

P1 + K1,1 = V1,2 with probability 3/4	(1)

U2,5 = K2,5 + V1,2 always and
U2,5 = V2,6 with probability 3/4	(2)

Therefore from (1) and (2) we get K2,5 + P1 + K1,1 = V2,6 with probability 1/2 + 2(3/4 – 1/2)(3/4 – 1/2) = 5/8	(3)

U3,6 = K3,6 + V2,6 always and
U3,6 = V3,5 + V3,6 with probability 3/4	(4)

From (3) and (4) we get K3,6 + K2,5 + P1 + K1,1 = V3,5 + V3,6 with probability 1/2 + 2(5/8 – 1/2)(3/4 – 1/2) = 9/16

As V3,5 + K4,2 = U4,2 and V3,6 + K4,6 = U4,6 we have
K3,6 + K2,5 + P1 + K1,1 = U4,2 + K4,2 + U4,6 + K4,6 with probability 9/16

As the XOR of all the key bits is fixed we remove them, leaving the final three round approximation as follows:

	P1 + U4,2 + U4,6 = 0 with probability 9/16


Approximation2 allows us to discover the 4 key bits K5,13 to K5,16 inclusive. It also involves K5,5 to K5,8 inclusive but as they have already been targeted by Approximation1 we can hard code the correct value when we implement the attack.

P6 + K1,6 + P7 + K1,7 + P8 + K1,8 = V1,8 with probability 1/4	(1)

U2,14 = K2,14 + V1,8 always and
U2,14 = V2,13 with probability 5/8	(2)

Therefore from (1) and (2) we get K2,14 + P6 + K1,6 + P7 + K1,7 + P8 + K1,8 = V2,13
with probability 1/2 + 2(1/4 – 1/2)(5/8 – 1/2) = 7/16	(3)

U3,4 = K3,4 + V2,13 always and
U3,4 = V3,2 + V3,4 with probability 5/8	(4)

Therefore from (3) and (4) we get K3,4 + K2,14 + P6 + K1,6 + P7 + K1,7 + P8 + K1,8 = V3,2 + V3,4
with probability 1/2 + 2(7/16 – 1/2)(5/8 – 1/2) = 31/64

As V3,2 + K4,5 = U4,5 and V3,4 + K4,13 = U4,13 we have
K3,4 + K2,14 + P6 + K1,6 + P7 + K1,7 + P8 + K1,8 = U4,5 + K4,5 + U4,13 + K4,13 with probability 31/64

As the XOR of all the key bits is fixed we remove them, leaving the final three round approximation as follows:

	P6 + P7 + P8 + U4,5 + U4,13 = 0 with probability 31/64


Approximation3 allows us to discover the 4 key bits K5,9 to K5,12 inclusive. It also involves K5,1 to K5,4 inclusive but as they have already been targeted by Approximation1 we can hard code the correct value when we implement the attack.

P13 + K1,13 + P15 + K1,15 = V1,15 + V1,16 with probability 3/4	(1)

U2,12 = K2,12 + V1,15 always and
U2,12 = V2,12 with probability 3/4	(2)

U2,16 = K2,16 + V1,16 always and
U2,16 = V2,16 with probability 3/4	(3)

Therefore from (2) and (3) we get V2,12 + V2,16 + K2,12 + V1,15 + K2,16 + V1,16 = 0		(4)
with probability 1/2 + 2(3/4 – 1/2)(3/4 – 1/2) = 5/8 

From (1) and (4) we get P13 + K1,13 + P15 + K1,15 + V2,12 + V2,16 + K2,12 + K2,16 = 0	(5)
with probability 1/2 + 2(3/4 – 1/2)(5/8 – 1/2) = 9/16 

U3,15 = K3,15 + V2,12 always and
U3,16 = K3,16 + V2,16 always and
U3,15 + U3,16 = V3,13 + V3,15 with probability 1/4	(6)

From (5) and (6) we have P13 + K1,13 + P15 + K1,15 + K3,15 + K3,16 + K2,12 + K2,16 + V3,13 + V3,15 = 0	(7)
with probability 1/2 + 2(9/16 – 1/2)(1/4 – 1/2) = 15/32

As V3,13 + K4,4 = U4,4 and V3,15 + K4,12 = U4,12 from (7) we have
P13 + K1,13 + P15 + K1,15 + K3,15 + K3,16 + K2,12 + K2,16 + U4,4 + K4,4 + U4,12 + K4,12 = 0
with probability 15/32

As the XOR of all the key bits is fixed we remove them, leaving the final three round approximation as follows:
	
	P13 + P15 + U4,4 + U4,12 = 0 with probability 15/32


So in summary the three approximations that I used to carry out my linear cryptanalysis attack are as follows.

Approximation1 to find bits K5,1 to K5,8:	P1 + U4,2 + U4,6 = 0 with probability 9/16

Approximation2 to find bits K5,13 to K5,16:	P6 + P7 + P8 + U4,5 + U4,13 = 0 with probability 31/64

Approximation3 to find bits K5,9 to K5,12:	P13 + P15 + U4,4 + U4,12 = 0 with probability 15/32


As already mentioned, by the time we use approximations 2 and 3 we already know 4 of the 8 key bits that they each target and hence only need to iterate over the remaining, unknown 4 bits. This attack therefore allows us to find all 16 bits of subkey5 by checking only (2 ^ 8) + (2 ^ 4) + (2 ^ 4) = 288 different keys. This is more efficient than implementing the attack using only two approximations and therefore having to check (2 ^ 8) + (2 ^ 8) = 512 different keys.

In order to implement the attack I did the following in linear-cryptanalysis.py for each of the three approximations. The script iterates through all possible values for the partial subkey5 bits that we are trying to recover. For each key guess it goes through the 65,536 plaintext-ciphertext pairs and evaluates the expression. It keeps a counter for how many times it holds true. Whichever partial subkey guess gives the greatest deviation from 32,768 (that is, the greatest deviation from 50%) we assume is the correct guess.

To do this it is of course necessary to be able to recover U4 bits from ciphertext bits. This is achieved by XORing the subkey guess bits with the corresponding ciphertext bits and sending the result backwards through the round 4 S-boxes. To do the reverse S-box lookup I simply created a second python list data structure that is the inverse of the one used for the forward S-box lookups. So essentially I had two lookup tables for the S-box, one forwards and one backwards.

Once I had finished writing the linear-cryptanalysis.py script I ran it against the plaintext-ciphertext.txt and it revealed the entire subkey5 to be 1101 1101 1101 1101 in binary which is 56797 in decimal.


### Improving The Cipher

The cipher could be made more resilient to linear cryptanalysis by replacing the S-Box with one which exhibits a higher non-linearity. For example, a search could be made for a different 4x4 S-box that has no bias greater than +/- 1/8 (this corresponds to a +/- 2 in the linear approximation table). This would make it impossible to create a three round linear approximation with any bias greater than 1/128, as can be seen by considering the piling up lemma [1]. Even if an S-box with those properties cannot be found, the general principle of minimising biases and maximising non-linearity holds. Creating a better S-box has much in common with the process of creating a better combining function for the stream cipher in the stream-cipher-correlation-attack folder. The code that I developed for that (combining-function.py) could probably be modified to perform this task although exhaustive search would not be a good approach this time. A more elegant approach, especially when dealing with bigger S-boxes, is to use an evolutionary search method. For example, [2] covers the use of simulated annealing to solve this problem.

A second improvement to the S-box would be to make it larger. According to [3] as the dimensions of the S-box increase, so too does the ease of finding one with high non-linearity to use in the cipher. It states that “large, randomly selected S-boxes are very likely to have high nonlinearity”. The number of known plaintexts required in order to successfully carry out linear cryptanalysis also increases with the size of the S-boxes.

As a successful linear cryptanalysis attack requires the creation of an n-1 round approximation when attacking an n round cipher, increasing the number of rounds from 4 to a larger number such as 16 will make linear cryptanalysis harder. Every extra round decreases the overall bias of the final n-1 round approximation. This can again be seen by considering the piling up lemma [1]. Of course, increasing the number of rounds also makes the cipher slower and more expensive to implement, so there is a balance to be found.

Rather than using the same S-Box in all places throughout the SPN (Substitution Permutation Network), another improvement may be to design multiple different S-boxes to use and vary them throughout the network. It can be observed that ciphers based on an SPN such as DES and LOKI do not rely on just one S-box duplicated throughout the network but rather use multiple. Intuitively this would make the creation of the n-1 round approximation more complicated as multiple linear approximation tables would need to be generated and referred to.

In [4] the principles of 'confusion' and 'diffusion' are described. We have already discussed the 'confusion' part by considering the S-box. The 'diffusion' part refers to the permutation. The existing permutation already ensures that the output bits of each S-box are spread amongst the inputs of all the different S-boxes of the next round. That is to say, there is no situation where two or more output bits from one S-box enter into the inputs of a single S-box in the next round. However, I was still able to construct three round linear approximations that only involved one S-box per round. According to [3] this can be prevented by replacing the permutation between rounds with an appropriate linear transformation. The paper proposes “another class of invertible linear transformations that may be used between rounds of S-boxes to increase the resistance to differential and linear cryptanalysis”.

Increasing the block size and hence the key size would improve the security of the cipher. For example, if the SPN was 128 bits wide instead of 16 bits, and hence each subkey was also 128 bits, this would increase the complexity of a linear cryptanalysis attack as well as defending against brute force attacks.


### References

[1] - Howard M. Heys, “A Tutorial on Linear and Differential Cryptanalysis”. Cryptologia. Volume 26 Issue 3, pp 189-221. July 2002.

[2] - John A. Clark, Jeremy L. Jacob, Susan Stepney. “The Design of S-Boxes by Simulated Annealing”. Congress on Evolutionary Computation, 2004. CEC2004. pp1533-1537 Vol.2.

[3] - Howard M. Heys, “Substitution-Permutation Networks Resistant to Differential and Linear Cryptanalysis”. Journal of Cryptology, Volume 9, Issue 1, pp 1-19. March 1996.

[4] - C. E. Shannon. “Communication theory of secrecy systems”. Bell System Technical Journal, 28:656–715, 1949.



