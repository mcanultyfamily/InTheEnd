#!/usr/bin/env python
import time
import datetime
import pygame
import utils
import data

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 500

class ClockPane(utils.Pane):
    end_time = None # End-Time survives multiple ClockPanes...
    time_left = None
    clock_ticking = False
    tick_sound = None
    tick_base_volume = None
    
    def __init__(self, sit):
        utils.Pane.__init__(self, sit, 600, 0, 800, 30, (0,0,0))   
        self.ticks_to_play = 0
        self.fade_out_ticks = 3
        self.time_str = ""
        

    def set_time(self, time_str):
        self.time_str = time_str
        self.render()
    
    def render(self):
        self.g.screen.blit(self.background, (self.x_offset, self.y_offset))
        self.render_text(self.time_str, utils.GameFont("monospace", 22, (255, 40, 40)), 10, 2)
    
    def start_clock(self, seconds, restart=False):
        if restart:
            ClockPane.clock_ticking = False
            
        if not ClockPane.clock_ticking:
            ClockPane.tick_sound = pygame.mixer.Sound("default_cant_move_back.wav")
            ClockPane.tick_base_volume = ClockPane.tick_sound.get_volume()
            ClockPane.endtime = datetime.datetime.now()+datetime.timedelta(seconds=seconds)
            ClockPane.clock_ticking = True
            ClockPane.time_left = ClockPane.endtime-datetime.datetime.now()
            self.tick()
    
    def start_sound(self, ticks=6, fade_out_ticks=3):
        self.ticks_to_play = ticks
        self.fade_out_ticks = fade_out_ticks
    
    def stop_sound(self):
        self.ticks_to_play = 0
    
    def play_tick(self):
        if self.ticks_to_play:
            if self.fade_out_ticks:
                volume = ClockPane.tick_base_volume*min(1.0, self.ticks_to_play/(self.fade_out_ticks+1.0))
            else:
                volume = ClockPane.tick_base_volume
            #print "TICK VOLUME - %s ticks to play, %s fade_out_ticks, %0.4f base vol : %0.4f vol" % (self.ticks_to_play, self.fade_out_ticks, self.tick_base_volume, volume)
            ClockPane.tick_sound.set_volume(volume)
            ClockPane.tick_sound.play()
            self.ticks_to_play -= 1
            
            
    def stop_clock(self):
        ClockPane.clock_ticking = False
        
    def tick(self):
        if ClockPane.clock_ticking:
            time_left = ClockPane.endtime-datetime.datetime.now()
            if self.ticks_to_play and int(time_left.seconds)!=int(ClockPane.time_left.seconds):
                self.play_tick()
                
            ClockPane.time_left = time_left
            time_left = str(time_left)[:-2]
            self.set_time(time_left)
 

class Possesion(object):
    def __init__(self, image_file, name=None, full_image=None):
        self.count = 1
        self.image = data.load_image(image_file)
        if full_image:
            self.full_image = data.load_image(full_image)
        else:
            self.full_image = None
            
        if not name:
            name = image_file.split(".")[0]
        self.name = name
        self.rect = None
        self.selected = None
        
    def render(self, g, x, y):
        if not self.count:
            return 0, 0
            
        g.screen.blit(self.image, (x, y))
        if self.count!=1:
            g.render_text(str(self.count), utils.GameFont("monospace", 12, (0,0,0)), x, y)
        self.rect = self.image.get_rect().move(x, y)
        
        if self.selected:
            BORDER = 4
            self.rect = self.rect.inflate(BORDER, BORDER)
            pygame.draw.rect(g.screen, (0,255,0), self.rect, BORDER)
        return self.rect[2], self.rect[3]
    
    
        
# TODO - handle move move to hover...


