import numpy as np
import neat
import neat.config
import sys
import os
import random
import math
import pygame as pg
import matplotlib.pyplot as plt

screen_width = 1920
screen_height = 1080
generation = 0

CAR_SIZE_X = 50
CAR_SIZE_Y = 50

# light shade of the button 
color_light = (170,170,170) 
  
# dark shade of the button 
color_dark = (100,100,100)


quit_button_pos = [screen_width/2, screen_height/2]

#number of remaining cars for every generation where generation 1 is index 0 and generation n is index n-1
no_remaining_cars = []
average_distance_per_generation = []

class Car:
    def __init__(self):
        #add sprite to car
        self.surface = pg.image.load("car.png")
        self.surface = pg.transform.scale(self.surface, (CAR_SIZE_X, CAR_SIZE_Y))
        #rotate image with respect to angle
        self.rotate_surface = self.surface 
        #initialize position
        self.pos = [830, 920]
        #initialize angle to 0
        self.angle = 0
        #initialize speed to 0
        self.speed = 0
        #check whether speed has been changed
        self.speed_set = False
        #initialize center of object
        self.center = [self.pos[0] + CAR_SIZE_X/2, self.pos[1] + CAR_SIZE_Y/2]
        #initialize array to store 'radars' (sensors)
        self.radars = []
        #initialize array of radars for the purpose of drawing to the screen
        self.radars_for_draw = []
        #initialize state is_alive, if dead then failed the course
        self.is_alive = True
        #initialize bool for if object has reached its goal (in this case, finish line)
        self.goal = False
        #initialize distance travelled by object to 0
        self.distance = 0
        #initialize time spent to 0
        self.time_spent = 0

    def draw(self, screen):
        #draw object's image on screen
        screen.blit(self.rotate_surface, self.pos)
        #draw radars
        #self.draw_radar(screen)

    #function to draw radars on screen (sensors)
    def draw_radar(self, screen):
        #for each radar object has
        for r in self.radars:
            #set position and distance as values set in the array
            pos, dist = r
            #draw radar's line
            pg.draw.line(screen, (0, 255, 0), self.center, pos, 1)
            #draw circle at the end of line
            pg.draw.circle(screen, (0, 255, 0), pos, 5)

    #function to check for collision of object with map
    def check_collision(self, map):
        self.is_alive = True
        #if car collides with a black pixel, terminate
        for p in self.four_points:
            if map.get_at((int(p[0]), int(p[1]))) == (255, 255, 255, 255):
                self.is_alive = False
                break 

    #makes radars which are sensors that help the car measure how close the car is to the wall
    def check_radar(self, degree, map):
        len = 0
        x = int(self.center[0] + math.cos(math.radians(360 - (self.angle + degree))) * len)
        y = int(self.center[1] + math.sin(math.radians(360 - (self.angle + degree))) * len)

        while not map.get_at((x, y)) == (255, 255, 255, 255) and len < 300:
            len = len + 1
            x = int(self.center[0] + math.cos(math.radians(360 - (self.angle + degree))) * len)
            y = int(self.center[1] + math.sin(math.radians(360 - (self.angle + degree))) * len)

        dist = int(math.sqrt(math.pow(x - self.center[0], 2) + math.pow(y - self.center[1], 2)))
        self.radars.append([(x, y), dist])

    #updates object for each unit of time spent
    def update(self, map):
        #check speed
        if not self.speed_set:
            self.speed = 15
            self.speed_set = True

        #check position
        self.rotate_surface = self.rot_center(self.surface, self.angle)
        self.pos[0] += math.cos(math.radians(360 - self.angle)) * self.speed
        if self.pos[0] < 20:
            self.pos[0] = 20
        elif self.pos[0] > screen_width - 120:
            self.pos[0] = screen_width - 120

        self.distance += self.speed
        self.time_spent += 1
        self.pos[1] += math.sin(math.radians(360 - self.angle)) * self.speed
        if self.pos[1] < 20:
            self.pos[1] = 20
        elif self.pos[1] > screen_height - 120:
            self.pos[1] = screen_height - 120


        # caculate 4 collision points
        self.center = [int(self.pos[0]) + CAR_SIZE_X/2, int(self.pos[1]) + CAR_SIZE_Y/2]
        len = CAR_SIZE_X/2;
        left_top = [self.center[0] + math.cos(math.radians(360 - (self.angle + 30))) * len, self.center[1] + math.sin(math.radians(360 - (self.angle + 30))) * len]
        right_top = [self.center[0] + math.cos(math.radians(360 - (self.angle + 150))) * len, self.center[1] + math.sin(math.radians(360 - (self.angle + 150))) * len]
        left_bottom = [self.center[0] + math.cos(math.radians(360 - (self.angle + 210))) * len, self.center[1] + math.sin(math.radians(360 - (self.angle + 210))) * len]
        right_bottom = [self.center[0] + math.cos(math.radians(360 - (self.angle + 330))) * len, self.center[1] + math.sin(math.radians(360 - (self.angle + 330))) * len]
        self.four_points = [left_top, right_top, left_bottom, right_bottom]

        #check if car has collided with wall
        self.check_collision(map)
        #clear radars for next frame
        self.radars.clear()
        #for each angle, make a new radar (sensor)
        for d in range(-90, 120, 45):
            self.check_radar(d, map)

    #returns radar data  i.e. gets how close the car is to the border
    def get_data(self):
        radars = self.radars
        ret = [0, 0, 0, 0, 0]
        for i, r in enumerate(radars):
            ret[i] = int(r[1] / 30)

        return ret
    
    #check if car is alive
    def get_alive(self):
        return self.is_alive
    
    #get reward for a car proprotional to its size
    def get_reward(self):
        return self.distance/(CAR_SIZE_X/2)
    
    #rotate car
    def rot_center(self, image, angle):
        orig_rect = image.get_rect()
        rot_image = pg.transform.rotate(image, angle)
        rot_rect = orig_rect.copy()
        rot_rect.center = rot_image.get_rect().center
        rot_image = rot_image.subsurface(rot_rect).copy()
        return rot_image
    
    def get_distance(self):
        return self.distance

