import sys
import os
import time
import optparse

import pygame

import data

_verbosity = 1
python_quit = False

def _log(msg, verbosity=1):
    global _verbosity
    if verbosity<=_verbosity:
        print msg


_font_cache = data.Cache()
class GameFont(object):
    def __init__(self, name, size, color):
        self.name = name
        self.size = size
        self.color = color
        key = (name, size)
        if not key in _font_cache:
            _font_cache[key] = pygame.font.SysFont(name, size, True, False)
        self.font = _font_cache[key]

    
class Button(object):
    def __init__(self, g, normal_image, pressing_image, pressed_image, x, y, name):
        self.g = g
        self.x = x
        self.y = y
        self.images = {}
        self.images['normal'] = normal_image
        self.images['pressing'] = pressing_image
        self.images['pressed'] = pressed_image
        self.name = name
        self.state = None
        self.set_state("normal")
        
    def set_state(self, state):
        if self.state!=state:
            self.state = state
            rect = self.images[state].get_rect()
            rect.topleft = self.x, self.y
            self.right, self.bottom = rect.bottomright
            print "BUTTON: ", self.x, self.y, self.right, self.bottom
            self.draw()
        
    def draw(self):
        self.g.screen.blit(self.images[self.state], (self.x, self.y))
            
    def mouse_down(self, mouse):
        if self.mouse_in_button(mouse):
            self.set_state("pressing")
            return True
        else:
            return False
    
    def mouse_up(self, mouse):
        if self.mouse_in_button(mouse):
            self.set_state("pressed")
            return True
        else:
            return False
    
    def mouse_in_button(self, mouse):
        x,y = mouse
        return  x>self.x and x<self.right and \
           y>self.y and y<self.bottom

# http://pygame.org/wiki/Spritesheet
class SpriteSheet(object):
    def __init__(self, filename):
        try:
            self.sheet = pygame.image.load(filename).convert_alpha()
        except pygame.error, message:
            print 'Unable to load spritesheet image:', filename
            raise SystemExit, message
    # Load a specific image from a specific rectangle
    def image_at(self, rectangle, colorkey = None):
        "Loads image from x,y,x+offset,y+offset"
        rect = pygame.Rect(rectangle)
        image = pygame.Surface(rect.size, flags=pygame.SRCALPHA)
        image.blit(self.sheet, (0, 0), rect)
        if colorkey is not None:
            if colorkey is -1:
                colorkey = image.get_at((0,0))
            image.set_colorkey(colorkey, pygame.RLEACCEL)
        return image
    # Load a whole bunch of images and return them as a list
    def images_at(self, rects, colorkey = None):
        "Loads multiple images, supply a list of coordinates" 
        return [self.image_at(rect, colorkey) for rect in rects]
    # Load a whole strip of images
    def load_strip(self, rect, image_count, colorkey = None):
        "Loads a strip of images and returns them as a list"
        tups = [(rect[0]+rect[2]*x, rect[1], rect[2], rect[3])
                for x in range(image_count)]
        return self.images_at(tups, colorkey)

    def image_at_index(self, row, col, w, h, colorkey=None):
        rect = (col*w, row*h, (col*w)+w, (row*h)+h)
        return self.image_at(rect, colorkey)
    
class RadioButtons(object):
    def __init__(self, g, tileset, locations=None):
        self.g = g
        self.buttons = []
        self.by_name = {}
        self.pressed = None
        tiles = SpriteSheet(tileset)
                
        self.normal_image = tiles.image_at_index(0, 0, 16, 16)
        self.pressing_image = tiles.image_at_index(0, 1, 16, 16)
        self.pressed_image = tiles.image_at_index(0, 2, 16, 16)
        
        if locations:
            for x, y, name in locations:
                self.add_button(x, y, name)
    
    def add_button(self, x, y, name):
        b = Button(self.g, self.normal_image, self.pressing_image, self.pressed_image, x, y, name)
        self.buttons.append(b)
        self.by_name[name] = b
        
    def mouse_down(self, mouse):
        print "RADIO MOUSE DOWN:", mouse
        for button in self.buttons:
            if button.mouse_down(mouse):
                self.pressed = button
            else:
                button.set_state("normal")

    def mouse_up(self, mouse):
        print "RADIO MOUSE UP:", mouse
        for button in self.buttons:
            if button.mouse_up(mouse):
                self.pressed = button
            else:
                button.set_state("normal")
    
    def draw(self):
        for button in self.buttons:
            button.draw()

