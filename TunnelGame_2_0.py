import tkinter as tk
import random
import winsound
import threading

# === Nastavení ===
WIDTH = 600
HEIGHT = 400
TUNNEL_WIDTH = 80
STEP = 2
JEMNOST = 5

kutloch_RADIUS = 5
kutloch_SPEED = 4
REVERSE_BONUS = 1
LIVES_START = 5

# === Stav hry ===
tunnel = []
debris = []
balls = []  # [x, y, color, idx_tunnel_start]
ball_colors = ["yellow", "white", "cyan", "magenta"]
score = 0
lives = LIVES_START

dy = 0
center_y = HEIGHT // 2
for _ in range(WIDTH // STEP + 1):
    tunnel.append(center_y)

kutloch_x = WIDTH // 4
kutloch_y = center_y
kutloch_dead = False
explosion_timer = 0
paused = False
wait_for_restart = False
frame_count = 0
game_over = False

# Pro plochy
PLOCHAPODKOULI = 10 # od kdy považujeme opakování za rovinku
ROZBEH = 100 # iniciační část tunelu
plocha = 0 # zatím nevyužito
rovinka = 0      # kolikrát se new_y opakuje za sebou
last_new_y = None   # pamatuje předchozí hodnotu new_y

# Klávesy
keys = {"Up": False, "Down": False, "Left": False, "Right": False}
space_pressed = False

last_ball_idx = -PLOCHAPODKOULI

# === Vytvoření okna ===
root = tk.Tk()
canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="black")
canvas.pack()

