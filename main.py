import os
import math
import random
import sys
import cv2
import pygame
from config import *

pygame.init()
pygame.mixer.init()

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Black hole sim ig")
clock = pygame.time.Clock()

font = pygame.font.SysFont("Orbitron", 18)
title_font = pygame.font.SysFont("Orbitron", 22, bold=True)

if os.path.exists("interstellar.mp3"):
    pygame.mixer.music.load("interstellar.mp3")
    pygame.mixer.music.play(-1)
    pygame.mixer.music.set_volume(0.6)
else:
    print("The music is not found so go and download intersteallar.mp3")

class BlackHole:
    def __init__(self, level_config):
        self.update_level(level_config)
        self.x = SCREEN_WIDTH / 2
        self.y = SCREEN_WIDTH / 2 - 100
        self.z = 0.0
    def update_level(self, level_config):
        self.name = level_config["name"] #from config
        self.mass = level_config["mass"]
        self.event_horizon = level_config["event_horizon"]
        self.description = level_config["description"]
class Spaceship:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        self.vx = 0.0
        self.vy = 0.0
        self.vz = 0.0
        self.trail = []
        self.is_launched = False
        self.crashed = False
        self.vertices, self.faces = self.load_stl("spaceship.stl")

    def load_stl(self, filename):
        vertices = [] # this is a import of spaceship 3d model
        faces = []
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                for line in f:
                    if line.startswith('v'):
                        parts = line.split()
                        vertices.append([float(parts[1]) * 15, float(parts[2]) * 15, float(parts[3]) * 15])
                    elif line.startswith('f'):
                        parts = line.split()
                        face = [int(p.split('/')[0]) - 1 for p in parts[1:]]
                        faces.append(face)
            print(f"ok 3d model : {filename} ({len(vertices)} vetices)")
        else: #tis for no crahes if no 3d file found
            vertices = [
                [0, -15, 0],
                [-10, 10, -5],
                [10, 10, -5],
                [0, 5, 10]
            ]
            faces = [
                [0, 1, 3],
                [0, 3, 2],
                [0, 2, 1],
                [1, 2, 3]
            ]
        return vertices, faces
        
    def reset(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        self.vx = 0.0
        self.vy = 0.0
        self.vz = 0.0
        self.trail.clear()
        self.is_launched = False
        self.crashed = False

def project_3d_to_2d(x, y, z, camera_rot_x, camera_rot_y): #camera settings
    cx, cy, cz = SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 100, 0
    dx = x - cx
    dy = y - cy
    dz = z - cz
    rad_y = math.radians(camera_rot_y)
    cos_y, sin_y = math.cos(rad_y), math.sin(rad_y)
    x1 = dx * cos_y - dz * sin_y
    z1 = dx * sin_y + dz * cos_y

    rad_x = math.radians(camera_rot_x)
    cos_x, sin_x = math.cos(rad_x), math.sin(rad_x)
    y2 = dx * cos_y - dz * sin_x
    z2 = dx * sin_y + dz * cos_x
    fov = 600.0
    scale = fov / (fov + z2 + 300)

    screen_x = cx + x1 * scale
    screen_y = cy + y2 * scale

def play_spaghetificaton_video():
    video_path = "video.mp4"
    if os.path.exists(video_path):
        cap = cv2.VideoCapture(video_path)
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.resize(frame, (SCREEN_WIDTH, SCREEN_HEIGHT))
            cv2.imsḥow("EVENT HORIZON", frame)
            if cv2.waitKey(30) & 0xFF == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()

def main():
    current_level = 1
    bh = BlackHole(LEVELS[current_level])
    ship = Spaceship(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 300, 0)
    cam_rot_x = 25
    cam_rot_y = 0
    is_dragging = False
    drag_start = (0, 0)
    drag_end = (0, 0)

    running = True
    while running:
        for event in pygame.event.get(): #lets get to mousebuttons and all keys pressed statements
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_UP:
                    current_level = min(3, current_level + 1)
                    bh.update_level(LEVELS[current_level])
                    ship.reset(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 300, 0)
                elif event.key == pygame.K_r:
                    ship.reset(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 300, 0)
            elif event.type == pygame.MOUSEBUTTONDOWN and not ship.is_launched:
                is_dragging = True
                drag_start = event.pos
                drag_end = event.pos
            elif event.type == pygame.MOUSEMOTION and is_dragging:
                drag_end = event.pos
            elif event.type == pygame.MOUSEBUTTONUP and is_dragging:
                is_dragging = False
                dx = drag_end[0] - drag_start[0]
                dy = drag_end[1] - drag_start[1]
                ship.vx = dx * 0.05
                ship.vy = dx * 0.05
                ship.vz = 0
                ship.is_launched = True

        if ship.is_launched and not ship.crashed:
            rx = bh.x - ship.x
            ry = bh.y - ship.y
            rz = bh.z - ship.z 
            dist_sq = rx**2 + ry**2 + rz**2 + 100
            dist = math.sqrt(dist_sq)

            if dist < bh.event_horizon:
                ship.crashed = True
                play_spaghetificaton_video()#now some education ingame
            else:
                








    





