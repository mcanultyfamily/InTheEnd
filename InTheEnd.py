#!/usr/bin/env python
import time
import datetime
import random
import pygame
import utils

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 500

class ClockPane(utils.Pane):
    end_time = None # End-Time survives multiple ClockPanes...
    def __init__(self, sit):
        utils.Pane.__init__(self, sit, 600, 0, 800, 30, (0,0,0))   
        self.clock_ticking = False
        
    def set_time(self, time_str):
        self.g.screen.blit(self.background, (self.x_offset, self.y_offset))
        self.render_text(time_str, utils.GameFont("monospace", 22, (255, 40, 40)), 10, 2)
    
    def start_clock(self, seconds):
        ClockPane.endtime = datetime.datetime.now()+datetime.timedelta(seconds=seconds)
        self.clock_ticking = True
        self.tick()
    
    def stop_clock(self):
        self.clock_ticking = False
        
    def tick(self):
        if self.clock_ticking:
            time_left = str(ClockPane.endtime-datetime.datetime.now())[:-2]
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
    


class QuestionPane(utils.Pane):
    def __init__(self, sit, width, background, picture, desc, responses, has_next):
        utils.Pane.__init__(self, sit, 0, 0, width, 500, (250,250,250))   
        self.background = background
        self.width = width
        self.picture = picture
        self.desc = desc
        self.has_next = has_next
        self.next_button = None
        self.responses = []
        self.answer = None
        
        if self.background:
            self.blit(self.background, (0,0))
        if self.picture:
            self.blit(self.picture, (10,10))

        black_font = utils.GameFont("monospace", 20, (0,0,0))
        self.unpressed_font = black_font
        self.pressed_font = utils.GameFont("monospace", 20, (30,148,89))

        if (width > 500):
            self.text_x = x = 150
            y = 75
        else:
            self.text_x = x = 10
            y = 25
        width = self.width-(20+x)
        ignored, rect = self.render_text_wrapped(desc, black_font, x, y, width)
        y += rect[3]
        if (y < 200):
            y = 200        
        for id, response, reply in responses:
<<<<<<< HEAD
            ct = utils.ClickableText(self, response, self.unpressed_font,  x, y, id, width)
            ct.reply = reply
            self.responses.append(ct)
            y += ct.rect[3]+5
=======
            if (response):
                print "A: %s, %s" % (x, y)
                ct = utils.ClickableText(self, response, self.unpressed_font,  x, y, id, width)
                ct.reply = reply
                self.responses.append(ct)
                print ct.rect
                y += ct.rect[3]+5
>>>>>>> Building on fire tweaks
        
        self.text_y = y
        
    def event_click(self, mouse, mouse_up):
        self.sit.log("event_click %s - %s [next button %s]" % (mouse, mouse_up, bool(self.next_button)))
        # Handle Next Button
        if self.next_button and self.next_button.mouse_in_rect(mouse):
            if mouse_up:
                self.sit.done = True
            elif self.next_button.set_font(utils.GameFont("monospace", 20, (80,80,80))):
                self.next_button.render()
            return True
        
        # Check answers
        answer = None
        for ct in self.responses:
            if ct.mouse_in_rect(mouse):
                answer = ct
        
        # Select answer
        if answer:
            self.sit.log("Clicked Answer: %s" % answer.text)
            if mouse_up:
                self.sit.log("mouse up %s" % answer.text)
                self.select(answer)
            return True
        else:
            return False
            
    def select(self, answer):
        if self.answer:
            self.answer.set_font(self.unpressed_font)
            self.answer.render()
            if self.answer.reply:
                # TODO - I think this can move into render_text_wrapped(...bg=)
                area = pygame.Rect(self.reply_left, self.reply_top, self.reply_width, self.reply_height)
                self.blit(self.background, (self.reply_left, self.reply_top), area=area)
        self.answer = answer
        self.answer.set_font(self.pressed_font)
        self.answer.render()
        if answer.reply:
            mono_font = utils.GameFont("monospace", 20, (153, 128, 18))
            y = self.text_y+5
            self.reply_width = self.w - self.text_x - 10
            self.reply_top = y
            self.reply_left = self.text_x
            ignored, rect = self.render_text_wrapped(answer.reply, mono_font, self.reply_left, self.reply_top, self.reply_width)
            self.reply_height = rect[3]

        if self.has_next and not self.next_button:
            x = (self.width*2)/3
            y = 400
            self.next_button = utils.ClickableText(self, "Next", utils.GameFont("monospace", 20, (0,0,0)), x, y)

    def event_key(self, event):
        if self.next_button and event.key in (pygame.K_n, pygame.K_RIGHT, pygame.K_SPACE):
            self.sit.done = True
            return True
        elif event.key==pygame.K_a:
            self.select(self.responses[0])
            return True
        elif event.key==pygame.K_b:
            self.select(self.responses[1])
            return True
        elif event.key==pygame.K_c:
            self.select(self.responses[2])
            return True
        else:
            return False


