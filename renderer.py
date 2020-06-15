from OpenGL import *
from OpenGL.GL import *
from OpenGL.GL import shaders
from OpenGL.GLUT import *
from OpenGL.GLU import *
import time
import numpy as np

class renderer:
    def __init__(self):
        self.nvertices = 0
        self.bus = 0
        glutInit()
        glutInitDisplayMode(GLUT_RGBA | GLUT_SINGLE)
        self.w = 1024 #1024
        self.h = 512 #512
        glutInitWindowSize(self.w, self.h)
        glutInitWindowPosition(0, 0)
        glutCreateWindow("PSX")
        glClearColor(0, 0, 0, 1)
        glClear(GL_COLOR_BUFFER_BIT)

        vertsrc = open("shader.vert", 'r').read()
        fragsrc = open("shader.frag", 'r').read()
        self.vertexshader = shaders.compileShader(vertsrc, GL_VERTEX_SHADER)
        self.fragmentshader = shaders.compileShader(fragsrc, GL_FRAGMENT_SHADER)
        self.program = shaders.compileProgram(self.vertexshader, self.fragmentshader)
        self.positions = buffer(2)
        self.colors = buffer(3)
        self.vertex_buffer_len = 64 * 1024


    def link_bus(self, bus):
        self.bus = bus
        glutIdleFunc(self.bus.clock)
        glutDisplayFunc(self.display)
        glutMainLoop()

    def check_for_error(self):
        fatal = False
        buffer = [0] * 4096
        severity = 0
        source = 0
        message_size = 0
        mtype = 0
        id = 0
        count = glGetDebugMessageLog(1, len(buffer), source, mtype, id, severity, message_size, buffer)
        message = bytearray(buffer).decode("utf-8")
        print("OPENGL", severity, source, mtype, id, message)


    def draw(self):
        #shaders.glUseProgram(self.program)
        glClear(GL_COLOR_BUFFER_BIT)
        print(self.positions.memory[0:30])
        print(self.colors.memory[0:30])
        print(self.nvertices)

        for j in range(self.nvertices // 3):
            glBegin(GL_POLYGON)
            for i in range(3):
                col1 = self.colors.memory[j*9 + i*3 + 0] / 255
                col2 = self.colors.memory[j*9 + i*3 + 1] / 255
                col3 = self.colors.memory[j*9 + i*3 + 2] / 255
                pos1 = (self.positions.memory[j*6 + i*2 + 0] / 512) - 1.0
                pos2 = 1.0 - (self.positions.memory[j*6 + i*2 + 1] / 256)
                glColor3f(col1, col2, col3)
                glVertex2f(pos1, pos2)
            glEnd()
            glFlush()
        self.nvertices = 0
        #shaders.glUseProgram(0)
        #self.check_for_error()

    def display(self):
        print("DISPLAY")
        self.draw()


    def find_program_attrib(self, program, attrib):
        index = glGetAttribLocation(program, attrib)
        if index < 0:
            print("ATTRIBUTE", attrib, "NOT FOUND")
        return index

    def drop(self):
        glDeleteVertexArrays(1, self.vao)
        glDeleteShader(self.vertexshader)
        glDeleteShader(self.fragmentshader)
        glDeleteProgram(self.program)

    def position_from_gp0(self, value):
        x = value & 0xFFFF
        y = (value >> 16) & 0xFFFF
        return (x, y)

    def color_from_gp0(self, value):
        r = value & 0xFF
        g = (value >> 8) & 0xFF
        b = (value >> 16) & 0xFF
        return (r, g, b)

    def push_triangle(self, positions, colors):
        if (self.nvertices + 3) > self.vertex_buffer_len:
            print("VERTEX ATTRIBUTE BUFFER FULL")
            self.draw()

        for i in range(3):
            self.positions.set(self.nvertices, positions[i])
            self.colors.set(self.nvertices, colors[i])
            self.nvertices += 1

    def push_quad(self, positions, colors):
        if (self.nvertices + 6) > self.vertex_buffer_len:
            self.draw()
        for i in range(3):
            self.positions.set(self.nvertices, positions[i])
            self.colors.set(self.nvertices, colors[i])
            self.nvertices += 1
        for i in range(1, 4):
            self.positions.set(self.nvertices, positions[i])
            self.colors.set(self.nvertices, colors[i])
            self.nvertices += 1


class buffer:
    def __init__(self, datanum):
        self.datanum = datanum
        self.vertex_buffer_len = 64 * 1024
        self.memory = [0] * self.vertex_buffer_len

    def set(self, index, value):
        for i in range(self.datanum):
            self.memory[index * self.datanum + i] = value[i]
