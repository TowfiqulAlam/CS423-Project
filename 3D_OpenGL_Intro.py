from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import sys
import time
import random
from collections import defaultdict

# Game states
MENU = 0
JERSEY_SELECTION = 1
PLAYER_NAME_INPUT = 2
PLAYING = 3
GAME_OVER = 4

current_state = MENU

# Window settings
WINDOW_WIDTH = 1920
WINDOW_HEIGHT = 1080

# Key states for continuous movement
key_states = defaultdict(bool)

# Power meter settings
power_meter = {
    'value': 0.0,
    'max_power': 2.0,
    'charging': False,
    'charge_rate': 3.0,
    'show_meter': False,
    'last_shot_power': 0.0,
    'last_shot_time': 0,
    'show_last_power': False
}

# Game state
class Game:
    def __init__(self):
        self.score = 0
        self.game_time = 0
        self.total_game_time = 240  # 4 minutes in seconds
        self.is_playing = True
        self.game_over = False
        self.ball_pos = [0, 0.3, 0]
        self.ball_vel = [0, 0, 0]
        self.player_has_ball = False
        self.last_goal_time = -5
        self.goal_message = ""
        self.goal_message_time = 0
        self.winner = None
        self.selected_jersey = "argentina"  # Default jersey
        self.player_name = "YOU"  # Default player name

game = Game()

# Field dimensions (square)
FIELD_SIZE = 20.0
GOAL_WIDTH = 3.0
GOAL_HEIGHT = 2.0
GOAL_DEPTH = 1.5
GOAL_LINE = FIELD_SIZE / 2  # Goal line position

# Stadium dimensions
STADIUM_SIZE = 35.0
STAND_HEIGHT = 5.0
STAND_DEPTH = 5.0
NUM_STAND_SEGMENTS = 20

# Player (you)
player = {
    'pos': [0, 0, 0],
    'rot': 0,
    'speed': 0.15,
    'team': 'blue',
    'jersey_number': 10
}

# Goalkeeper positions and collision boxes
goalies = {
    'north': {
        'pos': [0, 0, -GOAL_LINE],
        'dir': 1, 
        'anim': 0, 
        'team': 'blue',
        'collision_box': {'x': 0, 'z': -GOAL_LINE, 'width': GOAL_WIDTH, 'height': GOAL_HEIGHT, 'depth': 0.5}
    },
    'east': {
        'pos': [GOAL_LINE, 0, 0],
        'dir': 1, 
        'anim': 30, 
        'team': 'red',
        'collision_box': {'x': GOAL_LINE, 'z': 0, 'width': 0.5, 'height': GOAL_HEIGHT, 'depth': GOAL_WIDTH}
    },
    'south': {
        'pos': [0, 0, GOAL_LINE],
        'dir': 1, 
        'anim': 60, 
        'team': 'yellow',
        'collision_box': {'x': 0, 'z': GOAL_LINE, 'width': GOAL_WIDTH, 'height': GOAL_HEIGHT, 'depth': 0.5}
    },
    'west': {
        'pos': [-GOAL_LINE, 0, 0],
        'dir': 1, 
        'anim': 90, 
        'team': 'green',
        'collision_box': {'x': -GOAL_LINE, 'z': 0, 'width': 0.5, 'height': GOAL_HEIGHT, 'depth': GOAL_WIDTH}
    }
}

# Camera settings
camera_mode = "PLAYER"  # "PLAYER", "OVERHEAD", "GOAL"
camera_height = 3.0
camera_distance = 5.0

# Menu selection
menu_selection = 0  # 0: Start, 1: Quit
jersey_selection = 0  # 0: Argentina (Blue), 1: Brazil (Yellow)

# Player name input
player_name_input = ""
name_cursor_pos = 0
MAX_NAME_LENGTH = 15

#Ball ownership
ball_owner = None  # None or ("human",None) or ("ai",idx)

#3 AI players
ai_players = [
    {"pos": [ 4,0,4],"rot":180, "speed": 0.01, "name":"AI-1", "team":"red"},
    {"pos": [-4,0,4],"rot":180, "speed": 0.01, "name":"AI-2", "team":"green"},
    {"pos": [ 0,0,-6],"rot":0, "speed": 0.01, "name":"AI-3", "team":"yellow"},
]

#Ball pickup
PICKUP_COOLDOWN = 0.8 #sec
KNOCKBACK_DIST  = 2
last_pickup_block = {"human": 0.0, 0: 0.0, 1: 0.0, 2: 0.0}

def init():
    """Initialize OpenGL"""
    glClearColor(0.1, 0.2, 0.3, 1.0)  # Dark blue background
    glEnable(GL_DEPTH_TEST)
    glShadeModel(GL_SMOOTH)
    
    # Lighting
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    
    # Light position (above the field)
    glLightfv(GL_LIGHT0, GL_POSITION, [0.0, 20.0, 0.0, 1.0])
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 1.0, 1.0, 1.0])
    glLightfv(GL_LIGHT0, GL_SPECULAR, [0.5, 0.5, 0.5, 1.0])
    
    # Ambient light
    glLightModelfv(GL_LIGHT_MODEL_AMBIENT, [0.3, 0.3, 0.3, 1.0])
    
    # Material
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

def set_camera():
    """Set camera position based on mode"""
    if camera_mode == "OVERHEAD":
        # Overhead view
        glLoadIdentity()
        gluLookAt(0, 15, 0,
                  0, 0, 0,
                  0, 0, 1)
    elif camera_mode == "PLAYER":
        # Third person behind player
        angle_rad = math.radians(player['rot'])
        offset_x = math.sin(angle_rad) * camera_distance
        offset_z = math.cos(angle_rad) * camera_distance
        
        cam_x = player['pos'][0] - offset_x
        cam_y = camera_height
        cam_z = player['pos'][2] - offset_z
        
        # glLoadIdentity()
        # gluLookAt(cam_x, cam_y, cam_z,
        #           player['pos'][0], 1.0, player['pos'][2],
        #           0, 1, 0)
        glLoadIdentity()
        gluLookAt(0, 5, FIELD_SIZE/2 + 5,
                  0, 2, 0,
                  0, 1, 0)
    # elif camera_mode == "GOAL":
    #     # Goal view
    #     glLoadIdentity()
    #     gluLookAt(0, 5, FIELD_SIZE/2 + 5,
    #               0, 2, 0,
    #               0, 1, 0)


def draw_square_field():
    """Draw the square football field"""
    half_size = FIELD_SIZE / 2
    
    # Grass base
    glColor3f(0.2, 0.6, 0.2)
    glBegin(GL_QUADS)
    glNormal3f(0, 1, 0)
    glVertex3f(-half_size, 0, -half_size)
    glVertex3f(half_size, 0, -half_size)
    glVertex3f(half_size, 0, half_size)
    glVertex3f(-half_size, 0, half_size)
    glEnd()
    
    # Grass stripes
    stripe_width = 1.0
    for i in range(int(FIELD_SIZE / stripe_width)):
        x_start = -half_size + i * stripe_width
        
        if i % 2 == 0:
            glColor3f(0.15, 0.55, 0.15)
        else:
            glColor3f(0.25, 0.65, 0.25)
        
        glBegin(GL_QUADS)
        glVertex3f(x_start, 0.01, -half_size)
        glVertex3f(x_start + stripe_width, 0.01, -half_size)
        glVertex3f(x_start + stripe_width, 0.01, half_size)
        glVertex3f(x_start, 0.01, half_size)
        glEnd()
    
    # Field boundary (white lines)
    glDisable(GL_LIGHTING)
    glColor3f(1.0, 1.0, 1.0)
    glLineWidth(3.0)
    
    # Outer boundary
    glBegin(GL_LINE_LOOP)
    glVertex3f(-half_size, 0.02, -half_size)
    glVertex3f(half_size, 0.02, -half_size)
    glVertex3f(half_size, 0.02, half_size)
    glVertex3f(-half_size, 0.02, half_size)
    glEnd()
    
    # Center lines (both directions)
    glBegin(GL_LINES)
    glVertex3f(-half_size, 0.02, 0)
    glVertex3f(half_size, 0.02, 0)
    glVertex3f(0, 0.02, -half_size)
    glVertex3f(0, 0.02, half_size)
    glEnd()
    
    # Center circle
    glBegin(GL_LINE_LOOP)
    for i in range(32):
        angle = 2.0 * math.pi * i / 32
        x = 2.0 * math.cos(angle)
        z = 2.0 * math.sin(angle)
        glVertex3f(x, 0.02, z)
    glEnd()
    
    # Center dot
    glPointSize(8.0)
    glBegin(GL_POINTS)
    glVertex3f(0, 0.03, 0)
    glEnd()
    
    # Goal lines (thicker red lines)
    glColor3f(1.0, 0.0, 0.0)
    glLineWidth(4.0)
    
    # North goal line
    glBegin(GL_LINES)
    glVertex3f(-GOAL_WIDTH/2, 0.03, -GOAL_LINE)
    glVertex3f(GOAL_WIDTH/2, 0.03, -GOAL_LINE)
    glEnd()
    
    # East goal line
    glBegin(GL_LINES)
    glVertex3f(GOAL_LINE, 0.03, -GOAL_WIDTH/2)
    glVertex3f(GOAL_LINE, 0.03, GOAL_WIDTH/2)
    glEnd()
    
    # South goal line
    glBegin(GL_LINES)
    glVertex3f(-GOAL_WIDTH/2, 0.03, GOAL_LINE)
    glVertex3f(GOAL_WIDTH/2, 0.03, GOAL_LINE)
    glEnd()
    
    # West goal line
    glBegin(GL_LINES)
    glVertex3f(-GOAL_LINE, 0.03, -GOAL_WIDTH/2)
    glVertex3f(-GOAL_LINE, 0.03, GOAL_WIDTH/2)
    glEnd()
    
    glEnable(GL_LIGHTING)

