#!/usr/bin/env python
import time
import csv
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


        
        
class FirstNewspaperSituation(SpinImageSituation):
    def __init__(self, g):
        SpinImageSituation.__init__(self, g, "test.png", SecondNewspaperSituation)
        
class SecondNewspaperSituation(SpinImageSituation):
    def __init__(self, g):
        SpinImageSituation.__init__(self, g, "test.png", QuizSituation)
    
        
class QuizSummarySituation(utils.SituationBase):
    def __init__(self, g):
        utils.SituationBase.__init__(self, g)
        self.FRAME_RATE = 5
        self.background = pygame.Surface(self.g.screen.get_size()).convert()
        self.background.fill((255, 255, 255))
        self.g.screen.blit(self.background, (0, 0)) 
        
        self.g.render_text("This is you:", utils.GameFont("monospace", 30, (0, 0, 0)), 10, 10)        
        FONT_SIZE = 12
        y = 50
        for q, a in self.g.quiz_answers:        
            self.g.render_text(q, utils.GameFont("monospace", FONT_SIZE, (0, 0, 0)), 25, y)
            y += FONT_SIZE+2
            self.g.render_text(a, utils.GameFont("monospace", FONT_SIZE, (30,148,89)), 30, y)
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
    

class MainMapSituationBase(utils.SituationBase):
    def __init__(self, g):
        utils.SituationBase.__init__(self, g)
        
        size = self.g.screen.get_size()
        self.background = pygame.Surface(size).convert()
        self.background.fill((255, 255, 255))
        self.g.screen.blit(self.background, (0, 0)) 
        
        self.panes = {}
        self.panes['EVENT'] = utils.Pane(self, 0, 0, 400, 500, (180,180,180))
        self.panes['MAP'] = utils.Pane(self, 400, 0, 600, 500, (120,180,120))
        self.panes['CLOCK'] = utils.Pane(self, 600, 0, 800, 30, (0,0,0))
        self.panes['MINIMAP'] = utils.Pane(self, 600, 30, 800, 230, (140,180,160))
        self.panes['STATUS'] = utils.Pane(self, 600, 230, 800, 500, (200,180,180))
    
class FirstMainMapSituation(MainMapSituationBase):
    def __init__(self, g):
        MainMapSituationBase.__init__(self, g)
        
        
            
class QuizSituation(utils.SituationBase):
    questions = {}
    
    def __init__(self, g, q_num='1'):
        utils.SituationBase.__init__(self, g)
        self.FRAME_RATE = 5
        if not QuizSituation.questions:
            self.load_questions()
        self.this_rec = QuizSituation.questions[q_num]
        self.background = pygame.Surface(self.g.screen.get_size()).convert()
        self.background.fill((255, 255, 255))
        self.g.screen.blit(self.background, (0, 0)) 
        self.log("Q: %s" % self.this_rec['Question'])
        black_font = utils.GameFont("monospace", 20, (0,0,0))
        self.unpressed_font = black_font
        self.pressed_font = utils.GameFont("monospace", 20, (30,148,89))
        self.g.render_text(self.this_rec['Question'], black_font, 50, 50)
        self.responses = []
        self.init_response("A", 50, 100)
        self.init_response("B", 50, 130)
        self.init_response("C", 50, 160)
        self.answer = None
        self.next_button = None
        pygame.display.flip()
    
    def init_response(self, r, x, y):
        name = "Response %s" % r
        if self.this_rec[name]:
            ct = utils.ClickableText(self.g, self.this_rec[name], 
                                       self.unpressed_font, 
                                       x, y)
            ct.reply = self.this_rec["Answer to %s" % r]
            self.responses.append(ct)
            

    def next_situation(self):
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
                self.g.render_text(answer.reply, utils.GameFont("monospace", 20, (153,128,18)), 50, 200)
            self.g.add_quiz_answer(self.this_rec['Question'], answer.text)
            self.next_button = utils.ClickableText(self.g, "Next",
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

# TODO: layout blocks...

class InTheEndGame(utils.GameBase):
    def __init__(self):
        utils.GameBase.__init__(self)

        DISPLAY_SIZE = (800, 500)
        DISPLAY_MODE = 1
        self.init_display(DISPLAY_SIZE, DISPLAY_MODE)
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