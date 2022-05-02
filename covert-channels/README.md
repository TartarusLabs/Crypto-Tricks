# Demonstration of a Storage-based Covert Channel

### Design

The design involves a covert storage channel [1] between two Python scripts running on a multi-user Linux system. The design satisfies all four of the criteria presented in [5] as necessary for a storage channel. To paraphrase [5], this essentially means that a shared resource has been identified with an attribute which can be modified by one process whilst being observed by another, and that we have implemented some means of initiating and synchronising the covert communication that can take place in this way. The main design requirement beyond simply establishing a covert channel was to achieve an adequate balance between stealth and bandwidth. A high level summary of the design is now given followed by a more detailed description.

The process which intends to send a message first creates an empty file in the /tmp folder with an innocuous filename. Data is then communicated through it by changing the file's metadata in a specific way [8]. The actual content of the file is never used to store the hidden message. The receiving process examines the same file's metadata and extracts the message. As file metadata is being used in a way that was not intended or expected by the system's designers, the fact that the two processes are communicating will not be obvious. The US Department of Defense TCSEC (Trusted Computer System Evaluation Criteria) standard defines a covert channel as “any communication channel that can be exploited by a process to transfer information in a manner that violates the system’s security policy” [3]. Assuming the security policy on our system includes that the two processes described above should not be able to communicate with each other, our design satisfies this definition. The precise details of the design are now explained.

All users on a standard Linux system have access to the /tmp directory and can at least read the metadata (size, file permissions, timestamps etc) of each file in it even if they do not have permissions to read the file's content. This design will therefore work even when the two processes which have to communicate covertly are running as two different users on the system, as would often be the case in a realistic scenario where the sending process would be running at elevated privileges relative to the receiving process [7].

On a Linux system each file has three timestamps known as ctime, mtime and atime (changed, modified and accessed) [4]. The atime and mtime attributes can be modified at will by the user, whereas the operating system itself controls ctime and does not allow user applications to set arbitrary values. Each of the three timestamps is stored as a 32 bit number indicating the number of seconds that has passed since midnight UTC on 1 st January 1970. It is therefore possible to communicate 64 bits of data in a covert way by setting the atime and mtime attributes of a file to the appropriate 32 bit values. This therefore can be exploited as a covert storage channel [7].

There are other metadata for each file that could also be used in a similar way and that were considered for the design. For example, it would also be possible to hide 12 bits of data in the file permission metadata. On a Linux system each file has a permission which is specified as four numbers, each ranging from 0 to 7, and so each number can represent 3 bits of data. For example, to store 010 101 010 011 we would set the file permissions to 2523. There is nothing wrong with this in principle and including it would increase the bandwidth of the covert channel. However, I decided not to do this as the more items of metadata we vary the more likely the covert channel is to be noticed. The atime and mtime combined give us 64 bits of capacity as has been explained and modifying only that also gives a good level of stealth.

We exploit this storage based covert channel by repeatedly updating the metadata at a specific rate. The message is therefore communicated from one process to the other by repeatedly setting the file's timestamps at a specific rate. Each time this is done communicates another 64 bits of data. The reading process has to repeatedly read the timestamps at the same rate so that the two processes are synchronised. The faster this is attempted (ie the more times per second we update and read the atime and mtime) the more bandwidth we have. However, at some point the channel becomes unreliable. Where this threshold is will vary from server to server and will depend on factors such as how busy the server is at the time, how much CPU and RAM resources it has, and even what kind of disk storage it uses. It is also the case that the slower we communicate through the channel, the harder to detect it is [6].

Considering the possibility of the covert channel being discovered, the file itself is unlikely to stand out as it is common for applications to use the /tmp directory for obscure temporary files whilst executing. Even if the file is noticed, examining it at any moment in time will not reveal anything suspicious. Only if the file's timestamp metadata is monitored continuously over a period of time would the unusual fluctuations be noticed and the side channel potentially be identified. Also, once the message has been transmitted the cover file is deleted so it only exists at all for the period of time when the message is being sent.

There is typically a trade-off between stealth and bandwidth such that increasing one tends to decrease the other [6]. Indeed [2] also includes robustness in this trade-off stating that “capacity, robustness and stealth are conflicting goals” when designing a covert channel. I believe that the design proposed here meets a good balance. By communicating 64 bit blocks of data several times per second we have a useful amount of bandwidth but the covert channel is still stealthy enough that it is unlikely to be discovered without the use of advanced countermeasures that are specifically looking for this kind of activity on the system. The design also lends itself to having the channel's throughput easily adjusted to fit the requirements of any specific deployment. It can be slowed down as much as is deemed necessary to avoid detection.


### Implementation

The implementation of the covert channel described above is found in the files covert-write.py and covert-read.py. To use them it is necessary to start covert-read.py before starting covert-write.py.

Each python script has a settings section at the start with a few variables that can be set by the user. Both scripts have a variable called dummyFile which points to the file whose metadata will be used as the covert channel. This needs to be set the same in both scripts in order for them to communicate. The default setting is /tmp/gconfd-05 which is simply an innocuous filename that will not attract attention. 

