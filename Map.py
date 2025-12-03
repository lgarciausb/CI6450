import json
from math import inf
import rustworkx as rx
import numpy as np
import matplotlib.path as mpath
from numpy.linalg import norm

from Geometries import Rect, Circle, Polygon

class Map(object):

    def __init__(self):
        self.polygons = []
        self.polPoints = []
        self.walls = []
        self.fields = []
        self.mines = []
        self.oceans = []
        self.snow = []
        self.lava = []
        self.bases = []
        self.workshop = []
        self.read()
        self.change = False

    def buildGraph(self):

        p = self.polygons
        min = inf
        self.G = rx.PyGraph()
        sets = []
        for i in range(len(p)):
            p[i].i = self.G.add_node(p[i])
            sets.append(set(tuple(point) for point in p[i].points))
        for i in range(len(p)):
            for e in range(i+1, len(p)):
                if len(sets[i].intersection(sets[e])) == 2:
                    if min > norm(p[i].center.d - p[e].center.d):
                        min = norm(p[i].center.d - p[e].center.d) 
                    self.G.add_edge(p[i].i, p[e].i, (p[i], p[e]))
        #print(min)


    def drag(self,dx,dy):
        for pol in self.polygons:
            pol.points = [p + [dx,dy] for p in pol.points]
        for wall in self.walls:
            wall.d += [dx,dy]
        for c in self.polPoints:
            wall.d += [dx,dy]

    def addWall(self, corners):
        self.walls.append(Rect(
            np.array([min(corners[0][0], corners[1][0]), min(corners[0][1], corners[1][1])]),
            abs(corners[0][0] - corners[1][0]),
            abs(corners[0][1] - corners[1][1]),
            (80,10,0)
        ))

    def addPolygon(self, pol):
        self.polygons.append(Polygon(pol))
        for p in pol:
            self.polPoints.append(Circle(p, 30))

    def Geometries(self, showPP = True):
        return  self.polygons + \
                (self.polPoints if showPP else []) + \
                [pol.center for pol in self.polygons] + \
                [[self.polygons[p1].center.d, self.polygons[p2].center.d] for (p1,p2) in self.G.edge_list()] +\
                self.walls
    
    def save(self):
        f = open("map.json", "w")
        f.write(json.dumps({
            "polygons":[[p.tolist() for p in pol.points] for pol in self.polygons], 
            "walls":[[wall.d.tolist(), (wall.d + [wall.width, wall.height]).tolist()] for wall in self.walls]
            }))
        f.close()

    def read(self):
        f = open("map.json", "r")
        jzon = json.loads(f.read())
        newPols = [[np.array(p) for p in pol] for pol in jzon["polygons"]]
        newWalls = [[np.array(p) for p in pol] for pol in jzon["walls"]]
        f.close()

        self.walls = []
        for w in newWalls: 
            self.addWall(w)

        self.polygons = []
        self.polPoints = []
        for pol in newPols: 
            if not len(pol): continue
            self.addPolygon(pol)

        self.buildGraph()

    def getPolygon(self, pos):
        for pol in self.polygons:
            if pol.mpath.contains_point(pos): return pol
        return None
    
    def getLocation(self, C):
        if not C.pol: C.pol = self.getPolygon(C.d)
        elif not C.pol.mpath.contains_point(C.d):
            for i in self.G.neighbors(C.pol.i):
                if self.polygons[i].mpath.contains_point(C.d): 
                    C.pol = self.polygons[i]
                    break
        return C.pol

    def getNeighbors(self, pos):
        pol = self.getPolygon(pos)
        return self.G.neighbors(pol.i)
    
    def astar(self,u, v, fn):
        return rx.astar_shortest_path(self.G, u,lambda p: p.i == v, fn,lambda p: norm(p.center.d - self.polygons[v].center.d)
        )