class ClickableText(object):
    def __init__(self, g, text, font, x, y, id=None, width=None):
        self.g = g
        self.id = id
        self.text = text
        self.font = font
        self.x, self.y = x, y
        self.width = width
        self.render()
        
    def render(self):
        text = self.text
        if self.id:
            text = "%s. %s" % (self.id, text)
        
        if self.width:
            text, self.rect = self.g.render_text_wrapped(text, self.font, self.x, self.y, self.width)
        else:
            text, self.rect = self.g.render_text(text, self.font, self.x, self.y)
        left = self.rect[0]-5
        top = self.rect[1]-5
        if hasattr(self.g, "w"):
            w = self.g.w
        else:
            w = 50
        width = max(self.rect[2]+5, w-left+5)
        height = self.rect[3]+10
        self.rect = pygame.Rect(left, top, width, height)
        
    def mouse_in_rect(self, mouse):
        return self.rect.collidepoint(mouse)
    
    def set_font(self, font):
        if self.font!=font:
            self.font = font
            return True
        else:
            return False
            
        
class GameBase(object):
    def __init__(self):
        self.get_options()
        pygame.init()
        self.clock = pygame.time.Clock()
        
    def init_display(self, display_size, display_mode):
        self.screen = pygame.display.set_mode(display_size, display_mode)
    
    def init_options(self):
        class MyParser(optparse.OptionParser):
            def format_epilog(self, formatter):
                if self.epilog and self.epilog[-1]!='\n':
                    self.epilog = "%s\n" % self.epilog
                return self.epilog
    
        self.opt_parser = MyParser(epilog=self.make_opt_epilog())
        self.opt_parser.add_option("--debug", action='store_true', dest='debug')
        self.opt_parser.add_option("--quiet", action='store_true', dest='quiet')
        self.opt_parser.add_option("--jump-to", action='store', default="", dest='jump_to')
        self.opt_parser.add_option("--record", action='store', default="", dest='record_to')
        self.opt_parser.add_option("--playback", action='store', default="", dest='playback_from')
        self.opt_parser.add_option("--playback-rate", action='store', type=float, default=1.0, dest='playback_rate')
    
    def make_opt_epilog(self):
        return None
        
    def get_options(self): 
        global _verbosity
        self.jump_to = None
        
        self.init_options()
        
        self.cli_options, self.cli_args = self.opt_parser.parse_args()    
        
        if self.cli_options.debug:
            _verbosity = 2
        if self.cli_options.quiet:
            _verbosity = 0
        
        self.playback_events = []
        if self.cli_options.playback_from:
            self.playback_events = data.read_playback_events(self.cli_options.playback_from, self.cli_options.playback_rate)
            print "Loaded %s playback events" % len(self.playback_events)
        elif self.cli_options.record_to:
            print "Recording enabled to %r" % self.cli_options.record_to
            data.start_recording(self.cli_options.record_to)
        self.jump_to = self.cli_options.jump_to
        return self.cli_options, self.cli_args
        
    def first_situation(self):
        return None
    
    def _first_situation(self):
        if self.jump_to:
            return self._jump_to_situation()
        else:
            return self.first_situation()

    def _jump_to_situation(self):
        calling_module = __import__("__main__")
        cls = getattr(calling_module, self.jump_to)
        _log("JUMPING TO SITUATION: %s (%s)" % (self.jump_to, cls.__class__.__name__))
        return cls(self)
        
    def render_text(self, s, game_font, x, y, bg=None):
        antialias = True
        text = game_font.font.render(s, antialias, game_font.color)
        textRect = text.get_rect()
        textRect.left = self.screen.get_rect().left+x
        textRect.top = self.screen.get_rect().top+y
        if bg:
            self.screen.blit(bg, textRect, area=textRect)
        self.screen.blit(text, textRect) 
        return text, textRect
    
    def render_text_wrapped(self, s, game_font, x, y, width, leading=2, bg=None):
        textlines = wrapline(s, game_font.font, width)
        top = left = None
        bottom = right = 0
        for line in textlines:
            text, textRect = self.render_text(line, game_font, x, y, bg=bg)
            if left==None: left = textRect[0]
            if top==None: top = textRect[1]
            bottom = textRect[1]+textRect[3]
            right = max(right, textRect[2])
            y += textRect[3]+leading
        return s, pygame.Rect(left, top, right-left, bottom-top)
        
    def quit(self):
        pygame.quit()


