import pygame
from enum import Enum
from math import sqrt, atan2, pi, cos, sin, inf
import time
import rustworkx as rx
import numpy as np
from numpy.linalg import norm
from random import random


class Screen(object):
    def __init__(self, pg:pygame, screen_width, screen_height):
        self.pg = pg
        self.sc = self.pg.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
        self.pg.display.set_caption("CI6450")
        self.font = pg.font.Font(size=32)

    def draw(self, elements):
        for el in elements:
            if type(el) == Rect: 
                self.drawRect(el)
            elif type(el) == Circle: self.drawCircle(el)

    def drawRect(self, rect):
        self.pg.draw.rect(self.sc, rect.square_color, (rect.d[0], rect.d[1], rect.width, rect.height), rect.outline)

    def drawCircle(self, circle):
        self.pg.draw.circle(self.sc, circle.color, circle.d, circle.radius)
        if circle.color == (0,0,0): return
        H = circle.radius+20
        self.pg.draw.line(self.sc, circle.color, circle.d, circle.d+[-H*sin(circle.o), H*cos(circle.o)], 5)


    def clearScreen(self):
        self.sc.fill((255, 255, 255))

    def display(self): self.pg.display.flip()

    def write(self, text, doko):
        text_surface = self.font.render(text, True, (0, 0, 0))
        text_rect = text_surface.get_rect()
        text_rect.center = doko
        self.sc.blit(text_surface, text_rect)

class gEvent(Enum):
        QUIT=0
        LEFTCLICKUP = 1
        MOUSEMOTION = 2
        DRAG = 3
        LEFTCLICKDOWN = 4
        MOUSEWHEEL = 5
        NUMBER = 6
        CHAR = 7
        RIGHTCLICKUP = 8
        RIGHTCLICKDOWN = 9
        DOUBLECLICK = 10

class Input(object):

    def __init__(self, pg):
        self.pg = pg
        self.drag = None
        self.lastClick = 0
        self.doubleClickTime = 0.150 #seconds

    def getEvents(self): 
        for event in self.pg.event.get():
            if event.type == pygame.QUIT:
                yield gEvent.QUIT, None
            
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if self.drag != None:
                    self.drag = None
                    yield gEvent.LEFTCLICKUP, pygame.mouse.get_pos()

            elif event.type == pygame.MOUSEMOTION:
                if self.drag != None: yield gEvent.DRAG, [pygame.mouse.get_pos(), self.drag]
                else: yield gEvent.MOUSEMOTION, pygame.mouse.get_pos()

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.lastClick+self.doubleClickTime > time.time():
                    self.lastClick = 0
                    yield gEvent.DOUBLECLICK, pygame.mouse.get_pos()
                else:
                    self.lastClick = time.time()
                    self.drag = pygame.mouse.get_pos()
                    yield gEvent.LEFTCLICKDOWN, pygame.mouse.get_pos()

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                yield gEvent.RIGHTCLICKDOWN, pygame.mouse.get_pos()
            
            elif event.type == pygame.MOUSEWHEEL:
                yield gEvent.MOUSEWHEEL, event.y
                
            elif event.type == pygame.KEYDOWN:
                if event.unicode.isdigit(): yield gEvent.NUMBER, int(event.unicode)
                else: yield gEvent.CHAR, event.unicode


class Rect(object):
    def __init__(self,d,width, height, square_color, outline = 0):
        self.d = d
        self.square_color =  square_color
        self.height = height
        self.width = width
        self.outline = outline

    def topright(self): return (self.d[0]+self.width,self.d[1])
    def bottomleft(self): return (self.d[0]+self.width,self.d[1]+self.height)
    def bottomright(self): return (self.d[0]+self.width,self.d[1]+self.height)

    def inside(self,mp):
        return (self.height != 0 and self.width != 0
                ) and (mp[0] >= self.d[0] and mp[1] >= self.d[1]
                ) and (mp[0] <= self.d[0] + self.width and mp[1] >= self.d[1]
                ) and (mp[0] >= self.d[0] and mp[1] <= self.d[1] + self.height
                ) and (mp[0] <= self.d[0] + self.width and mp[1] <= self.d[1] + self.height)
    
    def normal(self, mp, ad):
        Dleft = abs(mp[0] - self.d[0])
        Dright = abs(mp[0] - self.d[0]-self.width)
        Dup = abs(mp[1] - self.d[1])
        Ddown = abs(mp[1] - self.d[1]-self.height)

        if min(Dleft, Dright, Dup, Ddown) == Dleft:
            return np.array([self.d[0]-ad, mp[1]])
        elif min(Dleft, Dright, Dup, Ddown) == Dright:
            return np.array([self.d[0] + self.width + ad, mp[1]])
        if min(Dleft, Dright, Dup, Ddown) == Dup:
            return np.array([mp[0], self.d[1]-ad])
        else:
            return np.array([mp[0], self.d[1] + self.height + ad])
  

