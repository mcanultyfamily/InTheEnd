#!/usr/bin/env python
import time
import datetime
import csv
import random
import pygame
import utils

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 500

class ClockPane(utils.Pane):
    def __init__(self, sit):
        utils.Pane.__init__(self, sit, 600, 0, 800, 30, (0,0,0))   
        self.clock_ticking = False
        
    def set_time(self, time_str):
        self.g.screen.blit(self.background, (self.x_offset, self.y_offset))
        self.render_text(time_str, utils.GameFont("monospace", 22, (255, 40, 40)), 10, 2)
    
    def start_clock(self, seconds):
        self.endtime = datetime.datetime.now()+datetime.timedelta(seconds=seconds)
        self.clock_ticking = True
        self.tick()
    
    def stop_clock(self):
        self.clock_ticking = False
        
    def tick(self):
        if self.clock_ticking:
            time_left = str(self.endtime-datetime.datetime.now())[:-2]
            self.set_time(time_left)
        

class SituationBase(utils.SituationBase):
    def __init__(self, g):
        utils.SituationBase.__init__(self, g)
        
        size = self.g.screen.get_size()
        self.background = pygame.Surface(size).convert()
        self.background.fill((255, 255, 255))
        self.g.screen.blit(self.background, (0, 0)) 
        
        self.panes = {}
        self.panes['CLOCK'] = ClockPane(self)
        # TODO: create StatusPane()
        self.panes['STATUS'] = utils.Pane(self, 600, 230, 800, 500, (200,180,180))
        #self.panes['EVENT'] = utils.Pane(self, 0, 0, 400, 500, (180,180,180))
        #self.panes['MAP'] = utils.Pane(self, 400, 0, 600, 500, (120,180,120))
        #self.panes['MINIMAP'] = utils.Pane(self, 600, 30, 800, 230, (140,180,160))
    
    def display(self):
        self.panes['CLOCK'].tick()
        pygame.display.flip()

class SpinImageSituation(SituationBase):
    def __init__(self, g, image_file, next_situation_class, time_text, spin_rate=100, rotations=2, press_next=True):
        SituationBase.__init__(self, g)
        self.next_situation_class = next_situation_class
        self.FRAME_RATE = spin_rate
        self.ROTATE_INCREMENT = 5
        self.base_image = utils.load_image(image_file)
        self.base_center = self.base_image.get_rect().center
        self.main_pane = self.panes['PAPER'] = utils.Pane(self, 0, 0, 600, 500, (255, 255, 255))
        self.panes['MINIMAP'] = utils.Pane(self, 600, 30, 800, 230, (140,180,160))
        self.panes['CLOCK'].set_time(time_text)
        self.current_angle = 0
        self.rotations_left = rotations
        self.need_draw = True
        
        if (press_next):
            font = pygame.font.Font(None, 36)
            text = font.render("Press Space to continue", 1,  (10, 10, 10))
            textpos = text.get_rect()
            textpos.centerx = self.main_pane.background.get_rect().centerx
            textpos.y = self.main_pane.background.get_rect().bottom - 40
            self.main_pane.background.blit(text, textpos)


    def rotate_image(self):
        #self.log("Rotations Left %s, current angle: %s" % (self.rotations_left, self.current_angle))
        if self.current_angle==0:
            image = self.base_image
            rect = image.get_rect()
        else:
            image = pygame.transform.rotate(self.base_image, self.current_angle)
            rect = image.get_rect()
            rect.center = self.base_center
        return image, rect
        
        
    def display(self):
        if self.need_draw:     
            self.main_pane.blit(self.main_pane.background, (0, 0)) 
            if self.rotations_left:
                for i in range(3):
                    image, rect = self.rotate_image()
                    self.main_pane.blit(image, rect.topleft)   
                    self.current_angle += 5
                    if self.current_angle>=360:
                        self.current_angle = 0
                        self.rotations_left -= 1
                        break
            else:
                self.main_pane.blit(self.base_image, (0,0))
                self.need_draw = False
            pygame.display.flip()


        
        
