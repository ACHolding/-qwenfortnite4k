import pygame
import math
import sys
import random

# --- Engine Initialization ---
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Python 3D Software Render Engine (60 FPS Target)")
clock = pygame.time.Clock()

# --- Camera Settings ---
cam_pos = [0, 2, -5]  # X, Y, Z position
cam_rot = [0, 0]      # Pitch (X), Yaw (Y)
mouse_sensitivity = 0.2
move_speed = 0.15

# --- 3D Math Functions ---
def rotate_point(p, rx, ry):
    """Rotates a 3D point around the Y (yaw) and X (pitch) axes."""
    # Yaw (Y-axis)
    rady = math.radians(ry)
    x = p[0] * math.cos(rady) - p[2] * math.sin(rady)
    z = p[0] * math.sin(rady) + p[2] * math.cos(rady)
    y = p[1]
    
    # Pitch (X-axis)
    radx = math.radians(rx)
    y2 = y * math.cos(radx) - z * math.sin(radx)
    z2 = y * math.sin(radx) + z * math.cos(radx)
    return [x, y2, z2]

def project(p):
    """Projects a 3D point to 2D screen coordinates using perspective division."""
    fov = 500
    z = p[2] if p[2] > 0.1 else 0.1  # Prevent division by zero / near-plane clipping
    factor = fov / z
    return [int(p[0] * factor + WIDTH / 2), int(-p[1] * factor + HEIGHT / 2)]

# --- World Generation (Voxel/Block System) ---
def create_cube(x, y, z, size=1, color=(100, 100, 100)):
    """Generates the vertices and polygon faces for a 3D cube."""
    s = size / 2
    v = [
        [x-s, y-s, z-s], [x+s, y-s, z-s], [x+s, y+s, z-s], [x-s, y+s, z-s],
        [x-s, y-s, z+s], [x+s, y-s, z+s], [x+s, y+s, z+s], [x-s, y+s, z+s]
    ]
    # 6 Faces (ordered indices of vertices)
    faces = [
        ([4, 5, 6, 7], color), # Back
        ([0, 1, 5, 4], color), # Bottom
        ([3, 2, 6, 7], color), # Top
        ([0, 3, 7, 4], color), # Left
        ([1, 2, 6, 5], color), # Right
        ([0, 1, 2, 3], color)  # Front
    ]
    return {'v': v, 'f': faces}

random.seed(42) # Consistent map generation
cubes = []

# Generate terrain and objects
for x in range(-15, 16):
    for z in range(-5, 35):
        # Grass floor
        cubes.append(create_cube(x, 0, z, color=(34, 139, 34)))
        
        # Random Trees
        if random.random() < 0.04 and x != 0 and z > 2:
            for y in range(1, 5): cubes.append(create_cube(x, y, z, color=(101, 67, 33)))
            for tx in range(-1, 2):
                for tz in range(-1, 2):
                    for ty in range(4, 7):
                        if abs(tx) + abs(tz) + abs(ty-5) < 3:
                            cubes.append(create_cube(x+tx, ty, z+tz, color=(0, 100, 0)))
                            
        # Random "Fortnite" Structures
        if random.random() < 0.02 and x > 0 and z > 5:
            for y in range(1, 4):
                for bx in range(0, 3):
                    for bz in range(0, 3):
                        if bx == 0 or bx == 2 or bz == 0 or bz == 2: # Walls
                            if not (y == 2 and bx == 1 and bz == 0): # Doorway
                                cubes.append(create_cube(x+bx, y, z+bz, color=(150, 150, 150)))

# Add a "loot" pile
for i in range(5):
    cubes.append(create_cube(0, i+1, 5, color=(200, 200, 50)))

# --- Mouse Capture Setup ---
pygame.event.set_grab(True)
pygame.mouse.set_visible(False)

font = pygame.font.SysFont("Arial", 18)
running = True

