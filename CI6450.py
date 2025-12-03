from random import random
import pygame
from math import inf
import numpy as np
from numpy.linalg import norm
import matplotlib.path as mpath

from IO import Screen, Input, gEvent
from Geometries import Circle, Rect, Polygon, circle_rect_collision
from Algos import Algos
from Map import Map
from StateMachine import StateMachine

class Game(object):
    mousepos = Circle(None,None,[0,0])
    scenario = -2
    scText = ""
    selection = None
    A = Algos()
    M = Map()
    circle = []
    SM = StateMachine(circle, M, A)
    def __init__(self):
        self.debug = []


            

    def drag(self, data):
        dx = data[0] - self.mousepos.d[0]
        dy = data[1] - self.mousepos.d[1]

        for c in self.Geometries():
            if type(c) == Polygon:
                c.points = [p + [dx,dy] for p in c.points]
                c.mpath = mpath.Path(c.points)
            elif type(c) == Circle or type(c) == Rect: c.d += [dx,dy]
                            
        G.mousepos.d = data

    def tick(self):
        self.debug.clear()
        for c in self.circle:
            c.food -=1
            if not c.food: 
                c.status[0] = "ded"

            pol = self.M.getLocation(c)
            if pol and ((pol.type == "ocean" and random() > 0.996) or (pol.type == "snow" and not c.items["coat"] and random() > 0.999) or pol.type == "lava"): 
                c.status[0] = "ded"

            

        self.circle[:] = [c for c in self.circle if c.status[0] != "ded"]

        if self.M.change:
            for c in self.circle:
                c.status[1] = c.path_goal
                c.status[0] = c.path2_goal
        self.M.change = False

        for c in self.circle:       
            self.SM.runAlg(c)

        for wall in self.M.walls:
            for c in self.circle:
                if circle_rect_collision(c, wall):
                    c.d = c.d - c.v


    def Geometries(self, showPP = True): 
        circlepath = []
        if type(self.selection) == Circle:
            circlepath = [Circle(c.d.copy(), 6, (255,0,0)) for c in self.selection.path]
            for i in range(len(self.selection.path)-1):
                circlepath.append([circlepath[i].d, circlepath[i+1].d])

        return self.M.Geometries(showPP) + self.circle + self.debug + circlepath



    newPol = []

    mode = "n"

    def addPolygon(self, pos):
        if self.mode not in ("q", "e"): return

        if len(self.M.polygons) == 0 or self.mode == "q":
            if len(self.newPol) < 3:
                gotchu = 0
                for p in self.M.polPoints:
                    if p.clicked(pos):
                        pos = p.d
                        gotchu = 1
                        break
                if (gotchu or len(self.newPol) == 2 or len(self.M.polygons) == 1): 
                    for p in self.newPol:
                        if p[0] == pos[0] and p[1] == pos[1]: return
                    self.newPol.append(pos.copy())
        else:
            if len(self.newPol) != 0:
                self.newPol.clear()
            first = None
            distance = inf
            for p in self.M.polPoints:
                d = norm(p.d - pos)
                if d < distance:
                    first = p.d
                    distance = d
            second = None
            distance = inf
            for p in self.M.polPoints:
                d = norm(p.d - pos)
                if d < distance and p.d[0] != first[0] and p.d[1] != first[1]:
                    second = p.d
                    distance = d
            self.newPol = [pos.copy(), first.copy(), second.copy()]
                    
        if len(self.newPol) == 3:
            self.M.addPolygon(self.newPol.copy())
            self.newPol.clear()
            
            
    def addWall(self, corners):
        if self.mode != "w": return
        self.M.addWall(corners)

    def addPeasant(self,pos):
        C = Circle(np.array(pos), 25, (0,255,0), 1)
        self.SM.assign(C, "peasant")
        self.circle.append(C)

    def addMiner(self,pos):
        C = Circle(np.array(pos), 25, (255,0,0), 1)
        self.SM.assign(C, "miner")
        self.circle.append(C)

    def addArtisan(self,pos):
        C = Circle(np.array(pos), 25, (230,80,0), 1)
        self.SM.assign(C, "artisan")
        self.circle.append(C)

    def addField(self,pos):
        self.M.change = True
        pol = self.M.getPolygon(pos)
        if not pol: return
        pol.type = "field"
        pol.productivity = 10
        pol.fieldColor()
        self.M.fields.append(pol)

    def addIron(self,pos):
        self.M.change = True
        pol = self.M.getPolygon(pos)
        if not pol: return
        pol.type = "iron"
        pol.productivity = 10
        pol.ironColor()
        self.M.mines.append(pol)
    
    def changeProductivity(self, pos, val):
        self.M.change = True
        pol = self.M.getPolygon(pos)
        if not pol or pol.type not in ("field", "iron"): return
        pol.productivity += val
        if pol.productivity > 45: pol.productivity = 45
        if pol.productivity < 1: pol.productivity = 1
        if pol.type == "field":pol.fieldColor()
        else: pol.ironColor()

    def addwater(self, pos):
        self.M.change = True
        pol = self.M.getPolygon(pos)
        if not pol: return
        pol.type = "ocean"
        pol.color = (80,80,200)
        self.M.oceans.append(pol)

    def addice(self, pos):
        self.M.change = True
        pol = self.M.getPolygon(pos)
        if not pol: return
        pol.type = "snow"
        pol.color = (255,255,255)
        self.M.snow.append(pol)

    def addBase(self, pos):
        self.M.change = True
        pol = self.M.getPolygon(pos)
        if not pol: return
        pol.type = "base"
        pol.color = (10,10,10)
        self.M.bases.append(pol)

    def addLava(self, pos):
        self.M.change = True
        pol = self.M.getPolygon(pos)
        if not pol: return
        pol.type = "lava"
        pol.color = (200,40,0)
        self.M.lava.append(pol)

    def addWorkshop(self, pos):
        self.M.change = True
        pol = self.M.getPolygon(pos)
        if not pol: return
        pol.type = "workshop"
        pol.color = (255, 69, 0)
        self.M.workshop.append(pol)

    def select(self, pos):
        for c in self.circle:
            if c.clicked(pos): 
                self.selection = c
                return
        for pol in self.M.polygons:
            if pol.mpath.contains_point(pos):
                self.selection = pol
                return
        self.selection = None



