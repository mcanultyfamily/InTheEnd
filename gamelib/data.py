'''Simple data loader module.

Loads data files from the "data" directory shipped with a game.

Enhancing this to handle caching etc. is left as an exercise for the reader.
'''

import os
import csv
import pygame
import time
import atexit

data_py = os.path.abspath(os.path.dirname(__file__))
data_dir = os.path.normpath(os.path.join(data_py, '..', 'data'))

def filepath(filename):
    '''Determine the path to a file in the data directory.
    '''
    return os.path.join(data_dir, filename)

def load(filename, mode='rb'):
    '''Open a file in the data directory.

    "mode" is passed as the second arg to open().
    '''
    return open(os.path.join(data_dir, filename), mode)


class Cache(dict):
    pass    
    

_image_cache = Cache()
def load_image(file_name, colorkey=None):
    key = (file_name, colorkey)
    if not key in _image_cache:
        fullname = filepath(file_name)
        try:
            image = pygame.image.load(fullname)
        except pygame.error, message:
            print 'Cannot load image:', fullname
            raise SystemExit, message
        image = image.convert()
        if colorkey is not None:
            if colorkey is -1:
                colorkey = image.get_at((0,0))
            image.set_colorkey(colorkey, RLEACCEL)
        _image_cache[key] = image
    return _image_cache[key]


def read_csv(file_name, slam_data={}): 
    def _slam(v, d):
        if not "{{" in v:
            return v
        pieces = []
        for p in v.split("{{"):
            if pieces:
                key, end = p.split("}}")
                key = key.strip()
                p = "%s%s" % (slam_data.get(key, ""), end)                
            pieces.append(p)
        return ''.join(pieces)
        
    file_name = filepath(file_name)
    records = []
    f = open(file_name, "rU")
    try:
        reader = csv.reader(f)
        header = reader.next()
        for row in reader:
            row = [_slam(r, slam_data) for r in row]
            rec = dict(map(None, header, row))
            
            records.append(rec)
    finally:
        f.close()
    return records

def read_playback_events(filename, playback_rate):
    f = open(filename)
    events = []
    start_time = time.time()
    for line in f:
        tick, e_kind, e_dict = eval(line)
        tick = tick/playback_rate
        events.append((start_time+tick, pygame.event.Event(e_kind, e_dict)))
    
    f.close()
    return events

_recording_start_time = None
_recording_file = None
def start_recording(filename):
    global _recording_file, _recording_start_time
    _recording_start_time = time.time()
    _recording_file = open(filename, "w")
    atexit.register(_close_recording)
    
def _close_recording():
    global _recording_file, _last_recording_tick
    if _recording_file:
        _recording_file.flush()
        _recording_file.close()
        _recording_file = None
        _recording_start_time = None
        
def record_event(event):
    global _recording_file, _recording_start_time
    if _recording_file:
        now = time.time()
        tick = now-_recording_start_time
        e_str = str(event).replace("<Event(", "").replace(")>", "")
        e_kind = e_str.split("-", 1)[0]
        e_dict = e_str.split("{", 1)[-1]
        e_str = "%s, {%s" % (e_kind, e_dict)
        #print event, '->', e_str
        _recording_file.write("%s, %s\n" % (tick, e_str))
        _recording_file.flush()
