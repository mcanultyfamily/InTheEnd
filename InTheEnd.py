#!/usr/bin/env python
import time
import pygame
import utils


class SpinImageSituation(utils.SituationBase):
    def __init__(self, g, image_file, next_situation_class, spin_rate=100, rotations=2):
        utils.SituationBase.__init__(self, g)
        self.next_situation_class = next_situation_class
        self.FRAME_RATE = spin_rate
        self.ROTATE_INCREMENT = 5
        self.base_image = pygame.image.load(image_file).convert()
        self.base_center = self.base_image.get_rect().center

        self.background = pygame.Surface(self.g.screen.get_size()).convert()
        self.background.fill((255, 255, 255))
        self.current_angle = 0
        self.rotations_left = rotations
        self.need_draw = True
        self.done = False

    def rotate_image(self):
        self.log("Rotations Left %s, current angle: %s" % (self.rotations_left, self.current_angle))
        if self.current_angle==0:
            image = self.base_image
            rect = image.get_rect()
        else:
            image = pygame.transform.rotate(self.base_image, self.current_angle)
            rect = image.get_rect()
            rect.center = self.base_center
        return image, rect
        
    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.next_situation_class = None
            self.done = True
        elif event.type==pygame.KEYDOWN:
            self.done = True
    
    def still_running(self):
        return not self.done
        
    def display(self):
        if self.need_draw:                        
            self.g.screen.blit(self.background, (0, 0)) 
            if self.rotations_left:
                for i in range(3):
                    image, rect = self.rotate_image()
                    self.g.screen.blit(image, rect)   
                    self.current_angle += 5
                    if self.current_angle>=360:
                        self.current_angle = 0
                        self.rotations_left -= 1
                        break
            else:
                self.g.screen.blit(self.base_image, (0,0))
                self.need_draw = False
            pygame.display.flip()

    def next_situation(self):
        if self.next_situation_class:
            return self.next_situation_class(self.g)
        else:
            return None

        
        
class FirstNewspaperSituation(SpinImageSituation):
    def __init__(self, g):
        
        SpinImageSituation.__init__(self, g, "test.png", SecondNewspaperSituation)
        
class SecondNewspaperSituation(SpinImageSituation):
    def __init__(self, g):
        SpinImageSituation.__init__(self, g, "test.png", None)
        
        
class InTheEndGame(utils.GameBase):
    def __init__(self):
        utils.GameBase.__init__(self)
        self.screen = pygame.display.set_mode((600,600),1)
        #self.screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)


    def firstSituation(self):
        utils._log("first sit")
        sit = FirstNewspaperSituation(self)
        utils._log(sit)
        return sit

        

if __name__ == '__main__':
    utils.main(InTheEndGame)