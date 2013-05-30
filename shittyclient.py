#! /usr/bin/env python3
from client import *

USERNAME = "<CHANGEME>"
PASSWORD = "<CHANGEME>"

def round(state):
    if not state.my_planets or not state.enemy_planets:
        return "nop"
    else:
        best_planet = sorted(state.my_planets, key=lambda p: sum(p.ships))[-1]
        target_planet = random.choice(state.enemy_planets)
        return best_planet.flyto(target_planet, [s//6 for s in best_planet.ships])

play(USERNAME, PASSWORD, round)