def draw_simple_goal(side, color):
    """Draw a simple goal with colored posts"""
    half_size = FIELD_SIZE / 2
    
    if side == "north":
        x, z = 0, -half_size
        rotation = 0
    elif side == "east":
        x, z = half_size, 0
        rotation = 270
    elif side == "south":
        x, z = 0, half_size
        rotation = 180
    else:  # west
        x, z = -half_size, 0
        rotation = 90
    
    glPushMatrix()
    glTranslatef(x, 0, z)
    glRotatef(rotation, 0, 1, 0)
    
    # Goal posts (colored based on team)
    glColor3f(color[0], color[1], color[2])
    
    # Left post
    draw_cuboid(-GOAL_WIDTH/2, GOAL_HEIGHT/2, 0, 0.1, GOAL_HEIGHT, 0.1)
    # Right post
    draw_cuboid(GOAL_WIDTH/2 - 0.1, GOAL_HEIGHT/2, 0, 0.1, GOAL_HEIGHT, 0.1)
    # Crossbar - CENTERED
    draw_cuboid(-0.055, GOAL_HEIGHT, 0, GOAL_WIDTH, 0.1, 0.1)
    
    glPopMatrix()

def draw_goal_box(side):
    """Draw goal box (penalty area)"""
    half_size = FIELD_SIZE / 2
    box_size = 4.0
    
    glDisable(GL_LIGHTING)
    glColor3f(1.0, 1.0, 1.0)
    glLineWidth(2.0)
    
    if side == "north":
        glBegin(GL_LINE_LOOP)
        glVertex3f(-box_size/2, 0.02, -half_size)
        glVertex3f(box_size/2, 0.02, -half_size)
        glVertex3f(box_size/2, 0.02, -half_size + 2.0)
        glVertex3f(-box_size/2, 0.02, -half_size + 2.0)
        glEnd()
    elif side == "east":
        glBegin(GL_LINE_LOOP)
        glVertex3f(half_size - 2.0, 0.02, -box_size/2)
        glVertex3f(half_size, 0.02, -box_size/2)
        glVertex3f(half_size, 0.02, box_size/2)
        glVertex3f(half_size - 2.0, 0.02, box_size/2)
        glEnd()
    elif side == "south":
        glBegin(GL_LINE_LOOP)
        glVertex3f(-box_size/2, 0.02, half_size - 2.0)
        glVertex3f(box_size/2, 0.02, half_size - 2.0)
        glVertex3f(box_size/2, 0.02, half_size)
        glVertex3f(-box_size/2, 0.02, half_size)
        glEnd()
    else:  # west
        glBegin(GL_LINE_LOOP)
        glVertex3f(-half_size, 0.02, -box_size/2)
        glVertex3f(-half_size + 2.0, 0.02, -box_size/2)
        glVertex3f(-half_size + 2.0, 0.02, box_size/2)
        glVertex3f(-half_size, 0.02, box_size/2)
        glEnd()
    
    glEnable(GL_LIGHTING)

def draw_cuboid(x, y, z, width, height, depth):
    """Draw a 3D cuboid"""
    glPushMatrix()
    glTranslatef(x, y, z)
    
    half_w = width / 2
    half_h = height / 2
    half_d = depth / 2
    
    glBegin(GL_QUADS)
    
    # Front
    glNormal3f(0, 0, 1)
    glVertex3f(-half_w, -half_h, half_d)
    glVertex3f(half_w, -half_h, half_d)
    glVertex3f(half_w, half_h, half_d)
    glVertex3f(-half_w, half_h, half_d)
    
    # Back
    glNormal3f(0, 0, -1)
    glVertex3f(-half_w, -half_h, -half_d)
    glVertex3f(-half_w, half_h, -half_d)
    glVertex3f(half_w, half_h, -half_d)
    glVertex3f(half_w, -half_h, -half_d)
    
    # Top
    glNormal3f(0, 1, 0)
    glVertex3f(-half_w, half_h, -half_d)
    glVertex3f(-half_w, half_h, half_d)
    glVertex3f(half_w, half_h, half_d)
    glVertex3f(half_w, half_h, -half_d)
    
    # Bottom
    glNormal3f(0, -1, 0)
    glVertex3f(-half_w, -half_h, -half_d)
    glVertex3f(half_w, -half_h, -half_d)
    glVertex3f(half_w, -half_h, half_d)
    glVertex3f(-half_w, -half_h, half_d)
    
    # Right
    glNormal3f(1, 0, 0)
    glVertex3f(half_w, -half_h, -half_d)
    glVertex3f(half_w, half_h, -half_d)
    glVertex3f(half_w, half_h, half_d)
    glVertex3f(half_w, -half_h, half_d)
    
    # Left
    glNormal3f(-1, 0, 0)
    glVertex3f(-half_w, -half_h, -half_d)
    glVertex3f(-half_w, -half_h, half_d)
    glVertex3f(-half_w, half_h, half_d)
    glVertex3f(-half_w, half_h, -half_d)
    
    glEnd()
    glPopMatrix()

def draw_head():
    """Draw head made of two cuboids (black back, skin front)"""
    # Back cuboid (black)
    glColor3f(0.0, 0.0, 0.0)
    glPushMatrix()
    glTranslatef(0, 0, -0.03)
    glScalef(0.15, 0.2, 0.05)
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Front cuboid (skin color)
    glColor3f(0.9, 0.8, 0.7)
    glPushMatrix()
    glTranslatef(0, 0, 0.03)
    glScalef(0.15, 0.2, 0.05)
    glutSolidCube(1.0)
    glPopMatrix()

def draw_goalkeeper(side, color):
    """Draw a goalkeeper with left-right animation"""
    goalie = goalies[side]
    
    # Update goalkeeper animation
    goalie['anim'] += goalie['dir'] * 0.5
    if goalie['anim'] >= 60:
        goalie['anim'] = 60
        goalie['dir'] = -1
    elif goalie['anim'] <= -60:
        goalie['anim'] = -60
        goalie['dir'] = 1
    
    # Calculate goalkeeper position
    if side == "north":
        x = goalie['pos'][0] + math.sin(goalie['anim'] * 0.05) * 2.0
        z = goalie['pos'][2]
        rotation = 0
    elif side == "east":
        x = goalie['pos'][0]
        z = goalie['pos'][2] + math.sin(goalie['anim'] * 0.05) * 2.0
        rotation = 270
    elif side == "south":
        x = goalie['pos'][0] + math.sin(goalie['anim'] * 0.05) * 2.0
        z = goalie['pos'][2]
        rotation = 180
    else:  # west
        x = goalie['pos'][0]
        z = goalie['pos'][2] + math.sin(goalie['anim'] * 0.05) * 2.0
        rotation = 90
    
    # Update collision box position
    if side == "north" or side == "south":
        goalie['collision_box']['x'] = x
    else:
        goalie['collision_box']['z'] = z
    
    glPushMatrix()
    glTranslatef(x, 0, z)
    glRotatef(rotation, 0, 1, 0)
    
    # Goalkeeper body
    glColor3f(color[0] * 0.7, color[1] * 0.7, color[2] * 0.7)
    
    # Torso
    glPushMatrix()
    glTranslatef(0, 0.9, 0)
    glScalef(0.3, 0.6, 0.2)
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Head (using new two-cuboid head)
    glPushMatrix()
    glTranslatef(0, 1.3, 0)
    draw_head()
    glPopMatrix()
    
    # Arms (skin color)
    glColor3f(0.667, 0.455, 0.290)
    
    # Right arm
    glPushMatrix()
    glTranslatef(0.4, 1.0, 0)
    glRotatef(45, 0, 0, 1)
    glScalef(0.08, 0.4, 0.08)
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Left arm
    glPushMatrix()
    glTranslatef(-0.4, 1.0, 0)
    glRotatef(-45, 0, 0, 1)
    glScalef(0.08, 0.4, 0.08)
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Legs (skin color)
    glColor3f(0.9, 0.8, 0.7)
    
    # Right leg
    glPushMatrix()
    glTranslatef(0.1, 0.3, 0)
    glScalef(0.1, 0.5, 0.1)
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Left leg
    glPushMatrix()
    glTranslatef(-0.1, 0.3, 0)
    glScalef(0.1, 0.5, 0.1)
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Goalkeeper number on back
    glDisable(GL_LIGHTING)
    glColor3f(1.0, 1.0, 1.0)
    
    # Draw number 1 on goalkeeper's back
    glRasterPos3f(-0.02, 1.1, -0.15)
    num_str = "1"
    for ch in num_str:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(ch))
    
    glEnable(GL_LIGHTING)
    
    glPopMatrix()