class FirstNewspaperSituation(SpinImageSituation):
    def __init__(self, g):
        SpinImageSituation.__init__(self, g, "first_news.png", SecondNewspaperSituation, "Sept. 10, 2312")
        
class SecondNewspaperSituation(SpinImageSituation):
    def __init__(self, g):
        SpinImageSituation.__init__(self, g, "second_news.png", QuizSituation, "Sept. 19, 2407")
    

class QuizSituationBase(SituationBase):
    def __init__(self, g):
        SituationBase.__init__(self, g)
        self.FRAME_RATE = 5
        self.panes['BADGE'] = utils.Pane(self, 600, 30, 800, 230, (255,255,255))
        badge = utils.load_image("fbi_badge.png")
        self.panes['BADGE'].blit(badge, (0,0))
        self.main_pane = self.panes['SURVEY'] = utils.Pane(self, 0, 0, 600, 500, (255, 255, 255))
        self.main_pane.blit(self.main_pane.background, (0, 0)) 
        self.panes['CLOCK'].set_time("Oct. 3, 2407")
            
class QuizSituation(QuizSituationBase):
    questions = {}
    
    def __init__(self, g, q_num='1'):
        QuizSituationBase.__init__(self, g)
        if not QuizSituation.questions:
            self.load_questions()
        self.this_rec = QuizSituation.questions[q_num]
        self.main_pane.blit(utils.load_image("InterviewGuyLarge.png"), (0,0))
        self.log("Q: %s" % self.this_rec['Question'])
        black_font = utils.GameFont("monospace", 20, (0,0,0))
        self.unpressed_font = black_font
        self.pressed_font = utils.GameFont("monospace", 20, (30,148,89))
        self.main_pane.render_text(self.this_rec['Question'], black_font, 50, 50)
        self.responses = []
        self.init_response("A", 50, 100)
        self.init_response("B", 50, 130)
        self.init_response("C", 50, 160)
        self.answer = None
        self.next_button = None
        self.python_quit = False
        pygame.display.flip()
    
    def init_response(self, r, x, y):
        name = "Response %s" % r
        if self.this_rec[name]:
            ct = utils.ClickableText(self.main_pane, 
                                     self.this_rec[name], 
                                     self.unpressed_font, 
                                     x, y)
            ct.reply = self.this_rec["Answer to %s" % r]
            self.responses.append(ct)
            

    def next_situation(self):
        if (self.python_quit):
            return None;
        q_num = self.this_rec['Next Number']
        if q_num in QuizSituation.questions:
            return QuizSituation(self.g, q_num)
        else:
            return QuizSummarySituation(self.g)

    def _click(self, mouse_up):        
        mouse = pygame.mouse.get_pos()
        if not self.answer:
            return self._click_response(mouse, mouse_up)
        else:
            self._click_next(mouse, mouse_up)
    
    def _click_response(self, mouse, mouse_up):
        answer = None
        for ct in self.responses:
            if ct.mouse_in_rect(mouse):
                answer = ct
                if ct.set_font(self.pressed_font):
                    ct.render()
            elif ct.set_font(self.unpressed_font):
                ct.render()
                
        if answer:
            self.log("Clicked Answer: %s" % answer.text)
        if mouse_up and answer:
            self.log("mouse up %s" % answer.text)
            self.answer = answer
            if answer.reply:
                self.main_pane.render_text(answer.reply, utils.GameFont("monospace", 20, (153,128,18)), 50, 200)
            self.g.add_quiz_answer(self.this_rec['Question'], answer.text)
            self.next_button = utils.ClickableText(self.main_pane, "Next",
                                       utils.GameFont("monospace", 20, (0,0,0)), 
                                       200,250)
                                       
    def _click_next(self, mouse, mouse_up):
        if self.next_button.mouse_in_rect(mouse):
            if mouse_up:
                self.done = True
            elif self.next_button.set_font(utils.GameFont("monospace", 20, (80,80,80))):
                self.next_button.render()
                
    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.next_situation_class = None
            self.done = True
            self.python_quit = True
            self.log("Quit detected in Quiz")
        elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            self._click(event.type==pygame.MOUSEBUTTONUP)
            # TODO: trigger next situation...
        elif event.type==pygame.KEYDOWN and self.next_button:
            self.done = True

        
    def load_questions(self):
        f = open("InterviewQuiz.csv", "rU")
        try:
            reader = csv.reader(f)
            header = reader.next()
            for row in reader:
                rec = dict(map(None, header, row))
                if rec['Number']:
                    QuizSituation.questions[rec['Number']] = rec
        finally:
            f.close()
        
