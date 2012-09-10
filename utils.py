import sys
import time
import pygame

_verbosity = 1

def _log(msg, verbosity=1):
    if verbosity<=_verbosity:
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
            _log("debug enabled")
        
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
        _log("%s: %s" % (self.__class__.__name__, msg), verbosity=2)
        
    def run(self):
        start = time.time()
        ticks = 0
        while self.still_running():
            self.g.clock.tick(self.FRAME_RATE)
            ticks += 1
            for event in pygame.event.get():
                self.handle_event(event)
            self.do_stuff_before_display()
            self.display()
            self.do_stuff_after_display()
        actual_frame_rate = ticks/(time.time()-start)
        self.log("Requested frame rate: %0.2f, actual frame rate: %0.2f" % (self.FRAME_RATE, actual_frame_rate))
        return self.next_situation()
    
    def still_running(self):
        return True
        
    def handle_event(self, event):
        pass
    
    def do_stuff_before_display(self):
        pass
        
    def display(self):
        pass
        
    def do_stuff_after_display(self):
        pass
    
    def next_situation(self):
        return None

def main(game_class):
    gc = game_class()
    sit = gc.firstSituation()
    _log("first sit: %s" % sit.__class__.__name__)
    while sit:
        sit = sit.run()
    gc.quit()