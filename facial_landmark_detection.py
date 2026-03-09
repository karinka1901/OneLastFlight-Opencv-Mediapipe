import pygame
import cv2import cv2 as cv
from detection import FaceDetector

class Game:























            # handle events, read camera, update, draw...        while self.running:    def run(self):            # clamp to screen...        self.box_y += self.velocity            self.velocity += self.gravity        else:            self.velocity = self.lift        if blowing:    def update(self, blowing):            self.camera = cv.VideoCapture(0)        self.detector = FaceDetector()        self.running = True        self.lift = -8        self.gravity = 0.5        self.velocity = 0        self.box_y = height // 2        self.clock = pygame.time.Clock()        self.screen = pygame.display.set_mode((width, height))        pygame.init()    def __init__(self, width=600, height=400):mp_drawing_styles = mp.solutions.drawing_styles

face_cascade = cv.CascadeClassifier(cv.data.haarcascades + 'haarcascade_frontalface_default.xml')
mouth_cascade = cv.CascadeClassifier(cv.data.haarcascades + 'haarcascade_smile.xml')
eye_cascade = cv.CascadeClassifier(cv.data.haarcascades + 'haarcascade_eye.xml')

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True, min_detection_confidence=0.5)

def detect_features(frame):
    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
          
    for (x, y, w, h) in faces:
        frame = cv.rectangle(frame, (x, y), (x+w, y+h),
                            color=(0, 255, 0), thickness=5)
        face = frame[y : y+h, x : x+w]
        gray_face = gray[y : y+h, x : x+w]
        mouth = mouth_cascade.detectMultiScale(gray_face, 
                            2.5, minNeighbors=9)
        for (xp, yp, wp, hp) in mouth:
            face = cv.rectangle(face, (xp, yp), (xp+wp, yp+hp),
                    color=(0, 0, 255), thickness=5)
        
        eyes = eye_cascade.detectMultiScale(gray_face, 
                    2.5, minNeighbors=7)
        for (xp, yp, wp, hp) in eyes:
            face = cv.rectangle(face, (xp, yp), (xp+wp, yp+hp),
                    color=(255, 0, 0), thickness=5)
    
    return frame

def is_smiling(frame):
    rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)
    
    if not results.multi_face_landmarks:
        return False
    
    face_landmarks = results.multi_face_landmarks[0]
    landmarks = face_landmarks.landmark
    h, w = frame.shape[:2]
    
    # Draw the full face mesh
    mp_drawing.draw_landmarks(
        frame, face_landmarks,
        mp_face_mesh.FACEMESH_TESSELATION,
        landmark_drawing_spec=None,
        connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_tesselation_style())
    
    # Draw mouth/lip contours 
    mp_drawing.draw_landmarks(
        frame, face_landmarks,
        mp_face_mesh.FACEMESH_LIPS,
        landmark_drawing_spec=None,
        connection_drawing_spec=mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2))
    
    # specific landmarks we use for blow detection
    for idx in [61, 291, 13, 14]:
        x_pos = int(landmarks[idx].x * w)
        y_pos = int(landmarks[idx].y * h)
        cv.circle(frame, (x_pos, y_pos), 5, (0, 255, 255), -1)  # yellow dots
    
    # Mouth corners 
    left_corner = landmarks[61]
    right_corner = landmarks[291]
    mouth_width = abs(right_corner.x - left_corner.x) * w
    
    # Upper and lower lip 
    upper_lip = landmarks[13]
    lower_lip = landmarks[14]
    mouth_height = abs(lower_lip.y - upper_lip.y) * h
    
    ratio = mouth_width / (mouth_height + 1e-6)
    
    # # Show the ratio on screen
    # cv.putText(frame, f"Ratio: {ratio:.2f}", (10, 30),
    #            cv.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    return ratio < 2.0  # tune this threshold for your face

def detect_expression(frame):
    rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)
    
    if not results.multi_face_landmarks:
        return "neutral"
    
    face_landmarks = results.multi_face_landmarks[0]
    landmarks = face_landmarks.landmark
    h, w = frame.shape[:2]
    
    # Draw mesh
    mp_drawing.draw_landmarks(
        frame, face_landmarks,
        mp_face_mesh.FACEMESH_TESSELATION,
        landmark_drawing_spec=None,
        connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_tesselation_style())
    
    mp_drawing.draw_landmarks(
        frame, face_landmarks,
        mp_face_mesh.FACEMESH_LIPS,
        landmark_drawing_spec=None,
        connection_drawing_spec=mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2))
    
    # Key landmarks
    for idx in [61, 291, 13, 14]:
        x_pos = int(landmarks[idx].x * w)
        y_pos = int(landmarks[idx].y * h)
        cv.circle(frame, (x_pos, y_pos), 5, (0, 255, 255), -1)
    
    left_corner = landmarks[61]
    right_corner = landmarks[291]
    mouth_width = abs(right_corner.x - left_corner.x) * w
    
    upper_lip = landmarks[13]
    lower_lip = landmarks[14]
    mouth_height = abs(lower_lip.y - upper_lip.y) * h
    
    ratio = mouth_width / (mouth_height + 1e-6)
    
    # Debug: show on screen
    cv.putText(frame, f"Ratio: {ratio:.2f} H: {mouth_height:.1f}", (10, 30),
               cv.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    if ratio < 3.0 and mouth_height > 10:
        return "blowing"
    elif ratio > 5.0:
        return "smile"
    else:
        return "neutral"

prev_expression = "neutral"

stream = cv.VideoCapture(0)

if not stream.isOpened():
    print("Cannot open camera")
    exit()

fps = stream.get(cv.CAP_PROP_FPS) 
stream.set(cv.CAP_PROP_FPS, 30)
width = int(stream.get(3))
height = int(stream.get(4))

output = cv.VideoWriter("captures/stream.mp4",
            cv.VideoWriter_fourcc('m', 'p', '4', 'v'),
            fps=fps, frameSize=(width, height))

was_smiling = False

while True:
    ret, frame = stream.read()
    if not ret:
        break

    frame = cv.resize(frame, (width, height))
    output.write(frame)
    
    expression = detect_expression(frame)
    if expression != prev_expression:
        if expression == "blowing":
            print("Blowing!")
        elif expression == "smile":
            print("You smiled!")
        # elif expression == "neutral":
        #     print("Neutral expression")
    prev_expression = expression
    
    cv.imshow('Camera Stream', frame)
    if cv.waitKey(1) == ord('q'):
        break

stream.release()
output.release()
cv.destroyAllWindows()