import socket, json
import random, pprint
import sys
import math
import re

class arith_list(list):
    def __add__(self, other):
        return arith_list([x + y for x, y in zip(self, other)])

    def __rmul__(self, other):
        return arith_list([x * other for x in self])

class Planet:
    def __init__(self, json):
        self.player_id = json['owner_id']
        self.ships = arith_list(json['ships'])
        self.production = arith_list(json['production'])
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
        
    def can_intercept(self, origin_planet, current_round):
        combined_ships = origin_planet.ships
        for i in range(0, len(self.target.ships)):
            combined_ships[i] += self.target.ships[i]
        return (origin_planet.ships[0] > 0 or origin_planet.ships[1] > 0 or origin_planet.ships[2] > 0 ) and origin_planet.dist(self.target) < (self.eta - current_round) and self.battle(self.ships, combined_ships)
        
    def will_conquer_target(self):
        return sum(self.battle(self.ships, self.target.ships)[1]) == 0
        
    def battle(self, s1,s2):
        ships1 = s1[::]
        ships2 = s2[::]
        while sum(ships1) > 0 and sum(ships2) >0:
            new1 = self.battle_round(ships2,ships1)
            ships2 = self.battle_round(ships1,ships2)
            ships1 = new1
            #print ships1,ships2
            
        ships1 = map(int,ships1)
        ships2 = map(int,ships2)
        #print ships1,ships2
        return ships1, ships2
    
    def battle_round(self, attacker,defender):
        #nur eine asymmetrische runde. das hier muss mal also zweimal aufrufen.
        numships = len(attacker)
        defender = defender[::]
        for def_type in range(0,numships):
            for att_type in range(0,numships):
                multiplier = 0.1
                absolute = 1
                if (def_type-att_type)%numships == 1:
                    multiplier = 0.25
                    absolute = 2
                if (def_type-att_type)%numships == numships-1:
                    multiplier = 0.01
                defender[def_type] -= (attacker[att_type]*multiplier) + (attacker[att_type] > 0) * absolute
            defender[def_type] = max(0,defender[def_type])
        return defender

class State:
    def __init__(self, json):
        self.planets = [Planet(p) for p in json['planets']]
        self.fleets = [Fleet(p, self.planets) for p in json['fleets']]
        self.player_id = json['player_id']
        self.round = json['round']

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
            print("\r[{}/{}] {} - {} - {} ".format(state['round'], state['max_rounds'],
              sum([sum(planet.ships) for planet in s.my_planets]),
              sum([sum(planet.ships) for planet in s.neutral_planets]),
              sum([sum(planet.ships) for planet in s.enemy_planets])),
              end='')
        elif re.match('command received|welcome|calculating|waiting for', data):
            pass
        elif re.match('game ended', data):
            print()
            msg = data.replace('player 1', 'YOU' if s.player_id == 1 else 'enemy')
            msg = msg.replace('player 2', 'YOU' if s.player_id == 2 else 'enemy')
            print(msg)
        else:
            print(data)