class QuizSummarySituation(QuizSituationBase):
    def __init__(self, g):
        QuizSituationBase.__init__(self, g)
        
        self.main_pane.render_text("This is you:", utils.GameFont("monospace", 30, (0, 0, 0)), 10, 10)        
        FONT_SIZE = 12
        y = 50
        for q, a in self.g.quiz_answers:        
            self.main_pane.render_text(q, utils.GameFont("monospace", FONT_SIZE, (0, 0, 0)), 25, y)
            y += FONT_SIZE+2
            self.main_pane.render_text(a, utils.GameFont("monospace", FONT_SIZE, (30,148,89)), 30, y)
            y += FONT_SIZE+4
        
        self.next_button = utils.ClickableText(self.g, "Next",
                                       utils.GameFont("monospace", 20, (0,0,0)), 
                                       200,y+40)
        pygame.display.flip()

        self.next_situation_class = FirstMainMapSituation
        self.key_down_enabled_after = time.time()+0.2
        self.done = False
        
    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.next_situation_class = None
            self.done = True
        elif event.type==pygame.MOUSEBUTTONUP:
            mouse = pygame.mouse.get_pos()
            if self.next_button.mouse_in_rect(mouse):
                self.done = True
        elif event.type==pygame.KEYDOWN:
            self.done = True
    

class MapElem(object):
    def __init__(self, surface, name, rect, color):
        self.surface = surface
        self.name = name
        self.rect = pygame.Rect(rect[0],rect[1],rect[2],rect[3])
        self.color = color
        
    def render(self):
        width = 3
        pygame.draw.rect(self.surface, self.color, self.rect, width)
    
class MapPane(utils.Pane):
    def __init__(self, sit):
        utils.Pane.__init__(self,sit, 400, 0, 600, 500, (120,180,120))
        self.whole_map_image = utils.load_image("whole_map.png")
        map_size = self.whole_map_image.get_size()
        self.map_w, self.map_h = map_size
        self.whole_map = pygame.Surface(map_size).convert()
        print "MAP SIZE: %s", map_size
        
        # TODO: load in map elements...
        self.elems = []
        self.elems_by_xy = []
        self.elems_by_name = {}
        self.add_element("Home", (240, 1230, 265, 1260), (0,255,0), sort_xy=False)
        self.elems_by_xy.sort()        
        self.render_whole_map()
    
        self.curr_x = None
        self.curr_y = None
        self.icon = pygame.Surface((10,10)).convert()
        pygame.draw.circle(self.icon, (255,0,0), (5, 5), 10)
        
    def set_location_by_xy(self, x, y):
        self.curr_x = x
        self.curr_y = y
        self.render_visible()
    
    def set_location_by_name(self, name):
        elem = self.elems_by_name[name]
        x, y = elem.rect.center
        self.set_location_by_xy(x, y)
        
    def add_element(self, name, loc_rect, color, sort_xy=True):
        elem = MapElem(self.whole_map, name, loc_rect, color)
        self.elems.append(elem)
        x, y = loc_rect[:2]
        self.elems_by_xy.append((x, y, elem))
        self.elems_by_name[name] = elem
        if sort_xy:
            self.elems_by_xy.sort()

    def render_whole_map(self):
        self.whole_map.blit(self.whole_map_image, (0,0))
        for elem in self.elems: 
            elem.render()
    
    def render_visible(self):
        v_rect = self._calc_visible_rect()
        x = self.curr_x-v_rect.topleft[0]
        y = self.curr_y-v_rect.topleft[1]

        self.blit(self.whole_map, (0, 0), area=v_rect) 
        self.blit(self.icon, (x, y))


    def _calc_visible_rect(self):
        bottom = min(self.curr_y+10, self.map_h)
        top = max(bottom-self.h, 0)
        bottom = top+self.h
        
        left = max(0, self.curr_x-(self.w/2))
        right = min(self.map_w, left+self.w)
        left = right-self.w
        return pygame.Rect(left, top, right, bottom)
        