class ItemsPane(utils.Pane):
    def __init__(self, sit):
        utils.Pane.__init__(self, sit,  600, 230, 800, 500, (200,180,180))   
        if hasattr(sit, "g"):
            self.real_g = sit.g      
        else:
            self.real_g = g
        self.render()
        
    def add_possession(self, item):
        self.real_g.add_possession(item)
        self.render()

    def remove_possession(self, item):
        self.real_g.remove_possession(item)
        self.render()
        
    def render(self):
        self.sit.log("RENDER ITEMS PANE")
        self.g.screen.blit(self.background, (self.x_offset, self.y_offset))
        x = 604
        y = 234
        max_h = 0
        for item in self.real_g.possessions:
            iw, ih = item.image.get_size()
            bottom = y+ih
            if bottom>496:
                print "TOO MANY POSSESSIONS! - can't print %s" % item.name
                continue
            right = x+iw
            if right>796:
                x = 604
                y += max_h
                max_h = 0            
                bottom = y+ih
                
            if bottom>496:
                print "TOO MANY POSSESSIONS! - can't print %s" % item.name
                continue
            w, h = item.render(self.g, x, y)
            max_h = max(max_h, h)
            x += (w+4)

    def event_click(self, mouse, mouse_up):
        need_render = False
        show_overlay_item = None
        DOUBLE_CLICK_TIME = 0.1
        for item in self.real_g.possessions:
            if item.rect.collidepoint(mouse):
                if not item.selected:
                    need_render = True
                elif time.time()>(item.selected+DOUBLE_CLICK_TIME):
                    show_overlay_item = item
                item.selected = time.time()
            elif item.selected:
                item.selected = False
                need_render = True
        
        if need_render:
            self.render()
        
        if show_overlay_item and not mouse_up:
            self.sit.show_overlay(show_overlay_item.full_image)
                
class SituationBase(utils.SituationBase):
    def __init__(self, g):
        utils.SituationBase.__init__(self, g)
        
        size = self.g.screen.get_size()
        self.background = pygame.Surface(size).convert()
        self.background.fill((255, 255, 255))
        
        self.panes = {}
        self.clock_pane = self.add_pane("CLOCK", ClockPane(self))
        self.items_pane = self.add_pane("ITEMS", ItemsPane(self))
        self.rendered = False
        
    def add_pane(self, name, pane):
        pane.name = name
        self.panes[name] = pane
        return pane
    
    def event_click(self, mouse, mouse_up):
        self.log("SITUATION BASE EVENT CLICK")
        for n, p in self.panes.items():
            if p.rect.collidepoint(mouse):
                self.log("EVENT CLICK : %s" % n)
                p.event_click(mouse, mouse_up)
                return
        
    def display(self):
        if not self.rendered:
            self.render()
        self.panes['CLOCK'].tick()
        pygame.display.flip()
    
    def render(self):
        self.log("RENDER Situation Base")
        self.rendered = True
        self.g.screen.blit(self.background, (0, 0)) 
        for n, p in self.panes.items():
            p.render()
        
class SpinImageSituation(SituationBase):
    def __init__(self, g, image_file, next_situation_class, time_text, spin_rate=100, rotations=2, press_next=True):
        SituationBase.__init__(self, g)
        self.next_situation_class = next_situation_class
        self.FRAME_RATE = spin_rate
        self.ROTATE_INCREMENT = 5
        self.base_image = data.load_image(image_file)
        self.base_center = self.base_image.get_rect().center
        self.main_pane = self.add_pane("PAPER", utils.Pane(self, 0, 0, 600, 500, (255, 255, 255)))
        self.add_pane("MINIMAP", MapPane(self))
        if time_text:
            self.clock_pane.set_time(time_text)
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
        self.g.add_possession(Possesion("first_news_item.png", "First Newspaper", full_image="first_news.png"))
        
class SecondNewspaperSituation(SpinImageSituation):
    def __init__(self, g):
        SpinImageSituation.__init__(self, g, "second_news.png", InvitationSituation, "Sept. 19, 2407")
        self.g.add_possession(Possesion("second_news_item.png", "Second Newspaper", full_image="second_news.png"))
        
class EmergencyNewspaperSituation(SpinImageSituation):
    def __init__(self, g):
        SpinImageSituation.__init__(self, g, "emergencydeclared.png", MainSituation_apartment, "Dec. 19, 2407")
        self.g.add_possession(Possesion("emergencydeclared_item.png", "Emergency Declared", full_image="emergencydeclared.png"))


class InvitationSituation(SpinImageSituation):
    def __init__(self, g):
        SpinImageSituation.__init__(self, g, "letterforinterview.png", QuizSituation, "Sept 16, 2407", spin_rate=100, rotations=0)
        self.g.add_possession(Possesion("letterforinterview_item.png", "Interview Invitation", full_image="letterforinterview.png"))


class OpeningCredits(SpinImageSituation):
    def __init__(self, g):
        SpinImageSituation.__init__(self, g, "openingcredits.png", FirstNewspaperSituation, "Sept 19, 2407", spin_rate=100, rotations=0)


