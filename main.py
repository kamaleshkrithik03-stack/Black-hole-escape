import os
import math
import sys
import cv2
import struct
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
        self.mass = 1.0
        self.trail = []
        self.is_launched = False
        self.crashed = False
        self.vertices, self.faces = self.load_stl("spaceship.stl")

def load_stl(self, filename):
        vertices = [] # this is a import of spaceship 3d model
        faces = []
        if os.path.exists(filename):
            file_size = os.path.getsize(filename)
            with open(filename, 'rb') as f:
                header = f.read(80)
                count_bytes = f.read(4)
                if len(count_bytes) == 4:
                    tri_count = struct.unpack('<I', count_bytes)[0]
                    if file_size == 84 + tri_count * 50:
                        for _ in range(tri_count):
                            tri_data = f.read(50)
                            if len(tri_data) < 50:
                                break
                            vals = struct.unpack('<12fH', tri_data)
                            v1 = [vals[3] * 15, vals[4] * 15, vals[5] * 15]
                            v2 = [vals[6] * 15, vals[7] * 15, vals[8] * 15]
                            v3 = [vals[9] * 15, vals[10] * 15, vals[11] * 15]
                            idx = len(vertices)
                            vertices.extend([v1, v2, v3])
                            faces.append([idx, idx + 1, idx + 2])
                        print(f"ok 3d model : {filename} ({len(vertices)} vetices)")
                        return vertices, faces

            with open(filename, 'r', errors='ignore') as f:
                tri_verts = []
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 4 and parts[0].lower() == 'vertex':
                        tri_verts.append([float(parts[1]) * 15, float(parts[2]) * 15, float(parts[3]) * 15])
                        if len(tri_verts) == 3:
                            idx = len(vertices)
                            vertices.extend(tri_verts)
                            faces.append([idx, idx + 1, idx + 2])
                            tri_verts = []
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
    y2 = dx * cos_y - z1 * sin_x
    z2 = dx * sin_y + z2 * cos_x
    fov = 600.0
    scale = fov / (fov + z2 + 300)

    screen_x = cx + x1 * scale
    screen_y = cy + y2 * scale
    return screen_x, screen_y, scale

def play_spaghetificaton_video():
    video_path = "video.mp4"
    if os.path.exists(video_path):
        cap = cv2.VideoCapture(video_path)
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.resize(frame, (SCREEN_WIDTH, SCREEN_HEIGHT))
            cv2.imshow("EVENT HORIZON", frame)
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
                elif event.key == pygame.K_DOWN:
                    current_level = max(3, current_level - 1)
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
                force = (G * ship.mass * bh.mass) / dist_sq
                accel_scale = 10**-12
                ax = (rx / dist) * (force / ship.mass) * accel_scale
                ay = (ry / dist) * (force / ship.mass) * accel_scale
                az = (rz / dist) * (force / ship.mass) * accel_scale
                ship.vx += ax
                ship.vy += ay
                ship.vz += az
                ship.x += ship.vx
                ship.y += ship.vy
                ship.z += ship.vz
                ship.trail.append((ship.x, ship.y, ship.z))
                if len(ship.trail) > 150:
                    ship.trail.pop(0)

        screen.fill(COLOR_BG)
        grid_spacing = 80
        for gx in range(0, SCREEN_WIDTH + 1, grid_spacing):
            points = []
            for gy in range(0, SCREEN_HEIGHT + 1, 30):
                dx = gx - bh.x
                dy = gy - bh.y
                d = math.sqrt(dx**2 + dy**2)
                warp_z = 0
                if 20 < d < 400:
                    warp_z = -min(80, 2000 / d)
                px, py, _ = project_3d_to_2d(gx, gy, warp_z, cam_rot_x, cam_rot_y)
                points.append((px, py))
            if len(points) > 1:
                pygame.draw.lines(screen, COLOR_GRID, False, points, 1)
        for gy in range(0, SCREEN_HEIGHT + 1, grid_spacing):
            points = []
            for gx in range(0, SCREEN_WIDTH + 1, 30):
                dx = gx - bh.x
                dy = gy - bh.y
                d = math.sqrt(dx**2 + dy**2)
                warp_z = 0
                if 20 < d < 400:
                    warp_z = -min(80, 2000 / d)
                px, py, _ = project_3d_to_2d(gx, gy, warp_z, cam_rot_x, cam_rot_y)
                points.append((px, py))
            if len(points) > 1:
                pygame.draw.lines(screen, COLOR_GRID, False, points, 1)
        bh_px, bh_py, bh_scale = project_3d_to_2d(bh.x, bh.y, bh.z, cam_rot_x, cam_rot_y)
        bh_radius = int(bh.event_horizon * bh_scale)
        accretion_radius = int(bh_radius * 1.6)
        pygame.draw.ellipse(screen, COLOR_ACCRETION,#renders of black hole
                            (bh_px - accretion_radius, bh_py - int(accretion_radius * 0.5),
                             accretion_radius * 2, accretion_radius), 3)
        pygame.draw.circle(screen, COLOR_BH, (int(bh_px), int(bh_py)), bh_radius)
        pygame.draw.circle(screen, (200, 100, 0), (int(bh_px), int(bh_py)), bh_radius)

        if len(ship.trail) > 1:
            trail_points = [project_3d_to_2d(tx, ty, tz, cam_rot_x, cam_rot_y)[:2] for tx, ty, tz in ship.trail] #used ail forthis idk bout doing the trail bit of the ship
            pygame.draw.lines(screen, (100, 150, 255), False, trail_points, 2)

        projected_vertices = []
        for vx, vy, vz in ship.vertices:
            world_x = ship.x + vx #not earth lol
            world_y = ship.y + vy
            world_z = ship.z + vz
            px, py, _ = project_3d_to_2d(world_x, world_y, world_z, cam_rot_x, cam_rot_y)
            projected_vertices.append((px, py))
        for face in ship.faces:
            face_points = [projected_vertices[i] for i in face]
            pygame.draw.polygon(screen, COLOR_SHIP, face_points, 1)
        if is_dragging:
            pygame.draw.line(screen, (255, 255, 255), drag_start, drag_end, 2)
            pygame.draw.circle(screen, (255, 255, 255), drag_start, 6, 1)
        ui_rect = pygame.Rect(20, 20, 760, 90)
        pygame.draw.rect(screen, (20, 22, 30), ui_rect, border_radius=10)
        pygame.draw.rect(screen, (60, 60, 90), ui_rect, 1, border_radius=10)

        title_surf = title_font.render(bh.name, True, COLOR_TEXT)
        desc_surf = font.render(bh.description, True, (160, 175, 195))
        controls_surf = font.render("drag it for launch and up/down for level switch[r] for reset", True, (120, 140, 170))
        screen.blit(title_surf, (35, 30))
        screen.blit(desc_surf, (35, 55))
        screen.blit(controls_surf, (35, 80))

        if ship.crashed:
            crash_surf = title_font.render("you FAILURE- cant do basic phy huhh?", True, (255, 50 ,50))
            screen.blit(crash_surf, (SCREEN_WIDTH / 2 - 230, SCREEN_HEIGHT / 2 + 120))
        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()
    sys.exit()
if __name__ == "__main__":
    main()
















    





