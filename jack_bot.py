from collections import defaultdict
from copy import deepcopy
import heapq

import numpy as np
from game_world.racetrack import RaceTrack

Point = tuple[int, int]


def bot_action(location: Point, track: RaceTrack) -> Point:
    # planned_moves = plan(location, deepcopy(track), set())[1]
    # print(planned_moves)

    # if there is only one legal move
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

    # if planned_moves != [] or (
    #     path is not None and len(path) > distance(location, track.target)
    # ):
    #     path = astar(location, track, planned_moves[0][2])

    if path is None:
        print("bad")
        return (0, 0)

    next = path.pop(0)
    return (next[0] - location[0], next[1] - location[1])


def distance(point_a: Point, point_b: Point):
    return abs(point_b[0] - point_a[0]) + abs(point_b[1] - point_a[1])


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
        button = track.button_colors[neighbor[0]][neighbor[1]]
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

"""
def plan(location: Point, track: RaceTrack, has_been: set[tuple[Point, bytes]] = set()) -> tuple[int, list[tuple[int, int, Point]]]:
    buttons: set[tuple[int, Point]] = set(
        (color, (row_idx, column_idx))
        for row_idx, row in enumerate(track.button_colors)
        for column_idx, color in enumerate(row)
        if color != 0
    )
    possible_actions = list(buttons)
    possible_actions.append((0, track.target))

    moves: list[tuple[int, int, Point]] = []

    for act in possible_actions:
        path = astar(location, track, act[1])
        if path is None:
            continue
        if act[0] != 0: # it is a button
            new_track = deepcopy(track)
            new_track.toggle(act[0])
            if (act[1], new_track.active.tobytes()) in has_been:
                print('has been')
                return len(path) + distance(act[1], track.target), moves
            has_been.add((act[1], new_track.active.tobytes()))
            heapq.heappush(moves, (plan(act[1], new_track, has_been)[0], 1, act[1]))
        else: # end
            heapq.heappush(moves, (len(path), 0, act[1]))
            print(len(path))
            print('hit')
            return len(path), moves
    
    return 0, moves
"""


def astar(
    start_point: Point, track: RaceTrack, end_point: Point | None = None
) -> list[Point] | None:
    # input points, output list of moves
    if not end_point:
        end_point = track.target
    found_path: bool = False
    frontier = []
    tie_break: int = 0
    heapq.heappush(frontier, (distance(start_point, end_point), tie_break, start_point))
    g_scores = defaultdict(lambda: float("inf"))
    g_scores[start_point] = 0
    backtracking: dict[Point, Point | None] = {start_point: None}
    curr: Point = start_point
    max_x, max_y = track.active.shape

    while frontier != []:
        curr_f, _, curr = heapq.heappop(frontier)

        if curr == end_point:
            found_path = True
            break

        if curr_f > g_scores[curr] + distance(curr, end_point):
            continue

        for opt in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
            neighbor = (curr[0] + opt[0], curr[1] + opt[1])
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
            tie_break += 1
            new_cost: float = g_scores[curr] + distance(curr, neighbor)

            if new_cost < g_scores[neighbor]:
                heapq.heappush(
                    frontier,
                    (new_cost + distance(neighbor, end_point), tie_break, neighbor),
                )
                backtracking[neighbor] = curr
                g_scores[neighbor] = new_cost

    if (
        not found_path
    ):  # if the while ends and we never found a path then there are no paths
        print("path not found")
        return None

    last: Point | None = curr
    moves: list[Point] = []
    while last is not None:
        moves.append(last)
        last = backtracking[last]

    return moves[::-1][1:]
