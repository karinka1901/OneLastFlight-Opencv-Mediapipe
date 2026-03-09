import cv2 as cv
import pygame
import sys
import random
from detection import FaceDetector


class Game:
    def __init__(self, width=600, height=400):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("One Last Flight")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 36)

        # Bird sprite
        self.bird_up = pygame.transform.flip(pygame.image.load("assets/sprites/up.png").convert_alpha(), True, False)
        self.bird_down = pygame.transform.flip(pygame.image.load("assets/sprites/down.png").convert_alpha(),True, False)
        self.bird_frame = 0 
        self.bird_anim_speed = 6
        self.bird_image = self.bird_up

        # Bird position
        self.bird_w = self.bird_up.get_width()
        self.bird_h = self.bird_up.get_height()
        self.bird_x = 100 # fixed x position
        self.bird_y = height // 2 # start in the middle of the screen
        self.velocity = 0 
        self.gravity = 1
        self.lift = -3

        # Scrolling
        self.scroll_speed = 4
        self.background_offset = 0

        # Bugs to catch
        self.bug_images = [
            pygame.transform.scale(pygame.image.load("assets/sprites/bug.png").convert_alpha(), (30, 24)),
            pygame.transform.scale(pygame.image.load("assets/sprites/bug1.png").convert_alpha(), (30, 24)),
            pygame.transform.scale(pygame.image.load("assets/sprites/bug2.png").convert_alpha(), (30, 24)),
            pygame.transform.scale(pygame.image.load("assets/sprites/bug3.png").convert_alpha(), (30, 24)),
        ]
        self.bug_w = self.bug_images[0].get_width()
        self.bug_h = self.bug_h = self.bug_images[0].get_height()
        self.bugs = []  #all active bugs on screen
        self.bug_spawn_timer = 0
        self.bug_spawn_interval = 60  # spawn a new bug every 60 frames 
        self.distance = 0
        self.energy = 100   
        self.energy_drain = 0.2 # energy lost per frame
        self.energy_boost = 15  # energy gained per butterfly
        self.game_over = False

        # Face Detection
        self.detector = FaceDetector()
        self.camera = cv.VideoCapture(0)
        self.running = True

        # Moving background
        self.background = pygame.image.load("assets/sprites/sky.png").convert_alpha()
        self.background_y = height - self.background.get_height() 

        # Blow image
        self.blow_img =pygame.transform.scale(pygame.image.load("assets/sprites/blow.png").convert_alpha(), (70, 50))
        self.notblow_img = pygame.transform.scale(pygame.image.load("assets/sprites/notblow.png").convert_alpha(), (70, 50))
        self.is_blowing = False

    def spawn_bug(self):
        x = self.width
        y = random.randint(20, self.height - self.bug_h - 20) #spawn within screen bounds
        self.bugs.append([x, y, random.randint(0, len(self.bug_images) - 1)]) 

    def update(self, blowing):
        if self.game_over:
            return
        
        self.is_blowing = blowing
        # Distance
        self.distance += self.scroll_speed

        # Energy drains over time
        self.energy -= self.energy_drain
        if self.energy <= 0:
            self.energy = 0
            self.game_over = True
            return

        if blowing:
            self.velocity = self.lift
            self.bird_anim_speed = 6
        else:
            self.velocity += self.gravity
            self.bird_anim_speed = 10

        self.bird_y += self.velocity

        # Clamp to screen
        if self.bird_y < 0:
            self.bird_y = 0
            self.velocity = 0
        if self.bird_y > self.height - self.bird_h:
            self.bird_y = self.height - self.bird_h
            self.velocity = 0

        # Scroll
        self.background_offset = (self.background_offset + self.scroll_speed) % self.width

        # Animate bird wings
        self.bird_frame += 1 
        if self.bird_frame >= self.bird_anim_speed * 2: #reset after a full cycle 
            self.bird_frame = 0
        if self.bird_frame < self.bird_anim_speed: #flap up for the first half of the cycle, down for the second half
            self.bird_image = self.bird_up
        else:
            self.bird_image = self.bird_down

        # Spawn bugs
        self.bug_spawn_timer += 1
        if self.bug_spawn_timer >= self.bug_spawn_interval:
            self.spawn_bug()
            self.bug_spawn_timer = 0

        # Move bugs and check collision
        bird_collider = pygame.Rect(self.bird_x+13, int(self.bird_y)+40, self.bird_w-30, self.bird_h-90)
        remaining_bugs = []
        for bug in self.bugs:
            bug[0] -= self.scroll_speed  # move left with the world

            bug_collider = pygame.Rect(bug[0], bug[1], self.bug_w, self.bug_h)
            if bird_collider.colliderect(bug_collider):
                self.energy = min(100, self.energy + self.energy_boost)  # replaces self.score += 1
            elif bug[0] + self.bug_w > 0:  # still on screen
                remaining_bugs.append(bug)
        self.bugs = remaining_bugs

    def draw(self): 
        self.screen.blit(self.background, (-self.background_offset, self.background_y))
        self.screen.blit(self.background, (self.width - self.background_offset, self.background_y))

        # Bugs
        for bug in self.bugs:
            self.screen.blit(self.bug_images[bug[2]], (bug[0], bug[1]))

        # Bird
        self.screen.blit(self.bird_image, (self.bird_x, int(self.bird_y)))

        # Distance
        dist_text = self.font.render(f"Distance: {self.distance / 100:.1f} m", True, (112, 130, 156))
        self.screen.blit(dist_text, (10, 10))

        # Energy bar
        bar_w = 100
        bar_h = 16
        bar_x = 10
        bar_y = 45
        pygame.draw.rect(self.screen, (80, 80, 80), (bar_x, bar_y, bar_w, bar_h))
        fill_w = int(bar_w * self.energy / 100)
        color = (0, 200, 0) if self.energy > 30 else (200, 0, 0)
        pygame.draw.rect(self.screen, color, (bar_x, bar_y, fill_w, bar_h))

        indicator = self.blow_img if self.is_blowing else self.notblow_img
        self.screen.blit(indicator, (self.width - indicator.get_width() - 10, 10))

        # Game over
        if self.game_over:
            go_text = self.font.render("The little birdie needs to rest", True, (112, 130, 156))
            self.screen.blit(go_text, (self.width // 2 - go_text.get_width() // 2, self.height // 2))

        pygame.display.flip()

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            blowing = False
            ret, frame = self.camera.read()
            if ret:
                frame = cv.flip(frame, 1)
                expression = self.detector.get_expression(frame)
                self.detector.draw_mouth(frame)
                blowing = expression == "blowing"
                gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
                cv.imshow("Camera", cv.resize(frame, (320, 240)))
                cv.waitKey(1)

            if not self.game_over:
                self.update(blowing)
            self.draw()
            self.clock.tick(30)

        self.camera.release()
        cv.destroyAllWindows()
        pygame.quit()

game = Game()
game.run()