class Pane(object):
    def __init__(self, sit, left, top, right, bottom, color, background=None):
        self.sit = sit
        _log("NEW PANE %s : %s, %s, %s, %s" % (self.__class__.__name__, left, top, right, bottom), verbosity=2)
        self.g = sit.g
        self.rect = pygame.Rect(left, top, right, bottom)
        self.x_offset = left
        self.y_offset = top
        self.w = right-left
        self.h = bottom-top
        if background:
            self.background = background
        else:
            self.background = pygame.Surface((self.w, self.h)).convert()
            self.background.fill(color)

        
    def render(self):
        self.g.screen.blit(self.background, (self.x_offset, self.y_offset)) 
        
    def render_text(self, text, font, x, y, bg=None):
        return self.g.render_text(text, font, self.x_offset+x, self.y_offset+y)

    def render_text_wrapped(self, text, font, x, y, width, bg=None):
        return self.g.render_text_wrapped(text, font, self.x_offset+x, self.y_offset+y, width, bg=bg)

    def window_to_pane_xy(self, x, y):
        return x-self.x_offset, y-self.y_offset

    def pane_to_window_xy(self, x, y):
        return x+self.x_offset, y+self.y_offset
        
    def blit(self, img, topleft, area=None):
        _log("PANE BLIT: %s, %s" % (topleft, area), verbosity=3)
        x, y = topleft
        x, y = self.pane_to_window_xy(x, y)
        if area:
            area.topleft = self.pane_to_window_xy(x, y)
        self.g.screen.blit(img, (x, y), area=area)

    def event_click(self, mouse, mouse_up):
        return self.mouse_in_pane(mouse)
    
    def mouse_in_pane(self, mouse):
        x, y = mouse
        return x>self.x_offset and y>self.y_offset and x<(self.x_offset+self.w) and y<(self.y_offset+self.h)
        