# --- Main Game Loop ---
while running:
    # 1. Frame Timing (60 FPS Lock)
    dt = clock.tick(60) / 1000.0
    
    # 2. Event Handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False

    # 3. Mouse Look (Pitch/Yaw)
    mx, my = pygame.mouse.get_rel()
    cam_rot[1] -= mx * mouse_sensitivity
    cam_rot[0] -= my * mouse_sensitivity
    cam_rot[0] = max(-89, min(89, cam_rot[0])) # Clamp vertical look

    # 4. Keyboard Movement (WASD + Fly)
    keys = pygame.key.get_pressed()
    move = [0, 0, 0]
    if keys[pygame.K_w]: move[2] += move_speed
    if keys[pygame.K_s]: move[2] -= move_speed
    if keys[pygame.K_a]: move[0] -= move_speed
    if keys[pygame.K_d]: move[0] += move_speed
    if keys[pygame.K_SPACE]: move[1] += move_speed
    if keys[pygame.K_LSHIFT]: move[1] -= move_speed

    # Apply Yaw rotation to movement vector
    rady = math.radians(cam_rot[1])
    cam_pos[0] += move[0] * math.cos(rady) + move[2] * math.sin(rady)
    cam_pos[2] += -move[0] * math.sin(rady) + move[2] * math.cos(rady)
    cam_pos[1] += move[1]

    # 5. 3D Rendering Pipeline
    screen.fill((135, 206, 235)) # Sky Blue
    faces_to_draw = []

    for c in cubes:
        # Translate vertices relative to camera
        tv = [[v[0]-cam_pos[0], v[1]-cam_pos[1], v[2]-cam_pos[2]] for v in c['v']]
        # Rotate vertices
        rv = [rotate_point(p, cam_rot[0], cam_rot[1]) for p in tv]
        
        # Process faces
        for idx, color in c['f']:
            fv = [rv[i] for i in idx]
            # Near-plane clipping (only draw if all vertices are in front of camera)
            if all(p[2] > 0.1 for p in fv):
                # Calculate average depth for sorting
                avg_z = sum(p[2] for p in fv) / 4
                points_2d = [project(p) for p in fv]
                faces_to_draw.append((avg_z, points_2d, color))

    # Painter's Algorithm: Sort faces back-to-front based on Z-depth
    faces_to_draw.sort(key=lambda x: x[0], reverse=True)
    
    # Draw Polygons
    for _, pts, col in faces_to_draw:
        pygame.draw.polygon(screen, col, pts)
        pygame.draw.polygon(screen, (0,0,0), pts, 1) # Black outline for 3D definition

    # 6. 2D UI Overlay
    fps_txt = font.render(f"FPS: {int(clock.get_fps())} | Pure Math 3D Render", True, (255,255,255))
    ctrl_txt = font.render("WASD: Move | Space/Shift: Fly | Mouse: Look | ESC: Quit", True, (255,255,255))
    
    # Crosshair
    pygame.draw.line(screen, (255,255,255), (WIDTH//2-10, HEIGHT//2), (WIDTH//2+10, HEIGHT//2), 2)
    pygame.draw.line(screen, (255,255,255), (WIDTH//2, HEIGHT//2-10), (WIDTH//2, HEIGHT//2+10), 2)
    
    # Fortnite-style Material UI
    mat_font = pygame.font.SysFont("Arial", 14)
    pygame.draw.rect(screen, (50,50,50), (10, HEIGHT-50, 300, 40))
    pygame.draw.rect(screen, (139,69,19), (20, HEIGHT-40, 20, 20)) # Wood
    pygame.draw.rect(screen, (150,150,150), (60, HEIGHT-40, 20, 20)) # Stone
    pygame.draw.rect(screen, (50,50,255), (100, HEIGHT-40, 20, 20)) # Metal
    
    screen.blit(fps_txt, (10, 10))
    screen.blit(ctrl_txt, (10, 35))
    screen.blit(mat_font.render("Wood: 342", True, (255,255,255)), (45, HEIGHT-38))
    screen.blit(mat_font.render("Stone: 128", True, (255,255,255)), (85, HEIGHT-38))
    screen.blit(mat_font.render("Metal: 44", True, (255,255,255)), (125, HEIGHT-38))

    # Update Display
    pygame.display.flip()

pygame.quit()
sys.exit()