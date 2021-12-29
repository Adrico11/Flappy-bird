from typing import DefaultDict
import pygame
import neat
import time
import os
import random
pygame.font.init()

WIN_WIDTH = 500
WIN_HEIGHT = 800

GEN = 0

# Load the bird images + make them 2 times bigger
BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bird1.png"))),
    pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bird2.png"))),
    pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bird3.png")))]
PIPE_IMGS = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","pipe.png")))
BASE_IMGS = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","base.png")))
BG_IMGS = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bg.png")))
STAT_FONT = pygame.font.SysFont("comicsans",50)

class Bird:

    #class constants
    IMGS = BIRD_IMGS
    MAX_ROTATION = 25
    ROT_VEL = 20
    ANIMATION_TIME = 5

    def __init__(self,x,y):
        #starting position of our bird
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0 #physics of the flight
        self.vel = 0
        self.height = self.y
        #image of bird
        self.img_count = 0 
        self.img = self.IMGS[0]

    def jump(self):
        self.vel = -10.5 #positive = to the right and to the bottom (up is negative)
        self.tick_count = 0 #keeps track of when we last jumped
        self.height = self.y #where the bird jumped from

    def move(self):
        #move our bird at every single frame during the jump
        self.tick_count += 1 #discrete time
        d = self.vel*self.tick_count + 1.5*self.tick_count**2 #displacement during the jump
        # y(t) = a*t^2 + v0*t -> idem lancé de balle dans un champ de pesanteur (v0<0 car vers le haut)
        # donc a = g/2 = 5 (valeur à tester...)
        if d >= 16:
            d = 16 #set 16 as max displacement (happens if no jump is pressed after an initial one)
        if d < 0:
            d -= 2 #fine tune our jump
        self.y += d
        if d < 0 or self.y < self.height + 50 : #if bird is moving upwards or above middle line
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION #tilt the bird +25°
        else:
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL #tilt incrementally when going down (nosing towards the ground)
    
    def draw(self,win):
        self.img_count += 1
        #flap the bird's wings
        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME * 2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME * 3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME * 4:
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME * 4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0
        
        #no flapping when going down
        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME*2 #so that when it goes back up : smooth flapping

        #rotate bird image aroung its center
        rotated_image = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_image.get_rect(center = self.img.get_rect(topleft=(self.x,self.y)).center)
        win.blit(rotated_image, new_rect.topleft)

    def get_mask(self):
        return pygame.mask.from_surface(self.img)


class Pipe :
    GAP = 200
    VEL = 5

    def __init__(self,x):
        self.x = x #left corner of the pipe
        self.height = 0
        self.top = 0
        self.bottom = 0
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMGS,False,True) #top pipe
        self.PIPE_BOTTOM = PIPE_IMGS #bottom pipe
        self.passed = False #did the bird pass the pipe ?
        self.set_height()

    def set_height(self):
        #random position of the top and bottom pipes
        self.height = random.randrange(50,450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        self.x -= self.VEL * 1 #move to the left 

    def draw(self, win):
        win.blit(self.PIPE_TOP, (self.x,self.top))
        win.blit(self.PIPE_BOTTOM, (self.x,self.bottom))

    def collide(self,bird):
        # Two types of collision : 
        # 1. Box collision : the box around an object collides with the box around another object
        # (this can be problematic since the objects themselves might not touch...)
        # 2. Pixel perfect collision : use masks (-> 2D lists) to determine all the pixels used to show an object
        # and precisely determine if there is a collision or not
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)
        # "distance" between top left corners of bird and pipe masks
        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))
        # collision ?
        # returns first overlap point if it exists and None otherwise
        t_point = bird_mask.overlap(top_mask,top_offset)
        b_point = bird_mask.overlap(bottom_mask,bottom_offset)
        if t_point or b_point:
            return True #collision !!!
        return False

class Base:
    VEL = 5 #same as pipe for same speed
    WIDTH = BASE_IMGS.get_width()
    IMG = BASE_IMGS

    def __init__(self,y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        #we need two base images which move to the left and come back to the right again and again...
        self.x1 -= self.VEL
        self.x2 -= self.VEL
        if self.x1 + self.WIDTH < 0:  #image 1 is off the screen
            self.x1 = self.x2 + self.WIDTH #we cycle it back to the right
        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self,win):
        win.blit(self.IMG, (self.x1,self.y))
        win.blit(self.IMG, (self.x2,self.y))

