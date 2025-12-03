from numpy.linalg import norm
from math import atan2, pi, cos, sin, inf
import numpy as np
from random import random

from Geometries import Circle, Rect, Polygon

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

    def seek(self, S, T, maxS = 1.0): 
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

    def Dseek(self, S, T, maxA = 0.15, maxS = 1):
        delta =  T.d- S.d
        H = norm(delta)
        a = maxA*delta/H
        S.v = S.v + a
        if abs(norm(S.v)) > maxS:
            S.v = maxS*S.v/norm(S.v)
        self.newOrientation(S, S.v)
        self.move(S)

    def Dflee(self, S, T, maxA = 0.005, maxS = 0.10):
        delta =  T.d- S.d
        H = norm(delta)
        a = maxA*delta/H
        S.v = S.v - a
        if abs(norm(S.v)) > maxS:
            S.v = maxS*S.v/norm(S.v)
        self.newOrientation(S, S.v)
        self.move(S)

    def Darrive(self, S, T, minD = 100, slowD = 500, maxS = 0.55, maxA = 0.15, ttt= 1000):
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

    def align(self, S, T, minD = pi/2, slowD = pi/32, maxR = 0.005, maxAlpha = 0.0005, ttt= 500):
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
    
    def wander(self, S, maxS = 0.05, maxR = pi/128):
        r = (random()-random()) * maxR
        self.rotate(S,r)
        S.v = np.array([-maxS*sin(S.o), maxS*cos(S.o)])
        self.move(S)

    def face(self, S, T, minD = pi/128, slowD = pi/32, maxR = 0.01, maxAlpha = 0.005, ttt= 500):

        delta = S.d - T.d
        T2 = Circle([0,0])
        T2.o = atan2(delta[0], -delta[1])
        self.align(S, T2, minD, slowD, maxR, maxAlpha, ttt)


    def pursue(self, S, T, maxPrediction = 1000 , minD = 25, slowD = 100, maxS = 0.20, maxA = 0.0005, ttt= 500):
        delta =  T.d- S.d
        H = norm(delta)
        s = norm(S.v)

        if s <= H/maxPrediction: prediction = maxPrediction
        else: prediction = H/s

        T2 = Circle([0,0])
        T2.d = T.d + T.v*prediction
        self.Darrive(S, T2, minD, slowD, maxS, maxA, ttt)

    def evade(self, S, T, maxPrediction = 1000 , minD = 25, slowD = 100, maxS = 0.25, maxA = 0.0005, ttt= 500):
        delta =  T.d- S.d
        H = norm(delta)
        s = norm(S.v)

        if s <= H/maxPrediction: prediction = maxPrediction
        else: prediction = H/s

        T2 = Circle()
        T2.d = T.d + T.v*prediction
        self.Dflee(S, T2, maxA, maxS)

    def lwyg(self, S, minD = pi/128, slowD = pi/32, maxR = 0.5, maxAlpha = 0.05, ttt= 500):
        
        T2 = Circle()
        T2.o = atan2(-S.v[0], S.v[1])
        self.align(S, T2, minD, slowD, maxR, maxAlpha, ttt)

    improvO = 0 
    def Dwander(self, S, debug, minD = pi/128, slowD = pi/32, maxR = 0.5, maxAlpha = 0.005, ttt= 500, Wrate = pi/8096, Woffset = 750, maxA = 0.00005, maxS = 0.05):
        self.improvO += (random()-random()) * Wrate
        targetO = S.o + self.improvO
        target = S.d + Woffset*np.array([-sin(targetO), cos(targetO)])

        T2 = Circle(target, 10)
        debug.append(T2)
        T2.d = target
        self.face(S, T2, minD, slowD, maxR, maxAlpha, ttt)

        S.a = maxA *np.array([-sin(S.o), cos(S.o)])
        S.v = S.v +  S.a
        if abs(norm(S.v)) > maxS:
            S.v = maxS*S.v/norm(S.v)
        self.move(S)


    def pathFollow(self, S, minD = 25):
        P = S.path
        if S.target == None:
            newTarget = None
            targetH = inf
            for i in range(len(P)):
                H = norm(P[i].d - S.d)
                if H < targetH:
                    targetH = H
                    newTarget = i
            S.target = newTarget
        elif norm(P[S.target].d - S.d) < minD:
            S.target = (S.target + 1)
            if S.target >= len(P):
                return True
        try:T = P[S.target]
        except:
            T = P[-1]
        self.Dseek(S, T)
        return False

    def avoidWall(self, S, walls, debug, lookahead = 100, avoidDistance = 100):
        ray = []
        o = atan2(S.v[1], S.v[0])
        for i in range(11,1,-1):
            ray.append(S.d + np.array([lookahead*cos(o)/i,lookahead*sin(o)/i]))
        for w in walls:
            for p in ray:
                if w.inside(p):
                    T = Circle(w.normal(p, avoidDistance))
                    self.Dseek(S, T)
                    return True
        return False
    
    def wall_plus_Pursue(self, S, T, walls, debug):
        if not self.avoidWall(S, walls, debug): self.pursue(S,T)
        

    def wall_plus_Evade(self, S, T, walls, debug):
        if not self.avoidWall(S, walls, debug): self.evade(S,T)