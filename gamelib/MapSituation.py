
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
