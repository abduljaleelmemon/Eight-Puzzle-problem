from utils import distance_squared, turn_heading
from statistics import mean
from ipythonblocks import BlockGrid
from IPython.display import HTML, display
from time import sleep
import numpy as np
import queue as Queue
from queue import Queue
from copy import deepcopy
import sys

import random
import copy
import collections

class Thing:
    """This represents any physical object that can appear in an Environment.
    You subclass Thing to get the things you want. Each thing can have a
    .__name__  slot (used for output only)."""

    def __repr__(self):
        return '<{}>'.format(getattr(self, '__name__', self.__class__.__name__))

    def is_alive(self):
        """Things that are 'alive' should return true."""
        return hasattr(self, 'alive') and self.alive

    def show_state(self):
        """Display the agent's internal state. Subclasses should override."""
        print("I don't know how to show_state.")

    def display(self, canvas, x, y, width, height):
        """Display an image of this Thing on the canvas."""
        # Do we need this?
        pass

class NumberBlock(Thing):
    def __init__(self, number=0):
        self.number = number

class Agent(Thing):
    """An Agent is a subclass of Thing with one required slot,
    .program, which should hold a function that takes one argument, the
    percept, and returns an action. (What counts as a percept or action
    will depend on the specific environment in which the agent exists.)
    Note that 'program' is a slot, not a method. If it were a method,
    then the program could 'cheat' and look at aspects of the agent.
    It's not supposed to do that: the program can only look at the
    percepts. An agent program that needs a model of the world (and of
    the agent itself) will have to build and maintain its own model.
    There is an optional slot, .performance, which is a number giving
    the performance measure of the agent in its environment."""

    def __init__(self, program=None):
        self.alive = True
        self.bump = False
        self.holding = []
        self.performance = 0
        if program is None or not isinstance(program, collections.Callable):
            print("Can't find a valid program for {}, falling back to default.".format(
                self.__class__.__name__))

            def program(percept):
                return eval(input('Percept={}; action? '.format(percept)))

        self.program = program

    def can_grab(self, thing):
        """Return True if this agent can grab this thing.
        Override for appropriate subclasses of Agent and Thing."""
        return False

class Environment:
    def __init__(self):
        self.things = []
        self.agents = []

    def thing_classes(self):
        return []  # List of classes that can go into environment

    def percept(self, agent):
        """Return the percept that the agent sees at this point. (Implement this.)"""
        raise NotImplementedError

    def execute_action(self, agent, action):
        """Change the world to reflect this action. (Implement this.)"""
        raise NotImplementedError

    def default_location(self, thing):
        """Default location to place a new thing with unspecified location."""
        return None

    def exogenous_change(self):
        """If there is spontaneous change in the world, override this."""
        pass

    def is_done(self):
        """By default, we're done when we can't find a live agent."""
        return not any(agent.is_alive() for agent in self.agents)

    def step(self):
        """Run the environment for one time step. If the
        actions and exogenous changes are independent, this method will
        do. If there are interactions between them, you'll need to
        override this method."""
        if not self.is_done():
            actions = []
            for agent in self.agents:
                if agent.alive:
                    actions.append(agent.program(self.percept(agent)))
                else:
                    actions.append("")
            for (agent, action) in zip(self.agents, actions):
                self.execute_action(agent, action)
            self.exogenous_change()
    def delete_thing(self, thing):
        """Remove a thing from the environment."""
        try:
            self.things.remove(thing)
        except ValueError as e:
            print(e)
            print("  in Environment delete_thing")
            print("  Thing to be removed: {} at {}".format(thing, thing.location))
            print("  from list: {}".format([(thing, thing.location) for thing in self.things]))
        if thing in self.agents:
            self.agents.remove(thing)
    
    def run(self, steps=1000):
        """Run the Environment for given number of time steps."""
        for step in range(steps):
            if self.is_done():
                return
            self.step()

    def list_things_at(self, location, tclass=Thing):
        """Return all things exactly at a given location."""
        return [thing for thing in self.things
                if thing.location == location and isinstance(thing, tclass)]

    def some_things_at(self, location, tclass=Thing):
        """Return true if at least one of the things at location
        is an instance of class tclass (or a subclass)."""
        return self.list_things_at(location, tclass) != []

    def add_thing(self, thing, location=None):
        """Add a thing to the environment, setting its location. For
        convenience, if thing is an agent program we make a new agent
        for it. (Shouldn't need to override this.)"""
        if not isinstance(thing, Thing):
            thing = Agent(thing)
        if thing in self.things:
            print("Can't add the same thing twice")
        else:
            thing.location = location if location is not None else self.default_location(thing)
            self.things.append(thing)
            if isinstance(thing, Agent):
                thing.performance = 0
                self.agents.append(thing)