class ClosingCredits(SpinImageSituation):
    def __init__(self, g):
        SpinImageSituation.__init__(self, g, "closingcredits.png", None, "Sept 19, 2407", spin_rate=100, rotations=0)
    
    def next_situation(self):
        utils.python_quit = True
    
class QuestionPane(utils.Pane):
    def __init__(self, sit, width, background, picture, desc, responses, show_next, 
                  text_x=None, font_size=20, answer_y=200):
        utils.Pane.__init__(self, sit, 0, 0, width, 500, (250,250,250)) 
        if background:
            self.background = background
        self.width = width
        self.picture = picture
        self.desc = desc
        self.show_next = show_next
        self.next_button = None
        self.answer = None
        self.font_size = font_size
        if text_x:
            self.text_x = text_x
            self.text_y = 25
        elif (width > 500):
            self.text_x = 150
            self.text_y = 75
        else:
            self.text_x = 10
            self.text_y = 25
        
        self.answer_y = answer_y
        self.unpressed_font = utils.GameFont("monospace", self.font_size, (0,0,0))
        self.pressed_font = utils.GameFont("monospace", self.font_size, (30,148,89))
        
        self.responses = []
        x = self.text_x
        y = self.render_question()
        width = self.width-(20+x)
        y = max(self.answer_y, y)
        for id, response, reply in responses:
            response = response.strip()
            if response:
                ct = utils.ClickableText(self, response, self.unpressed_font,  x, y, id, width)
                ct.reply = reply
                ct.id = id
                self.responses.append(ct)                
                y += ct.rect[3]+(self.font_size/5)
        
        if not self.responses:
            self.next_y = y
            self.show_next = True
            self.create_next_button()
        else:
            self.next_y = 400
        
        self.sit.key_handlers[pygame.K_n] = self._next_key
        self.sit.key_handlers[pygame.K_RIGHT] = self._next_key
        self.sit.key_handlers[pygame.K_SPACE] = self._next_key
        self.sit.key_handlers[pygame.K_RETURN] = self._next_key
        self.sit.key_handlers[pygame.K_a] = self._select_A
        self.sit.key_handlers[pygame.K_b] = self._select_B
        self.sit.key_handlers[pygame.K_c] = self._select_C

    def render(self):
        self.sit.log("RENDER QUESTION PANE")
        if self.background:
            self.blit(self.background, (0,0))
        if self.picture:
            self.blit(self.picture, (0, 0))

        self.render_question()
    
        for ct in self.responses:
            ct.render()
        
        self.render_reply()
        
        if self.next_button:
            self.next_button.render()
        
    def render_question(self):
        width = self.width-(20+self.text_x)
        ignored, rect = self.render_text_wrapped(self.desc, self.unpressed_font, self.text_x, self.text_y, width)
        return self.text_y+rect[3]+30
        

    def event_click(self, mouse, mouse_up):
        self.sit.log("event_click %s - %s [next button %s]" % (mouse, mouse_up, bool(self.next_button)))
        # Handle Next Button
        if self.next_button and self.next_button.mouse_in_rect(mouse):
            if mouse_up:
                self.sit.done = True
            elif self.next_button.set_font(utils.GameFont("monospace", self.font_size, (80,80,80))):
                self.next_button.render()
            return True
        
        # check for fake Next button
        if not self.responses:
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
        if not self.responses:
            self.sit.done = True
            return
                    
            
        if self.answer:
            # -- Reset the answer text and clear the reply
            self.answer.set_font(self.unpressed_font)
            self.answer.render()
            self.clear_reply()
            self.answer = None
            
        self.answer = answer
        self.answer.set_font(self.pressed_font)
        self.answer.render()
        self.render_reply()
        self.create_next_button()

    def clear_reply(self):
        if self.answer and self.answer.reply:
            area = pygame.Rect(self.reply_left, self.reply_top, self.reply_width, self.reply_height)
            self.blit(self.sit.background, (self.reply_left, self.reply_top), area=area)
            self.blit(self.background, (self.reply_left, self.reply_top), area=area)
            self.next_y -= self.reply_height
            self.sit.log("Cleared reply, %s, new next_y: %s" % (area, self.next_y))
    
    def render_reply(self):
        if self.answer and self.answer.reply:
            mono_font = utils.GameFont("monospace", 20, (153, 128, 18))
            self.reply_top = y = self.next_y
            self.reply_width = self.w - self.text_x - 10            
            self.reply_left = self.text_x
            ignored, rect = self.render_text_wrapped(self.answer.reply, mono_font, self.reply_left, self.reply_top, self.reply_width)
            
            self.reply_height = rect[3]
            area = pygame.Rect(self.reply_left, self.reply_top, self.reply_width, self.reply_height)
            self.next_y += self.reply_height
            self.sit.log("Rendered reply, %s, new next_y: %s" % (rect, self.next_y))

    def create_next_button(self):
        if self.show_next and not self.next_button:
            x = (self.width*2)/3
            self.next_button = utils.ClickableText(self, "Next", utils.GameFont("monospace", 20, (0,0,0)), x, self.next_y)
        
        
    def _next_key(self, event):
        if self.next_button:
            self.sit.done = True

    def _select(self, id):
        if self.responses:
            resp = self.responses[id]
        else:
            resp = None
        self.select(resp)
        
    def _select_A(self, event):
        self._select(0)
        
    def _select_B(self, event):
        self._select(1)
        
    def _select_C(self, event):
        self._select(2)

