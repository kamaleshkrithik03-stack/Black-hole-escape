import os
import math
import sys
import cv2
import struct
import pygame
from config import *

pygame.init()
pygame.mixer.init()

SIDE_PANEL_WIDTH = 320
screen = pygame.display.set_mode((SCREEN_WIDTH + SIDE_PANEL_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Black hole sim ig")
clock = pygame.time.Clock()

font = pygame.font.SysFont("Orbitron", 16)
small_font = pygame.font.SysFont("Orbitron", 14)
title_font = pygame.font.SysFont("Orbitron", 20, bold=True)

if os.path.exists("interstellar.mp3"):
    pygame.mixer.music.load("interstellar.mp3")
    pygame.mixer.music.play(-1)
    pygame.mixer.music.set_volume(0.6)
else:
    print("The music is not found so go and download intersteallar.mp3")

def normalize_mesh(vertices, target_radius):
    if not vertices:
        return vertices
    xs = [v[0] for v in vertices]
    ys = [v[1] for v in vertices]
    zs = [v[2] for v in vertices]
    cx = 0.5 * (min(xs) + max(xs))
    cy = 0.5 * (min(ys) + max(ys))
    cz = 0.5 * (min(zs) + max(zs))
    max_extent = max(max(xs) - min(xs), max(ys) - min(zs) - min(zs), 10**-6)
    scale = (target_radius * 2) / max_extent
    return [[(v[0] - cx) * scale, (v[1] - cy) * scale, (v[2] - cz) * scale] for v in vertices]
def load_stl(filename, target_radius, max_faces=800):
    vertices = []
    faces = []
    if os.path.exists(filename):
        file_size = os.path.getsize(filename)
        with open(filename, 'rb') as f:
            header = f.read(80)
            count_bytes = f.read(4)
            if len(count_bytes) == 4:
                tri_count = struct.unpack('<I', count_bytes)[0]
                if file_size == 84 + tri_count * 50:
                    step = max(1, tri_count // max_faces)
                    for i in range(0, tri_count, step):
                        f.seek(84 + i * 50)
                        tri_data = f.read(50)
                        if len(tri_data) < 50:
                            break
                        vals = struct.unpack('<12fH', tri_data) #after lots of research and back breakers
                        v1 = [vals[3], vals[4], vals[5]]
                        v2 = [vals[6], vals[7], vals[8]]
                        v3 = [vals[9], vals[10], vals[11]]
                        idx = len(vertices)
                        vertices.extend([v1, v2, v3])
                        faces.append([idx, idx + 1, idx + 2])
                    return normalize_mesh(vertices, target_radius), faces
        with open(filename, 'r', errors='ignore') as f:
            tri_verts = []
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 4 and parts[0].lower() == 'vertex':
                    tri_verts.append([float(parts[1]), float(parts[2]), float(parts[3])])
                    if len(tri_verts) == 3:
                        if len(faces) < max_faces:
                            idx = len(vertices)
                            vertices.extend(tri_verts)
                            faces.append([idx, idx + 1, idx + 2])
                        tri_verts = []
        return normalize_mesh(vertices, target_radius), faces

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
                                                
class BlackHole:
    def __init__(self, level_config):
        self.update_level(level_config)
        self.x = 0
        self.y = 0
        self.z = 0
        self.stl_vertices, self.stl_faces = load_stl("blackhole.stl", target_radius=45, max_faces=700)
        self.sprite = None
        for ext in ("blackhole.png", "blackhole.jpg", "blackhole.JPG"):
            if os.path.exists(ext):
                self.sprite = pygame.image.load(ext).convert_alpha()
                break

    def update_level(self, level_config):
        self.name = level_config["name"] #from config
        self.mass = level_config["mass"]
        self.event_horizon = level_config["event_horizon"]
        self.description = level_config["description"]
    @property
    def mu(self):
        return 18000.0 * (self.event_horizon / 25.0)
class Spaceship:
    def __init__(self, x, y, z, mass=100.0, fuel=120):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.vx = 3.2
        self.vy = -0.6
        self.vz = 0.0
        self.mass = float(mass)
        self.fuel = float(fuel)
        self.trail = []
        self.is_launched = False
        self.crashed = False
        self.vertices, self.faces = self.load_stl("spaceship.stl", target_radius=18, max_faces=1000)
    def reset(self, x, y, z, mass=None, fuel=None):
        if mass is not None:
            self.mass = max(1.0, float(mass))
        if fuel is not None:
            self.fuel = max(0.0, float(fuel))
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.vx = 3.2
        self.vy = -0.6
        self.vz = 0
        self.trail.clear()
        self.crashed = False
        self.escaped = False
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

def project_3d_to_2d(x, y, z, camera_rot_x, camera_rot_y, cam_x=0, cam_y=0): #camera settings
    cx, cy, = SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2
    dx = x - cam_x
    dy = y - cam_y
    dz = z 
    rad_y = math.radians(camera_rot_y)
    cos_y, sin_y = math.cos(rad_y), math.sin(rad_y)
    x1 = dx * cos_y - dz * sin_y
    z1 = dx * sin_y + dz * cos_y

    rad_x = math.radians(camera_rot_x)
    cos_x, sin_x = math.cos(rad_x), math.sin(rad_x)
    y2 = dy * cos_x - z1 * sin_x
    z2 = dy * sin_x + z1 * cos_x
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

class InputBox:
    def __init__(self, rect, label, default_text):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.text = default_text
        self.active = False
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        elif event.unicode.isdigit() or event.unicode == ".":
            if event.unicode != "." or "." not in self.text:
                self.text += event.unicode
    def value(self, fallback):
        try:
            val = float(self.text)
            return val if val > 0 else fallback
        except ValueError:
            return fallback
    def draw(self, surface):
        surface.blit(small_font.render(self.label, True, (170, 185, 210)), (self.rect.x, self.rect.y - 20)) #used ai in the def(copy paste no worries) and also i used it only for the specific numbers 
        border_col = (90, 170, 255) if self.active else (70, 80, 105)
        pygame.draw.rect(surface, (28, 32, 44), self.rect, border_radius=6)
        pygame.draw.rect(surface, border_col, self.rect, 2, border_radius=6)
        surface.blit(font.render(self.text or "0", True, COLOR_TEXT), (self.rect.x + 10, self.rect.y + 7))
def predict_path(ship, bh, steps=160): #for the trajectory
    px, py, pz = ship.x, ship.y, ship.z
    vx, vy, vz = ship.vx, ship.vy, ship. vz
    path = []
    for _ in range(steps):
        rx = bh.x - px
        ry = bh.y - py
        rz = bh.z - pz
        dist_sq = rx * rx + ry * ry + rz * rz + 1
        dist = math.sqrt(dist_sq)
        if dist < bh.event_horizon:
            break
        accel = bh.mu / dist_sq
        vx += (rx / dist) * accel
        vy += (ry / dist) * accel
        vz += (rz / dist) * accel
        px += vx
        py += vy
        pz += vz
        path.append((px, py, pz))
        if dist > 1400:
            break
    return path
def main():
    current_level = 1
    bh = BlackHole(LEVELS[current_level])
    fuel_box = InputBox((SCREEN_WIDTH + 24, 155, 270, 36), "Fuel", "120")
    mass_box = InputBox((SCREEN_WIDTH + 24, 230, 270, 36), "ship weight or mass", "100")
    apply_btn = pygame.Rect(SCREEN_WIDTH + 24, 282, 270, 36)

    ship = Spaceship(0.0, 210, 0.0, mass=mass_box.value(100), fuel=fuel_box.value(120))
    cam_rot_x = 22
    cam_rot_y = 0
    cam_x = ship.x
    cam_y = ship.y * 0.5

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            fuel_box.handle_event(event)
            mass_box.handle_event(event)

            
    pygame.quit()
    sys.exit()
if __name__ == "__main__":
    main()
















    





