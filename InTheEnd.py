#!/usr/bin/env python
import time
import pygame
import utils


class SpinImageSituation(utils.SituationBase):
    def __init__(self, g, image_file, spin_rate=100, rotations=2):
        utils.SituationBase.__init__(self, g)
        self.FRAME_RATE = spin_rate
        self.ROTATE_INCREMENT = 5
        self.base_image = pygame.image.load(image_file).convert()
        self.base_center = self.base_image.get_rect().center

        self.background = pygame.Surface(self.g.screen.get_size()).convert()
        self.background.fill((255, 255, 255))
        self.current_angle = 0
        self.rotations = 2

    def rot_center(image, angle):
        """rotate a Surface, maintaining position."""
        loc = rot_image.get_rect().center
        rot_sprite = pygame.transform.rotate(image_orig, angle)
        rot_image.get_rect().center = loc
        return rot_image

    def still_running(self):
        return True
        
    def display(self):
        if self.rotations:
            if self.current_angle==0:
                image = self.base_image
                rect = image.get_rect()
            else:
                image = pygame.transform.rotate(self.base_image, self.current_angle)
                rect = image.get_rect()
                rect.center = self.base_center
            self.g.screen.blit(self.background, (0, 0))        
            self.g.screen.blit(image, rect)        
            pygame.display.flip()
    
            self.current_angle = (self.current_angle+self.ROTATE_INCREMENT)
            if self.current_angle > 360:
                self.rotations -= 1
                self.current_angle -= 360

        
class InTheEndGame(utils.GameBase):
    def __init__(self):
        utils.GameBase.__init__(self)
        self.screen = pygame.display.set_mode((600,600),1)
        #self.screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)


    def firstSituation(self):
        return SpinImageSituation(self, "test.png", 100)

        

if __name__ == '__main__':
    utils.main(InTheEndGame)