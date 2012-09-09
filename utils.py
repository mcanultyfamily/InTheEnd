import sys
import pygame

_verbosity = 1

def _log(msg, verbosity=1):
    if verbosity>=_verbosity:
        print msg

class GameBase(object):
    def __init__(self):
        pygame.init()
        self.clock = pygame.time.Clock()
        self.get_options()
        
    def get_options(self):
        # TODO: support optparse for more detailed options
        global _verbosity
        if "--debug" in sys.argv[1:]:
            _verbosity = 2
        
    def firstSituation(self):
        return None
        
    def quit(self):
        pygame.quit()


class SituationBase(object):
    """Base class provides a loop that does some basic stuff"""
    def __init__(self, game_obj):
        self.g = game_obj
        self.FRAME_RATE = 30
        self.log("init")
    
    def log(self, msg):
        _log("%s: %s" % (self.__class__.__name__, msg))
        
    def run(self):
        while self.still_running():
            self.g.clock.tick(self.FRAME_RATE)
            self.handle_events()
            self.display()
        return None
    
    def still_running(self):
        return False
        
    def handle_events(self):
        pass
    
    def display(self):
        pass

def main(game_class):
    gc = game_class()
    sit = gc.firstSituation()
    while sit:
        sit = sit.run()
    gc.quit()