class QuizSituationBase(SituationBase):
    questions = {}
    questions_by_q = {}
    def __init__(self, g):
        SituationBase.__init__(self, g)
        self.FRAME_RATE = 5
        badge = data.load_image("fbi_badge.png")
        self.panes['BADGE'] = utils.Pane(self, 600, 30, 800, 230, (255,255,255), background=badge)
        self.panes['BADGE'].render()
        self.clock_pane.set_time("Oct. 3, 2407")
        if not QuizSituationBase.questions:
            self.load_questions()
        
    def load_questions(self):
        records = data.read_csv("InterviewQuiz.csv", self.g.game_data)
        QuizSituationBase.questions = dict([(rec['Number'], rec) for rec in records])
        QuizSituationBase.questions_by_q = dict([(rec['Question'], rec) for rec in records])
        
class QuizSituation(QuizSituationBase):
    
    def __init__(self, g, q_num='1'):
        QuizSituationBase.__init__(self, g)
        self.this_rec = QuizSituationBase.questions[q_num]
        background_image = data.load_image("interview_room2.jpg")
        interviewGuy = pygame.transform.smoothscale(data.load_image("InterviewGuyLarge.png"), (117, 192));

        p = QuestionPane(self, 600, background_image, 
                                      interviewGuy,
                                      self.this_rec['Question'],
                                      [(c, self.this_rec["Response %s" % c], self.this_rec['Answer to %s' % c]) for c in "ABC"],
                                      show_next=True)
        self.main_pane = self.add_pane("MAIN", p)
        self.render()
        self.log("Q: %s" % self.this_rec['Question'])
                

    def next_situation(self):
        if utils.python_quit:
            return None;
        self.g.add_quiz_answer(self.this_rec['Question'], self.main_pane.answer.text)
        q_num = self.this_rec['Next Number']
        if q_num in QuizSituationBase.questions:
            return QuizSituation(self.g, q_num)
        else:
            return QuizSummarySituation(self.g)


    def event_key_any(self, event):
        pass
                    
        
PLANET_INFO = [
    ["EndoDelta", "Endo Delta (aka Emotionally Disturbed)", 1],
    ["Shokugak", "Shokugaki (aka Shotgun)", 2],
    ["Mizar3", "Mizar 3 (aka Mystery)", 0],
]

