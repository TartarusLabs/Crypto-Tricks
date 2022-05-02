# LSB Steganography with Pseudorandom Embedding Algorithm

### Design and implementation

The design presented assumes a passive warden adversary rather than an active warden [12]. We are therefore concerned only with the hidden data inside the stego-image not being detected by someone examining the image. The design does not take into account a need for the stego-image to retain its hidden data if it is modified by an adversary who is trying to disrupt all possible covert communications, such as by converting all images from one format to another or randomising all of the least significant bits (LSBs).

The design presented here is a variation of the standard LSB technique in the spatial domain [9]. It is well documented in the literature that the human eye cannot distinguish between small differences in RGB (Red, Green, Blue) levels in an image. It is therefore possible to hide data by modifying the least significant bit of each of the RGB bytes for each pixel in a raster graphics image such as a BMP or PNG file [1]. To develop this idea further, our design involves selecting which pixels (and indeed which of the RGB elements of each pixel) to modify in a pseudorandom way based on a password provided by the user rather than simply starting in the top left of the image and working through the pixels sequentially as a naive implementation might do. Variations of this theme are covered in the literature [2] although they do not function in exactly the same way as the design presented here.

This modification increases the security of the system in two ways. Firstly, spreading the hidden data out amongst the available pixels instead of concentrating it in one area of the image makes detection more difficult (although certainly not impossible), as degradation of image quality is also spread out [11]. The HideSeek algorithm described in [7] uses the same approach although the researchers report that it "often causes the resulting stego-image to look speckled". Our design improves upon this by treating the RGB components of each pixel as separate entities and selecting each of them in a pseudorandom way rather than only selecting whole pixels in this way. So for example, in our system it is possible for a pixel to have only its Green element's LSB altered while the Red and Blue components of that same pixel may go unmodified. The resulting stego-image looks indistinguishable from the cover image to the naked eye.

Secondly, without the password it is impossible for an adversary to extract the hidden data, even if they suspect that it is present. For example, a passive warden may choose to simply extract the LSBs in left-to-right, top-to-bottom order from each image being examined and attempt to determine if the result has any meaning [7]. In a naive system this attack would work, assuming the data is not encrypted before embedding. For our system it would not work, as it is impossible to extract the hidden message without knowing the password that was used when hiding it. This is true even if the adversary has a copy of our steganography software and understands exactly how it works. Kerckhoff's prinicple is satisfied as security depends only upon keeping the password secret and not on keeping the algorithm secret [8].

The precise way the pseudorandom embedding is achieved is as follows. The application first calculates how many LSBs are available in the cover image. For a 24 bit colour PNG file this is simply a calculation of image height x image width x 3. An array is then created of the form [0,1,2,3,4....n-1] where n is the number of available LSBs. Each number in the array represents a specific LSB in the image, starting from the top left and working through Red, Green and then Blue for each pixel. So for example, 0 is the Red component of the top left pixel, 4 is the Green component of the pixel immediately to its right, and n-1 is the Blue component of the bottom right pixel. Thus we have an array where each item represents a specific single LSB in the cover image that can be modified to conceal one bit of message data.

The password that was provided by the user is then hashed and the result is used to seed Python's built-in pseudorandom number generator. This means that every time the same password is used the same pseudorandom sequence will be generated. Next the Python random function is used to 'shuffle' the array of LSBs and create a pseudorandom permutation of it. Once the array has been permutated it is used as the order in which the software picks LSBs to hide the data in. So to hide 100 bits of data the application would now use the first 100 LSBs as listed in the shuffled array.

To recover the hidden message from the stego-image, the same password must be used again. The array of LSBs is shuffled in the exact same way and the relevant LSBs are read to reconstruct the message. Without the correct password it is not possible to create the correct permutation and hence it is not possible to determine the correct pixels to examine.

An additional feature of the design is that after converting a text file into a stream of bits suitable for hiding, our application also adds a 24 bit header which contains the length of the hidden message in bits. When recovering the message back from the stego-image this allows the application to easily determine how many bits need extracting.

Running stego.py -h reveals all the command line options and their functions. These will also now be explained here.

The -m switch allows the user to specify which mode to run in. This must be set to either 'embed' or 'recover' depending on whether the intention is to hide a new message in a cover image, or recover a message from an existing stego-image. In 'embed' mode the stego-image will be called out.png. In 'recover' mode the message will be saved to out.txt.

The -p switch specifies the password to use. The usual rules for picking strong passwords apply here, as an attacker could carry out a dictionary attack against a suspected stego-image.

