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
    max_extent = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs), 10**-6)
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
        if os.path.exists("blackhole.stl"):
            self.stl_vertices, self.stl_faces = load_stl("blackhole.stl", target_radius=45, max_faces=700)
        else:
            self.stl_vertices, self.stl_faces = [], []
        self.sprite = None
        for ext in ("blackhole.jpeg", "blackhole.jpg", "blackhole.png", "blackhole.JPG"): #i made it so that any file type can be accepted:)
            if os.path.exists(ext):
                self.sprite = pygame.image.load(ext).convert()
                break

    def update_level(self, level_config):
        self.name = level_config["name"]
        self.mass = level_config["mass"]
        self.event_horizon = level_config["event_horizon"]
        self.description = level_config["description"]
    @property
    def mu(self):
        return 18000 * (self.event_horizon / 25)

class Spaceship:
    def __init__(self, x, y, z, mass=100, fuel=120):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.vx = 0.0
        self.vy = 0.0
        self.vz = 0.0
        self.mass = float(mass)
        self.fuel = float(fuel)
        self.trail = []
        self.is_launched = False
        self.crashed = False
        self.escaped = False
        self.vertices, self.faces = load_stl("spaceship.stl", target_radius=90, max_faces=1000)

    def reset(self, x, y, z, mass=None, fuel=None):
        if mass is not None:
            self.mass = max(1.0, float(mass))
        if fuel is not None:
            self.fuel = max(0.0, float(fuel))
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.vx = 0.0
        self.vy = 0.0
        self.vz = 0.0
        self.trail.clear()
        self.is_launched = True
        self.crashed = False
        self.escaped = False

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
        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
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

            if event.type == pygame.MOUSEBUTTONDOWN and apply_btn.collidepoint(event.pos):
                ship.reset(0.0, 210.0, 0.0, mass=mass_box.value(100), fuel=fuel_box.value(120))
                cam_x = ship.x
                cam_y = ship.y * 0.5
            elif event.type == pygame.KEYDOWN:
                if fuel_box.active or mass_box.active:
                    if event.key == pygame.K_RETURN:
                        fuel_box.active = False
                        mass_box.active = False
                    continue
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_UP:
                    current_level = min(3, current_level + 1)
                    bh.update_level(LEVELS[current_level])
                    ship.reset(0.0, 210.0, 0.0, mass=mass_box.value(100), fuel=fuel_box.value(120))
                elif event.key == pygame.K_DOWN:
                    current_level = max(1, current_level - 1)
                    bh.update_level(LEVELS[current_level])
                    ship.reset(0.0, 210.0, 0.0, mass=mass_box.value(100), fuel=fuel_box.value(120))
                elif event.key == pygame.K_r:
                    ship.reset(0, 210, 0, mass=mass_box.value(100), fuel=fuel_box.value(120))

        keys = pygame.key.get_pressed()
        thruster_fired = False
        thrust_power = 0.0
        if not (fuel_box.active or mass_box.active) and not ship.crashed:
            if keys[pygame.K_w] and ship.fuel > 0:
                thruster_fired = True
                thrust_power = 26.0
                ship.fuel = max(0, ship.fuel - 0.8)
            elif keys[pygame.K_s] and ship.fuel > 0:
                thruster_fired = True
                thrust_power = 18
                ship.fuel = max(0.0, ship.fuel - 0.6)
        rx = bh.x - ship.x
        ry = bh.y - ship.y
        rz = bh.z - ship.z
        dist_sq = rx * rx + ry * ry + rz * rz + 1
        dist = math.sqrt(dist_sq)
        speed = math.hypot(ship.vx, ship.vy)
        esc_vel = math.sqrt((2.0 * bh.mu) / max(1.0, dist))
        if speed >= esc_vel:
            ship.escaped = True
        if not ship.crashed:
            grav_accel = bh.mu / dist_sq
            ax = (rx / dist) * grav_accel
            ay = (ry / dist) * grav_accel
            az = (rz / dist) * grav_accel

            if thruster_fired:
                out_x = -rx / dist
                out_y = -ry / dist
                tan_x = -out_y if keys[pygame.K_w] else out_y
                tan_y = out_x if keys[pygame.K_w] else -out_x
                thrust_accel = thrust_power / max(1.0, ship.mass)
                ax += (out_x * 0.85 + tan_x * 0.55) * thrust_accel
                ay += (out_y * 0.85 + tan_y * 0.55) * thrust_accel
            ship.vx += ax
            ship.vy += ay
            ship.vz += az
            ship.x += ship.vx
            ship.y += ship.vy
            ship.z += ship.vz

            if thruster_fired and dist <= bh.event_horizon + 8.0:
                 safe_dist = bh.event_horizon + 10
                 ship.x = bh.x - (rx / dist) * safe_dist
                 ship.y = bh.y - (ry / dist) * safe_dist
                 ship.vx = max(ship.vx, -rx / dist * 2.5)
                 ship.vy = max(ship.vy, -ry / dist * 2.5)
            elif not thruster_fired and dist < bh.event_horizon:
                ship.crashed = True
                play_spaghetificaton_video()
            ship.trail.append((ship.x, ship.y, ship.z))
            if len(ship.trail) > 220:
                ship.trail.pop(0)



        cam_x += ((ship.x * 0.75 + bh.x * 0.25) - cam_x) * 0.08
        cam_y += ((ship.y * 0.75 + bh.y * 0.25) - cam_y) * 0.08

        screen.fill(COLOR_BG)
        grid_spacing = 120
        for gx in range(-600, 601, grid_spacing):
            points = []
            for gy in range(-600, 601, 40):
                d = math.hypot(gx - bh.x, gy - bh.y)
                warp_z = -min(70, 3500 / max(15, d)) if d < 420 else 0
                px, py, _ = project_3d_to_2d(gx, gy, warp_z, cam_rot_x, cam_rot_y, cam_x, cam_y)
                points.append((px, py))
            if len(points) > 1:
                pygame.draw.lines(screen, COLOR_GRID, False, points, 1)

        bh_px, bh_py, bh_scale = project_3d_to_2d(bh.x, bh.y, bh.z, cam_rot_x, cam_rot_y, cam_x, cam_y)
        bh_radius = max(24, int(bh.event_horizon * bh_scale * 1.6))
        if bh.sprite is not None:
            size = max(160, bh_radius * 6)
            scaled_sprite = pygame.transform.smoothscale(bh.sprite, (size, size))
            screen.blit(scaled_sprite, (int(bh_px - size / 2), int(bh_py - size / 2)))
        elif bh.stl_vertices and bh.stl_faces:
            bh_proj = [
                project_3d_to_2d(bh.x + vx * 2, bh.y + vy * 2, bh.z + vz * 2, cam_rot_x, cam_rot_y, cam_x, cam_y)[:2]
                for vx, vy, vz in bh.stl_vertices
            ]
            for face in bh.stl_faces:
                pygame.draw.polygon(screen, COLOR_ACCRETION, [bh_proj[i] for i in face], 1)
        else:
            accretion_radius = int(bh_radius * 2.2)
            pygame.draw.ellipse(
                screen,
                COLOR_ACCRETION,
                (bh_px - accretion_radius, bh_py - int(accretion_radius * 0.45), accretion_radius * 2, accretion_radius),
                3,
            )
            pygame.draw.circle(screen, COLOR_BH, (int(bh_px), int(bh_py)), bh_radius)
            pygame.draw.circle(screen, (200, 100, 0), (int(bh_px), int(bh_py)), bh_radius, 2)
            

        pred_pts = [
            project_3d_to_2d(px, py, pz, cam_rot_x, cam_rot_y, cam_x, cam_y)[:2]
            for px, py, pz in predict_path(ship, bh)
        ]
        if len(pred_pts) > 1:
            pygame.draw.lines(screen, (90, 230, 170), False, pred_pts, 2)

        if len(ship.trail) > 1:
            trail_points = [
                project_3d_to_2d(tx, ty, tz, cam_rot_x, cam_rot_y, cam_x, cam_y)[:2]
                for tx, ty, tz in ship.trail
            ]
            pygame.draw.lines(screen, (100, 150, 255), False, trail_points, 2)

        projected_vertices = []
        for vx, vy, vz in ship.vertices:
            px, py, _ = project_3d_to_2d(ship.x + vx, ship.y + vy, ship.z + vz, cam_rot_x, cam_rot_y, cam_x, cam_y)
            projected_vertices.append((px, py))
        for face in ship.faces:
            pygame.draw.polygon(screen, COLOR_SHIP, [projected_vertices[i] for i in face], 1)

        panel_rect = pygame.Rect(SCREEN_WIDTH, 0, SIDE_PANEL_WIDTH, SCREEN_HEIGHT)
        pygame.draw.rect(screen, (18, 21, 30), panel_rect)
        pygame.draw.line(screen, (60, 72, 98), (SCREEN_WIDTH, 0), (SCREEN_WIDTH, SCREEN_HEIGHT), 2)
        screen.blit(title_font.render("Mission config", True, COLOR_TEXT), (SCREEN_WIDTH + 24, 24))
        screen.blit(small_font.render(bh.name, True, (150, 180, 230)), (SCREEN_WIDTH + 24, 58))
        screen.blit(small_font.render("[up/down-level]  |  [r-reset obiously]", True, (130, 145, 170)), (SCREEN_WIDTH + 24, 86))
        screen.blit(small_font.render("[w/s thrustcontrols]", True, (130, 145, 170)), (SCREEN_WIDTH + 24, 110))

        fuel_box.draw(screen)
        mass_box.draw(screen)
        pygame.draw.rect(screen, (45, 110, 195), apply_btn, border_radius=6)
        screen.blit(font.render("apply and ze launch ship", True, COLOR_TEXT), (apply_btn.x + 48, apply_btn.y + 7))

        y_info = 345
        for line in [
            f"fuel left: {ship.fuel:.1f}",
            f"mass: {ship.mass:.1f}",
            f"speed: {speed:.2f}",
            f"escape vel: {esc_vel:.2f}",
            f"distance: {dist:.1f}",
        ]:
            screen.blit(small_font.render(line, True, (190, 200, 220)), (SCREEN_WIDTH + 24, y_info))
            y_info += 26

        if ship.crashed:
            status_txt, status_col = "event horizon is breached", (255, 65, 65)
        elif ship.escaped:
            status_txt, status_col = "escape vel  passed-good", (80, 240, 150)
        else:
            status_txt, status_col = "in gravity well of bh", (245, 190, 70)
        screen.blit(font.render(status_txt, True, status_col), (SCREEN_WIDTH + 24, y_info + 12))
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()
if __name__ == "__main__":
    main()
















    