class QuizSituationBase(SituationBase):
    def __init__(self, g):
        SituationBase.__init__(self, g)
        self.FRAME_RATE = 5
        self.panes['BADGE'] = utils.Pane(self, 600, 30, 800, 230, (255,255,255))
        badge = utils.load_image("fbi_badge.png")
        self.panes['BADGE'].blit(badge, (0,0))
        self.panes['CLOCK'].set_time("Oct. 3, 2407")

        self.main_pane = self.panes['SURVEY'] = utils.Pane(self, 0, 0, 600, 500, (255, 255, 255))
        self.main_pane.blit(self.main_pane.background, (0, 0)) 
        
        
class QuizSituation(QuizSituationBase):
    questions = {}
    
    def __init__(self, g, q_num='1'):
        QuizSituationBase.__init__(self, g)
        if not QuizSituation.questions:
            self.load_questions()
        self.this_rec = QuizSituation.questions[q_num]
        background_image = utils.load_image("interview_room2.jpg")
        interviewGuy = pygame.transform.smoothscale(utils.load_image("InterviewGuyLarge.png"), (117, 192));

        self.main_pane = QuestionPane(self, 
                                      600,
                                      background_image, 
                                      interviewGuy,
                                      self.this_rec['Question'],
                                      [(c, self.this_rec["Response %s" % c], self.this_rec['Answer to %s' % c]) for c in "ABC"],
                                      has_next=True)
                                      
        self.log("Q: %s" % self.this_rec['Question'])
        pygame.display.flip()
                

    def next_situation(self):
        if utils.python_quit:
            return None;
        self.g.add_quiz_answer(self.this_rec['Question'], self.main_pane.answer.text)
        q_num = self.this_rec['Next Number']
        if q_num in QuizSituation.questions:
            return QuizSituation(self.g, q_num)
        else:
            return QuizSummarySituation(self.g)

        
    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.next_situation_class = None
            self.done = True
            utils.python_quit = True
            self.log("Quit detected in Quiz")
        elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            mouse = pygame.mouse.get_pos()
            self.main_pane.event_click(mouse, event.type==pygame.MOUSEBUTTONUP)
            # TODO: trigger next situation...
        elif event.type==pygame.KEYDOWN:
            self.main_pane.event_key(event)

        
    def load_questions(self):
        records = utils.read_csv("InterviewQuiz.csv")
        QuizSituation.questions = dict([(rec['Number'], rec) for rec in records])
        
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
    shape_funcs = {}
    def __init__(self, surface, rec):
        if not MapElem.shape_funcs:
            MapElem.shape_funcs = {"rect":MapElem.draw_rect,
                                   "ellipse":MapElem.draw_ellipse,
                                   "triangle":MapElem.draw_triangle,}
    
        self.surface = surface
        self.rec = rec
        self.name = rec['Name']
        
        self.left, self.top, self.width, self.height = [int(self.rec[k]) for k in ['Left', 'Top', 'Width', 'Height']]
        if rec['Image File']:
            self.image = utils.load_image(rec['Image File'])
            self.width, self.height = self.image.get_size()
        else:
            color = eval("(%s)" % self.rec['Color'])
            self.image = pygame.Surface((self.width, self.height))
            self.shape_funcs[rec['Shape']](self, color)
    
        
    def draw_rect(self, color):
        rect = pygame.Rect(0, 0, self.width, self.height)
        pygame.draw.rect(self.image, color, rect)
    
    def draw_ellipse(self, color):
        rect = pygame.Rect(0, 0, self.width, self.height)
        pygame.draw.ellipse(self.image, color, rect)

    def draw_triangle(self, color):
        rect = pygame.Rect(0, 0, self.width, self.height)
        points = [(0, self.height), (self.width/2, 0), (self.width, self.height), (0, self.height)]
        pygame.draw.polygon(self.image, color, points)

    def render(self):
        
        self.surface.blit(self.image, (self.left, self.top))
    
