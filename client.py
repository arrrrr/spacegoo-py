import socket, json
import random, pprint
import sys
import math
import re

class Planet:
    def __init__(self, json):
        self.player_id = json['owner_id']
        self.ships = json['ships']
        self.production = json['production']
        self.x = json['x']
        self.y = json['y']
        self.id = json['id']

    def dist(self, other):
        return int(math.sqrt((self.x-other.x)**2 + (self.y-other.y)**2))

    def flyto(self, other, ships):
        return ("send %s %s %d %d %d" % (self.id, other.id, ships[0], ships[1], ships[2]))
        
class Fleet:
    def __init__(self, json, planets):
        self.id = json['id']
        self.player_id = json['owner_id']
        target_string = json['target']
        origin_string = json['origin']
        
        self.target = [planet for planet in planets if planet.id == target_string][0]
        self.origin = [planet for planet in planets if planet.id == origin_string][0]
        self.ships = json['ships']
        self.eta = json['eta']
        
    def can_intercept(origin_planet, current_round):
        return (origin_planet.ships[0] > 0 or origin_planet.ships[1] > 0 or origin_planet.ships[2] > 0 ) and origin_planet.dist(self.target) < (self.eta - current_round)

class State:
    def __init__(self, json):
        self.planets = [Planet(p) for p in json['planets']]
        self.fleets = [Fleet(p, self.planets) for p in json['fleets']]
        self.player_id = json['player_id']

    def my(self, thing):
        return thing.player_id == self.player_id

    @property
    def my_planets(self):
        return [p for p in self.planets if self.my(p)]

    @property
    def neutral_planets(self):
        return [p for p in self.planets if p.player_id == 0]

    @property
    def enemy_planets(self):
        return [p for p in self.planets if p.player_id != 0 and not self.my(p)]

def play(user, password, ai):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('spacegoo.gpn.entropia.de', 6000))
    io = s.makefile('rw')

    def write(data):
        io.write('%s\n' % (data,))
        io.flush()

    write('login %s %s' % (user, password))
    while True:
        data = io.readline().strip()
        if not data:
            return
        if data[0] == "{":
            state = json.loads(data)
            if state['winner'] is not None:
                break

            s = State(state)
            write(ai(s))
            print("\r[{}/{}] {} - {} - {}".format(state['round'], state['max_rounds'], len(s.my_planets), len(s.neutral_planets), len(s.enemy_planets)), end='')
        elif re.match('command received|welcome|calculating|waiting for', data):
            pass
        elif re.match('game ended', data):
            print()
            msg = data.replace('player 1', 'YOU' if s.player_id == 1 else 'enemy')
            msg = msg.replace('player 2', 'YOU' if s.player_id == 2 else 'enemy')
            print(msg)
        else:
            print(data)