def run_car(genomes, config):
    nets = []
    cars = []
    global no_remaining_cars
    global average_distance_per_generation
    #create a feedforward network
    for id, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        g.fitness = 0

        #init car
        cars.append(Car())
    
    #init game
    pg.init()

    screen = pg.display.set_mode([screen_width, screen_height])

    clock = pg.time.Clock()

    generation_font = pg.font.SysFont("Arial", 70)
    font = pg.font.SysFont("Arial", 30)
    map = pg.image.load('map4.png')
    map = pg.transform.scale(map, (screen_width, screen_height))

    #main loop

    global generation

    generation += 1
    counter = 0

    done = False
    while not done:
        mouse = pg.mouse.get_pos()
        final_distances = []
        for event in pg.event.get():
            if event.type == pg.MOUSEBUTTONDOWN:  
            #if the mouse is clicked on the 
            #button the game is terminated 
                if screen_width/2 <= mouse[0] <= screen_width/2+140 and screen_height/2 <= mouse[1] <= screen_height/2+40: 
                    sys.exit(0)
                elif screen_width/2 <= mouse[0] <= screen_width/2+140 and screen_height/2 + 60 <= mouse[1] <= screen_height/2+100:
                    done = True
                    break
            elif event.type == pg.QUIT:
                sys.exit(0)
        
        for i, car in enumerate(cars):
            #neural network corresponds to each car in cars
            output = nets[i].activate(car.get_data())
            choice = output.index(max(output))
            if choice == 0:
                car.angle += 10 # Left
            elif choice == 1:
                car.angle -= 10 # Right
            elif choice == 2:
                if(car.speed - 2 >= 12):
                    car.speed -= 2 # Slow Down
            else:
                car.speed += 2 # Speed Up
            
        
        remain_cars = 0

        for i, car in enumerate(cars):
            if car.get_alive():
                remain_cars += 1
                car.update(map)
                genomes[i][1].fitness += car.get_reward()
            else:
                final_distances.append(car.get_distance())


        
        #check if any cars remain
        if remain_cars == 0:
            no_remaining_cars.append(0)
            break
        
        counter += 1
        if counter == 40 * 40: 
            no_remaining_cars.append(remain_cars)
            for car in cars:
                final_distances.append(car.get_distance())
            break
        #Drawing (outputing to the screen)

        screen.blit(map, (0,0))

        for car in cars:
            if car.get_alive():
                car.draw(screen)
        
        #Show which generation we're on in the UI
        text = generation_font.render("Generation: " + str(generation), True, (0,255,0))
        text_rect = text.get_rect()
        text_rect.center = (screen_width/2, 100)
        screen.blit(text, text_rect)

        #show remaining cars
        text = font.render("Cars remaining: " + str(remain_cars), True, (0,255,0))
        text_rect = text.get_rect()
        text_rect.center = (screen_width/2, 200)
        screen.blit(text, text_rect)

        #Next Generation Button
        if screen_width/2 <= mouse[0] <= screen_width/2+140 and screen_height/2 +60 <= mouse[1] <= screen_height/2+100: 
            pg.draw.rect(screen,color_light,[screen_width/2-30,screen_height/2+60,200,40]) 
          
        else: 
            pg.draw.rect(screen,color_dark,[screen_width/2-30,screen_height/2+60,200,40])

        text = font.render("Next Generation", True, (0,255,0))
        screen.blit(text , (screen_width/2-20, screen_height/2 + 60))
    
        #Quit button
        if screen_width/2 <= mouse[0] <= screen_width/2+140 and screen_height/2 <= mouse[1] <= screen_height/2+40: 
            pg.draw.rect(screen,color_light,[screen_width/2,screen_height/2,140,40]) 
          
        else: 
            pg.draw.rect(screen,color_dark,[screen_width/2,screen_height/2,140,40])

        text = font.render("Quit", True, (0,255,0))
        screen.blit(text , (screen_width/2+50, screen_height/2))

        pg.display.flip()
        clock.tick(165)
    sum = 0
    number = len(final_distances)
    for i in final_distances:
        sum += i
    average = sum/number
    average_distance_per_generation.append(average)




if __name__ == "__main__":   
    # Load Config
    config_path = "./config.txt"
    config = neat.config.Config(neat.DefaultGenome,
                                neat.DefaultReproduction,
                                neat.DefaultSpeciesSet,
                                neat.DefaultStagnation,
                                config_path)

    # Create Population And Add Reporters
    population = neat.Population(config)
    population.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    population.add_reporter(stats)
    
    # Run Simulation For A Maximum of n Generations where its population.run(run_car, n)
    population.run(run_car, 200)
    


    

    