# === Zvuk1 ===
def play_explosion():
    def _play():
        winsound.PlaySound("boom.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)
    threading.Thread(target=_play).start()

def generate_debris():
    global debris
    debris = []
    for _ in range(100):
        dx = random.randint(-8, 8)
        dy = random.randint(-8, 8)
        debris.append([kutloch_x, kutloch_y, dx, dy])
        
def update_debris():
    for d in debris:
        d[0] += d[2]
        d[1] += d[3]
        idx = int(d[0] // STEP)
        if 0 <= idx < len(tunnel):
            bottom = tunnel[idx] + TUNNEL_WIDTH // 2
            if d[1] < bottom:
                d[1] += 1

# === Zvuk2 ===
def play_explosion2():
    def _play():
        winsound.PlaySound("boom2.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)
    threading.Thread(target=_play).start()

# === Ovládání ===
def key_press(event):
    global space_pressed
    if event.keysym in keys:
        keys[event.keysym] = True
    if event.keysym == "space":
        space_pressed = True

def key_release(event):
    if event.keysym in keys:
        keys[event.keysym] = False
        
canvas.bind_all("<KeyPress>", key_press)
canvas.bind_all("<KeyRelease>", key_release)

# === Aktualizace tunelu ===
def update_tunnel():
    global dy, tunnel, score, new_y, rovinka
    global jetuplocha, last_new_y, plocha, balls

    tunnel.pop(0)
    if len(tunnel) < ROZBEH:
        new_y = center_y
    else:
        if random.random() < 5:
            dy += random.choice([-JEMNOST, 0, JEMNOST])
            dy = max(-5, min(5, dy))
        new_y = tunnel[-1] + dy
        new_y = max(40, min(350, new_y))
    tunnel.append(new_y)
    score += STEP

    # Detekce rovinek
    if new_y == last_new_y:
        rovinka += 1
    else:
        rovinka = 1
    last_new_y = new_y

    # Posun koulí doleva
    for ball in balls:
        ball[0] -= STEP  # Posun na ose X
        balls = [b for b in balls if b[0] > -10]




# === Generování objektů na rovné plošce ===
def detect_and_place_balls():
    global rovinka, balls

    if rovinka >= PLOCHAPODKOULI:
        print("Ploška nalezena, délka:", rovinka)
        rovinka = 0
        # Umístíme kouli do tunelu
        idx = len(tunnel) - 1  # Index posledního bodu tunelu (aktuální konec)
        x = WIDTH  # protože nová pozice je úplně vpravo
        y = tunnel[idx]
        color = random.choice(ball_colors)
        balls.append([x, y, color, idx])  # idx slouží jako referenční bod v tunelu

        
# === Pohyb raketky ===
def update_kutloch():
    global kutloch_x, kutloch_y
    if keys["Up"]:
        kutloch_y -= kutloch_SPEED
    if keys["Down"]:
        kutloch_y += kutloch_SPEED
    if keys["Left"]:
        kutloch_x -= (STEP + REVERSE_BONUS)
    if keys["Right"]:
        kutloch_x += kutloch_SPEED
    kutloch_x = max(0, min(WIDTH, kutloch_x))
    kutloch_y = max(0, min(HEIGHT, kutloch_y))

# === Kolize a sbírání koulí ===
def check_collision():
    idx = int(kutloch_x // STEP)
    if 0 <= idx < len(tunnel):
        center = tunnel[idx]
        top = center - TUNNEL_WIDTH // 2
        bottom = center + TUNNEL_WIDTH // 2
        if not (top < kutloch_y < bottom):
            return True
    return False

def collect_balls():
    global score
    to_remove = []
    for b in balls:
        bx, by, color, _ = b
        if (kutloch_x - kutloch_RADIUS) < bx < (kutloch_x + kutloch_RADIUS) and (kutloch_y - kutloch_RADIUS) < by < (kutloch_y + kutloch_RADIUS):
            to_remove.append(b)
            score += 50
    for b in to_remove:
        balls.remove(b)

# === Kreslení ===
def draw_tunnel():
    canvas.delete("all")
    canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="blue", outline="")

    for i in range(len(tunnel) - 1):
        x1 = i * STEP
        x2 = (i + 1) * STEP
        y1_top = tunnel[i] - TUNNEL_WIDTH // 2
        y2_top = tunnel[i + 1] - TUNNEL_WIDTH // 2
        y1_bot = tunnel[i] + TUNNEL_WIDTH // 2
        y2_bot = tunnel[i + 1] + TUNNEL_WIDTH // 2
        canvas.create_polygon(x1, y1_top, x2, y2_top, x2, y2_bot, x1, y1_bot, fill="black", outline="black")
            # Kreslení koulí
    for ball in balls:
        x, y, color, _ = ball
        canvas.create_oval(
            x - 4, y - 4,
            x + 4, y + 4,
            fill=color,
            outline="white"
        )


    if not kutloch_dead:
        canvas.create_oval(
            kutloch_x - kutloch_RADIUS, kutloch_y - kutloch_RADIUS,
            kutloch_x + kutloch_RADIUS, kutloch_y + kutloch_RADIUS,
            fill="red"
        )
    elif explosion_timer > 50:
        # fáze: "katastrofický posun dolů"
        idx = kutloch_x // STEP
        if 0 <= idx < len(tunnel):
            base_y = tunnel[idx] + TUNNEL_WIDTH // 2
            for i in range(8):
                offset_x = random.randint(-16, 16)
                offset_y = random.randint(-16, 16)
                canvas.create_oval(
                    kutloch_x + offset_x - 1, base_y + offset_y - 1,
                    kutloch_x + offset_x + 1, base_y + offset_y + 1,
                    fill="orange"
                )
    else:
        # fáze: "rozptýlení trosek"
        for d in debris:
            canvas.create_oval(
                d[0] - 1, d[1] - 1,
                d[0] + 1, d[1] + 1,
                fill="yellow"
            )

    for i in range(lives):
        canvas.create_oval(10 + i * 15, 10, 20 + i * 15, 20, fill="red", outline="white")

    canvas.create_text(WIDTH - 10, 15, text=f"Score: {score}", anchor="ne", fill="white", font=("Courier", 12, "bold"))
    canvas.create_text(WIDTH - 10, 380, text=f"New_y: {new_y}", anchor="ne", fill="red", font=("Courier", 12, "bold"))

# === Restart hry ===
def restart_game():
    global kutloch_x, kutloch_y, kutloch_dead, explosion_timer, tunnel, dy
    kutloch_x = WIDTH // 4
    kutloch_y = center_y
    dy = 0
    kutloch_dead = False
    explosion_timer = 0
#    score = 0
    tunnel = [center_y for _ in range(WIDTH // STEP + 1)]


# === Hlavní smyčka ===
def game_loop():
    global kutloch_dead, explosion_timer, lives, space_pressed, game_over, paused, wait_for_restart, frame_count, score

    frame_count += 1

    if game_over:
        draw_tunnel()
        canvas.create_text(WIDTH // 2, HEIGHT // 2, text="GAME OVER", fill="white", font=("Courier", 24, "bold"))
        canvas.create_text(WIDTH // 2, HEIGHT // 2 + 30, text="Stiskni SPACE pro nový pokus", fill="gray", font=("Courier", 14))
        score = 0
        if space_pressed:
            lives = LIVES_START
            restart_game()
            game_over = False
            space_pressed = False

    elif paused:
        draw_tunnel()

        # Ztmavení scény
#        canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#000000", stipple="gray50", outline="")

        # Blikající text
        if (frame_count // 20) % 2 == 0:
            canvas.create_text(550,350, text="PAUZA", fill="white", font=("Courier", 8, "bold"))
            canvas.create_text(550,370, text="Stiskni SPACE", fill="gray", font=("Courier", 8))

        if space_pressed:
            paused = False
            space_pressed = False

    elif wait_for_restart:
        draw_tunnel()
        canvas.create_text(WIDTH // 2, HEIGHT // 2, text="ZTRÁTA LODI!", fill="orange", font=("Courier", 24, "bold"))
        canvas.create_text(WIDTH // 2, HEIGHT // 2 + 30, text="SPACE = pokračuj", fill="gray", font=("Courier", 14))
        if space_pressed:
            restart_game()
            wait_for_restart = False
            space_pressed = False

    else:
        if space_pressed:
            paused = True
            space_pressed = False
        else:
            update_tunnel()
            
            detect_and_place_balls()

            if not kutloch_dead:
                update_kutloch()
                if check_collision():
                    kutloch_dead = True
                    explosion_timer = 100
                    lives -= 1
                    play_explosion()
            else:
                if explosion_timer == 70:
                    generate_debris()
                if explosion_timer == 50:
                   play_explosion2()

                if explosion_timer <= 50:
                   update_debris()

                    
                explosion_timer -= 1
                if explosion_timer <= 0:
                    if lives > 0:
                        wait_for_restart = True
                    else:
                        game_over = True
            draw_tunnel()
    root.after(50, game_loop)
game_loop()
root.mainloop()
