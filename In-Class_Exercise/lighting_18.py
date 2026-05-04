# Basic OBJ file viewer. needs objloader from:
#  http://www.pygame.org/wiki/OBJFileLoader
# LMB + move: rotate
# RMB + move: pan
# Scroll wheel: zoom in/out
import sys, pygame
from pygame.locals import *
from pygame.constants import *
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

from OBJFileLoader_18 import *

#import numpy as np
from collections import defaultdict

width, height = 800, 600                                                    # width and height of the screen created
bDrawWireframe = False    # a flag indicating whether or not drawing edges and veritices    

########################################### Drawing Functions ####################################################
def drawAxes():                                                             # draw x-axis and y-axis
    glDisable(GL_LIGHTING)
    glLineWidth(3.0)                                                        # specify line size (1.0 default)
    glBegin(GL_LINES)                                                       # replace GL_LINES with GL_LINE_STRIP or GL_LINE_LOOP
    glColor3f(1.0, 0.0, 0.0)                                                # x-axis: red
    glVertex3f(0.0, 0.0, 0.0)                                               # v0
    glVertex3f(100.0, 0.0, 0.0)                                             # v1
    glColor3f(0.0, 1.0, 0.0)                                                # y-axis: green
    glVertex3f(0.0, 0.0, 0.0)                                               # v0
    glVertex3f(0.0, 100.0, 0.0)                                             # v1
    glColor3f(0.0, 0.0, 1.0)                                                # z-axis: green
    glVertex3f(0.0, 0.0, 0.0)                                               # v0
    glVertex3f(0.0, 0.0, 100.0)                                             # v1
    glEnd()

def draw_vertices(obj):
    glDisable(GL_LIGHTING)                                                  # points are not affected by lighting
    glColor3f(1.0, 1.0, 1.0)                                                # set point color
    glPointSize(4.0)                                                        # set point size

    glBegin(GL_POINTS)
    for v in obj.vertices:
        glVertex3fv(v)
    glEnd()

    glEnable(GL_LIGHTING)


def draw_edges(obj):
    glDisable(GL_LIGHTING)
    glColor3f(0.8, 0.8, 0.8)                                                # set edge color (black)
    glLineWidth(1.0)                                                        # set line thickness
    glBegin(GL_LINES)

    drawn_edges = set()
    for face in obj.faces:
        vertices = face[0]                                                  # just vertex indices

        num_vertices = len(vertices)
        for i in range(num_vertices):
            v1 = vertices[i] - 1
            v2 = vertices[(i + 1) % num_vertices] - 1                       # wrap around

            # ensure each edge is drawn only once (unordered pair)
            edge = tuple(sorted((v1, v2)))
            if edge in drawn_edges:
                continue
            drawn_edges.add(edge)

            glVertex3fv(obj.vertices[v1])
            glVertex3fv(obj.vertices[v2])
    glEnd()

    glEnable(GL_LIGHTING)

# draw the mesh and its edges and vertices
def draw_mesh(obj, model_name): 
    # Enable rendering settings
    glEnable(GL_LIGHTING)
    if model_name == "Car":
        glEnable(GL_COLOR_MATERIAL) # disable or not enable to use the setting in MTL file
    glEnable(GL_DEPTH_TEST)
    glShadeModel(GL_SMOOTH)

    glPushMatrix()
    # Light 0 - point light from above, left, front
    glEnable(GL_LIGHT0)
    glLightfv(GL_LIGHT0, GL_POSITION, (0, 200, 100, 0.0))  # directional light (sunlight)
    glLightfv(GL_LIGHT0, GL_AMBIENT, (0.3, 0.3, 0.3, 1.0))
    glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.5, 0.5, 0.5, 1.0))
    glLightfv(GL_LIGHT0, GL_SPECULAR, (0.5, 0.5, 0.5, 1.0))

    # Light 1 - point light from the left
    glEnable(GL_LIGHT1)
    glLightfv(GL_LIGHT1, GL_POSITION, (-100, 100, 100, 1.0))  # point light
    if model_name == "Car":
        glLightfv(GL_LIGHT1, GL_DIFFUSE, (0.5, 0.5, 0.5, 1.0))
    elif model_name == "panther":
        glLightfv(GL_LIGHT1, GL_DIFFUSE, (0.2, 0.2, 0.2, 1.0))
    glLightfv(GL_LIGHT1, GL_SPECULAR, (0.5, 0.5, 0.5, 1.0))

    # Light 2 - point light from the right
    glEnable(GL_LIGHT2)
    glLightfv(GL_LIGHT2, GL_POSITION, (100.0, 100.0, 100.0, 1.0))   # point light
    if model_name == "Car":
        glLightfv(GL_LIGHT2, GL_DIFFUSE, (0.5, 0.5, 0.5, 1.0))
    elif model_name == "panther":
        glLightfv(GL_LIGHT2, GL_DIFFUSE, (0.2, 0.2, 0.2, 1.0))
    glLightfv(GL_LIGHT2, GL_SPECULAR, (0.5, 0.5, 0.5, 1.0))

    # Light 3 - splotlight (point + direction) from top-front 
    #glEnable(GL_LIGHT3)
    glLightfv(GL_LIGHT3, GL_POSITION, (0, 100, -100, 1.0))  # position of the light
    glLightfv(GL_LIGHT3, GL_SPOT_DIRECTION, (0.0, -1.0, 1.0)) # direction of the spotlight is pointing
    glLightf(GL_LIGHT3, GL_SPOT_CUTOFF, 30.0) # Spotlight cone angle (0 to 90 degrees)
    glLightf(GL_LIGHT3, GL_SPOT_EXPONENT, 2.0) # Spotlight intensity distribution
    glLightfv(GL_LIGHT3, GL_DIFFUSE, (0.5, 0.5, 0.5, 1.0))
    glLightfv(GL_LIGHT3, GL_SPECULAR, (0.5, 0.5, 0.5, 1.0))

    glPopMatrix()

    # Material properties for specular highlight
    glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, (0.5, 0.5, 0.5, 1.0))   # less shiny white
    glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 50.0)                  # [0–128], higher = tighter highlight

    glPushMatrix()
    # draw mesh
    glCallList(obj.gl_list)

    # Draw edges and vertices over shaded mesh
    if bDrawWireframe:
        draw_edges(obj)
        draw_vertices(obj)

    glPopMatrix()