def draw_player():
    global ball_owner
    glPushMatrix()
    glTranslatef(player['pos'][0], 0, player['pos'][2])
    glRotatef(player['rot'], 0, 1, 0)
    
    # Player body color based on selected jersey
    if game.selected_jersey == "argentina":
        body_color = (0.2, 0.6, 1.0)  # Blue for Argentina
    else:  # brazil
        body_color = (1.0, 0.8, 0.0)  # Yellow for Brazil
    
    # Body (torso)
    glColor3f(*body_color)
    glPushMatrix()
    glTranslatef(0, 0.8, 0)
    glScalef(0.25, 0.5, 0.15)
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Head (using new two-cuboid head)
    glPushMatrix()
    glTranslatef(0, 1.1, 0)
    draw_head()
    glPopMatrix()
    
    # Arms (skin color)
    glColor3f(0.776, 0.525, 0.259)
    
    # Right arm
    glPushMatrix()
    glTranslatef(0.2, 0.9, 0)
    if ball_owner == ("human", None):
        glRotatef(90, 1, 0, 0)   # rotate
    glScalef(0.07, 0.3, 0.07)
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Left arm
    glPushMatrix()
    glTranslatef(-0.2, 0.9, 0)
    if ball_owner == ("human", None):
        glRotatef(90, 1, 0, 0)   # rotate
    glScalef(0.07, 0.3, 0.07)
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Legs (skin color)
    glColor3f(0.776, 0.525, 0.259)
    
    # Right leg
    glPushMatrix()
    glTranslatef(0.08, 0.25, 0)
    glScalef(0.08, 0.4, 0.08)
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Left leg
    glPushMatrix()
    glTranslatef(-0.08, 0.25, 0)
    glScalef(0.08, 0.4, 0.08)
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Jersey number on BACK (so you can see which way you're facing)
    glDisable(GL_LIGHTING)
    glColor3f(1.0, 1.0, 1.0)
    
    # Draw number on player's back (negative Z direction)
    glRasterPos3f(-0.03, 1.1, -0.12)
    num_str = str(player['jersey_number'])
    for ch in num_str:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(ch))
    
    # Draw player name text above player
    glColor3f(1.0, 1.0, 0.0)
    glRasterPos3f(-0.05 * len(game.player_name), 1.5, 0.1)
    for ch in game.player_name:
        glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(ch))
    
    glEnable(GL_LIGHTING)
    
    glPopMatrix()

def draw_ball():
    """Draw the football"""
    glPushMatrix()
    glTranslatef(game.ball_pos[0], game.ball_pos[1], game.ball_pos[2])
    
    # Rotate based on velocity
    vel_mag = math.sqrt(game.ball_vel[0]**2 + game.ball_vel[1]**2 + game.ball_vel[2]**2)
    rotation = game.game_time * vel_mag * 30
    
    glRotatef(rotation, 1, 0, 0)
    
    # White base
    glColor3f(1.0, 1.0, 1.0)
    glutSolidSphere(0.2, 16, 16)
    
    # Black patches
    glColor3f(0.0, 0.0, 0.0)
    
    # Draw pentagon-like patches
    for i in range(6):
        angle = 2.0 * math.pi * i / 6
        patch_x = 0.15 * math.cos(angle)
        patch_z = 0.15 * math.sin(angle)
        
        glPushMatrix()
        glTranslatef(patch_x, 0, patch_z)
        glutSolidSphere(0.08, 8, 8)
        glPopMatrix()
    
    glPopMatrix()

def draw_power_meter():
    """Draw the power meter on the bottom right of the screen"""
    glDisable(GL_LIGHTING)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Power meter background (bottom right)
    meter_width = 200
    meter_height = 25
    meter_x = WINDOW_WIDTH - meter_width - 20
    meter_y = 40
    
    # Background
    glColor3f(0.2, 0.2, 0.2)
    glBegin(GL_QUADS)
    glVertex2f(meter_x, meter_y)
    glVertex2f(meter_x + meter_width, meter_y)
    glVertex2f(meter_x + meter_width, meter_y + meter_height)
    glVertex2f(meter_x, meter_y + meter_height)
    glEnd()
    
    # Power level (color changes based on power)
    power_percentage = power_meter['value'] / power_meter['max_power']
    fill_width = meter_width * power_percentage
    
    # Color gradient: green -> yellow -> red
    if power_percentage < 0.5:
        # Green to yellow
        r = 2.0 * power_percentage
        g = 1.0
        b = 0.0
    else:
        # Yellow to red
        r = 1.0
        g = 2.0 * (1.0 - power_percentage)
        b = 0.0
    
    glColor3f(r, g, b)
    glBegin(GL_QUADS)
    glVertex2f(meter_x, meter_y)
    glVertex2f(meter_x + fill_width, meter_y)
    glVertex2f(meter_x + fill_width, meter_y + meter_height)
    glVertex2f(meter_x, meter_y + meter_height)
    glEnd()
    
    # Border
    glColor3f(1.0, 1.0, 1.0)
    glLineWidth(2.0)
    glBegin(GL_LINE_LOOP)
    glVertex2f(meter_x, meter_y)
    glVertex2f(meter_x + meter_width, meter_y)
    glVertex2f(meter_x + meter_width, meter_y + meter_height)
    glVertex2f(meter_x, meter_y + meter_height)
    glEnd()
    
    # Power meter label
    glColor3f(1.0, 1.0, 1.0)
    glRasterPos2f(meter_x, meter_y + meter_height + 5)
    label = "SHOT POWER:"
    for ch in label:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(ch))
    
    # Power value text
    power_text = f"{power_percentage*100:.0f}%"
    glColor3f(1.0, 1.0, 0.0)
    text_width = len(power_text) * 8
    glRasterPos2f(meter_x + meter_width/2 - text_width/2, meter_y + meter_height/2 - 4)
    for ch in power_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(ch))
    
    # Last shot power indicator (above the meter)
    if power_meter['show_last_power'] and time.time() - power_meter['last_shot_time'] < 2.0:
        last_power_y = meter_y + meter_height + 25
        
        # Draw indicator line
        last_power_x = meter_x + (power_meter['last_shot_power'] / power_meter['max_power']) * meter_width
        glColor3f(1.0, 1.0, 0.0)
        glLineWidth(3.0)
        glBegin(GL_LINES)
        glVertex2f(last_power_x, meter_y + meter_height)
        glVertex2f(last_power_x, last_power_y)
        glEnd()
        
        # Draw text
        glRasterPos2f(last_power_x - 20, last_power_y + 5)
        last_power_text = f"{power_meter['last_shot_power']:.1f}"
        for ch in last_power_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_10, ord(ch))
    
    # Instructions for power charging
    if power_meter['charging']:
        glColor3f(1.0, 1.0, 0.0)
        glRasterPos2f(meter_x, meter_y - 20)
        charge_text = "HOLD SPACE to charge power, RELEASE to shoot"
        for ch in charge_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_10, ord(ch))
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glEnable(GL_LIGHTING)

def check_goalkeeper_collision():
    """Check if ball collides with any goalkeeper"""
    for side, goalie in goalies.items():
        box = goalie['collision_box']
        
        # Check collision with goalkeeper's collision box
        if (abs(game.ball_pos[0] - box['x']) < box['width']/2 and
            abs(game.ball_pos[2] - box['z']) < box['depth']/2 and
            game.ball_pos[1] < box['height']):
            
            # Ball hit goalkeeper - bounce back
            if side == "north" or side == "south":
                # Bounce in X direction
                game.ball_vel[0] = -game.ball_vel[0] * 0.8
                # Add some random deflection
                game.ball_vel[0] += random.uniform(-0.3, 0.3)
            else:
                # Bounce in Z direction
                game.ball_vel[2] = -game.ball_vel[2] * 0.8
                # Add some random deflection
                game.ball_vel[2] += random.uniform(-0.3, 0.3)
            
            # Add upward bounce
            game.ball_vel[1] = abs(game.ball_vel[1]) * 0.5 + 0.2
            
            return True
    
    return False

def check_goal():
    """Check if a goal is scored (ball passes goal line without hitting goalkeeper)"""
    # North goal (blue)
    if (game.ball_pos[2] < -GOAL_LINE + 0.2 and 
        abs(game.ball_pos[0]) < GOAL_WIDTH/2 and 
        game.ball_pos[1] < GOAL_HEIGHT):
        
        # Check if it hit the goalkeeper first
        if not check_goalkeeper_collision():
            # Goal scored!
            if game.game_time - game.last_goal_time > 2:
                game.score += 1
                game.last_goal_time = game.game_time
                game.goal_message = "GOAL! +1 Point"
                game.goal_message_time = game.game_time
                reset_ball()
                return True
    
    # East goal (red)
    elif (game.ball_pos[0] > GOAL_LINE - 0.2 and 
          abs(game.ball_pos[2]) < GOAL_WIDTH/2 and 
          game.ball_pos[1] < GOAL_HEIGHT):
        
        if not check_goalkeeper_collision():
            if game.game_time - game.last_goal_time > 2:
                game.score += 1
                game.last_goal_time = game.game_time
                game.goal_message = "GOAL! +1 Point"
                game.goal_message_time = game.game_time
                reset_ball()
                return True
    
    # South goal (yellow)
    elif (game.ball_pos[2] > GOAL_LINE - 0.2 and 
          abs(game.ball_pos[0]) < GOAL_WIDTH/2 and 
          game.ball_pos[1] < GOAL_HEIGHT):
        
        if not check_goalkeeper_collision():
            if game.game_time - game.last_goal_time > 2:
                game.score += 1
                game.last_goal_time = game.game_time
                game.goal_message = "GOAL! +1 Point"
                game.goal_message_time = game.game_time
                reset_ball()
                return True
    
    # West goal (green)
    elif (game.ball_pos[0] < -GOAL_LINE + 0.2 and 
          abs(game.ball_pos[2]) < GOAL_WIDTH/2 and 
          game.ball_pos[1] < GOAL_HEIGHT):
        
        if not check_goalkeeper_collision():
            if game.game_time - game.last_goal_time > 2:
                game.score += 1
                game.last_goal_time = game.game_time
                game.goal_message = "GOAL! +1 Point"
                game.goal_message_time = game.game_time
                reset_ball()
                return True
    
    return False

