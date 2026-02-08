from collections import defaultdict
from copy import deepcopy
from functools import cache
import heapq

import numpy as np
from game_world.racetrack import RaceTrack

Point = tuple[int, int]


def bot_action(location: Point, track: RaceTrack) -> Point:
    # if there is only one legal move
    on_button = find_button_color(track, location)
    if on_button != 0:
        track.toggle(on_button)
    legal_move = []
    max_x, max_y = track.active.shape
    for opt in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
        possible_move = (location[0] + opt[0], location[1] + opt[1])
        if (
            possible_move[0] < 0
            or possible_move[1] < 0
            or possible_move[0] >= max_x
            or possible_move[1] >= max_y
            or (
                track.active[possible_move[0]][possible_move[1]] == 1
                and track.walls[possible_move[0]][possible_move[1]] != 0
            )
        ):
            continue
        legal_move.append(opt)

    if len(legal_move) == 1:
        return legal_move[0]

    path = plan(location, track)

    if path is None:
        print("bad")
        return (0, 0)

    next = path.pop(0)
    return (next[0] - location[0], next[1] - location[1])


def distance(point_a: Point, point_b: Point):
    return abs(point_b[0] - point_a[0]) + abs(point_b[1] - point_a[1])

def find_button_color(track: RaceTrack, pt: Point):
    return track.button_colors[pt[0]][pt[1]] if track.buttons[pt[0]][pt[1]] == 1 else 0

@cache
def actions_from_state(
    location: Point, track: RaceTrack
) -> set[tuple[Point, RaceTrack]]:
    actions = set()
    max_x, max_y = track.active.shape
    for opt in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
        neighbor = (location[0] + opt[0], location[1] + opt[1])
        if (
            neighbor[0] < 0
            or neighbor[1] < 0
            or neighbor[0] >= max_x
            or neighbor[1] >= max_y
            or (
                track.active[neighbor[0]][neighbor[1]] == 1
                and track.walls[neighbor[0]][neighbor[1]] != 0
            )
        ):
            continue
        button = find_button_color(track, neighbor)
        new_track = deepcopy(track)
        if button != 0:
            new_track.toggle(button)
        actions.add((neighbor, new_track))
    return actions


def plan(start_point: Point, track: RaceTrack):
    found_path: bool = False
    frontier = []
    tie_break: int = 0
    heapq.heappush(
        frontier,
        (
            distance(start_point, track.target),
            0,
            tie_break,
            start_point,
            deepcopy(track),
        ),
    )
    g_scores = defaultdict(lambda: float("inf"))
    g_scores[(start_point, track.active.tobytes())] = 0
    backtracking: dict[tuple[Point, bytes], tuple[Point, bytes] | None] = {(start_point, track.active.tobytes()): None}
    curr: Point = start_point
    curr_track = deepcopy(track)

    while frontier != []:
        curr_f, curr_g, _, curr, curr_track = heapq.heappop(frontier)

        if curr == track.target:
            found_path = True
            break

        if curr_g > g_scores[(curr, curr_track.active.tobytes())]:
            continue

        for act_point, act_track in actions_from_state(curr, deepcopy(curr_track)):
            new_cost = g_scores[(curr, curr_track.active.tobytes())] + 1
            act_track = deepcopy(act_track)
            if g_scores[(act_point, act_track.active.tobytes())] > new_cost:
                g_scores[(act_point, act_track.active.tobytes())] = new_cost
                tie_break += 1
                heapq.heappush(
                    frontier,
                    (
                        new_cost + distance(act_point, act_track.target),
                        new_cost,
                        tie_break,
                        act_point,
                        act_track,
                    ),
                )
                backtracking[(act_point, act_track.active.tobytes())] = (curr, curr_track.active.tobytes())
    
    if (
        not found_path
    ):  # if the while ends and we never found a path then there are no paths
        print("path not found")
        return None

    last: tuple[Point, bytes] | None = (curr, curr_track.active.tobytes())
    moves: list[Point] = []
    while last is not None:
        moves.append(last[0])
        last = backtracking[last]

    return moves[::-1][1:]