########################################### OpenGL Program ####################################################
def main():
    pygame.init()                                                           # initialize a pygame program
    glutInit()                                                              # initialize glut library 

    screen = (width, height)                                                # specify the screen size of the new program window
    display_surface = pygame.display.set_mode(screen, DOUBLEBUF | OPENGL)   # create a display of size 'screen', use double-buffers and OpenGL
    pygame.display.set_caption('CPSC 360: Lighting')                        # set title of the program window

    glEnable(GL_DEPTH_TEST)
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)                                             # set mode to projection transformation
    glLoadIdentity()                                                        # reset transf matrix to an identity
    gluPerspective(45.0, width/height, 0.1, 1000.0)                         # specify an perspective-projection view volume

    glMatrixMode(GL_MODELVIEW)                                              # set mode to modelview (geometric + view transf)
    gluLookAt(0, 0, 50, 0, 0, 0, 0, 1, 0)                                   # set camera's eye, look-at, and view-up in the world
    initmodelMatrix = glGetFloat(GL_MODELVIEW_MATRIX)

    # load OBJ mesh
    model_name = "panther" # switch model here: "Car", "panther"
    model_path = os.path.join("./resources/models/", model_name + ".obj")
    if not os.path.exists(model_path):
        raise ValueError(f"OBJ file not found: {model_path}")
    obj = OBJ(filename=model_path, swapyz=False) 

    # mouse controled dynamic view
    rx, ry = (0,0)
    tx, ty = (0,0)
    zpos = 5
    rotate = False
    move = False
    move_left, move_right = False, False
    global bDrawWireframe
    while True:
        move_left = False
        move_right = False
        for e in pygame.event.get():
            if e.type == QUIT:
                sys.exit()
            elif e.type == KEYDOWN and e.key == K_ESCAPE:
                sys.exit()
            elif e.type == KEYDOWN and e.key == K_w:
                bDrawWireframe = not bDrawWireframe
            elif e.type == KEYDOWN and e.key == K_c:
                bDrawBV = not bDrawBV           
            elif e.type == MOUSEBUTTONDOWN:
                if e.button == 4: zpos = max(1, zpos-1)
                elif e.button == 5: zpos += 1
                elif e.button == 1: rotate = True
                elif e.button == 3: move = True
            elif e.type == MOUSEBUTTONUP:
                if e.button == 1: rotate = False
                elif e.button == 3: move = False
            elif e.type == MOUSEMOTION:
                i, j = e.rel
                if rotate:
                    rx += i
                    ry += j
                if move:
                    tx += i
                    ty -= j
        
        # Clear screen ONCE per frame
        glClearColor(0, 0, 0, 1)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # draw mesh
        glLoadIdentity()
        glTranslate(tx/20., ty/20., - zpos)
        glRotate(ry, 1, 0, 0)
        glRotate(rx, 0, 1, 0)
        glPushMatrix()
        # draw obj1
        draw_mesh(obj=obj, model_name=model_name)
        glPopMatrix()
        drawAxes()

        pygame.display.flip()
        pygame.time.wait(10)

main()