def draw_menu():
    """Draw the main menu"""
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    # Disable 3D features for 2D menu
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)
    
    # Set 2D orthographic projection for menu
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)
    
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    
    # Dark background
    glColor3f(0.0, 0.1, 0.2)
    glBegin(GL_QUADS)
    glVertex2f(0, 0)
    glVertex2f(WINDOW_WIDTH, 0)
    glVertex2f(WINDOW_WIDTH, WINDOW_HEIGHT)
    glVertex2f(0, WINDOW_HEIGHT)
    glEnd()
    
    # Title
    glColor3f(1.0, 1.0, 0.0)
    glRasterPos2f(WINDOW_WIDTH/2 - 150, WINDOW_HEIGHT - 150)
    title = "FOOTBALL CHALLENGE"
    for ch in title:
        glutBitmapCharacter(GLUT_BITMAP_TIMES_ROMAN_24, ord(ch))
    
    # Subtitle
    glColor3f(1.0, 1.0, 1.0)
    glRasterPos2f(WINDOW_WIDTH/2 - 200, WINDOW_HEIGHT - 200)
    subtitle = "Single Player - Score Against 4 Goalkeepers!"
    for ch in subtitle:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
    
    # Menu options
    start_color = (0.0, 1.0, 0.0) if menu_selection == 0 else (0.5, 0.5, 0.5)
    quit_color = (1.0, 0.0, 0.0) if menu_selection == 1 else (0.5, 0.5, 0.5)
    
    # Start button
    glColor3f(*start_color)
    glRasterPos2f(WINDOW_WIDTH/2 - 50, WINDOW_HEIGHT/2 + 50)
    start_text = "START GAME"
    for ch in start_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
    
    # Quit button
    glColor3f(*quit_color)
    glRasterPos2f(WINDOW_WIDTH/2 - 30, WINDOW_HEIGHT/2 - 50)
    quit_text = "QUIT"
    for ch in quit_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
    
    # Selection indicator
    glColor3f(1.0, 1.0, 0.0)
    glRasterPos2f(WINDOW_WIDTH/2 - 80, WINDOW_HEIGHT/2 + 50 if menu_selection == 0 else WINDOW_HEIGHT/2 - 50)
    glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord('>'))
    
    # Instructions
    glColor3f(0.8, 0.8, 0.8)
    glRasterPos2f(50, 100)
    instructions = "Use UP/DOWN to navigate, ENTER to select"
    for ch in instructions:
        glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(ch))
    
    # Game description
    glColor3f(0.6, 0.8, 1.0)
    glRasterPos2f(100, WINDOW_HEIGHT/2 - 150)
    desc1 = "Game Features:"
    for ch in desc1:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(ch))
    
    glRasterPos2f(120, WINDOW_HEIGHT/2 - 180)
    desc2 = "- 4-minute timed match"
    for ch in desc2:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(ch))
    
    glRasterPos2f(120, WINDOW_HEIGHT/2 - 200)
    desc3 = "- 4 Goals with different colored posts"
    for ch in desc3:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(ch))
    
    glRasterPos2f(120, WINDOW_HEIGHT/2 - 220)
    desc4 = "- 4 Goalkeepers with collision detection"
    for ch in desc4:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(ch))
    
    glRasterPos2f(120, WINDOW_HEIGHT/2 - 240)
    desc5 = "- Choose your name and jersey (Argentina or Brazil)"
    for ch in desc5:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(ch))
    
    # New feature descriptions
    glRasterPos2f(120, WINDOW_HEIGHT/2 - 280)
    desc6 = "- NEW: Stadium stands around the field"
    for ch in desc6:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(ch))
    
    glRasterPos2f(120, WINDOW_HEIGHT/2 - 300)
    desc7 = "- NEW: Power meter for shooting (hold SPACE)"
    for ch in desc7:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(ch))
    
    # Re-enable 3D features
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)

def draw_jersey_selection():
    """Draw jersey selection screen"""
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    # Disable 3D features for 2D menu
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)
    
    # Set 2D orthographic projection
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)
    
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    
    # Dark background
    glColor3f(0.0, 0.1, 0.2)
    glBegin(GL_QUADS)
    glVertex2f(0, 0)
    glVertex2f(WINDOW_WIDTH, 0)
    glVertex2f(WINDOW_WIDTH, WINDOW_HEIGHT)
    glVertex2f(0, WINDOW_HEIGHT)
    glEnd()
    
    # Title
    glColor3f(1.0, 1.0, 0.0)
    glRasterPos2f(WINDOW_WIDTH/2 - 120, WINDOW_HEIGHT - 100)
    title = "SELECT YOUR JERSEY"
    for ch in title:
        glutBitmapCharacter(GLUT_BITMAP_TIMES_ROMAN_24, ord(ch))
    
    # Argentina option
    if jersey_selection == 0:
        glColor3f(0.0, 1.0, 0.0)  # Green for selected
    else:
        glColor3f(0.7, 0.7, 0.7)  # Gray for not selected
    
    # Argentina box
    glBegin(GL_LINE_LOOP)
    glVertex2f(WINDOW_WIDTH/2 - 200, WINDOW_HEIGHT/2 + 100)
    glVertex2f(WINDOW_WIDTH/2 - 50, WINDOW_HEIGHT/2 + 100)
    glVertex2f(WINDOW_WIDTH/2 - 50, WINDOW_HEIGHT/2 - 100)
    glVertex2f(WINDOW_WIDTH/2 - 200, WINDOW_HEIGHT/2 - 100)
    glEnd()
    
    # Argentina text
    glRasterPos2f(WINDOW_WIDTH/2 - 180, WINDOW_HEIGHT/2 + 150)
    argentina_text = "HOME"
    for ch in argentina_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
    
    # Argentina jersey color preview
    glColor3f(0.2, 0.6, 1.0)  # Blue
    glBegin(GL_QUADS)
    glVertex2f(WINDOW_WIDTH/2 - 180, WINDOW_HEIGHT/2 + 80)
    glVertex2f(WINDOW_WIDTH/2 - 70, WINDOW_HEIGHT/2 + 80)
    glVertex2f(WINDOW_WIDTH/2 - 70, WINDOW_HEIGHT/2 - 80)
    glVertex2f(WINDOW_WIDTH/2 - 180, WINDOW_HEIGHT/2 - 80)
    glEnd()
    
    # Argentina number
    glColor3f(1.0, 1.0, 1.0)
    glRasterPos2f(WINDOW_WIDTH/2 - 125, WINDOW_HEIGHT/2)
    for ch in "10":
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
    
    # Brazil option
    if jersey_selection == 1:
        glColor3f(0.0, 1.0, 0.0)  # Green for selected
    else:
        glColor3f(0.7, 0.7, 0.7)  # Gray for not selected
    
    # Brazil box
    glBegin(GL_LINE_LOOP)
    glVertex2f(WINDOW_WIDTH/2 + 50, WINDOW_HEIGHT/2 + 100)
    glVertex2f(WINDOW_WIDTH/2 + 200, WINDOW_HEIGHT/2 + 100)
    glVertex2f(WINDOW_WIDTH/2 + 200, WINDOW_HEIGHT/2 - 100)
    glVertex2f(WINDOW_WIDTH/2 + 50, WINDOW_HEIGHT/2 - 100)
    glEnd()
    
    # Brazil text
    glRasterPos2f(WINDOW_WIDTH/2 + 90, WINDOW_HEIGHT/2 + 150)
    brazil_text = "AWAY"
    for ch in brazil_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
    
    # Brazil jersey color preview
    glColor3f(1.0, 0.8, 0.0)  # Yellow
    glBegin(GL_QUADS)
    glVertex2f(WINDOW_WIDTH/2 + 70, WINDOW_HEIGHT/2 + 80)
    glVertex2f(WINDOW_WIDTH/2 + 180, WINDOW_HEIGHT/2 + 80)
    glVertex2f(WINDOW_WIDTH/2 + 180, WINDOW_HEIGHT/2 - 80)
    glVertex2f(WINDOW_WIDTH/2 + 70, WINDOW_HEIGHT/2 - 80)
    glEnd()
    
    # Brazil number
    glColor3f(0.0, 0.0, 0.0)  # Black for contrast on yellow
    glRasterPos2f(WINDOW_WIDTH/2 + 125, WINDOW_HEIGHT/2)
    for ch in "10":
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
    
    # Selection indicator
    glColor3f(1.0, 1.0, 0.0)
    if jersey_selection == 0:
        glRasterPos2f(WINDOW_WIDTH/2 - 220, WINDOW_HEIGHT/2)
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord('>'))
    else:
        glRasterPos2f(WINDOW_WIDTH/2 + 210, WINDOW_HEIGHT/2)
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord('<'))
    
    # Instructions
    glColor3f(0.8, 0.8, 0.8)
    glRasterPos2f(WINDOW_WIDTH/2 - 150, 150)
    instructions = "Use LEFT/RIGHT to choose, ENTER to confirm, ESC to go back"
    for ch in instructions:
        glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(ch))
    
    # OK button
    glColor3f(0.0, 1.0, 0.0)
    glRasterPos2f(WINDOW_WIDTH/2 - 20, 80)
    ok_text = "OK"
    for ch in ok_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
    
    # Re-enable 3D features
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)

