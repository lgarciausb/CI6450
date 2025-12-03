from enum import Enum
import time
import pygame
from math import cos, sin

from Geometries import Circle, Rect, Polygon

class Screen(object):
    def __init__(self, pg:pygame, screen_width, screen_height):
        self.pg = pg
        self.sc = self.pg.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
        self.pg.display.set_caption("CI6450")
        self.font = pg.font.Font(size=32)
        self.screen_width = screen_width
        self.screen_height = screen_height

    def draw(self, elements):
        for el in elements:
            if type(el) == Rect: 
                self.drawRect(el)
            elif type(el) == Circle: self.drawCircle(el)
            elif type(el) == Polygon: self.drawPolygon(el)
            elif type(el) == list and len(el) == 2: self.drawLine(el)

    def drawRect(self, rect):
        self.pg.draw.rect(self.sc, rect.square_color, (rect.d[0], rect.d[1], rect.width, rect.height), rect.outline)

    def drawCircle(self, circle):
        self.pg.draw.circle(self.sc, circle.color, circle.d, circle.radius)
        if not circle.npc: return
        H = circle.radius+20
        self.pg.draw.line(self.sc, circle.color, circle.d, circle.d+[-H*sin(circle.o), H*cos(circle.o)], 5)

    def drawPolygon(self, pol):
        pygame.draw.polygon(self.sc, pol.color, pol.points)
        pygame.draw.polygon(self.sc, (0,0,0), pol.points, 2)

    def drawLine(self, L):
        pygame.draw.line(self.sc, (0,0,0), L[0], L[1])


    def clearScreen(self):
        self.sc.fill((200, 200, 200))

    def display(self): self.pg.display.flip()

    def write(self, text, doko):
        text_surface = self.font.render(text, True, (0, 0, 0))
        text_rect = text_surface.get_rect()
        text_rect.center = doko
        self.sc.blit(text_surface, text_rect)

    def info(self, object):

        if object == None: return

        self.pg.draw.rect(self.sc, (150,150,150), (self.screen_width-200, self.screen_height-200, 175, 175))

        if type(object) == Circle:
            self.write(f"hunger: {object.food}", (self.screen_width-112.5, self.screen_height-160))
            self.write(f"food: {object.items['food']}", (self.screen_width-112.5, self.screen_height-140))
            self.write(f"iron: {object.items['iron']}", (self.screen_width-112.5, self.screen_height-120))
            self.write(f"pickaxe: {object.items['pickaxe']}", (self.screen_width-112.5, self.screen_height-100))
            self.write(f"fiber: {object.items['fiber']}", (self.screen_width-112.5, self.screen_height-80))
            self.write(f"coat: {object.items['coat']}", (self.screen_width-112.5, self.screen_height-60))

        elif type(object) == Polygon:
            if object.type == "base":
                self.write(f"food: {object.items['food']}", (self.screen_width-112.5, self.screen_height-160))
                self.write(f"iron: {object.items['iron']}", (self.screen_width-112.5, self.screen_height-140))
                self.write(f"pickaxe: {object.items['pickaxe']}", (self.screen_width-112.5, self.screen_height-120))
                self.write(f"fiber: {object.items['fiber']}", (self.screen_width-112.5, self.screen_height-100))
                self.write(f"coat: {object.items['coat']}", (self.screen_width-112.5, self.screen_height-80))
            elif object.type in ("field", "iron"):
                self.write(f"productivity: {object.productivity}", (self.screen_width-112.5, self.screen_height-160))

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
        RDRAG = 11
        RIGHTDRAGUP = 12

class Input(object):

    def __init__(self, pg):
        self.pg = pg
        self.drag = None
        self.rdrag = None
        self.lastClick = 0
        self.doubleClickTime = 0.450 #seconds

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
                elif self.rdrag != None: yield gEvent.RDRAG, [pygame.mouse.get_pos(), self.rdrag]
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
                self.rdrag = pygame.mouse.get_pos()
                yield gEvent.RIGHTCLICKDOWN, pygame.mouse.get_pos()

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 3:
                if self.rdrag != None:
                    rdrag = self.rdrag
                    self.rdrag = None
                    yield gEvent.RIGHTDRAGUP, [rdrag, pygame.mouse.get_pos()]
                else: yield gEvent.RIGHTCLICKUP, pygame.mouse.get_pos()
            
            elif event.type == pygame.MOUSEWHEEL:
                yield gEvent.MOUSEWHEEL, [pygame.mouse.get_pos(), event.y]
                
            elif event.type == pygame.KEYDOWN:
                if event.unicode.isdigit(): yield gEvent.NUMBER, int(event.unicode)
                else: yield gEvent.CHAR, event.unicode