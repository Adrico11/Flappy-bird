Fallpy Bird is a 2-part project :
1. Coding the Flappy Bird game using Pygame (Python, Object Oriented Programming)
2. Applying the NEAT algorithm so that birds eventually master the game after a few generations (Neat library)

Following are some of the main parameters of the NEAT algorithm and a short description for each of them :
-	Inputs = info given to the network : horizontal distance from start, distance between bird and next pipe (top and bottom distances)
-	Outputs = what the character can do (what button we can press) : jump or not 
-	Activation function = evaluate the output neuron to decide what to do : here binary classification -> tanh and jump if output value > 0.5
-	Population size =  number of birds per generation : 100 (higher as the complexity of the game increases)
-	Fitness function = evaluate how good our birds are (VERY IMPORTANT) : distance from start + genomes and config file as parameters
-	Max generations = number of generations to test : 30 (if still not good after 30 generations, start over)

PS : All of this needs to be written in a configuration file with a specific format to then be fed into the algorithm