def draw_player_name_input():
    """Draw player name input screen"""
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    # Disable 3D features for 2D menu
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)
    
    # Set 2D orthographic projection
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)
    
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    
    # Dark background
    glColor3f(0.0, 0.1, 0.2)
    glBegin(GL_QUADS)
    glVertex2f(0, 0)
    glVertex2f(WINDOW_WIDTH, 0)
    glVertex2f(WINDOW_WIDTH, WINDOW_HEIGHT)
    glVertex2f(0, WINDOW_HEIGHT)
    glEnd()
    
    # Title
    glColor3f(1.0, 1.0, 0.0)
    glRasterPos2f(WINDOW_WIDTH/2 - 150, WINDOW_HEIGHT - 150)
    title = "ENTER YOUR NAME"
    for ch in title:
        glutBitmapCharacter(GLUT_BITMAP_TIMES_ROMAN_24, ord(ch))
    
    # Instruction
    glColor3f(1.0, 1.0, 1.0)
    glRasterPos2f(WINDOW_WIDTH/2 - 200, WINDOW_HEIGHT - 200)
    instruction = "This name will appear above your player in the game"
    for ch in instruction:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
    
    # Name input box
    glColor3f(0.5, 0.5, 0.5)
    glBegin(GL_LINE_LOOP)
    glVertex2f(WINDOW_WIDTH/2 - 200, WINDOW_HEIGHT/2 + 30)
    glVertex2f(WINDOW_WIDTH/2 + 200, WINDOW_HEIGHT/2 + 30)
    glVertex2f(WINDOW_WIDTH/2 + 200, WINDOW_HEIGHT/2 - 30)
    glVertex2f(WINDOW_WIDTH/2 - 200, WINDOW_HEIGHT/2 - 30)
    glEnd()
    
    # Current name
    glColor3f(1.0, 1.0, 1.0)
    glRasterPos2f(WINDOW_WIDTH/2 - 190, WINDOW_HEIGHT/2)
    display_name = player_name_input
    if len(display_name) == 0:
        display_name = "Type your name..."
    
    for ch in display_name:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
    
    # Cursor
    if time.time() % 1.0 < 0.5:  # Blinking cursor
        glColor3f(1.0, 1.0, 0.0)
        cursor_x = WINDOW_WIDTH/2 - 190 + len(display_name) * 10
        glRasterPos2f(cursor_x, WINDOW_HEIGHT/2)
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord('|'))
    
    # Instructions
    glColor3f(0.8, 0.8, 0.8)
    glRasterPos2f(WINDOW_WIDTH/2 - 250, WINDOW_HEIGHT/2 - 100)
    instructions1 = "Type your name (max 15 characters), then press ENTER"
    for ch in instructions1:
        glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(ch))
    
    glRasterPos2f(WINDOW_WIDTH/2 - 200, WINDOW_HEIGHT/2 - 120)
    instructions2 = "Press BACKSPACE to delete, ESC to go back"
    for ch in instructions2:
        glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(ch))
    
    # OK button
    glColor3f(0.0, 1.0, 0.0)
    glRasterPos2f(WINDOW_WIDTH/2 - 20, 100)
    ok_text = "ENTER to Start Game"
    for ch in ok_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
    
    # Re-enable 3D features
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)

def draw_hud():
    """Draw heads-up display during game"""
    glDisable(GL_LIGHTING)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Time remaining
    time_left = max(0, game.total_game_time - game.game_time)
    minutes = int(time_left // 60)
    seconds = int(time_left % 60)
    
    glColor3f(1.0, 1.0, 0.0)  # Yellow for timer
    glRasterPos2f(WINDOW_WIDTH/2 - 50, WINDOW_HEIGHT - 40)
    time_text = f"TIME: {minutes:02d}:{seconds:02d}"
    for ch in time_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
    
    # Score display
    glColor3f(0.2, 0.6, 1.0)  # Blue
    glRasterPos2f(50, WINDOW_HEIGHT - 40)
    score_text = f"SCORE: {game.score}"
    for ch in score_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
    
    # Controls
    glColor3f(0.8, 0.8, 0.8)
    glRasterPos2f(20, 60)
    controls = "Arrow Keys: Move | SPACE: Hold to charge shot | C: Camera | P: Pause | R: Reset Ball"
    for ch in controls:
        glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(ch))
    
    # Player info
    if game.selected_jersey == "argentina":
        team_color = (0.2, 0.6, 1.0)
        team_name = "Argentina (Blue)"
    else:
        team_color = (1.0, 0.8, 0.0)
        team_name = "Brazil (Yellow)"
    
    glColor3f(*team_color)
    glRasterPos2f(20, 40)
    player_text = f"Player: {game.player_name} - Team: {team_name} - #{player['jersey_number']}"
    for ch in player_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(ch))
    
    # Camera mode
    glRasterPos2f(20, 20)
    camera_text = f"CAMERA: {camera_mode} (C to change)"
    for ch in camera_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(ch))
    
    # Ball possession
    if game.player_has_ball:
        glColor3f(0.0, 1.0, 0.0)
        glRasterPos2f(WINDOW_WIDTH/2 - 50, 40)
        ball_text = "YOU HAVE THE BALL! (HOLD SPACE to charge shot)"
        for ch in ball_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
    
    # Goal message (appears for 2 seconds after scoring)
    if game.game_time - game.goal_message_time < 2.0 and game.goal_message:
        glColor3f(0.0, 1.0, 0.0)  # Green
        glRasterPos2f(WINDOW_WIDTH/2 - 80, WINDOW_HEIGHT/2 + 50)
        for ch in game.goal_message:
            glutBitmapCharacter(GLUT_BITMAP_TIMES_ROMAN_24, ord(ch))
    
    # Pause indicator
    if not game.is_playing and not game.game_over:
        glColor3f(1.0, 1.0, 0.0)
        glRasterPos2f(WINDOW_WIDTH/2 - 30, WINDOW_HEIGHT/2)
        pause_text = "GAME PAUSED"
        for ch in pause_text:
            glutBitmapCharacter(GLUT_BITMAP_TIMES_ROMAN_24, ord(ch))
    
    # Game over screen
    if game.game_over:
        glColor4f(0.0, 0.0, 0.0, 0.7)
        glBegin(GL_QUADS)
        glVertex2f(0, 0)
        glVertex2f(WINDOW_WIDTH, 0)
        glVertex2f(WINDOW_WIDTH, WINDOW_HEIGHT)
        glVertex2f(0, WINDOW_HEIGHT)
        glEnd()
        
        glColor3f(1.0, 1.0, 0.0)
        glRasterPos2f(WINDOW_WIDTH/2 - 80, WINDOW_HEIGHT/2 + 50)
        game_over_text = "GAME OVER!"
        for ch in game_over_text:
            glutBitmapCharacter(GLUT_BITMAP_TIMES_ROMAN_24, ord(ch))
        
        # Final score
        glColor3f(0.2, 0.6, 1.0)
        glRasterPos2f(WINDOW_WIDTH/2 - 60, WINDOW_HEIGHT/2)
        score_text = f"FINAL SCORE: {game.score}"
        for ch in score_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
        
        # Performance message
        performance = ""
        color = (1.0, 1.0, 1.0)
        
        if game.score >= 10:
            performance = "EXCELLENT! You're a football star!"
            color = (1.0, 1.0, 0.0)
        elif game.score >= 5:
            performance = "GOOD JOB! Keep practicing!"
            color = (0.0, 1.0, 0.0)
        elif game.score >= 2:
            performance = "NOT BAD! Try again!"
            color = (0.8, 0.8, 0.8)
        else:
            performance = "KEEP PRACTICING!"
            color = (0.5, 0.5, 0.5)
        
        glColor3f(*color)
        glRasterPos2f(WINDOW_WIDTH/2 - 120, WINDOW_HEIGHT/2 - 50)
        for ch in performance:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
        
        # Restart instructions
        glColor3f(1.0, 1.0, 1.0)
        glRasterPos2f(WINDOW_WIDTH/2 - 100, 50)
        restart_text = "Press R to Restart Game | ESC to Quit"
        for ch in restart_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glEnable(GL_LIGHTING)
    
    # Draw power meter on top of HUD
    if current_state == PLAYING and game.player_has_ball:
        draw_power_meter()