The -i switch specifies the image to read in. When in 'embed' mode this will be the cover image to use, when in 'recover' mode this will be the stego-image to recover the message from.

The -t switch is only used when in 'embed' mode and it specifies the text file containing the message to hide. 

For example, below we see what was typed to run the program in embed mode with a password of 'm0uNta1n123', a cover image of in.png and a text file to hide of secret.txt. The application's output is also shown.

`./stego.py -m embed -p m0uNta1n123 -i in.png -t secret.txt`

`Data hidden (including 24 bit header we add): 64185 bits.`
`Total capacity of cover image: 145200 bits.`
`Utilisation: 44.20%`
`Saving resulting stego image to out.png`

Viewing out.png reveals that it looks exactly like in.png. There are no differences perceivable to the naked eye. We would then run it in recover mode with the same password and out.png as the image to recover the hidden text.

`./stego.py -m recover -p m0uNta1n123 -i out.png`

`Data extracted (excluding 24 bit header): 64161 bits.`
`Saving recovered hidden message to out.txt`

Checking the contents of the out.txt file now reveals the message that was in secret.txt which confirms that the system is working. If an incorrect password is used it can also be seen that random nonsense is the result instead.


### Measuring the performance using steganalysis

Mean Square Error (MSE) and Peak Signal to Noise Ratio (PSNR) are two measures of image quality degradation that can be calculated when comparing the stego image to the original cover image [6]. I have implemented these two measures in the python script steganalyse.py. When executed to compare the in.png cover image to the resulting out.png stego-image the following values are calculated.

Mean Square Error (MSE): 0.165909090909
Peak Signal to Noise Ratio (PSNR): 55.9660974699

Keeping a low embedding rate is helpful for avoiding detection [4]. For this reason an improved embedding scheme would compress the message text file before performing the actual stego embedding. The less message bits we have to hide, the better. Another way of achieving this would be to use batch steganography where a message is spread over multiple cover images as necessary to maintain some maximum embedding rate in each each image [5]. Either of these modifications to the presented design, or indeed combining both, would reduce the disruption caused.

Another improvement to our original embedding scheme would be to preserve the first order statistics of the cover image as much as possible when choosing which pixels to use for embedding. This could be achieved by incorporating an edge detection algorithm [7]. If we only make use of pixels that are in areas of the image with a lot of contrast, and skip over any parts of the image with similar colours this will make it harder to detect using statistical techniques such as those above and more advanced techniques like RS analysis[3], Sample Pair attack[3] and Chi-Square attack [10].


### References

[1] - Neil F. Johnson and Sushil Jajodia, George Mason University. “Exploring Steganography: Seeing the Unseen” in IEEE Computer, February 1998, pp 26-34.

[2]- Kshetrimayum Jenita Devi, Department of Computer Science and Engineering, National Institute of Technology-Rourkela Odisha. “A Secure Image Steganography Using LSB Technique and Pseudo Random Encoding Technique”.

[3] - Benedikt Boehm, School of Computing, University of Kent. “StegExpose: A Tool For Detecting LSB Steganography”, October 2014.

[4] - Andrew D. Ker et al. “The Square Root Law of Steganographic Capacity”.

[5] - Andrew D. Ker, Oxford University Computing Laboratory. “Batch Steganography and Pooled Steganalysis” in Information Hiding, Springer, pp 265-281.

[7] - Kathryn Hempstalk, University of Waikato. “Hiding Behind Corners: Using Edges in Images for Better Steganography“ in Intelligent Computing Theories, Volume 7995 of the series Lecture Notes in Computer Science, pp 593-600.

[8] - Auguste Kerckhoffs, "La cryptographie militaire", Journal des sciences militaires, vol. IX, pp. 5–83, Jan. 1883, pp. 161–191, Feb. 1883.

[9] - Charles Kurak and John McHugh, Department of Computer Science, University of North Carolina. “A Cautionary Note on Image Downgrading” in proceedings of 8th Computer Security Applications Conference, 1992, pp 153-159.

[10] - Andreas Westfeld and Andreas Pfitzmann, Dresden University of Technology. “Attacks on Steganographic Systems” in Third International Workshop, IH’99, Dresden, Germany, September 29 - October 1, 1999 Proceedings, pp 61-76.

[11] - Niels Provos and Peter Honeyman, University of Michigan. “Hide and Seek: An Introduction to Steganography” in IEEE Privacy and Security, 2003.

[12] - Mark Owens, SANS Institute Reading Room. “A Discussion of Covert Channels and Steganography”, March 2002.

