import random
from game_world.racetrack import RaceTrack
import heapq
from typing import Callable

import pygame
import pygame.locals
import sys
from collections import defaultdict
from copy import deepcopy


Point = tuple[int, int]

# class Counter:
#     def __init__(self):
#         self.count = 0

#     def __call__(self):
#         self.count += 1
#         return self.count
# c = Counter()
class Node:
    def __init__(self, state, position, cost, parent, action):
        self.state = state              
        self.position = position       
        self.cost = cost
        self.parent = parent
    def __lt__(self, other):
        return self.cost < other.cost
    
def reachable_buttons(track: RaceTrack, agent_pos):
    buttons = []

    for pos in track.find_buttons():
        path = astar(agent_pos, pos, track, True)
        if path is not None:
            color = track.button_colors[pos]
            buttons.append((int(color), pos, len(path)))

    return buttons

def apply_state(track, pressed_colors):

    t = deepcopy(track)
    for color in pressed_colors:
        t.toggle(color)
    return t

def make_plan(track: RaceTrack):

    start_node = {
        "state": frozenset(),
        "pos": track.spawn,
        "cost": 0,
        "parent": None,
        "action": None,
    }

    frontier = []
    counter = 0
    heapq.heappush(frontier, (0, counter, start_node))
    counter += 1
    best_cost = {}
    if track.buttons[start_node["pos"]] != 0:
        start_node["state"] = start_node["state"] ^ {track.button_colors[start_node["pos"]]} 
    while frontier:
        _, _, node = heapq.heappop(frontier)

        key = (node["state"], node["pos"])

        if key in best_cost and node["cost"] >= best_cost[key]:
            continue

        best_cost[key] = node["cost"]

        state_track = apply_state(track, node["state"])

        path = astar(node["pos"], state_track.target, state_track)
        
        if path is not None:
            if simulate_path(path, node["state"], track):
                return reconstruct_plan(node, state_track)
        
        for color, pos, dist in reachable_buttons(state_track, node["pos"]):

            if pos == node["pos"]:
                continue

            new_state = node["state"] ^ {color}

            child = {
                "state": new_state,
                "pos": pos,
                "cost": node["cost"] + dist, # think about cost 
                "parent": node,
                "action": color,
            }
            heapq.heappush(frontier, (child["cost"], counter, child))
            counter += 1

def simulate_path(path, initial_state, track: RaceTrack):

    button_state = initial_state
    pos = path[0]

    for next_pos in path[1:]:
        #should astar just exclude buttons? , path is returning green button
        state_track = apply_state(track, button_state)

        if next_pos not in state_track.find_traversable_cells():
            return False  

        pos = next_pos
        button = pos in track.find_buttons()
        if button:
            button_state = button_state ^ {track.button_colors[pos]}

    return pos == track.target



def reconstruct_plan(node, track):
    actions = []
    moves = []
    while node ["parent"] is not None:
        actions.append(node["action"])
        moves.append(node["pos"])
        node = node["parent"]
    actions.reverse()
    moves.reverse()

    return actions, moves

def reconstruct_path(cameFrom, current, end):
    total_path =[]
    current = end
    while current != None :
        total_path.append(current)
        current = cameFrom[current]
    return total_path[::-1]

def astar(start_point, end_point, track: RaceTrack, find_buttons=False):

    open_heap = []
    open_set = {start_point}
    heapq.heappush(
        open_heap,
        (abs(start_point[0] - end_point[0]) + abs(start_point[1] - end_point[1]), start_point)
    )

    cameFrom = {start_point: None}
    gScore = defaultdict(lambda: float("inf"))
    gScore[start_point] = 0

    closed = set()

    while open_heap:
        current = heapq.heappop(open_heap)[1]
        open_set.remove(current)

        if current == end_point:
            return reconstruct_path(cameFrom, current, end_point)

        closed.add(current)

        safe = track.find_traversable_cells()
        for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
            neighbor = (current[0] + dx, current[1] + dy)

            if neighbor not in safe or neighbor in closed:
                continue

            if find_buttons == False and track.buttons[neighbor] != 0:
                continue
            tentative_g = gScore[current] + 1

            if tentative_g < gScore[neighbor]:
                cameFrom[neighbor] = current
                gScore[neighbor] = tentative_g
                f = tentative_g + abs(neighbor[0] - end_point[0]) + abs(neighbor[1] - end_point[1])

                if neighbor not in open_set:
                    open_set.add(neighbor)
                    heapq.heappush(open_heap, (f, neighbor))

    return None


def random_move(loc: Point, track: RaceTrack) -> Point:
   #print(track.get_grid_coord(loc[0], loc[1]))
    safe = track.find_traversable_cells()
    options = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    neighbors = {opt: (loc[0] + opt[0], loc[1] + opt[1]) for opt in options}
    safe_options = [opt for opt in neighbors if neighbors[opt] in safe]

    plan, moves = make_plan(track)
    print(plan)
    print(moves)
        
    #move = astar(loc, track.target, track)[1]

    #return move[0]-loc[0], move[1]-loc[1]