def draw_ai_player(ai, idx):
    global ball_owner
    glPushMatrix()
    glTranslatef(ai["pos"][0], 0, ai["pos"][2])
    glRotatef(ai["rot"], 0, 1, 0)

    # Body color per team (simple mapping)
    if ai["team"] == "red":
        body_color = (1.0, 0.2, 0.2)
    elif ai["team"] == "green":
        body_color = (0.2, 1.0, 0.2)
    else:
        body_color = (1.0, 1.0, 0.2)

    glColor3f(*body_color)
    glPushMatrix()
    glTranslatef(0, 0.8, 0)
    glScalef(0.25, 0.5, 0.15)
    glutSolidCube(1.0)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(0, 1.1, 0)
    draw_head()
    glPopMatrix()

    # Arms
    glColor3f(0.776, 0.525, 0.259)

    #Right arm
    glPushMatrix()
    glTranslatef(0.2, 0.9, 0)
    if ball_owner == ("ai", idx):    
        glRotatef(90, 1, 0, 0)   #rotate
    glScalef(0.07, 0.3, 0.07)
    glutSolidCube(1.0)
    glPopMatrix()

    #Left arm
    glPushMatrix()
    glTranslatef(-0.2, 0.9, 0)
    if ball_owner == ("ai", idx):    
        glRotatef(90, 1, 0, 0)   #rotate
    glScalef(0.07, 0.3, 0.07)
    glutSolidCube(1.0)
    glPopMatrix()

    #Legs
    glColor3f(0.776, 0.525, 0.259)
    glPushMatrix()
    glTranslatef(0.08, 0.25, 0)
    glScalef(0.08, 0.4, 0.08)
    glutSolidCube(1.0)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(-0.08, 0.25, 0)
    glScalef(0.08, 0.4, 0.08)
    glutSolidCube(1.0)
    glPopMatrix()

    #Name label
    glDisable(GL_LIGHTING)
    glColor3f(1.0, 1.0, 1.0)
    glRasterPos3f(-0.05 * len(ai["name"]), 1.5, 0.1)
    for ch in ai["name"]:
        glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(ch))
    glEnable(GL_LIGHTING)
    glPopMatrix()


def update_physics():
    """Update ball physics"""
    if not game.is_playing or game.game_over:
        return
    
    # Update game time
    game.game_time += 1/60.0
    
    # Check if game time is up
    if game.game_time >= game.total_game_time:
        game.game_over = True
        game.is_playing = False
        return
    
    # Ball physics
    gravity = -0.098
    friction = 0.99
    bounce_damping = 0.7
    
    # Apply gravity
    game.ball_vel[1] += gravity
    
    # Apply friction
    game.ball_vel[0] *= friction
    game.ball_vel[2] *= friction
    
    # Update position
    game.ball_pos[0] += game.ball_vel[0]
    game.ball_pos[1] += game.ball_vel[1]
    game.ball_pos[2] += game.ball_vel[2]
    
    # Ground collision
    if game.ball_pos[1] < 0.2:
        game.ball_pos[1] = 0.2
        game.ball_vel[1] = -game.ball_vel[1] * bounce_damping
    
    # Boundary collision (walls)
    half_size = FIELD_SIZE / 2 - 0.5
    if abs(game.ball_pos[0]) > half_size:
        game.ball_pos[0] = half_size if game.ball_pos[0] > 0 else -half_size
        game.ball_vel[0] = -game.ball_vel[0] * 0.8
    
    if abs(game.ball_pos[2]) > half_size:
        game.ball_pos[2] = half_size if game.ball_pos[2] > 0 else -half_size
        game.ball_vel[2] = -game.ball_vel[2] * 0.8
    
    # Check goalkeeper collision
    check_goalkeeper_collision()
    
    # Check for goals
    check_goal()
    
    # Check ball possession
    if ball_owner is not None:
        owner_type, owner_idx = ball_owner

        if owner_type == "human":
            game.ball_pos = hand_attach_position(player["pos"], player["rot"])
        else:
            ai = ai_players[owner_idx]
            game.ball_pos = hand_attach_position(ai["pos"], ai["rot"])

        #Ball is carried
        game.ball_vel = [0, 0, 0]
        game.player_has_ball = (owner_type == "human")
    else:
        #Nobody owns ball
        dx = player['pos'][0] - game.ball_pos[0]
        dz = player['pos'][2] - game.ball_pos[2]
        dist = math.sqrt(dx*dx + dz*dz)
        game.player_has_ball = (dist < 1.0 and game.ball_pos[1] < 0.8)
    
    # Update power meter charging
    if power_meter['charging'] and game.player_has_ball and game.is_playing:
        power_meter['value'] += power_meter['charge_rate'] / 60
        if power_meter['value'] > power_meter['max_power']:
            power_meter['value'] = power_meter['max_power']


def try_steal_ball_human():
    global ball_owner

    #only steal if AI currently owns
    if ball_owner is None:
        return
    owner_type, owner_idx = ball_owner
    if owner_type != "ai":
        return

    ai = ai_players[owner_idx]

    dx = ai["pos"][0] - player["pos"][0]
    dz = ai["pos"][2] - player["pos"][2]
    dist = math.sqrt(dx*dx + dz*dz)

    #ball steal distance
    if dist < 2.25:
        #check if facing ball
        if not is_ball_in_front(player["pos"], player["rot"], ai["pos"], min_dot=0.0):
            return
        # STEAL
        knockback_loser(ai["pos"], player["pos"], dist=KNOCKBACK_DIST)
        block_entity_pickup(owner_idx)
        ball_owner = ("human", None)
        game.player_has_ball = True
        game.ball_vel = [0, 0, 0]
        game.ball_pos = hand_attach_position(player["pos"], player["rot"])



def update_ai_players():
    global ball_owner
    if not game.is_playing or game.game_over:
        return

    half_size = FIELD_SIZE / 2 - 2

    # goal centers (x,z)
    goals = [
        {"side":"north", "pos": (0, -GOAL_LINE), "team":"blue"},
        {"side":"east",  "pos": (GOAL_LINE, 0),  "team":"red"},
        {"side":"south", "pos": (0, GOAL_LINE),  "team":"yellow"},
        {"side":"west",  "pos": (-GOAL_LINE, 0), "team":"green"},
    ]  

    for i, ai in enumerate(ai_players):
        # If AI has ball, go for goal
        if ball_owner == ("ai", i):
            #choose nearest goal
            best = None
            best_d = 1e9
            for g in goals:
                if g["team"] == ai["team"]:
                    continue   #skip own goal

                gx, gz = g["pos"]
                dx = gx - ai["pos"][0]
                dz = gz - ai["pos"][2]
                d = dx*dx + dz*dz

                if d < best_d:
                    best_d = d
                    best = (gx, gz)
            

            tx, tz = best
            vx = tx - ai["pos"][0]
            vz = tz - ai["pos"][2]
            dist = math.sqrt(vx*vx + vz*vz)

            if dist > 0.05:
                vx /= dist
                vz /= dist
                ai["pos"][0] += vx * ai["speed"]
                ai["pos"][2] += vz * ai["speed"]
                ai["rot"] = math.degrees(math.atan2(vx, vz))

            #If close to post,just shoot
            if dist < 3.0:
                shoot_ball_ai(i, power=1.25)

            continue  

        #Otherwise just follow ball
        if ball_owner == ("human", None):
            tx, tz = player["pos"][0], player["pos"][2]
        else:
            tx, tz = game.ball_pos[0], game.ball_pos[2]
        vx = tx - ai["pos"][0]
        vz = tz - ai["pos"][2]
        dist = math.sqrt(vx*vx + vz*vz)

        if dist > 0.05:
            vx /= dist
            vz /= dist
            ai["pos"][0] += vx * ai["speed"]
            ai["pos"][2] += vz * ai["speed"]
            ai["rot"] = math.degrees(math.atan2(vx, vz))

        ai["pos"][0] = max(-half_size, min(half_size, ai["pos"][0]))
        ai["pos"][2] = max(-half_size, min(half_size, ai["pos"][2]))
        separate_ai(i, min_sep=1.1, push=0.04)    

def separate_ai(i, min_sep=1.0, push=0.03):
    ax, az = ai_players[i]["pos"][0], ai_players[i]["pos"][2]
    for j, other in enumerate(ai_players):
        if j == i:
            continue
        bx, bz = other["pos"][0], other["pos"][2]
        dx = ax - bx
        dz = az - bz
        d = math.sqrt(dx*dx + dz*dz)
        if d < 1e-6:
            # exact overlap: random tiny nudge
            dx = random.uniform(-1, 1)
            dz = random.uniform(-1, 1)
            d = math.sqrt(dx*dx + dz*dz)

        if d < min_sep:
            # push away
            dx /= d
            dz /= d
            ai_players[i]["pos"][0] += dx * push
            ai_players[i]["pos"][2] += dz * push

def separate_player_from_ai(min_sep=1.0, push=0.06):
    px, pz = player["pos"][0], player["pos"][2]
    for ai in ai_players:
        ax, az = ai["pos"][0], ai["pos"][2]
        dx = px - ax
        dz = pz - az
        d = math.sqrt(dx*dx + dz*dz)

        if d < 1e-6:
            dx = random.uniform(-1, 1)
            dz = random.uniform(-1, 1)
            d = math.sqrt(dx*dx + dz*dz)

        if d < min_sep:
            dx /= d
            dz /= d

            player["pos"][0] += dx * push
            player["pos"][2] += dz * push
            ai["pos"][0] -= dx * push
            ai["pos"][2] -= dz * push


def shoot_ball_ai(i, power=1.2):
    global ball_owner
    ai = ai_players[i]

    ball_owner = None  #release ownership

    angle_x = math.sin(math.radians(ai['rot']))
    angle_z = math.cos(math.radians(ai['rot']))

    game.ball_vel[0] = angle_x * power
    game.ball_vel[1] = 0.25 + (power * 0.08)
    game.ball_vel[2] = angle_z * power