class XYEnvironment(Environment):
    """This class is for environments on a 2D plane, with locations
    labelled by (x, y) points, either discrete or continuous.

    Agents perceive things within a radius. Each agent in the
    environment has a .location slot which should be a location such
    as (0, 1), and a .holding slot, which should be a list of things
    that are held."""

    def __init__(self, width=10, height=10):
        super().__init__()

        self.width = width
        self.height = height
        self.observers = []
        # Sets iteration start and end (no walls).
        self.x_start, self.y_start = (0, 0)
        self.x_end, self.y_end = (self.width, self.height)

    perceptible_distance = 1

    def percept(self, agent):
        """By default, agent perceives things within a default radius."""
        return self.things_near(agent.location)

    def things_near(self, location, radius=None):
        """Return all things within radius of location."""
        if radius is None:
            radius = self.perceptible_distance
        radius2 = radius * radius   
        return [(thing, thing.location, thing.number if str(type(thing)) == "<class '__main__.NumberBlock'>" else None)
                for thing in self.things if distance_squared(location, thing.location) <= radius2]
    
    def default_location(self, thing):
        return (random.choice(self.width), random.choice(self.height))

    def move_to(self, thing, destination):
        """Move a thing to a new location. Returns True on success or False if there is an Obstacle.
        If thing is holding anything, they move with him."""
        x, y = destination
        if x < 0 or y < 0 or x >= self.width or y >= self.width:
            print("Wrong Action")     
            return 
        loc_a = thing.location
        number = self.list_things_at(destination)[0]
        self.delete_thing(number)
        self.delete_thing(thing)
        self.add_thing(Agent,destination)
        self.add_thing(number, loc_a)

    def delete_thing(self, thing):
        """Deletes thing, and everything it is holding (if thing is an agent)"""
        if isinstance(thing, Agent):
            for obj in thing.holding:
                super().delete_thing(obj)
                for obs in self.observers:
                    obs.thing_deleted(obj)
        super().delete_thing(thing)
        for obs in self.observers:
            obs.thing_deleted(thing)
    
    def add_thing(self, thing, location=(1, 1), exclude_duplicate_class_items=False):
        """Add things to the world. If (exclude_duplicate_class_items) then the item won't be
        added if the location has at least one item of the same class."""
        if (self.is_inbounds(location)):
            if (exclude_duplicate_class_items and
                    any(isinstance(t, thing.__class__) for t in self.list_things_at(location))):
                return
            super().add_thing(thing, location)

    def is_inbounds(self, location):
        """Checks to make sure that the location is inbounds (within walls if we have walls)"""
        x, y = location
        return not (x < self.x_start or x >= self.x_end or y < self.y_start or y >= self.y_end)

    def random_location_inbounds(self, exclude=None):
        """Returns a random location that is inbounds (within walls if we have walls)"""
        location = (random.randint(self.x_start, self.x_end),
                    random.randint(self.y_start, self.y_end))
        if exclude is not None:
            while(location == exclude):
                location = (random.randint(self.x_start, self.x_end),
                            random.randint(self.y_start, self.y_end))
        return location

    def add_observer(self, observer):
        """Adds an observer to the list of observers.
        An observer is typically an EnvGUI.

        Each observer is notified of changes in move_to and add_thing,
        by calling the observer's methods thing_moved(thing)
        and thing_added(thing, loc)."""
        self.observers.append(observer)

    def turn_heading(self, heading, inc):
        """Return the heading to the left (inc=+1) or right (inc=-1) of heading."""
        return turn_heading(heading, inc)