class MapPane(utils.Pane):
    def __init__(self, sit):
        utils.Pane.__init__(self,sit, 400, 0, 600, 500, (120,180,120))
        self.whole_map_image = utils.load_image("whole_map.png")
        map_size = self.whole_map_image.get_size()
        self.map_w, self.map_h = map_size
        self.whole_map = pygame.Surface(map_size).convert()
        
        # TODO: load in map elements...
        self.elems = []
        self.elems_by_xy = []
        self.elems_by_name = {}
        for rec in utils.read_csv("map_data.csv"):
            if rec['Visibility']:
                self.add_element(rec, sort_xy=False)
        self.elems_by_xy.sort()        
        self.render_whole_map()
    
        self.curr_x = None
        self.curr_y = None
        self.icon = pygame.Surface((10,10)).convert()
        self.icon_size = self.icon.get_size()
        pygame.draw.circle(self.icon, (255,0,0), (5, 5), 10)
        
    def set_location_by_xy(self, x, y):
        self.curr_x = x
        self.curr_y = y
        self.render_visible()
    
    def set_location_by_name(self, name):
        elem = self.elems_by_name[name]
        x = elem.left+(elem.width/2)
        y = elem.top+(elem.height/2)
        self.set_location_by_xy(x, y)
    
    def mouse_to_elem(self, mouse):
        x, y = mouse
        for ex, ey, elem in self.elems_by_xy:
            if x<ex:
                continue
            if y<ey:
                continue
            if x>(elem.left+elem.width):
                continue
            if y>(elem.top+elem.height):
                continue
            return elem
        return None
        
    def add_element(self, rec, sort_xy=True):
        elem = MapElem(self.whole_map, rec)
        self.elems.append(elem)
        self.elems_by_xy.append((elem.left, elem.top, elem))
        self.elems_by_name[elem.name] = elem
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

    def mouse_to_pane(self, x, y):
        a, b = x, y
        x = x-self.x_offset
        y = y-self.y_offset
        return x, y
    
    def pane_to_map(self, x, y):
        a, b = x, y
        v_rect = self._calc_visible_rect()
        x = v_rect[0]+x
        y = v_rect[1]+y
        return x, y
    
    def mouse_to_map(self, x, y):
        x, y = self.mouse_to_pane(x, y)
        return self.pane_to_map(x, y)
        
    def _calc_visible_rect(self):
        bottom = min(self.curr_y+10, self.map_h)
        top = max(bottom-self.h, 0)
        bottom = top+self.h
        
        left = max(0, self.curr_x-(self.w/2))
        right = min(self.map_w, left+self.w-1)
        left = right-self.w
        return pygame.Rect(left, top, self.w, self.h)

    def move(self, dx, dy):
        icon_w, icon_h = self.icon_size
        start = (self.curr_x, self.curr_y)
        x = min(max(icon_w, self.curr_x+dx), self.map_w-icon_w)
        y = min(max(icon_h, self.curr_y+dy), self.map_h-icon_h)
        self.set_location_by_xy(x, y)
        self.render_visible()
        pygame.display.flip()
        end = (self.curr_x, self.curr_y)
        self.sit.log("MAP MOVE: %s -> %s" % (start, end), verbosity=2)