pygame.init()
screen_width = 1500
screen_height = 720
Sc = Screen(pygame, screen_width, screen_height)
I = Input(pygame)
G = Game()
running = True
while running:
    for (eType, data) in I.getEvents():
        if eType == gEvent.QUIT:
            running = False

        elif eType == gEvent.LEFTCLICKUP:
            pass

        elif eType == gEvent.DRAG:
            G.drag(data[0])

        elif eType == gEvent.RDRAG:
            pass

        elif eType == gEvent.RIGHTDRAGUP:
            G.addWall(data)

        elif eType == gEvent.LEFTCLICKDOWN:
            pass

        elif eType == gEvent.DOUBLECLICK:
            G.select(data)

        elif eType == gEvent.RIGHTCLICKDOWN:
            if G.mode == "p": G.addPeasant(data)
            if G.mode == "m": G.addMiner(data)
            if G.mode == "f": G.addField(data)
            if G.mode == "a": G.addwater(data)
            if G.mode == "i": G.addice(data)
            if G.mode == "b": G.addBase(data)
            if G.mode == "l": G.addLava(data)
            if G.mode == "o": G.addIron(data)
            if G.mode == "k": G.addWorkshop(data)
            if G.mode == "c": G.addArtisan(data)
            else: G.addPolygon(np.array(data))

        elif eType == gEvent.MOUSEWHEEL:
            G.changeProductivity(*data)
            pass

        elif eType == gEvent.MOUSEMOTION:
            G.mousepos.d = data

        elif eType == gEvent.CHAR:
            if data == "w":
                G.mode = "w"
                G.scText = "add wall"
            elif data == "q":
                G.mode = "q"
                G.scText = "manual add polygon"
            elif data == "e":
                G.mode = "e"
                G.scText = "smart add polygon"
            elif data == "s":
                G.M.save()
            elif data == "r":
                G.M.read()
            elif data == "p":
                G.mode = "p"
                G.scText = "add peasant"
            elif data == "f":
                G.mode = "f"
                G.scText = "add field"
            elif data == "a":
                G.mode = "a"
                G.scText = "add ocean"
            elif data == "i":
                G.mode = "i"
                G.scText = "add snow"
            elif data == "b":
                G.mode = "b"
                G.scText = "add base"
            elif data == "l":
                G.mode = "l"
                G.scText = "add lava"
            elif data == "o":
                G.mode = "o"
                G.scText = "add iron"
            elif data == "m":
                G.mode = "m"
                G.scText = "add miner"
            elif data == "k":
                G.mode = "k"
                G.scText = "add workshop"
            elif data == "c":
                G.mode = "c"
                G.scText = "add artisan"


    Sc.clearScreen()
    Sc.draw(G.Geometries(G.mode in ("q", "e", "w")))
    Sc.write(G.scText,(140, 620))
    Sc.info(G.selection)
    Sc.display()
    G.tick()
    
pygame.quit()