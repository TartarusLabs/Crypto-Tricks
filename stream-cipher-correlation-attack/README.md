# Stream Cipher Correlation Attack PoC

If you are new to cryptanalysis I recommend reading the four references listed at the bottom of this page before trying to follow any of this. They can be found online as PDFs if you just copy the papers' titles into a search engine.


### The Stream Cipher (stream-cipher.py)

This walkthrough is concerned with the implementation, cryptanalysis and then improvement of a stream cipher consisting of four Linear Feedback Shift Registers (LFSRs) and a combining function f(x1,x2,x3,x4) over four binary inputs. 

The truth table for the combining function is shown below.

![Original combining function truth table](https://github.com/TartarusLabs/Crypto-Tricks/blob/main/stream-cipher-correlation-attack/combining-function-truth-table-original.jpg?raw=true)

The sizes of the four LFSRs and their tap sequences are given below:

LFSR1: 7-bit register, tap={4, 7}
LFSR2: 11-bit register, tap={3, 8, 9, 11}
LFSR3: 13-bit register, tap={8, 11, 12, 13}
LFSR4: 15-bit register, tap={14, 15}

In the above, bit n is the least significant bit of the n-bit register. This is the bit that forms an input into the combining function when the register is shifted. This bit is always part of the corresponding tap sequence as the LFSRs have maximal periods.

The LFSRs are clocked synchronously and the least significant bit from each of the four LFSRs is used as input to the combining function. The output of the combining function f with these four inputs forms the next keystream bit.

The python script that implements this stream cipher is called stream-cipher.py 

The combining function is implemented simply as a list, with the 4 bit input to the function being used as an index and the output being the value stored at that index.

I first created a function to implement any desired LFSR. The inputs to this function consist of a list of bit positions making up the tap sequence, a BitArray specifying the initial state, and the number of bits of output that are required. When this function is called, its output is simply a BitArray containing the desired number of output bits from the LFSR described by the input. This entire function consists of only 12 lines of python code.

Using that function to implement the entire stream cipher is quite straightforward. The function is called four times with the four different initial states and tap sequences. This results in four BitArrays of LFSR output which are then fed into the combining function to produce a BitArray containing the keystream. 


### Correlation Attack (siegenthaler.py)

The stream.txt file contains 2000 bits of keystream produced by stream-cipher.py using initial states for the four LFSRs that are unknown to us as the attacker. Our challenge is to recover those initial states and thus break the entire stream.

To implement the Siegenthaler divide and conquer attack [1] it was first necessary to discover any correlation between the output of the combining function and its four inputs. That is to say, I needed to check if the output of the function is the same as any one of its inputs (or the XOR of any combination of them) either more than or less than 50% of the time.

I wrote a python script siegenthaler.py that generates a linear approximation table [4] of the combining function, in much the same way that an S-box is evaluated in a linear cryptanalysis attack. The script simply iterates through all 16 possible inputs to the boolean function for all 16 possible input sums and keeps track of how many times the input agrees with the output for each input sum. This table is included below:

Input | Sum Bias
----------------
0 | 0
1 | 0
2 | -4
3 | 0
4 | 0
5 | 0
6 | 0
7 | -4
8 | -2
9 | 2
10 | 2
11 | 2
12 | -2
13 | 2
14 | -2
15 | -2

If you calculate a Walsh-Hadamard spectrum of the combining function it can be seen that each value in that is exactly double the value of the bias at the equivalent point in the above linear approximation table. Hence the same information regarding correlations is revealed by both.

Both the Walsh-Hadamard spectrum and the linear approximation table revealed that input x1 is the same as the output f(x) 3/8 of the time and input x3 is the same as f(x) 2/8 of the time. For inputs x2 and x4 there was no first order correlation. This meant that it was possible to attack LFSR1 and LFSR3 individually straight away.

I began to add the implementation of the attack in siegenthaler.py by first reading in the 2000 bits of keystream we were given to attack and storing it in a BitArray. The script then began to iterate through the 2 ^ 7 = 128 different possible initial states for LFSR1, generating 2000 bits of output from it each time. Each time, the output was compared to the 2000 bits of keystream. This continued until an initial state was found that gave approximately 3/8 agreement between the output of LFSR1 and the provided keystream. In fact I had the script stop as soon as an initial state was found that gave less than 800/2000 agreement with the keystream. This recovered the following initial state.

LFSR1: 27

I then implemented the exact same approach with LFSR3. This consisted of iterating through 2 ^ 13 = 8192 different initial states and stopping when one was found that gave approximately 2/8 agreement between the LFSR output and the provided keystream. This time the script stops once an initial state is found that gives less than 600/2000 agreement. This recovered the following initial state.

LFSR3: 991

The Walsh-Hadamard spectrum and the linear approximation table both also revealed a second order correlation involving the XOR of x1 and x4 compared to the output f(x) of the combining function. They agree 5/8 of the time. Since I had already recovered the initial state of LFSR1 this meant I could now break LFSR4 by generating 2000 bits from it with each of the possible 2 ^ 15 = 32,768 initial states, XORing it with the known correct 2000 bits from LFSR1 and comparing the result to the 2000 bit target keystream. When I had guessed the correct initial value of LFSR4 this would give approximately 5/8 agreement whereas all the incorrect guesses would give about 50% agreement. Using this technique the following initial state was recovered for LFSR4.

LFSR4: 3254

I could now simply brute force the remaining register, LFSR2. There is in fact another second order correlation involving the XOR of LFSR1 and LFSR2 (this agrees with the combining function 3/8 of the time) which could be exploited but since LFSR2 was now the only remaining register this would be quite pointless and a simple brute force is actually no harder. The script therefore iterates through the 2 ^ 11 = 2048 initial states for LFSR2 and generates 2000 bits of output each time. These are combined with the known correct 2000 bits of output from each of the other three LFSRs and fed into the combining function to generate 2000 bits of keystream. Once this is found to generate the exact same 2000 bits as the target keystream the correct initial state of LFSR2 has been found. By this exhaustive search the following initial state was recovered for LFSR2.

LFSR2: 474

So in conclusion we have the following initial states for the four LFSRs.

LFSR1: 27
LFSR2: 474
LFSR3: 991
LFSR4: 3254

This divide and conquer attack reduced the complexity of finding the key from a worst case of checking 2 ^ (7+11+13+15) = 2 ^ 46 keys down to a worst case of checking (2 ^ 7) + (2 ^ 11) + (2 ^ 13) + (2 ^ 15) = 43136 keys.


### Improving The Cipher (combining-function.py)

It is possible to improve the cipher by replacing the combining function with a better one.

Given that the combining function has 4 inputs it is possible to represent each possible combining function as a vector of 2 ^ 4 = 16 outputs. There are therefore 2 ^ 16 = 65536 different possible combining functions to choose from.

I wrote a python script to simply iterate through each one carrying out some checks. The script is named combining-function.py. The first check was to make sure that the Hamming weight is 8 and hence the function is balanced. If this is true my script then generates a linear approximation table [4] and checks to see if any of the individual inputs (ie input sums 1, 2, 4 and 8) have a bias of anything other than zero. If all four have bias zero then this is a suitable function given the criteria specified in this question.

My script took only a couple of minutes to identify all 222 different boolean functions that are both balanced and correlation immune of order 1 [2].

This is not actually sufficient for finding a suitable combining function though, as it does not take into account how linear the function is. It would be useful to check that the candidate function is sufficiently non-linear by checking its minimum distance to any affine function. For example, one of the 222 combining functions that my script returned was simply the XOR of the first three inputs. This would in fact completely ignore the fourth LFSR and would also be completely linear and hence a very poor choice of combining function indeed, despite being balanced and correlation immune order 1.

I therefore decided to improve matters by modifying my python script to also calculate the non-linearity of each candidate combining function using the formula 1/2 (2^n – max_{w}|F(w)|), where n is the number of input bits and max_{w}|F(w)| is the maximum absolute value |F(w)| over all w, taken from the Walsh Hadamard spectrum.

This revealed that of the 222 balanced, correlation immune order 1 functions, 22 of them have a non-linearity of zero and the other 200 have a non-linearity of 4.

In addition to this I altered my script to check for input sums 3, 5, 6, 9, 10 and 12 all being zero too. Whenever this is true we have a boolean function that is correlation immune of order 2. Of the 222 order 1 immune functions only 10 were also order 2 immune. Unfortunately all 10 of them also had a non-linearity score of zero and hence were unsuitable. It is explained in [2] that there is in fact a trade off between non-linearity and the order of correlation immunity. As one increases the other decreases.

This effectively left me with a choice of 200 combining functions all of which are balanced, correlation immune order 1 and have a non-linearity of 4. These 200 are all equally suitable based on the criteria under consideration and therefore I picked one at random.

My new combining function is therefore [1,1,0,0,1,0,0,1,0,0,1,1,1,0,0,1]. The function is also represented as a truth table below.

![Improved combining function truth table](https://github.com/TartarusLabs/Crypto-Tricks/blob/main/stream-cipher-correlation-attack/combining-function-truth-table-improved.jpg?raw=true)

The original combining function also had a non-linearity of 4 and was balanced, but it was not correlation immune even of order 1 and hence it can immediately be seen that the new function is an improvement.

Using this as the combining function in our stream cipher increases the security as when executing the Siegenthaler divide and conquer attack [1] we now have to break two LFSRs at a time. The attacker is restricted to exploiting second order correlations. For example, the Walsh-Hadamard spectrum for the new function reveals that x3 + x4 = f(x) with probability 1/4. This can be exploited to find the initial state of LFSR3 and LFSR4 together with a worst case of checking 2 ^ (13 + 15) = 2 ^ 28 guesses. Just achieving that is vastly more costly than the entire attack was with the original combining function.

It should be noted that my method for identifying suitable combining functions works fine for a combining function with only 4 inputs (and hence 2 ^ 4 = 16 outputs and 2 ^ 16 = 65536 possible combining functions).

However, as the number of inputs to the combining function increases the feasibility of my technique decreases. Rather than attempting to iterate through all the possible functions in order and checking each one a more sophisticated approach covered in the literature is to use meta-heuristic search. One such example of this is covered in [3].


### References

[1] - T. Siegenthaler, “Decrypting a class of stream ciphers using ciphertext only”, IEEE Trans. On Computers, vol. C-34, 1985, pp. 81-85.

[2] - T. Siegenthaler, “Correlation-immunity of nonlinear combining functions for cryptographic applications,” IEEE Trans. Inform. Theory, vol. IT-30, pp. 776–780, Sept. 1984.

[3] - John A. Clark et al. “Almost Boolean Functions: the Design of Boolean Functions by Spectral Inversion”. Computational Intelligence, Vol 20, Issue 3. pp 450–462. August 2004.

[4] - Howard M. Heys, “A Tutorial on Linear and Differential Cryptanalysis”. Cryptologia. Volume 26 Issue 3, pp 189-221. July 2002.