class QuizSummarySituation(QuizSituationBase):
    def __init__(self, g):
        QuizSituationBase.__init__(self, g)
        self.main_pane = self.add_pane("MAIN", utils.Pane(self, 0, 0, 600, 500, (255,255,255)))
        self.calc_score()
        
    def calc_score(self):
        self.score = 0.0
        for q, a in self.g.quiz_answers:
            entry = QuizSituationBase.questions_by_q[q]
            for c in "ABC":
                if entry["Response %s" % c]==a:
                    self.add_score(entry['Score %s' % c])
                    found = True
                    break
                    
            assert(found)        
        self.log("QUIZ SCORE: %s" % self.score)
        self.g.game_data['QUIZ_SCORE'] = self.score
        
    def add_score(self, value):
        before = self.score
        if value.startswith("div "):
            val = int(value.replace("div ", "").strip())            
            self.score = self.score/val
            self.log("Add score %s/%s -> %s" % (before, val, self.score))
        elif value.startswith("mult "):
            val = int(value.replace("mult ", "").strip())
            self.score = self.score * val
            self.log("Add score %s * %s -> %s" % (before, val, self.score))
        else:
            val = int(value.strip())
            self.score += val
            self.log("Add score %s + %s -> %s" % (before, val, self.score))
            
        
    def render(self):
        QuizSituationBase.render(self)
        
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


    
    def next_situation(self):
        quiz_score = self.g.game_data['QUIZ_SCORE']
        if quiz_score>15:
            idx = 0
        elif quiz_score<-15:
            idx = 1
        else:
            idx = 2
            
        return TicketTo_Base(self.g, idx)
        
    def event_click(self, mouse, mouse_up):
        if mouse_up and self.next_button.mouse_in_rect(mouse):
            self.done = True
    
    def event_key(self, event):
        self.done = True
    
class Ticket(Possesion):
    def __init__(self, shortname, fullname):
        Possesion.__init__(self, "ticket%s_item.png" % shortname, fullname, "ticket%s.png" % shortname)
        
class TicketTo_Base(SpinImageSituation):
    def __init__(self, g, idx, next_situation=EmergencyNewspaperSituation, time_str="Oct 1st, 2407"):
        shortname, fullname, other_idx = PLANET_INFO[idx]
        SpinImageSituation.__init__(self, g, "ticket%s.png" % shortname,
                                    next_situation, time_str, spin_rate=100, rotations=0)
        self.g.add_possession(Ticket(shortname, fullname))
        self.g.game_data['HAVE_TICKET_IDX'] = idx
        self.g.game_data['HAVE_TICKET_TO'] = fullname
        self.g.game_data['DONT_HAVE_TICKET_TO'] = PLANET_INFO[other_idx][1]
        
    
class TicketTo_EndoDelta(TicketTo_Base):
    def __init__(self, g):
        TicketTo_Base.__init__(self, g, 0)
class TicketTo_Shokugak(TicketTo_Base):
    def __init__(self, g):
        TicketTo_Base.__init__(self, g, 1)
class TicketTo_Mizar3(TicketTo_Base):
    def __init__(self, g):
        TicketTo_Base.__init__(self, g, 2)
    
class MapPane(utils.Pane):
    locations = None
    def __init__(self, sit):
        utils.Pane.__init__(self, sit, 600, 30, 800, 230, (140,180,160))
        self.background = data.load_image("MiniMap.png")
        class Location(object):
            def __init__(self, rec):
                self.name = rec['Location']
                self.x = int(rec['x'])
                self.y = int(rec['y'])
        if not MapPane.locations:
            MapPane.locations = {}
            for rec in data.read_csv("map_locations.csv", self.g.game_data):
                if rec['Location']:
                    loc = Location(rec)
                    MapPane.locations[loc.name] = loc
            
        if not self.g.movement_path:
            self.move_to_location("Apartment")
        else:
            self.render()
            
    def event_click(self, mouse, mouse_up):
        if self.mouse_in_pane(mouse):
            x, y = self.window_to_pane_xy(mouse[0], mouse[1])
            self.sit.log("CLICKED MAP: %s, %s" % (x, y))
            return True
        else:
            return False
    
    def move_to_location(self, loc_name):
        if self.g.movement_path and \
           self.g.movement_path[-1].name==loc_name:
           return
        location = MapPane.locations[loc_name]
        self.g.movement_path.append(location)
        self.render()
        
    def render(self):
        self.sit.log("RENDER MAP PANE")
        self.blit(self.background, (0, 0))
        
        points = [(loc.x+self.x_offset, loc.y+self.y_offset) for loc in self.g.movement_path]
        if len(points)>1:
            closed = False
            width = 6
            pygame.draw.lines(self.g.screen, (255,0,0), closed, points, width)

        radius = 6
        width = 0
        pygame.draw.circle(self.g.screen, (255,0,0), points[-1], radius, width)            
        
        
        
        
