from math import sqrt
from numpy.linalg import norm
import numpy as np
import matplotlib.path as mpath


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
    def __init__(self, d=[0,0], radius=0, color=(0,0,0), npc = False):
        self.radius = radius
        self.color =  color
        self.d = d
        self.v = np.array([0,0])
        self.a = np.array([0,0])
        self.o = 0
        self.r = 0
        self.alpha = 0

        self.npc = npc
        self.status = [None, None]
        self.items = {"food":0, "iron":0, "pickaxe":0, "fiber":0, "coat":0}
        self.memory = {}
        self.target = None
        self.path = []
        self.food = 5000
        self.pol = None
        self.path_goal = None
        self.path2_goal = None

    def clicked(self, mp):
        distance = sqrt((self.d[0]-mp[0])**2 + (self.d[1]-mp[1])**2)
        return distance <= self.radius
    
    def clearPath(self):
        self.path.clear()
        self.target = None
    
class Polygon(object):
    def __init__(self, points, type = None, color = (80,80,80)):
        self.points = points
        self.color = color

        sum_x = sum([p[0] for p in points])
        sum_y = sum([p[1] for p in points])

        self.center = Circle(np.array([sum_x/3, sum_y/3]), 5)
        self.i = None
        self.mpath = mpath.Path(points)

        self.type = type
        self.productivity = 0
        self.worked = None
        self.items = {"food":0, "iron":0, "pickaxe":0, "fiber":0, "coat":0}


    def fieldColor(self):
        self.color = (80,80 + int(self.productivity*3.5),80)

    def ironColor(self):
        c = int(self.productivity*3) + 55
        self.color = (c+25, c, c) 


def circle_rect_collision(circle: Circle, rect: Rect):

    R_min_x = rect.d[0]
    R_max_x = rect.d[0] + rect.width
    
    R_min_y = rect.d[1]
    R_max_y = rect.d[1] + rect.height
    
    Cx, Cy = circle.d[0], circle.d[1]

    Px = np.clip(Cx, R_min_x, R_max_x)
    Py = np.clip(Cy, R_min_y, R_max_y)
    
    closest_point = np.array([Px, Py])

    distance_vector = circle.d - closest_point
    D = norm(distance_vector)
    
    return D <= circle.radius