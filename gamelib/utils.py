import sys
import os
import time
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
        
    def get_options(self):
        # TODO: support optparse for more detailed options
        global _verbosity
        self.jump_to = None
        for a in sys.argv[1:]:
            if a=='--debug':
                _verbosity = 2
                _log("debug enabled")
            elif a=='--quiet':
                _verbosity = 0
            elif a.startswith("--jump-to="):
                self.jump_to = a.split("=",1)[-1]
            elif a=='--help':
                self.help()
                sys.exit(0)
        
    def help(self):
        "This would be help..."
        
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
    def __init__(self, sit, left, top, right, bottom, color):
        self.sit = sit
        _log("NEW PANE %s : %s, %s, %s, %s" % (self.__class__.__name__, left, top, right, bottom), verbosity=2)
        self.g = sit.g
        self.x_offset = left
        self.y_offset = top
        self.w = right-left
        self.h = bottom-top
        self.background = pygame.Surface((self.w, self.h)).convert()
        self.background.fill(color)
        self.g.screen.blit(self.background, (left, top)) 

    def render_text(self, text, font, x, y, bg=None):
        return self.g.render_text(text, font, self.x_offset+x, self.y_offset+y)

    def render_text_wrapped(self, text, font, x, y, width, bg=None):
        return self.g.render_text_wrapped(text, font, self.x_offset+x, self.y_offset+y, width, bg=bg)

    def offset(self, x, y):
        return self.x_offset+x, self.y_offset+y
        
    def blit(self, img, topleft, area=None):
        _log("PANE BLIT: %s, %s" % (topleft, area), verbosity=3)
        x, y = topleft
        x, y = self.offset(x, y)
        self.g.screen.blit(img, (x, y), area=area)

    def event_click(self, mouse, mouse_up):
        return False
        
class SituationBase(object):
    """Base class provides a loop that does some basic stuff"""
    def __init__(self, game_obj):
        self.g = game_obj
        self.FRAME_RATE = 30
        self.next_situation_class = None
        self.done = False
        self.log("init")
        self.key_handlers = {}
        self.consec_keydowns = 0
        
    def log(self, msg, verbosity=2):
        _log("%s: %s" % (self.__class__.__name__, msg), verbosity=verbosity)
        
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
        return not self.done
        
    def handle_event(self, event):
        global python_quit
        if event.type == pygame.QUIT:
            self.next_situation_class = None
            self.done = True
            python_quit = True
        elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            mouse = pygame.mouse.get_pos()
            self.event_click(mouse, event.type==pygame.MOUSEBUTTONUP)
        elif event.type==pygame.KEYDOWN:
            if event.key in self.key_handlers:
                self.consec_keydowns += 1
                self.key_handlers[event.key](event)
        elif event.type==pygame.KEYUP:
            self.consec_keydowns += 1
    
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