def try_steal_ball_ai(i):
    global ball_owner

    if ball_owner is None:
        return

    owner_type, owner_idx = ball_owner

    #check if it is him
    if owner_type == "ai" and owner_idx == i:
        return

    ai = ai_players[i]

    if owner_type == "human":
        target_pos = player["pos"]
        target_key = "human"
    else:
        target_pos = ai_players[owner_idx]["pos"]
        target_key = owner_idx

    dx = target_pos[0] - ai["pos"][0]
    dz = target_pos[2] - ai["pos"][2]
    dist = math.sqrt(dx*dx + dz*dz)

    # tackle distance
    if dist < 1.25:
        #if AI is in front of ball,then steal
        if not is_ball_in_front(ai["pos"], ai["rot"], target_pos, min_dot=0.0):
            return

        #Knockback & steal
        knockback_loser(target_pos, ai["pos"], dist=KNOCKBACK_DIST)
        block_entity_pickup(target_key)
        ball_owner = ("ai", i)
        game.player_has_ball = False
        game.ball_vel = [0, 0, 0]
        game.ball_pos = hand_attach_position(ai["pos"], ai["rot"])
        


#Forward direction in xz plane
def forward_vector_y(rot_deg):   
    ang = math.radians(rot_deg)
    fx = math.sin(ang)
    fz = math.cos(ang)
    return fx, fz

#check if ball is front
def is_ball_in_front(entity_pos, entity_rot,ball_pos, min_dot=0.35):    #min_dot=cos(70)=0.34
    vx = ball_pos[0] - entity_pos[0]
    vz = ball_pos[2] - entity_pos[2]
    dist = math.sqrt(vx*vx + vz*vz)
    if dist < 1e-6:
        return True

    vx=vx/dist
    vz=vz/ dist

    fx, fz = forward_vector_y(entity_rot)
    dot = vx*fx + vz*fz
    return dot >= min_dot

#Hand position
def hand_attach_position(entity_pos, entity_rot):
    fx, fz = forward_vector_y(entity_rot)

    x = entity_pos[0] + fx * 0.45
    y = 1.0
    z = entity_pos[2] + fz * 0.45
    return [x, y, z]

def try_pickup_ball_human():
    global ball_owner    
    if ball_owner is not None:
        return
    
    if not can_entity_pickup("human"):
        return

    # close + low enough + in front
    dx = game.ball_pos[0] - player["pos"][0]
    dz = game.ball_pos[2] - player["pos"][2]
    dist = math.sqrt(dx*dx + dz*dz)

    if dist < 0.9 and game.ball_pos[1] < 0.8 and is_ball_in_front(player["pos"], player["rot"], game.ball_pos):
        ball_owner = ("human", None)
        game.player_has_ball = True
        game.ball_vel = [0, 0, 0]
        game.ball_pos = hand_attach_position(player["pos"], player["rot"])

def try_pickup_ball_ai(i):
    global ball_owner
    if ball_owner is not None:
        return
    if not can_entity_pickup(i):
        return

    ai = ai_players[i]
    dx = game.ball_pos[0] - ai["pos"][0]
    dz = game.ball_pos[2] - ai["pos"][2]
    dist = math.sqrt(dx*dx + dz*dz)

    if dist < 1.35 and game.ball_pos[1] < 0.95 and is_ball_in_front(ai["pos"], ai["rot"], game.ball_pos):
        ball_owner = ("ai", i)
        game.ball_vel = [0, 0, 0]
        game.ball_pos = hand_attach_position(ai["pos"], ai["rot"])

#entity_key:human or ai index(0/1/2)
def can_entity_pickup(entity_key):
    return (time.time() - last_pickup_block[entity_key]) >= PICKUP_COOLDOWN

def block_entity_pickup(entity_key):
    last_pickup_block[entity_key] = time.time()

def knockback_loser(loser_pos, winner_pos, dist=1.0):
    dx = loser_pos[0] - winner_pos[0]
    dz = loser_pos[2] - winner_pos[2]
    d = math.sqrt(dx*dx + dz*dz)
    if d < 1e-6:
        dx = random.uniform(-1, 1)
        dz = random.uniform(-1, 1)
        d = math.sqrt(dx*dx + dz*dz)

    dx /= d
    dz /= d
    loser_pos[0] += dx * dist
    loser_pos[2] += dz * dist



def reset_ball():
    """Reset ball to center"""
    global ball_owner
    ball_owner = None
    game.ball_pos = [0, 0.5, 0]
    game.ball_vel = [0, 0, 0]
    game.player_has_ball = False
    power_meter['value'] = 0.0
    power_meter['charging'] = False

def restart_game():
    """Restart the game"""
    global game, player, current_state, player_name_input, power_meter
    game = Game()
    player = {
        'pos': [0, 0, 0],
        'rot': 0,
        'speed': 0.03,
        'team': 'blue',
        'jersey_number': 10
    }
    player_name_input = ""
    power_meter = {
        'value': 0.0,
        'max_power': 2.0,
        'charging': False,
        'charge_rate': 3.0,
        'show_meter': False,
        'last_shot_power': 0.0,
        'last_shot_time': 0,
        'show_last_power': False
    }
    current_state = MENU

def process_player_movement():
    """Process player movement based on key states"""
    if not game.is_playing or game.game_over:
        return
    
    # Simple arrow key movement (up/down/left/right relative to field)
    if key_states[GLUT_KEY_UP]:
        player['pos'][2] -= player['speed']
        player['rot'] = 180
    if key_states[GLUT_KEY_DOWN]:
        player['pos'][2] += player['speed']
        player['rot'] = 0
    if key_states[GLUT_KEY_LEFT]:
        player['pos'][0] -= player['speed']
        player['rot'] = 270
    if key_states[GLUT_KEY_RIGHT]:
        player['pos'][0] += player['speed']
        player['rot'] = 90
    
    # Diagonal movement (combined keys)
    if key_states[GLUT_KEY_UP] and key_states[GLUT_KEY_LEFT]:
        player['rot'] = 315
    if key_states[GLUT_KEY_UP] and key_states[GLUT_KEY_RIGHT]:
        player['rot'] = 45
    if key_states[GLUT_KEY_DOWN] and key_states[GLUT_KEY_LEFT]:
        player['rot'] = 225
    if key_states[GLUT_KEY_DOWN] and key_states[GLUT_KEY_RIGHT]:
        player['rot'] = 135
    
    # Keep player in bounds
    half_size = FIELD_SIZE / 2 - 2
    player['pos'][0] = max(-half_size, min(half_size, player['pos'][0]))
    player['pos'][2] = max(-half_size, min(half_size, player['pos'][2]))

def shoot_ball(power):
    """Shoot the ball with specified power"""
    # Shoot in direction player is facing
    global ball_owner
    ball_owner = None
    angle_x = math.sin(math.radians(player['rot']))
    angle_z = math.cos(math.radians(player['rot']))
    
    # Apply power to velocity
    game.ball_vel[0] = angle_x * power
    game.ball_vel[1] = 0.3 + (power * 0.1)  # More lift with more power
    game.ball_vel[2] = angle_z * power
    
    game.player_has_ball = False
    power_meter['charging'] = False
    
    # Store last shot power for display
    power_meter['last_shot_power'] = power
    power_meter['last_shot_time'] = time.time()
    power_meter['show_last_power'] = True
    
    # Reset power meter
    power_meter['value'] = 0.0

def display():
    """Main display function"""
    if current_state == MENU:
        draw_menu()
    elif current_state == JERSEY_SELECTION:
        draw_jersey_selection()
    elif current_state == PLAYER_NAME_INPUT:
        draw_player_name_input()
    elif current_state == PLAYING:
        # Draw the game
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # Set projection
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(60.0, WINDOW_WIDTH/WINDOW_HEIGHT, 0.1, 100.0)
        
        # Set camera
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        set_camera()     
        
        # Draw field
        draw_square_field()
        
        # Draw simple colored goals
        draw_simple_goal("north", (0.0, 0.545, 0.545))  # Blue goal
        draw_goal_box("north")
        draw_simple_goal("east", (1.0, 0.2, 0.2))   # Red goal
        draw_goal_box("east")
        draw_simple_goal("south", (1.0, 1.0, 0.2))  # Yellow goal
        draw_goal_box("south")
        draw_simple_goal("west", (0.2, 1.0, 0.2))   # Green goal
        draw_goal_box("west")
        
        # Draw goalkeepers
        draw_goalkeeper("north", (0.0, 0.545, 0.545))  # Cyan
        draw_goalkeeper("east", (1.0, 0.2, 0.2))   # Red
        draw_goalkeeper("south", (1.0, 1.0, 0.2))  # Yellow
        draw_goalkeeper("west", (0.2, 1.0, 0.2))   # Green
        
        # Draw player
        draw_player()
        
        # Draw ball
        draw_ball()
        
        # Draw HUD
        draw_hud()

        #Draw AI players
        for i, ai in enumerate(ai_players):
            draw_ai_player(ai, i)
    elif current_state == GAME_OVER:
        # Draw the game with overlay
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # Set projection
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(60.0, WINDOW_WIDTH/WINDOW_HEIGHT, 0.1, 100.0)
        
        # Set camera
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        set_camera()
        
        # Draw stadium stands
        draw_stadium_stands()
        
        # Draw field
        draw_square_field()
        
        # Draw simple colored goals
        draw_simple_goal("north", (0.0, 0.545, 0.545))  # Blue goal
        draw_goal_box("north")
        draw_simple_goal("east", (1.0, 0.2, 0.2))   # Red goal
        draw_goal_box("east")
        draw_simple_goal("south", (1.0, 1.0, 0.2))  # Yellow goal
        draw_goal_box("south")
        draw_simple_goal("west", (0.2, 1.0, 0.2))   # Green goal
        draw_goal_box("west")
        
        # Draw goalkeepers
        draw_goalkeeper("north", (0.0, 0.545, 0.545))  # Blue
        draw_goalkeeper("east", (1.0, 0.2, 0.2))   # Red
        draw_goalkeeper("south", (1.0, 1.0, 0.2))  # Yellow
        draw_goalkeeper("west", (0.2, 1.0, 0.2))   # Green
        
        # Draw player
        draw_player()
        
        # Draw ball
        draw_ball()
        
        # Draw HUD (which includes game over screen)
        draw_hud()
    
    glutSwapBuffers()