class SituationBase(object):
    """Base class provides a loop that does some basic stuff"""
    def __init__(self, game_obj):
        self.g = game_obj
        self.FRAME_RATE = 30
        self.next_situation_class = None
        self.done = False
        self.log("Created")
        self.key_handlers = {}
        self.key_handlers[pygame.K_ESCAPE] = self.event_quit
        self.consec_keydowns = 0
        self.showing_overlay = False
        
    def log(self, msg, verbosity=2):
        _log("%s: %s" % (self.__class__.__name__, msg), verbosity=verbosity)
    
    def get_events(self):
        events = []
        now = time.time()                    
        while self.g.playback_events:
            if self.g.playback_events[0][0]>now:
                break
            tick, event = self.g.playback_events.pop(0)
            events.append(event)
            if event.type in (pygame.KEYUP,):
                break
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
                break
        return events+pygame.event.get()

    def run(self):
        global python_quit
        start = time.time()
        ticks = 0
        while not python_quit and self.still_running():
            self.g.clock.tick(self.FRAME_RATE)
            ticks += 1
            for event in self.get_events():
                if self.g.cli_options.record_to:
                    data.record_event(event)            
                self.handle_event(event)
            self.do_stuff_before_display()
            self.display()
            self.do_stuff_after_display()
        actual_frame_rate = ticks/(time.time()-start)        
        self.log("Requested frame rate: %0.2f, actual frame rate: %0.2f" % (self.FRAME_RATE, actual_frame_rate))
        if python_quit:
            self.log("run completing: QUIT")
            return None
        else:
            sit = self.next_situation()
            self.log("run completing: %s" % sit.__class__.__name__)
            return sit
            
    def still_running(self):
        return not self.done
    
    def event_keydown(self, event):
        if event.key in self.key_handlers:
            self.consec_keydowns += 1
            self.key_handlers[event.key](event)
        else:
            self.event_key_any(event)
    
    def event_keyup(self, event):
        self.consec_keydowns += 1
    
    def event_key_any(self, event):
        self.done = True
    
    def event_click(self, event, mouse_up):
        self.log("EMPTY EVENT CLICK")
        
    def handle_event(self, event):
        global python_quit
        if event.type == pygame.QUIT:
            self.event_quit(event)
        elif self.showing_overlay:
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                self.hide_overlay()
        elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            if self.showing_overlay:
                self.showing_overlay = False
            mouse = pygame.mouse.get_pos()
            self.log("EVENT: CLICK - %s" % repr(mouse))
            self.event_click(mouse, event.type==pygame.MOUSEBUTTONUP)
        elif event.type==pygame.KEYDOWN:
            self.log("EVENT: KEYDOWN - %s, %r" % (event.key, event.unicode))
            self.event_keydown(event)
        elif event.type==pygame.KEYUP:
            self.log("EVENT: KEYUP   - %s" % event.key)
            self.event_keyup(event)

    def event_quit(self, event):
        global python_quit
        self.log("EVENT: QUIT")
        self.next_situation_class = None
        self.done = True
        python_quit = True

    def do_stuff_before_display(self):
        pass
        
    def display(self):
        pygame.display.flip()
        
    def do_stuff_after_display(self):
        pass
    
    def next_situation(self):
        if self.next_situation_class:
            return self.next_situation_class(self.g)
        else:
            return None

    def show_overlay(self, image):
        if image:
            self.showing_overlay = True
            self.g.screen.blit(image, (0, 0))
        else:
            self.showing_overlay = True
            
    def hide_overlay(self):
        self.showing_overlay = False
        self.render()
        
    def render(self):
        pass
        
from itertools import chain
 
def truncline(text, font, maxwidth):
        real=len(text)       
        stext=text           
        l=font.size(text)[0]
        cut=0
        a=0                  
        done=1
        old = None
        while l > maxwidth:
            a=a+1
            n=text.rsplit(None, a)[0]
            if stext == n:
                cut += 1
                stext= n[:-cut]
            else:
                stext = n
            l=font.size(stext)[0]
            real=len(stext)               
            done=0                        
        return real, done, stext             
        
def wrapline(text, font, maxwidth): 
    done=0                      
    wrapped=[]                  
                               
    while not done:             
        nl, done, stext=truncline(text, font, maxwidth) 
        wrapped.append(stext.strip())                  
        text=text[nl:]                                 
    return wrapped
 
 
def wrap_multi_line(text, font, maxwidth):
    """ returns text taking new lines into account.
    """
    lines = chain(*(wrapline(line, font, maxwidth) for line in text.splitlines()))
    return list(lines)

def main(game_class):
    gc = game_class()
    sit = gc._first_situation()
    _log("first sit: %s" % sit.__class__.__name__, verbosity=2)
    while sit:
        sit = sit.run()
    gc.quit()