class QuestionSituation(SituationBase):
    def __init__(self, g, csv_path):
        SituationBase.__init__(self, g)
        self.FRAME_RATE = 22
        self.log("Reading config %s" % csv_path)
        self.scenes = dict([(rec['Number'], rec) for rec in data.read_csv(csv_path, self.g.game_data)])
        

        
        self.map_pane = self.add_pane("MINIMAP", MapPane(self))
    
        self.set_current_scene('1')
        

    def event_response_one(self, event):
        self._event_response("A")   
    def event_response_two(self, event):
        self._event_response("B")   
    def event_response_three(self, event):
        self._event_response("C")   
    
    def event_click(self, mouse, mouse_up):
        SituationBase.event_click(self, mouse, mouse_up)
        if self.main_pane.answer:
            NUM_ID_TO_ALPHA_ID = {1:'A', 2:'B', 3:'C'}
            self._event_response(NUM_ID_TO_ALPHA_ID[self.main_pane.answer.id])

    def event_key_any(self, event):
        pass
        

    def _event_response(self, id):
        next_scene = self.curr_scene.get('%s Next Number' % id)
        self.log("_event_response id: %s, next scene: %s" % (id, next_scene))
        if not next_scene or next_scene in ['0', '-1']:
            self.done = True
        else:
            self.set_current_scene(next_scene)
    
    def set_current_scene(self, scene_id):
        self.curr_scene = self.scenes[scene_id]
        if self.curr_scene.get("Item"):
            self.items_pane.add_possession(Possesion(self.curr_scene['Item']))
        if self.curr_scene.get("Location"):
            self.map_pane.move_to_location(self.curr_scene['Location'])
        picture_file = self.curr_scene.get("Picture to display")
        if picture_file:
            picture = data.load_image(picture_file)
        else:
            picture = None

        special_a_number = self.curr_scene['A Next Number'] 
        if not special_a_number or special_a_number in ['0','-1']:
            responses = []
            for k in [pygame.K_1, pygame.K_2, pygame.K_3]:
                if k in self.key_handlers:
                    del self.key_handlers[k]
        
        else:
            responses = [(idx+1, self.curr_scene["Response %s" % c].strip(), "") for idx, c in enumerate("ABC")]
            self.key_handlers[pygame.K_1] = self.event_response_one
            self.key_handlers[pygame.K_2] = self.event_response_two
            self.key_handlers[pygame.K_3] = self.event_response_three

        p = QuestionPane(self, 
                          600,
                          None, 
                          picture,
                          self.curr_scene['Scenario'],
                          responses,
                          show_next=False,
                          text_x = 20,
                          font_size=18,
                          answer_y=250)
        self.main_pane = self.add_pane("MAIN", p)                                      
        self.render()


class MainSituation(QuestionSituation):
    def __init__(self, g, sit_file, next_situation_class):
        QuestionSituation.__init__(self, g, sit_file)
        self.FRAME_RATE = 22
        self.log("Initialiing mainsituation - sit_file %r" % sit_file)
        self.next_situation_class = next_situation_class
        self.clock_pane.start_clock(60*60*2) # 2 hours
        #self.clock_pane.start_sound(10, 5)
        self.render()

    def next_situation(self):
        self.log("next_situation: entering")
        if utils.python_quit:
            self.log("next_situation: quit")
            sit = None
        elif self.curr_scene['A Next Number']=='0':
            sit = self.special_next_situation(self.curr_scene['B Next Number'])
            self.log("next_situation: special: %s" % sit)
        elif self.curr_scene['A Next Number']=='-1':
            sit = self.game_over()            
            self.log("next_situation: game over: %s" % sit)
        else:
            sit = self.next_situation_class(self.g)
        return sit
    
    def special_next_situation(self, id):
        """ Override this to handle 'special situations' based on responses """
        return self.next_situation_class(self.g)
    
    def game_over(self):
        """Override this to handle non-standard game-over paths"""
        return ClosingCredits(self.g)

        
class MainSituation_apartment(MainSituation):
    def __init__(self, g, sit_file="apartment.csv"):
        MainSituation.__init__(self, g, sit_file, MainSituation_initialstreet)

class MainSituation_initialstreet(MainSituation):
    def __init__(self, g, sit_file="initialstreet.csv"):
        MainSituation.__init__(self, g, sit_file, MainSituation_buildingonfire)

class MainSituation_religiousnuts(MainSituation):
    def __init__(self, g, sit_file="religiousnuts.csv"):
        MainSituation.__init__(self, g, sit_file, MainSituation_motherandchild)
    
    def special_next_situation(self, value):
        if value =='2':
            self.g.friendsMiddleSchoolers = True
        else:
            self.g.friendsMiddleSchoolers = False
        self.log("friendsMiddleSchoolers: %s, value: %r"%(self.g.friendsMiddleSchoolers, value))
        return MainSituation.special_next_situation(self,value)