def reshape(width, height):
    """Handle window resize"""
    global WINDOW_WIDTH, WINDOW_HEIGHT
    WINDOW_WIDTH = width
    WINDOW_HEIGHT = height
    glViewport(0, 0, width, height)

def keyboard(key, x, y):
    """Handle regular keyboard input"""
    global camera_mode, current_state, game, player_name_input
    
    # Convert byte to string
    if isinstance(key, bytes):
        key_char = key.decode('utf-8')
    else:
        return  # Not a regular key
    
    # Handle different states
    if current_state == MENU:
        if key_char == '\r':  # ENTER key
            if menu_selection == 0:  # Start Game
                current_state = JERSEY_SELECTION
            elif menu_selection == 1:  # Quit
                glutLeaveMainLoop()
        elif key_char == '\x1b':  # ESC key
            glutLeaveMainLoop()
    
    elif current_state == JERSEY_SELECTION:
        if key_char == '\r':  # ENTER key
            current_state = PLAYER_NAME_INPUT
        
        elif key_char == '\x1b':  # ESC key - go back to menu
            current_state = MENU
    
    elif current_state == PLAYER_NAME_INPUT:
        if key_char == '\r':  # ENTER key
            if player_name_input.strip():
                game.player_name = player_name_input.strip()
            else:
                game.player_name = "YOU"
            
            # Set selected jersey and start game
            if jersey_selection == 0:
                game.selected_jersey = "argentina"
                player['team'] = 'blue'
            else:
                game.selected_jersey = "brazil"
                player['team'] = 'yellow'
            
            current_state = PLAYING
            game.is_playing = True
        
        elif key_char == '\x1b':  # ESC key - go back to jersey selection
            current_state = JERSEY_SELECTION
        
        elif key_char == '\x08':  # BACKSPACE key
            if player_name_input:
                player_name_input = player_name_input[:-1]
        
        elif len(key_char) == 1 and key_char.isprintable() and len(player_name_input) < MAX_NAME_LENGTH:
            player_name_input += key_char
    
    elif current_state == PLAYING or current_state == GAME_OVER:
        # Game controls
        if key_char == 'c':
            modes = ["PLAYER","OVERHEAD"]
            current_idx = modes.index(camera_mode)
            camera_mode = modes[(current_idx + 1) % len(modes)]
        
        # Pause game
        elif key_char == 'p' and current_state == PLAYING:
            game.is_playing = not game.is_playing
        
        # Start charging shot when space is pressed
        elif key_char == ' ' and game.player_has_ball and game.is_playing and not game.game_over:
            if not power_meter['charging']:
                power_meter['charging'] = True
                power_meter['value'] = 0.1  # Start with minimal power
        
        # Reset/Restart
        elif key_char == 'r':
            if current_state == GAME_OVER:
                restart_game()
            else:
                reset_ball()
        
        # Quit to menu
        elif key_char == '\x1b':  # ESC
            current_state = MENU
    
    glutPostRedisplay()

def keyboard_up(key, x, y):
    """Handle key release"""
    global power_meter, game
    
    if isinstance(key, bytes):
        key_char = key.decode('utf-8')
    else:
        return
    
    # Handle space key release for shooting
    if key_char == ' ' and current_state == PLAYING and game.player_has_ball and game.is_playing and not game.game_over:
        if power_meter['charging']:
            # Shoot with current power
            shoot_ball(power_meter['value'])
            
            # Reset charging state
            power_meter['charging'] = False
    
    glutPostRedisplay()

def special_keys(key, x, y):
    """Handle special keys (arrow keys)"""
    global menu_selection, jersey_selection, current_state
    
    if current_state == MENU:
        # Menu navigation
        if key == GLUT_KEY_UP:
            menu_selection = max(0, menu_selection - 1)
        elif key == GLUT_KEY_DOWN:
            menu_selection = min(1, menu_selection + 1)
    
    elif current_state == JERSEY_SELECTION:
        # Jersey selection navigation
        if key == GLUT_KEY_LEFT:
            jersey_selection = 0
        elif key == GLUT_KEY_RIGHT:
            jersey_selection = 1
    
    elif current_state == PLAYING or current_state == GAME_OVER:
        # Store arrow key states for game movement
        if key == GLUT_KEY_UP:
            key_states[GLUT_KEY_UP] = True
        elif key == GLUT_KEY_DOWN:
            key_states[GLUT_KEY_DOWN] = True
        elif key == GLUT_KEY_LEFT:
            key_states[GLUT_KEY_LEFT] = True
        elif key == GLUT_KEY_RIGHT:
            key_states[GLUT_KEY_RIGHT] = True
    
    glutPostRedisplay()

def special_up(key, x, y):
    """Handle special key release"""
    # Clear arrow key states (only in game)
    if current_state == PLAYING or current_state == GAME_OVER:
        if key == GLUT_KEY_UP:
            key_states[GLUT_KEY_UP] = False
        elif key == GLUT_KEY_DOWN:
            key_states[GLUT_KEY_DOWN] = False
        elif key == GLUT_KEY_LEFT:
            key_states[GLUT_KEY_LEFT] = False
        elif key == GLUT_KEY_RIGHT:
            key_states[GLUT_KEY_RIGHT] = False
    
    glutPostRedisplay()

def update(value):
    """Update game state"""
    if current_state == PLAYING or current_state == GAME_OVER:
        process_player_movement()
        update_ai_players()

        separate_player_from_ai(min_sep=1.1, push=0.06)  # ✅ add
        for i in range(len(ai_players)):
            separate_ai(i, min_sep=1.1, push=0.04)

        update_physics()

        try_pickup_ball_human()
        try_steal_ball_human()

        for i in range(len(ai_players)):
            try_pickup_ball_ai(i)
            try_steal_ball_ai(i)

    glutPostRedisplay()
    glutTimerFunc(16, update, 0)

def main():
    """Main function"""
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutCreateWindow(b"Single Player Football - Score Goals!")
    
    init()
    
    # Set up callbacks
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboard)
    glutKeyboardUpFunc(keyboard_up)  # Add key up callback for shooting
    glutSpecialFunc(special_keys)
    glutSpecialUpFunc(special_up)
    glutTimerFunc(16, update, 0)
    
    print("=" * 70)
    print("FOOTBALL CHALLENGE - SINGLE PLAYER")
    print("=" * 70)
    print("\nGAME FLOW:")
    print("1. Start at Main Menu")
    print("2. Select Jersey (Argentina Blue or Brazil Yellow)")
    print("3. Enter Your Name")
    print("4. Play the Game!")
    print("\nGAME FEATURES:")
    print("- Single player only (YOU vs 4 goalkeepers)")
    print("- 4-minute timed match")
    print("- 4 Goals with colored posts (Blue, Red, Yellow, Green)")
    print("- 4 Goalkeepers with collision detection")
    print("- Score by shooting past goalkeepers")
    print("- Jersey number on your BACK shows which way you're facing")
    print("- NEW: Stadium stands around the field (45° tilted)")
    print("- NEW: Power meter for shooting - HOLD SPACE to charge!")
    print("\nHOW TO PLAY:")
    print("- Move with Arrow Keys")
    print("- Look at the number on your BACK to know your direction")
    print("- Get close to ball to pick it up")
    print("- HOLD SPACE to charge power, RELEASE to shoot")
    print("- Ball must pass goal line WITHOUT hitting goalkeeper")
    print("\nCONTROLS:")
    print("- Arrow Keys: Move (number on back shows direction)")
    print("- SPACE: Hold to charge shot power, release to shoot")
    print("- C: Change camera view (Player, Overhead, Goal)")
    print("- P: Pause/Resume game")
    print("- R: Reset ball (during game) / Restart (after game)")
    print("- ESC: Quit to menu")
    print("\nPOWER METER:")
    print("- Bottom right of screen shows shot power")
    print("- Green (low power) -> Yellow (medium) -> Red (high)")
    print("- After shooting, yellow line shows exact power used")
    print("\nOBJECTIVE:")
    print("Score as many goals as possible in 4 minutes!")
    print("Shoot past any of the 4 goalkeepers to score.")
    
    glutMainLoop()

if __name__ == "__main__":
    main()