class Node:
    def __init__(self, nine_puzzle, parent = None, action = ""):
        self.state = nine_puzzle
        self.parent = parent
        self.depth = 0
        if parent is not None:
            self.depth = parent.depth+1
            self.action = parent.action +" "+action
        else:
            self.depth = 0
            self.action = action
    def execute_moves(self, excpt_move = ""):
        moves = Queue() 
        _ = self.state.percept()
        for move in self.state.action:
            if move != excpt_move:
                nod = deepcopy(self.state)
                nod.execute_action(move)
                moves.put(Node(nod, self, move))
        return moves
class BFS:
    def __init__(self, puzzle_9, give_step = 500):
        self.start = Node(puzzle_9)
        self.step = 0
        self.chck = False
        self.give_step = give_step
    def search(self):
        closed = []
        child = Queue()
        child.put(self.start)
        correct = []
        while True:
            if child.empty():return max(correct), self.step
            actual = child.get()
            if self.chck==True:
                if child.empty():return max(correct), self.step
                correct.append(actual.state.total_correct())
                actual = child.get()
            elif actual.state.check():
                return actual.state.total_correct(), self.step
            elif actual.state.list_things_at not in closed:
                closed.append(actual.state.list_things_at)
                if actual.depth>1:exec = actual.execute_moves(actual.action.split()[-2])
                else:exec = actual.execute_moves()
                while not exec.empty():
                    if self.step >= self.give_step:
                        self.chck = True
                    else:
                        self.step += 1
                    child.put(exec.get())

class puzzleEnviroment(XYEnvironment):
    def __init__(self,width=6, height=6, steps=500):
        super().__init__(width, height)
        self.makeEnviroment()
        self.steps = steps
        self.action = ['Up','Down','Right','Left']
    def makeEnviroment(self):
        randomlist = random.sample(range(0, self.x_end*self.x_end), self.x_end*self.x_end )
        var = 0
        for i in range(self.width):
            for j in range(self.height):
                if max(randomlist) == randomlist[var]:self.add_thing(Agent, (i, j), True)
                else:self.add_thing(NumberBlock(number = randomlist[var] + 1), (i,j), True)
                var+=1
    def get_world(self):
        """Return the items in the world"""
        result = []
        for x in range(self.width):
            row = []
            for y in range(self.width):
                thing = self.list_things_at((x, y))[0]
                numb = thing.number if str(type(thing)) == "<class '__main__.NumberBlock'>" else 0
                row.append(numb)
            result.append(row)
        return result
    def percept(self):
        ag = self.agents[0]
        cv = self.things_near(ag.location)
        actions = []
        for i in cv:
            _, loc, _ = i
            c = tuple(x-y for x, y in zip(ag.location, loc))
            if c == (1,0):actions.append("Up")
            elif c == (0,-1):actions.append("Right")
            elif c == (0,1):actions.append("Left")
            elif c == (-1,0):actions.append("Down")
            self.action = actions
        return self.things_near(ag.location)
    def execute_action(self, action):
        agent = self.agents[0]
        """Modify the state of the environment based on the agent's actions.
        Performance score taken directly out of the book."""
        agent.bump = False
        loc_1, loc_2 = agent.location        
        if action == 'Up':
            self.move_to(agent, (loc_1 - 1, loc_2))
        elif action == 'Down':
            self.move_to(agent, (loc_1 + 1, loc_2))
        elif action == 'Right':
            self.move_to(agent, (loc_1 , loc_2 + 1))
        elif action == 'Left':
            self.move_to(agent, (loc_1 ,loc_2 - 1))
        else:
            pass
    def check(self):
        puzz = self.get_world()
        val = 1
        for x in range(self.width):
            for y in range(self.width):
                if x == self.width-1 and y == self.width-1:
                    return True
                if puzz[x][y] != val:
                    return False
                val+=1
        return True
    def total_correct(self):
        puzz = self.get_world()
        val = 1
        total = 0
        for x in range(self.width):
            for y in range(self.width):
                if x == self.width-1 and y == self.width-1:total+=0
                if puzz[x][y] == val:total+=1
                val+=1
        return total
    def run(self):
        a = puzzleEnviroment(self.height, self.height)
        agent = BFS(a,self.steps)
        x,y= agent.search()
        print("No of correct pieces = ",str(x)+", no of moves utilized = ", y)
a = puzzleEnviroment(int(sys.argv[1]), int(sys.argv[1]), steps = int(sys.argv[2]))
a.run()