class Circle(object):
    def __init__(self, d=[0,0], radius=0, color=(0,0,0)):
        self.radius = radius
        self.color =  color
        self.d = d
        self.v = np.array([0,0])
        self.a = np.array([0,0])
        self.o = 0
        self.r = 0
        self.alpha = 0
        self.target = None

    def clicked(self, mp):
        distance = sqrt((self.d[0]-mp[0])**2 + (self.d[1]-mp[1])**2)
        return distance <= self.radius

class Algos(object):

    def __init__(self):
        self.indexes = {}

    def __getitem__(self, key):
        return getattr(self, key)
    
    def assign(self, S, i, *t):
        self.indexes[S] = [i, t]

    def runAlg(self,S):
        i, t = self.indexes[S]
        if t: self[i](S, *t)
        else: self[i](S)

    def newOrientation(self, S, v):
        if v.any(): 
            S.o = atan2(-v[0], v[1])

    def move(self, S):
        S.d = S.d + S.v
    def rotate(self,S,r):
        S.o += r

    def seek(self, S, T, maxS = 0.25): 
        delta =  T.d- S.d
        H = norm(delta)
        S.v = maxS*delta/H
        self.newOrientation(S, S.v)
        self.move(S)

    def arrive(self, S, T, maxS = 0.25, ttt = 500, minD = 25): 
        delta =  T.d- S.d
        H = norm(delta)
        if H <= minD: S.v = np.array([0,0]) 
        else: S.v = min(maxS, H/ttt)*delta/H
        self.newOrientation(S, S.v)
        self.move(S)

    def flee(self, S, T, maxS = 0.05, ttt = 500): 
        delta =  T.d- S.d
        H = norm(delta)
        S.v = -min(maxS, H/ttt)*delta/H
        self.newOrientation(S, S.v)
        self.move(S)

    def Dseek(self, S, T, maxA = 0.001, maxS = 10):
        delta =  T.d- S.d
        H = norm(delta)
        a = maxA*delta/H
        S.v = S.v + a
        if abs(norm(S.v)) > maxS:
            S.v = maxS*S.v/norm(S.v)
        self.newOrientation(S, S.v)
        self.move(S)

    def Dflee(self, S, T, maxA = 0.00005, maxS = 0.20):
        delta =  T.d- S.d
        H = norm(delta)
        a = maxA*delta/H
        S.v = S.v - a
        if abs(norm(S.v)) > maxS:
            S.v = maxS*S.v/norm(S.v)
        self.newOrientation(S, S.v)
        self.move(S)

    def Darrive(self, S, T, minD = 25, slowD = 100, maxS = 0.25, maxA = 0.0005, ttt= 500):
        delta =  T.d- S.d
        H = norm(delta)
        if H <= minD: 
            S.v = np.array([0,0])
        else:
            if H < slowD: 
                targetV = maxS * H / slowD 
            else:
                targetV = maxS
            
            v = targetV*delta/H

            a = (v - S.v)/ttt
            if norm(a) > maxA:
                a = maxA*a/norm(a)
            S.v = S.v + a
            self.lwyg(S)
        self.move(S)

    def align(self, S, T, minD = pi/128, slowD = pi/32, maxR = 0.05, maxAlpha = 0.0005, ttt= 500):
        delta =  T.o- S.o
        delta = (delta + pi) % (2 * pi) - pi
        R = abs(delta)
        if R <= minD: 
            S.r = 0
        else:
            if R < slowD: 
                targetR = maxR * R / slowD 
            else:
                targetR = maxR
            
            r = targetR*delta/R

            alpha = (r - S.r)/ttt
            if norm(alpha) > maxAlpha:
                alpha = maxAlpha*alpha/norm(alpha)
            S.r = S.r + alpha
        self.rotate(S,S.r)

    def Vmatch(self, S, T, maxA = 0.0005, ttt= 500):

        v = T.v

        a = (v - S.v)/ttt
        if norm(a) > maxA:
            a = maxA*a/norm(a)
        S.v = S.v + a
        self.newOrientation(S, S.v)
        self.move(S)
    
    def wander(self, S, maxS = 0.25, maxR = pi/24):
        r = (random()-random()) * maxR
        self.rotate(S,r)
        S.v = np.array([-maxS*sin(S.o), maxS*cos(S.o)])
        self.move(S)

    def face(self, S, T, minD = pi/128, slowD = pi/32, maxR = 0.01, maxAlpha = 0.000005, ttt= 500):

        delta = S.d - T.d
        T2 = Circle([0,0])
        T2.o = atan2(delta[0], -delta[1])
        self.align(S, T2, minD, slowD, maxR, maxAlpha, ttt)


    def pursue(self, S, T, maxPrediction = 500 , minD = 25, slowD = 100, maxS = 0.25, maxA = 0.0005, ttt= 500):
        delta =  T.d- S.d
        H = norm(delta)
        s = norm(S.v)

        if s <= H/maxPrediction: prediction = maxPrediction
        else: prediction = H/s

        T2 = Circle([0,0])
        T2.d = T.d + T.v*prediction
        self.Darrive(S, T2, minD, slowD, maxS, maxA, ttt)

    def evade(self, S, T, maxPrediction = 500 , minD = 25, slowD = 100, maxS = 0.25, maxA = 0.0005, ttt= 500):
        delta =  T.d- S.d
        H = norm(delta)
        s = norm(S.v)

        if s <= H/maxPrediction: prediction = maxPrediction
        else: prediction = H/s

        T2 = Circle()
        T2.d = T.d + T.v*prediction
        self.Dflee(S, T2, maxA, maxS)

    def lwyg(self, S, minD = pi/128, slowD = pi/32, maxR = 0.05, maxAlpha = 0.0005, ttt= 500):
        
        T2 = Circle()
        T2.o = atan2(-S.v[0], S.v[1])
        self.align(S, T2, minD, slowD, maxR, maxAlpha, ttt)
        
    def Dwander(self, S, minD = pi/128, slowD = pi/32, maxR = 0.0005, maxAlpha = 0.0005, ttt= 500, Wrate = pi/128,Woffset = 75, Wradius = 25, maxA = 0.00005):
        o = (random()-random()) * Wrate
        targetO = S.o + o
        target = S.d + Woffset*np.array([cos(S.o), -sin(S.o)])
        target += Wradius * np.array([cos(targetO), -sin(targetO)])
        
        S.a = maxA *np.array([cos(S.o), -sin(S.o)])
        S.v = S.v +  S.a
        self.move(S)

        T2 = Circle()
        T2.d = [0,0]
        self.face(S, T2, minD, slowD, maxR, maxAlpha, ttt)


    def pathFollow(self, S, P, minD = 50):
        if S.target == None:
            newTarget = None
            targetH = inf
            for i in range(0, len(P)-1):
                H = norm(P[i].d - S.d)
                if H < targetH:
                    targetH = H
                    newTarget = i
            S.target = newTarget
        elif norm(P[S.target].d - S.d) < minD:

            S.target = (S.target + 1) % len(P)
        T = P[S.target]
        self.seek(S, T)

    def avoidWall(self, S, walls, rays, lookahead = 100, avoidDistance = 100):
        ray = []
        o = atan2(S.v[1], S.v[0])
        for i in range(11,1,-1):
            #rays.append(Circle(S.d + np.array([lookahead*cos(o)/i,lookahead*sin(o)/i])))
            ray.append(S.d + np.array([lookahead*cos(o)/i,lookahead*sin(o)/i]))
        for w in walls:
            for p in ray:
                if w.inside(p):
                    T = Circle(w.normal(p, avoidDistance))
                    self.seek(S, T)
                    return True
        return False
    
    def wall_plus_Pursue(self, S, T, walls, rays):
        if not self.avoidWall(S, walls, rays): self.pursue(S,T)
        

    def wall_plus_Evade(self, S, T, walls, rays):
        if not self.avoidWall(S, walls, rays): self.evade(S,T)