def draw_window(win,birds, pipes, base, score, gen):
    #window.blit() = draw
    win.blit(BG_IMGS, (0,0))
    for pipe in pipes: #list of pipes on the screen
        pipe.draw(win)
    text = STAT_FONT.render("Score: " + str(score),1,(255,255,255))
    win.blit(text, (WIN_WIDTH -10 - text.get_width(),10))
    text = STAT_FONT.render("Gen: " + str(gen),1,(255,255,255))
    win.blit(text, (10,10))
    text = STAT_FONT.render("Alive: " + str(len(birds)),1,(255,255,255))
    win.blit(text, (10,70))
    base.draw(win)
    for bird in birds:
        bird.draw(win)
    pygame.display.update() #update the screen


def main(genomes, config):
    "Fitness function"

    ### We can add energy (nb of flaps = jumps), vertical distance from pipe opening (favor goign through the center) to the fitness function ###

    global GEN
    GEN += 1
    nets = []
    ge = []
    birds = []

    # 3 things define an agent : genome + network + phyisical bird
    for _,g in genomes: #genome = list of tuples (id,object)
        net = neat.nn.FeedForwardNetwork.create(g,config) # create network based on the genome
        nets.append(net)
        birds.append(Bird(230,350))
        g.fitness = 0 # initial fitness value
        ge.append(g)


    base = Base(730)
    pipes = [Pipe(600)]
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    clock = pygame.time.Clock()
    score = 0
    run = True
    while run:
        clock.tick(30) #at most 30 ticks/s
        for event in pygame.event.get(): #check if user presses certain keys
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()

        # dealing with the case where all birds (same x for all) are between two pipes on screen : need to look at the next pipe for the distance !!
        pipe_ind = 0
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1
        else: # quit the game if no more birds are alive
            run = False
            break

        for x, bird in enumerate(birds):
            bird.move()
            ge[x].fitness += 0.1 #encourage bird to stay alive
            # output = nets(inputs)
            output = nets[x].activate((bird.y,abs(bird.y - pipes[pipe_ind].height),abs(bird.y - pipes[pipe_ind].bottom)))
            if output[0] > 0.5: # output is a list of all the outputs neurons (here we only have 1 output neuron so [O])
                bird.jump()
        #bird.move()
        add_pipe = False
        rem = [] #list of removed pipes

        for pipe in pipes:
            for x, bird in enumerate(birds): #for every bird
                if pipe.collide(bird): # check for collision
                    ge[x].fitness -= 1 #penalise birds which collide with a pipe
                    birds.pop(x) #bird is dead
                    nets.pop(x)
                    ge.pop(x)
                if not pipe.passed and pipe.x < bird.x: #did the bird pass the pipe ?
                    pipe.passed = True
                    add_pipe = True

            if pipe.x + pipe.PIPE_TOP.get_width() < 0: #is the pipe off the screen ?
                rem.append(pipe)
            pipe.move()
        if add_pipe:
            score += 1
            for g in ge:
                g.fitness += 5 #reward birds which go through a pipe
            pipes.append(Pipe(600))
        for r in rem:
            pipes.remove(r) #get rid of the passed pipes

        for x,bird in enumerate(birds): #for every bird
            if bird.y + bird.img.get_height() >= 730 or bird.y < 0: #did the bird hit the floor or left the screen ?
                birds.pop(x) #bird is dead
                nets.pop(x)
                ge.pop(x)

        if score > 50: # = fitness thershold ?
            break

        base.move()
        draw_window(win,birds,pipes,base,score,GEN)


def run(config_path):
    # read the configuration file
    config = neat.config.Config(neat.DefaultGenome,neat.DefaultReproduction,
    neat.DefaultSpeciesSet,neat.DefaultStagnation,config_path)
    p = neat.Population(config) # generate a population based on our config file

    # give some info/stats on the populations
    p.add_reporter(neat.StdOutReporter(True)) 
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    # launch the game and find the winner
    winner = p.run(main,50)
    print(winner)



if __name__ == '__main__':
    local_dir = os.path.dirname(__file__) #path to current directory
    config_path = os.path.join(local_dir,"config-feedforward.txt")
    run(config_path)
