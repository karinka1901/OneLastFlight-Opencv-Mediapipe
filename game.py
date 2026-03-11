import cv2 as cv
import pygame
import random
from face_detector import FaceDetector

class Game:
    def __init__(self, width=600, height=400):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("One Last Flight")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font("assets/fonts/WindowsXPFont.otf", 16)
        self.font_large = pygame.font.Font("assets/fonts/WindowsXPFont.otf", 32)

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
        self.bug_h = self.bug_images[0].get_height()
        self.bugs = []  #all active bugs on screen
        self.bug_spawn_timer = 0
        self.bug_spawn_interval = 60  # spawn a new bug every 60 frames 
       
       # Distance traveled
        self.distance = 0
        
        # Energy system
        self.stamina = 100   
        self.stamina_drain = 0.3 # energy lost per frame
        self.stamina_gain = 17 # energy gained per butterfly
        
        # Game state
        self.game_started = False
        self.game_over = False

        # Countdown
        self.countdown_active = False
        self.countdown_value = 0
        self.countdown_timer = 0
        self.countdown_duration = 30  #1 sec

        # Face Detection
        self.detector = FaceDetector()
        self.camera = cv.VideoCapture(0)
        self.running = True

        # Moving background
        self.background = pygame.image.load("assets/sprites/sky.png").convert_alpha()
        self.background_y = height - self.background.get_height() 

        # Cloud blow image
        self.cloud_blowing_img =pygame.transform.scale(pygame.image.load("assets/sprites/cloud_blow.png").convert_alpha(), (80, 55))
        self.cloud_idle_img = pygame.transform.scale(pygame.image.load("assets/sprites/cloud_idle.png").convert_alpha(), (80, 55))
        self.is_blowing = False

    def get_blowing_input(self):
        blowing = False
        ret, frame = self.camera.read()

        if not ret:
            return False

        frame = cv.flip(frame, 1)
        expression = self.detector.get_expression(frame)
        self.detector.draw_mouth(frame)

        blowing = expression == "blowing"

        cv.imshow("Camera", cv.resize(frame, (150, 110)))
        cv.waitKey(1)

        return blowing

    def spawn_bug(self): 
        x = random.randint(self.width - 80, self.width - 30)
        y = random.randint(15, self.height - self.bug_h - 100) #dont spawn on the bottowm of the screen
        self.bugs.append([x, y, random.randint(0, len(self.bug_images) - 1)]) 

    def reset_game(self): 
        self.bird_y = self.height // 2
        self.velocity = 0
        self.distance = 0
        self.stamina = 100
        self.bugs = []
        self.bug_spawn_timer = 0
        self.game_over = False

    def countdown(self): #handles the 3-2-1 countdown before the game starts
        self.countdown_timer += 1
        if self.countdown_timer >= self.countdown_duration:
            self.countdown_timer = 0
            self.countdown_value -= 1
            if self.countdown_value <= 0:
                self.countdown_active = False
                self.game_started = True
                return

        countdown_text = self.font_large.render(str(self.countdown_value), True, (112, 130, 156))
        self.screen.blit(countdown_text, (self.width // 2 - countdown_text.get_width() // 2, self.height // 2 - 16))

    def update(self, blowing): 
        if self.game_over: # bird falls down when game over
            self.velocity += 5 
            self.bird_y += self.velocity 
            return
        
        self.is_blowing = blowing

        # Distance
        self.distance += self.scroll_speed

        # Stamina drain over time
        self.stamina -= self.stamina_drain
        if self.stamina <= 0:
            self.stamina = 0
            self.game_over = True
            return

        if blowing: #bird flaps the wings faster when blowing
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

        # infinite scroll
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
            bug[0] -= self.scroll_speed  

            bug_collider = pygame.Rect(bug[0], bug[1], self.bug_w, self.bug_h)
            if bird_collider.colliderect(bug_collider):
                self.stamina = min(100, self.stamina + self.stamina_gain) 
            elif bug[0] + self.bug_w > 0: 
                remaining_bugs.append(bug)

        self.bugs = remaining_bugs

    def draw(self):
        #Scrolling background
        self.screen.blit(self.background, (-self.background_offset, self.background_y))
        self.screen.blit(self.background, (self.width - self.background_offset, self.background_y))

        if not self.game_started:
            if self.countdown_active:
                self.countdown()
            else:
                start_text = self.font_large.render("One Last Flight", True, (112, 130, 156))
                self.screen.blit(start_text, (self.width // 2 - start_text.get_width() // 2, self.height // 2 - 20))
                prompt_text = self.font.render("Press Enter to start", True, (112, 130, 156))
                self.screen.blit(prompt_text, (self.width // 2 - prompt_text.get_width() // 2, self.height // 2 + 20))
            pygame.display.flip()
            return
    
        # Bugs
        for bug in self.bugs:
            self.screen.blit(self.bug_images[bug[2]], (bug[0], bug[1]))

        # Bird
        self.screen.blit(self.bird_image, (self.bird_x, int(self.bird_y)))

        # Distance
        dist_text = self.font.render(f"Distance: {self.distance / 100:.1f} m", True, (112, 130, 156))
        self.screen.blit(dist_text, (10, 10))

        # Stamina bar
        stamina_bar_w = 115
        stamina_bar_h = 16
        stamina_bar_x = 10
        stamina_bar_y = 30
        pygame.draw.rect(self.screen, (171, 188, 206), (stamina_bar_x, stamina_bar_y, stamina_bar_w, stamina_bar_h))
        fill_w = int(stamina_bar_w * self.stamina / 100)
        color = (73, 163, 204) if self.stamina > 30 else (200, 0, 0)
        pygame.draw.rect(self.screen, color, (stamina_bar_x, stamina_bar_y, fill_w, stamina_bar_h))
        pygame.draw.rect(self.screen, (94, 107, 140), (stamina_bar_x, stamina_bar_y, stamina_bar_w, stamina_bar_h), 2)

        cloud_indicator = self.cloud_blowing_img if self.is_blowing else self.cloud_idle_img
        self.screen.blit(cloud_indicator, (self.width - cloud_indicator.get_width() - 10, 10))

        # Game over
        if self.game_over:
            go_text = self.font_large.render("The little sparrow rests its wings", True, (112, 130, 156))
            self.screen.blit(go_text, (self.width // 2 - go_text.get_width() // 2, self.height // 2 -20))
            restart_text = self.font.render("Press Enter to restart", True, (112, 130, 156))
            self.screen.blit(restart_text, (self.width // 2 - restart_text.get_width() // 2, self.height // 2 + 20))

        pygame.display.flip()

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    if self.game_over:
                        self.reset_game()
                    elif not self.game_started and not self.countdown_active:
                        self.countdown_active = True
                        self.countdown_value = 3
                        self.countdown_timer = 0

            blowing = self.get_blowing_input()
            if self.game_started:
                self.update(blowing)
            self.draw()
            self.clock.tick(30)

        self.camera.release()
        cv.destroyAllWindows()
        pygame.quit()

game = Game()
game.run()