class Geometry(object):
    mousepos = Circle(None,None,[0,0])
    scenario = 0
    A = Algos()
    def __init__(self):
        self.rays = []
        self.circle = [
        ]
        self.paths = [

        ]
        self.walls = [

        ]


    def setScenario(self, data):
        if data == "w": 
            self.scenario +=1
        elif data == "q": 
            self.scenario -=1
        else: return
        self.circle.clear()
        self.paths.clear()
        self.walls.clear()
        self.A.indexes.clear()

        i = self.scenario
        #seek player
        if i == 0:
            self.circle = [
                Circle(
                    np.array([800+50,720/2+50]),
                    25, 
                    (0,0,255),
                ),
                Circle(
                    np.array([400,720/2]),
                    25, 
                    (255,0,0),
                )
            ]
            self.A.assign(self.circle[0], "arrive", self.mousepos)
            self.A.assign(self.circle[1], "seek", self.circle[0])
        
        #arrive
        elif i == 1:
            self.circle = [
                Circle(
                    np.array([800+50,720/2+50]),
                    25, 
                    (0,0,255),
                ),
                Circle(
                    np.array([400,720/2]),
                    25, 
                    (255,0,0),
                )
            ]
            self.A.assign(self.circle[0], "arrive", self.mousepos)
            self.A.assign(self.circle[1], "arrive", self.circle[0])

        #flee
        elif i == 2:
            self.circle = [
                Circle(
                    np.array([800+50,720/2+50]),
                    25, 
                    (0,0,255),
                ),
                Circle(
                    np.array([400,720/2]),
                    25, 
                    (255,0,0),
                )
            ]
            self.A.assign(self.circle[0], "arrive", self.mousepos)
            self.A.assign(self.circle[1], "flee", self.circle[0])

        #wander
        elif i == 3:
            for i in range(5):
                self.circle.append(Circle(
                    np.array([400,720/2]),
                    25, 
                    (54,200,100),
                ))
                self.A.assign(self.circle[-1], "wander")

        #align
        elif i == 4:
            self.circle = [
                Circle(
                    np.array([800+50,720/2+50]),
                    25, 
                    (0,0,255),
                ),
                Circle(
                    np.array([400,720/2]),
                    25, 
                    (255,0,0),
                )
            ]
            self.A.assign(self.circle[0], "arrive", self.mousepos)
            self.A.assign(self.circle[1], "align", self.circle[0])

        #vmatch
        elif i == 5:
            self.circle = [
                Circle(
                    np.array([800+50,720/2+50]),
                    25, 
                    (0,0,255),
                ),
                Circle(
                    np.array([400,720/2]),
                    25, 
                    (255,0,0),
                )
            ]
            self.A.assign(self.circle[0], "arrive", self.mousepos)
            self.A.assign(self.circle[1], "Vmatch", self.circle[0])

        #face
        elif i == 6:
            self.circle = [
                Circle(
                    np.array([800+50,720/2+50]),
                    25, 
                    (0,0,255),
                )
            ]
            for e in range(10):
                self.circle.append(Circle(
                    np.array([850 + 200*cos(e*2*pi/10), 410 + 200*sin(e*2*pi/10)]),
                    25,
                    (255,0,0)
                ))
                self.A.assign(self.circle[-1], "face", self.circle[0])

            
            self.A.assign(self.circle[0], "arrive", self.mousepos)

        #pursue
        elif i == 7:
            self.circle = [
                Circle(
                    np.array([800+50,720/2+50]),
                    25, 
                    (0,0,255),
                ),
                Circle(
                    np.array([400,720/2]),
                    25, 
                    (255,0,0),
                )
            ]
            self.A.assign(self.circle[0], "arrive", self.mousepos)
            self.A.assign(self.circle[1], "pursue", self.circle[0])

        #evade
        elif i == 8:
            self.circle = [
                Circle(
                    np.array([800+50,720/2+50]),
                    25, 
                    (0,0,255),
                ),
                Circle(
                    np.array([400,720/2]),
                    25, 
                    (255,0,0),
                )
            ]
            self.A.assign(self.circle[0], "arrive", self.mousepos)
            self.A.assign(self.circle[1], "evade", self.circle[0])

        #Dseek
        elif i == 9:
            self.circle = [
                Circle(
                    np.array([800+50,720/2+50]),
                    25, 
                    (0,0,255),
                ),
                Circle(
                    np.array([400,720/2]),
                    25, 
                    (255,0,0),
                )
            ]
            self.A.assign(self.circle[0], "arrive", self.mousepos)
            self.A.assign(self.circle[1], "Dseek", self.circle[0])

        #Darrive
        elif i == 10:
            self.circle = [
                Circle(
                    np.array([800+50,720/2+50]),
                    25, 
                    (0,0,255),
                ),
                Circle(
                    np.array([400,720/2]),
                    25, 
                    (255,0,0),
                )
            ]
            self.A.assign(self.circle[0], "arrive", self.mousepos)
            self.A.assign(self.circle[1], "Darrive", self.circle[0])

        #Dflee
        elif i == 11:
            self.circle = [
                Circle(
                    np.array([800+50,720/2+50]),
                    25, 
                    (0,0,255),
                ),
                Circle(
                    np.array([400,720/2]),
                    25, 
                    (255,0,0),
                )
            ]
            self.A.assign(self.circle[0], "arrive", self.mousepos)
            self.A.assign(self.circle[1], "Dflee", self.circle[0])

        #followpath
        elif i == 12:
            self.paths = [
                [
                    Circle(np.array([100,100]), 5),
                    Circle(np.array([750,80]), 5),
                    Circle(np.array([1050,100]), 5),
                    Circle(np.array([950,450]), 5),
                    Circle(np.array([550,550]), 5),
                    Circle(np.array([200,350]), 5),
                    Circle(np.array([50,150]), 5)
                ]    
            ]
            self.circle = [
                    Circle(np.array([800+50,720/2+50]),25, (90,115,255),),
                    Circle(np.array([30,30]),25, (90,115,255),),
                    Circle(np.array([1400,680]),25, (90,115,255),),
                    Circle(np.array([20+50,680]),25, (90,115,255),),
                    Circle(np.array([500,360]),25, (90,115,255),)
            ]
            for c in self.circle:
                self.A.assign(c, "pathFollow", self.paths[0])

        #tom and jerry 
        elif i == 13:
            self.circle = [
            Circle(
                np.array([800+50,720/2+50]),
                25, 
                (0,0,255),
            ),
            Circle(
                np.array([400,720/2]),
                25, 
                (255,0,0),
            )
        ]
            self.paths = [

            ]
            

            self.walls = [
                Rect(np.array([50, 50]), 1500, 50, (0,0,0),1),
                Rect(np.array([50, 50]), 50, 720, (0,0,0),1),
                Rect(np.array([50, 680]), 1500, 50, (0,0,0),1),
                Rect(np.array([1450, 50]), 50, 720, (0,0,0),1),
                Rect(np.array([700, 300]), 50, 200, (0,0,0),1)
            ]

            self.A.assign(self.circle[0], "wall_plus_Pursue", self.circle[1], self.walls, self.rays)
            self.A.assign(self.circle[1], "wall_plus_Evade", self.circle[0], self.walls, self.rays)

    def drag(self, data):
        dx = data[0] - self.mousepos.d[0]
        dy = data[1] - self.mousepos.d[1]

        for c in self.Geometries():
            c.d += [dx,dy]
        G.mousepos.d = data

    def tick(self):

        for c in self.circle:
            self.A.runAlg(c)


    def Geometries(self): return self.circle + sum(self.paths, []) + self.walls + self.rays

pygame.init()
screen_width = 1500
screen_height = 720
Sc = Screen(pygame, screen_width, screen_height)
I = Input(pygame)
G = Geometry()

running = True
while running:
    for (eType, data) in I.getEvents():
        if eType == gEvent.QUIT:
            running = False

        elif eType == gEvent.LEFTCLICKUP:
            pass

        elif eType == gEvent.DRAG:
            G.drag(data[0])

        elif eType == gEvent.LEFTCLICKDOWN:
            pass

        elif eType == gEvent.DOUBLECLICK:
            pass

        elif eType == gEvent.RIGHTCLICKDOWN:
            pass

        elif eType == gEvent.MOUSEWHEEL:
            pass

        elif eType == gEvent.MOUSEMOTION:
            G.mousepos.d = data

        elif eType == gEvent.CHAR:
            G.setScenario(data)

    Sc.clearScreen()
    Sc.draw(G.Geometries())
    Sc.display()
    G.tick()
    
pygame.quit()