class MapSituationBase(SituationBase):
    def __init__(self, g):
        SituationBase.__init__(self, g)
        
        self.panes['EVENT'] = utils.Pane(self, 0, 0, 400, 500, (180,180,180))
        self.panes['MAP'] = self.map_pane = MapPane(self)
        self.panes['MINIMAP'] = utils.Pane(self, 600, 30, 800, 230, (140,180,160))

        self.key_handlers = {}
        self.key_handlers[pygame.K_w] = self.key_handlers[pygame.K_UP] = self.event_key_up
        self.key_handlers[pygame.K_a] = self.key_handlers[pygame.K_LEFT] = self.event_key_left
        self.key_handlers[pygame.K_s] = self.key_handlers[pygame.K_DOWN] = self.event_key_down
        self.key_handlers[pygame.K_d] = self.key_handlers[pygame.K_RIGHT] = self.event_key_right
        self.key_handlers[pygame.K_q] = self.key_handlers[pygame.K_ESCAPE] = self.event_key_done
        
        self.map_pane.set_location_by_name("Home")
        self.map_pane.render_visible()
        
    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.next_situation_class = None
            self.done = True
            self.python_quit = True
            self.log("Quit detected in Quiz")
        elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            self._click(event.type==pygame.MOUSEBUTTONUP)
            # TODO: trigger next situation...
        elif event.type==pygame.KEYDOWN:
            if event.key in self.key_handlers:
                self.key_handlers[event.key](event)

    def event_key_done(self, event):
        self.done = True
        
    
    def _set_loc(self, dx, dy):
        print "%4s, %4s -> " % (self.map_pane.curr_x, self.map_pane.curr_y),
        y = min(max(0, self.map_pane.curr_y+dy), self.map_pane.map_h)
        x = min(max(0, self.map_pane.curr_x+dx), self.map_pane.map_w)
        self.map_pane.set_location_by_xy(x, y)
        self.map_pane.render_visible()
        pygame.display.flip()
        print "%4s, %4s" % (self.map_pane.curr_x, self.map_pane.curr_y)
    
    def event_key_up(self, event):
        print "EVENT UP ",
        self._set_loc(0, -5)

    def event_key_down(self, event):
        print "EVENT DOWN",
        self._set_loc(0, 5)

    def event_key_left(self, event):
        print "EVENT LEFT",
        self._set_loc(-5, 0)
        
    def event_key_right(self, event):
        print "EVENT RIGHT",
        self._set_loc(5, 0)
        
class FirstMainMapSituation(MapSituationBase):
    def __init__(self, g):
        MapSituationBase.__init__(self, g)
        self.FRAME_RATE = 22
        self.panes['CLOCK'].start_clock(60*60*2) # 2 hours


# TODO: layout blocks...

class InTheEndGame(utils.GameBase):
    def __init__(self):
        utils.GameBase.__init__(self)

        DISPLAY_SIZE = (800, 500)
        DISPLAY_MODE = 1
        self.init_display(DISPLAY_SIZE, DISPLAY_MODE)
        pygame.display.set_caption("In the End")
        #self.screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)

        self.quiz_answers = []
        self.quiz_by_q = {}
    
    def add_quiz_answer(self, q, a):
        self.quiz_answers.append([q, a])
        self.quiz_by_q[q] = a

    def first_situation(self):
        return FirstNewspaperSituation(self)

        

if __name__ == '__main__':
    utils.main(InTheEndGame)