class MainSituation_buildingonfire(MainSituation):
    def __init__(self, g, sit_file="buildingonfire.csv"):
        MainSituation.__init__(self, g, sit_file, MainSituation_religiousnuts)

    def special_next_situation(self, value):
        if value !='0':
            self.g.savedPeople = True
        else:
            self.g.savedPeople = False
        self.log("savedPeople: %s, value: %r"%(self.g.savedPeople, value))
        return MainSituation.special_next_situation(self, value)

class MainSituation_motherandchild(MainSituation):
    def __init__(self, g, sit_file="motherandchild.csv"):
        MainSituation.__init__(self, g, sit_file, MainSituation_spaceportgeneral1)
        
    def special_next_situation(self, value):
        if value=='3':
            have_idx = self.g.game_data['HAVE_TICKET_IDX']
            shortname, fullname, get_idx = PLANET_INFO[have_idx]
            return TicketTo_Base(self.g, get_idx, next_situation=self.next_situation_class, time_str=None)
        else:
            return MainSituation.special_next_situation(self, value)

class MainSituation_spaceportgeneral2(MainSituation):
    def __init__(self, g, sit_file="spaceportgeneral2.csv"):
        MainSituation.__init__(self, g, sit_file, ClosingCredits)
                
class MainSituation_spaceportgeneral1(MainSituation):
    def __init__(self, g, sit_file="spaceportgeneral1.csv"):
        MainSituation.__init__(self, g, sit_file, MainSituation_spaceportgeneral2)
        
    def special_next_situation(self, value):
        if (self.g.savedPeople):
            return MainSituation_spaceportsavedpeople(self.g)
        elif (self.g.friendsMiddleSchoolers):
            return MainSituation_spaceportmiddleschool(self.g)
        else:
            self.log("HERE!  I'm HERE!")
            return MainSituation_spaceportgeneral2(self.g)

class MainSituation_spaceportsavedpeople(MainSituation):
    def __init__(self, g, sit_file="spaceportsavedpeople.csv"):
        MainSituation.__init__(self, g, sit_file, MainSituation_spaceportgeneral2)
    def special_next_situation(self, value):
        if (self.g.friendsMiddleSchoolers):
            return MainSituation_spaceportmiddleschool(self.g)
        else:
            return MainSituation_spaceportgeneral2(self.g)

class MainSituation_spaceportmiddleschool(MainSituation):
    def __init__(self, g, sit_file="spaceportmiddleschool.csv"):
        MainSituation.__init__(self, g, sit_file, MainSituation_spaceportgeneral2)
        
    def special_next_situation(self, value):
        return MainSituation_spaceportgeneral2(self.g)


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
        self.game_data = {}
        self.game_data['HAVE_TICKET_IDX'] = 0
        self.game_data['HAVE_TICKET_TO'] = 'TEST HAVE PLANET'
        self.game_data['DONT_HAVE_TICKET_TO'] = "TEST OTHER PLANET"
        self.quiz_answers = []
        self.possessions = []
        self.movement_path = []
        self.savedPeople = False
        self.friendsMiddleSchoolers = False
    
        
    def add_possession(self, item):
        if item.name in self.game_data:
            self.game_data[item.name].count += 1
        else:
            self.possessions.append(item)
            self.game_data[item.name] = item
    
    def remove_possession(self, name):
        item = self.game_data[name]
        item.count -= 1
        if not item.count:
            del self.game_data[name]
            self.possessions.remove(item)
        
        
                
    def make_opt_epilog(self):
        return ""
        
    def add_quiz_answer(self, q, a):
        self.game_data[q] = a
        self.quiz_answers.append([q,a])

    def first_situation(self):
        return OpeningCredits(self)

    def _jump_to_situation(self):
        if self.jump_to.endswith(".csv"):
            self.jump_to = "MainSituation_%s" % self.jump_to.split(".csv")[0]
        
        sit = globals()[self.jump_to](self)
        utils._log("JUMPING TO SITUATION: %s (%s)" % (self.jump_to, sit.__class__.__name__))
        return sit
        
        
if __name__ == '__main__':
    utils.main(InTheEndGame)