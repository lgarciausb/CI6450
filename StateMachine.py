
from math import inf
from numpy.linalg import norm
from random import choice, random

from Geometries import Circle
from Map import Map
from Algos import Algos

class StateMachine(object):

    def __init__(self, C:list[Circle], M:Map, A:Algos):
        self.C = C
        self.M = M
        self.A = A

        self.indexes = {}

    def __getitem__(self, key):
        return getattr(self, key)

    def assign(self, C, type):
        self.indexes[C] = ["hunger", type]

    def runAlg(self, C, i = 0):
        type = self.indexes[C]
        self[type[i]](C)

    def getPath(self, start_pol, cost_fn, target_pols):
        shortest_path = []
        lowest_cost = inf
        for end_pol in target_pols:
            path = self.M.astar(
                start_pol.i,
                end_pol.i,
                cost_fn
            )
            cost = 0
            for e in range(len(path)-1):
                cost += cost_fn([self.M.polygons[path[e]], self.M.polygons[path[e+1]]])
            cost -= end_pol.productivity*50
            if cost < lowest_cost:
                lowest_cost = cost
                shortest_path = path

        if len(shortest_path) > 1: shortest_path = shortest_path[1:]
        return [self.M.polygons[i].center for i in shortest_path]


    def hunger(self,c):

        cost_fn = lambda e: norm(e[0].center.d - e[1].center.d) \
                + (e[1].type == "snow" and not c.items["coat"])*250 \
                + (e[1].type == "ocean")*500 \
                + (e[1].type == "lava")*999999999

        if c.status[0] == None:
            if c.food < 1000:
                c.status[0] = "hunger"
            else: self.runAlg(c, 1)

        elif c.status[0] == "hunger":
            if c.items["food"] > 0:
                c.items["food"] -=1
                c.food = 5000
                c.status[0] = None
            else: 
                c.status[1] = c.path_goal
                c.status[0] = "path_to_base"
                c.pol.worked = None

        elif c.status[0] == "path_to_base":
            start_pol = self.M.getLocation(c)
            c.path = self.getPath(start_pol, cost_fn, [b for b in self.M.bases if b.items["food"]]) 
            if c.path: 
                c.status[0] = "base"
                c.path2_goal = "path_to_base"
                c.target = None
        
        elif c.status[0] == "base":
            if self.A.pathFollow(c):
                while c.pol.items["food"] and c.items["food"] < 10:
                    c.items["food"] +=1
                    c.pol.items["food"] -=1
                c.clearPath()
                c.status[0] = None
                if not c.items["food"]: c.status[0] = "hunger"
                else: c.path2_goal = None
                    
    def peasant(self, c:Circle):

        cost_fn = lambda e: norm(e[0].center.d - e[1].center.d) \
                + (e[1].type == "snow" and not c.items["coat"])*250 \
                + (e[1].type == "ocean")*500 \
                + (e[1].type == "lava")*99999999999

    
        if c.status[1] == None:
            start_pol = self.M.getLocation(c)
            c.path = self.getPath(start_pol, cost_fn, [field for field in self.M.fields if field.worked == None]) 
            if c.path: 
                c.status[1] = "search"
                c.path_goal = None
                c.target = None

        elif c.status[1] == "search":

            if self.A.pathFollow(c):
                pol = self.M.getLocation(c)
                if pol.worked != None:
                    c.status[1] = None
                else:
                    pol.worked = c
                    c.status[1] = "farm"
                    self.M.change = True
                    c.path_goal = "farm"

        elif c.status[1] == "farm":
            
            if random() < c.pol.productivity*0.000222: 
                c.items["fiber"] += 1
            if random() < c.pol.productivity*0.000222: 
                c.items["food"] +=1
                if random() > 0.96: 
                    c.pol.productivity -= 1 
                    c.pol.fieldColor()

            if c.pol.productivity <= 0: 
                c.pol.productivity = 0
                c.pol.type = None
                try:self.M.fields.remove(c.pol)
                except: pass
                c.status[1] = None

            if c.items["food"] > 9: 
                c.status[1] = "path_to_base"
                c.path_goal = "path_to_base"
                self.M.getLocation(c).worked = None
                self.M.change = True
                


        elif c.status[1] == "path_to_base":
            start_pol = self.M.getLocation(c)
            c.path = self.getPath(start_pol, cost_fn, self.M.bases) 
            if c.path: 
                c.status[1] = "base"
                c.target = None

        elif c.status[1] == "base":
            
            if self.A.pathFollow(c):
                c.pol.items["food"] += c.items["food"]//2
                c.items["food"] -= c.items["food"]//2
                c.pol.items["fiber"] += c.items["fiber"]
                c.items["fiber"] -= c.items["fiber"]

                if c.pol.items["coat"] and not c.items["coat"]:
                    c.pol.items["coat"] -= 1
                    c.items["coat"] += 1

                c.clearPath()
                c.status[1] = None
                c.path_goal = None
            


    def miner(self, c:Circle):

        cost_fn = lambda e: norm(e[0].center.d - e[1].center.d) \
                + (e[1].type == "snow" and not c.items["coat"])*250 \
                + (e[1].type == "ocean")*500 \
                + (e[1].type == "lava")*999999999

    
        if c.status[1] == None:
            start_pol = self.M.getLocation(c)
            c.path = self.getPath(start_pol, cost_fn, [mine for mine in self.M.mines if mine.worked == None and (c.items["pickaxe"] or mine.productivity >= 40)]) 
            if c.path: 
                c.status[1] = "search"
                c.path_goal = None
                c.target = None
            else: 
                c.path = self.getPath(start_pol, cost_fn, [base for base in self.M.bases if base.items["pickaxe"] and not c.items["pickaxe"]]) 
                if c.path: 
                    c.status[1] = "base"
                    c.path_goal = None
                    c.target = None

        elif c.status[1] == "search":

            if self.A.pathFollow(c):
                pol = self.M.getLocation(c)
                if pol.worked != None:
                    c.status[1] = None
                else:
                    pol.worked = c
                    self.M.change = True
                    c.status[1] = "mine"
                    c.path_goal = "mine"
                c.clearPath()

        elif c.status[1] == "mine":
            
            if random() < c.pol.productivity*0.000222: 
                c.items["iron"] +=1
                if random() > 0.9: 
                    c.pol.productivity -= 1 
                    c.pol.ironColor()

            if c.pol.productivity <= 0: 
                c.pol.productivity = 0
                c.pol.type = None
                try:self.M.mines.remove(c.pol)
                except: pass
                c.pol.worked = None
                self.M.change = True
                c.status[1] = None
                c.path_goal = None

            if c.items["iron"] > 9: 
                c.status[1] = "path_to_base"
                c.path_goal = "path_to_base"
                self.M.getLocation(c).worked = None
                self.M.change = True


        elif c.status[1] == "path_to_base":
            start_pol = self.M.getLocation(c)
            c.path = self.getPath(start_pol, cost_fn, self.M.bases) 
            if c.path: 
                c.status[1] = "base"
                c.target = None


        elif c.status[1] == "base":
            
            if self.A.pathFollow(c):
                c.pol.items["iron"] += c.items["iron"]
                c.items["iron"] -= c.items["iron"]

                if c.pol.items["coat"] and not c.items["coat"]:
                    c.pol.items["coat"] -= 1
                    c.items["coat"] += 1
                if c.pol.items["pickaxe"] and not c.items["pickaxe"]:
                    c.pol.items["pickaxe"] -= 1
                    c.items["pickaxe"] += 1


                c.clearPath()
                c.status[1] = None
                

    def artisan(self, c:Circle):

            cost_fn = lambda e: norm(e[0].center.d - e[1].center.d) \
                    + (e[1].type == "snow" and not c.items["coat"])*250 \
                    + (e[1].type == "ocean")*500 \
                    + (e[1].type == "lava")*999999999

        
            if c.status[1] == None:
                start_pol = self.M.getLocation(c)
                c.path = self.getPath(start_pol, cost_fn, [base for base in self.M.bases if base.items["fiber"] or base.items["iron"]]) 
                if c.path: 
                    c.status[1] = "searchBase"
                    c.path_goal = None
                    c.target = None

            elif c.status[1] == "searchBase":
                if self.A.pathFollow(c):
                    for item in ["pickaxe", "coat"]:
                        c.pol.items[item] += c.items[item]
                        c.items[item] -= c.items[item]

                    c.status[1] = "get_res"
                    c.path_goal = "get_res"
                    c.clearPath()

            elif c.status[1] == "get_res":
                opts = []
                if c.pol.items["fiber"] >= 10: opts.append("fiber")
                if c.pol.items["iron"] >= 10: opts.append("iron")
                try: item = choice(opts)
                except: return

                c.pol.items[item] -= 10
                c.items[item] += 10

                c.status[1] = "path_to_WS"
                c.path_goal = "path_to_WS"

            elif c.status[1] == "path_to_WS":
                start_pol = self.M.getLocation(c)
                c.path = self.getPath(start_pol, cost_fn, [ws for ws in self.M.workshop if ws.worked == None]) 
                if c.path: 
                    c.status[1] = "searchWS"
                    c.target = None

            elif c.status[1] == "searchWS":
                if self.A.pathFollow(c):
                    c.clearPath()
                    opts = []
                    if c.items["fiber"]: opts.append("fiber")
                    if c.items["iron"]: opts.append("iron")

                    c.timer = 0
                    c.crafting = choice(opts)
                    self.M.getLocation(c).worked = c
                    self.M.change = True
                    c.status[1] = "craft"
                    c.path_goal = "craft"


            elif c.status[1] == "craft":
                
                c.timer +=1

                if c.timer > 500: 
                    c.items[c.crafting] -= 10
                    c.items["pickaxe" if c.crafting == "iron" else "coat"] +=1

                    self.M.getLocation(c).worked = None
                    self.M.change = True
                    c.status[1] = None
                    c.path_goal = None
                