BASE_MOVE_SIZE = 5
MOVE_SIZE_INCREMENT = 5
MAX_MOVE_SIZE = 15
class MapSituationBase(SituationBase):
    def __init__(self, g):
        SituationBase.__init__(self, g)
        self.FRAME_RATE = 50
        self.move_size = BASE_MOVE_SIZE
        self.consec_keydowns = 0
        
        self.panes['EVENT'] = utils.Pane(self, 0, 0, 400, 500, (180,180,180))
        self.panes['MAP'] = self.map_pane = MapPane(self)
        self.panes['MINIMAP'] = utils.Pane(self, 600, 30, 800, 230, (140,180,160))

        self.key_handlers = {}
        self.key_handlers[pygame.K_w] = self.key_handlers[pygame.K_UP] = self.event_key_up
        self.key_handlers[pygame.K_a] = self.key_handlers[pygame.K_LEFT] = self.event_key_left
        self.key_handlers[pygame.K_s] = self.key_handlers[pygame.K_DOWN] = self.event_key_down
        self.key_handlers[pygame.K_d] = self.key_handlers[pygame.K_RIGHT] = self.event_key_right
        self.key_handlers[pygame.K_q] = self.key_handlers[pygame.K_ESCAPE] = self.key_handlers[pygame.K_n] = self.event_key_done
        
        self.move_back_allowed = False
        self.cant_move_back_sound = pygame.mixer.Sound("default_cant_move_back.wav")
        self.map_pane.set_location_by_name("Home")
        self.map_pane.render_visible()
        self.panes['CLOCK'].clock_ticking = True

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.next_situation_class = None
            self.done = True
            utils.python_quit = True
            self.log("Quit detected in Quiz")
        elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            self.event_click(event.type==pygame.MOUSEBUTTONUP)
            # TODO: trigger next situation...
        elif event.type==pygame.KEYDOWN:
            if event.key in self.key_handlers:
                self.key_handlers[event.key](event)
                self.consec_keydowns += 1
                if not self.consec_keydowns%5:
                    self.move_size = max(MAX_MOVE_SIZE, self.move_size+MOVE_SIZE_INCREMENT)
        elif event.type==pygame.KEYUP:
            self.move_size = BASE_MOVE_SIZE
            self.consec_keydowns = 0
    
    def event_click(self, mouse_up):
        mouse = pygame.mouse.get_pos()
        for p in self.panes.values():
            if p.event_click(mouse, mouse_up):
                return True
        return False
    def event_key_done(self, event):
        self.done = True
           
    def event_key_up(self, event):
        self.map_pane.move(0, -self.move_size)

    def event_key_down(self, event):
        if self.move_back_allowed:
            self.map_pane.move(0, self.move_size)
        elif self.cant_move_back_sound:
            self.cant_move_back_sound.play()

    def event_key_left(self, event):
        self.map_pane.move(-self.move_size, 0)
        
    def event_key_right(self, event):
        self.map_pane.move(self.move_size, 0)


class QuestionMapSituation(MapSituationBase):
    def __init__(self, g, csv_path):
        MapSituationBase.__init__(self, g)
        self.FRAME_RATE = 22
        self.log("Reading config %s" % csv_path)
        self.scenes = dict([(rec['Number'], rec) for rec in utils.read_csv(csv_path)])
        self.curr_scene = self.scenes['1']
        
        self.key_handlers[pygame.K_1] = self.event_response_one
        self.key_handlers[pygame.K_2] = self.event_response_two
        self.key_handlers[pygame.K_3] = self.event_response_three

        self.render()
        

    def event_response_one(self, event):
        self._event_response("A")   
    def event_response_two(self, event):
        self._event_response("B")   
    def event_response_three(self, event):
        self._event_response("C")   
        
    def _event_response(self, id):
        next_scene = self.curr_scene['%s Next Number' % id]
        if not next_scene or next_scene=='0':
            self.done = True
        else:
            self.curr_scene = self.scenes[next_scene]
            self.render()

    def render(self):
        self.main_pane = QuestionPane(self, 
                                      400,
                                      None, 
                                      None,
                                      self.curr_scene['Scenario'],
                                      [(idx+1, self.curr_scene["Response %s" % c], "") for idx, c in enumerate("ABC")],
                                      has_next=False)
                                      
        self.log("Q: %s" % self.curr_scene['Scenario'])
        pygame.display.flip()

        
class FirstMainMapSituation(QuestionMapSituation):
    def __init__(self, g):
        QuestionMapSituation.__init__(self, g, "buildingonfire.csv")
        self.FRAME_RATE = 22
        self.panes['CLOCK'].start_clock(60*60*2) # 2 hours
        self.next_situation_class = SecondMainMapSituation
        
class SecondMainMapSituation(MapSituationBase):
    pass
    
# TODO: layout blocks...

class InTheEndGame(utils.GameBase):
    def __init__(self):
        utils.GameBase.__init__(self)

        DISPLAY_SIZE = (800, 500)
        DISPLAY_MODE = 1
        self.init_display(DISPLAY_SIZE, DISPLAY_MODE)
        pygame.display.set_caption("In the End")
        #self.screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)
        pygame.key.set_repeat(250, 50)
        self.quiz_answers = []
        self.quiz_by_q = {}
    
    def add_quiz_answer(self, q, a):
        self.quiz_answers.append([q, a])
        self.quiz_by_q[q] = a

    def first_situation(self):
        return FirstNewspaperSituation(self)

    def help(self):
         print """
         --jump-to=FirstMainMapSituation
         --jump-to=FirstMainMapSituation
         --jump-to=SecondMainMapSituation
        """
        
if __name__ == '__main__':
    utils.main(InTheEndGame)