Both scripts also have a variable called delay which is the pause time in seconds between subsequent writes or reads of the file's timestamps. Once again this needs to be set to the same value in both scripts. I tested the system on an Ubuntu server and found that a delay of 0.005 seconds was reliable, but lower values started to cause corruption of the message being transmitted. This may well vary when running the scripts on different servers or even on the same server again on another occasion depending on how busy the system is at the time. A suitable value can always be found with a bit of experimentation in any case. The higher this value, the more stealthy the channel [2, 6] but the lower its bandwidth.

The covert-write.py script has a setting called messageFile which points to the file containing the message to communicate through the covert channel. The default is secret.txt.

The covert-read.py script has a setting called outFile which points to the file where is should save the received message. The default is received.txt.

When the covert-write.py script is executed with default settings it reads in secretTextFile.txt and converts it into a string of individual bits. A 24 bit header is added to specify the message length and then padding is added to the end to make the total length a multiple of 64 bits. The empty /tmp/gconfd-05 file is then created. Every 0.005 seconds the atime and mtime are updated each with 32 bits of the message. Once the whole message has been processed this way the /tmp/gconfd-05 file is finally deleted.

When the covert-read.py script is executed with default settings it first enters a while loop that does nothing until the /tmp/gconfd-05 file exists. This means the script can be started up and left running and it will simply wait for the covert-write.py process to be executed. Once the /tmp/gconfd-05 file is detected as existing the script executes a pause of 0.0025 seconds (half the configured delay) to allow the covert-write.py process to get slightly ahead and make its first update to the timestamps. The covert-read.py process then reads the atime and mtime timestamps and stores those 64 bits. It pauses for 0.005 seconds and then reads the timestamps again. This continues until /tmp/gconfd-05 disappears because it has been deleted by covert-write.py. At that point the first 24 bits of the message are interpreted to find the length of the actual message. The header is then discarded and a number of bits equal to that length are read. The padding from the end is discarded. The resulting bits are then turned back into ASCII and saved to received.txt.

The covert-read.py process also has functionality to allow it to measure and report the bandwidth of the covert channel. As soon as it detects the creation of the /tmp/gconfd-05 file it saves the current time. Once the file deletion is detected and the message is therefore finished the process saves the current time again. The difference between the two times of course tells us how long it took to transmit the message. The number of bits transmitted divided by this time gives us bandwidth. Running the two scripts under two separate user accounts on the test server with the secret.txt file gave the output below from covert-read.py.

`Time taken (seconds): 0.159503221512`
`Data transfered (bits): 1920`
`Bandwidth (bits per second): 12037.3744292`

The empirical assessment of the channel's bandwidth is therefore 12040 bits per second, rounded to the nearest 10 bps. According to [9] any covert channel with more than 100 bps of capacity is a serious threat to the security of a system.

We can compare this measurement to what we would expect from a simple calculation. With the default delay of 0.005 seconds the writer process embeds 64 bits of data into the covert channel slightly less than 200 times every second. The reason it is not exactly 200 times per second is because the operation itself takes some amount of time. So as well as the pause of 0.005 seconds every time there is also some amount of time elapsing for getting the next 64 bits to write and actually updating the file's timestamps. The expected bandwidth would therefore be a bit less than 200 x 64 = 12800 bits per second. This simple calculation agrees well with what was measured empirically.


### References

[1] - Mark Owens, SANS Institute Reading Room. “A Discussion of Covert Channels and Steganography”, March 2002.

[2] - Sebastian Zander, Centre for Advanced Internet Architectures, Swinburne University of Technology. “Performance of Selected Noisy Covert Channels and Their Countermeasures in IP Networks, Chapter 2: Covert Channels”. [Online] Available: http://caia.swin.edu.au/cv/szander/thesis/szander_thesis_chapter_2.pdf [Accessed: 11th December 2015]

[3] - US Department of Defense. “TCSEC (Trusted Computer System Evaluation Criteria) DoDD 5200.28-STD” also known as 'The Orange Book'.

[4] - Linux-Faqs.info, “Difference between mtime, ctime and atime”. [Online] Available: http://www.linux-faqs.info/general/difference-between-mtime-ctime-and-atime [Accessed: 11th December 2015]

[5] - Richard A. Kemmerer, University of California, Santa Barbara. “Shared Resource Matrix Methodology: An Approach to Identifying Storage and Timing Channels” in ACM Transactions on Computer Systems, Vol. 1, No. 3, August 1983, pp 256-277.

[6] - Annarita Giani, Vincent H. Berk and George V. Cybenko. Thayer School of Engineering, Dartmouth College. “Data Exfiltration and Covert Channels” in Proc. SPIE 6201, Sensors, and Command, Control, Communications, and Intelligence (C3I) Technologies for Homeland Security and Homeland Defense V, 620103 (May 10, 2006).

[7] - Hamed Okhravi, Stanley Bak and Samuel T. King. University of Illinois at Urbana-Champaign. “Design, Implementation and Evaluation of Covert Channel Attacks”. 2010 IEEE International Conference on Technologies for Homeland Security.

[8] - R. Trimble et al, Covert Channels Research Group, Indiana University of Pennsylvania. “Covert Storage Channels: A Brief Overview”.

[9] - NCSC, NSA. “Covert Channel Analysis of Trusted Systems (Light Pink Book).” NSA/NCSC-Rainbow Series publications, 1993.

