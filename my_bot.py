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

agent = None

class PlannerAgent:
    def __init__(self):
        self.plan = None
        self.moves = None
        self.path_index = 0

    def move(self, loc, track):

        if self.moves is None:
            self.moves = make_plan(track)
            self.path_index = 0

        next_pos = self.moves[self.path_index + 1]
        self.path_index += 1

        dx = next_pos[0] - loc[0]
        dy = next_pos[1] - loc[1]

        return (dx, dy)







    
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
        "path": None,
    }

    frontier = []
    counter = 0
    heapq.heappush(frontier, (0, counter, start_node))
    counter += 1
    best_cost = {}
    best_solution = None
    best_total_cost = float("inf")
    if track.buttons[start_node["pos"]] != 0:
        start_node["state"] = start_node["state"] ^ {track.button_colors[start_node["pos"]]} 
    while frontier:
        _, _, node = heapq.heappop(frontier)
        
        if node["cost"] >= best_total_cost:
            continue

        key = (node["state"], node["pos"])

        if key in best_cost and node["cost"] >= best_cost[key]:
            continue

        best_cost[key] = node["cost"]

        state_track = apply_state(track, node["state"])

        path = astar(node["pos"], state_track.target, state_track)
        
        if path is not None:
            if simulate_path(path, node["state"], track):
                total_cost = node["cost"] + len(path)
                if total_cost < best_total_cost:
                    best_total_cost = total_cost
                    best_path = node['path'] + path[1:] if node['path'] is not None else path
                    best_solution = (best_path, state_track)
        
        for button_color, pos, dist in reachable_buttons(state_track, node["pos"]):

            if pos == node["pos"]:
                continue

            new_state = node["state"]
            path = astar(node["pos"], pos, state_track)
            if path == None:
                path = astar(node["pos"], pos, state_track, True)
            for tile in path[1:]:
                if track.buttons[tile] != 0:
                    color = track.button_colors[tile]
                    new_state = new_state ^ {color}


            child = {
                "state": new_state,
                "pos": pos,
                "cost": node["cost"] + dist,  
                "parent": node,
                "action": button_color,
                "path": node['path'] + path[1:] if node['path'] is not None else path,
            }
            heapq.heappush(frontier, (child["cost"], counter, child))
            counter += 1
    if best_solution is not None:
        full_path, state_track = best_solution
        return full_path

def simulate_path(path, initial_state, track: RaceTrack):

    button_state = initial_state
    pos = path[0]

    for next_pos in path[1:]:
        state_track = apply_state(track, button_state)

        if next_pos not in state_track.find_traversable_cells():
            return False  

        pos = next_pos
        button = pos in track.find_buttons()
        if button:
            button_state = button_state ^ {track.button_colors[pos]}

    return pos == track.target





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

            if find_buttons == False and track.buttons[neighbor] != 0 and neighbor != end_point:
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

    global agent

    if agent is None:
        agent = PlannerAgent()

    return agent.move(loc, track)

        
    #move = astar(loc, track.target, track)[1]

    #return move[0]-loc[0], move[1]-loc[1]


