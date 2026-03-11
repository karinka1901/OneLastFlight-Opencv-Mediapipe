import cv2 as cv
import mediapipe as mp

mp_face_mesh = mp.solutions.face_mesh

class FaceDetector:
    def __init__(self):
        self.face_mesh = mp_face_mesh.FaceMesh(
            max_num_faces=1, refine_landmarks=True,
            min_detection_confidence=0.5)
    
    def get_expression(self, frame): 
        rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb)
        
        if not results.multi_face_landmarks:
            return "neutral"
        
        landmarks = results.multi_face_landmarks[0].landmark
        h, w = frame.shape[:2]
        
        left_corner = landmarks[61]
        right_corner = landmarks[291]
        mouth_width = abs(right_corner.x - left_corner.x) * w
        
        upper_lip = landmarks[13]
        lower_lip = landmarks[14]
        mouth_height = abs(lower_lip.y - upper_lip.y) * h
        
        ratio = mouth_width / (mouth_height + 1e-6)

        # print(f"W: {mouth_width:.1f}  H: {mouth_height:.1f}  R: {ratio:.2f}")

        # Blowing = small width, small height, points clustered
        if mouth_width < 40 and mouth_height < 15:
            return "blowing"
        # elif ratio > 5.0:
        #     return "smile"
        return "neutral"
    
    def draw_mouth(self, frame):
        rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb)
        
        if not results.multi_face_landmarks:
            return
        
        landmarks = results.multi_face_landmarks[0].landmark
        h, w = frame.shape[:2]
        
        # All mouth/lip landmark indices
        MOUTH_POINTS = [
            61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291,  # outer lower
            185, 40, 39, 37, 0, 267, 269, 270, 409,              # outer upper
            78, 95, 88, 178, 87, 14, 317, 402, 318, 324, 308,    # inner lower
            191, 80, 81, 82, 13, 312, 311, 310, 415               # inner upper
        ]
        
        for idx in MOUTH_POINTS:
            x = int(landmarks[idx].x * w)
            y = int(landmarks[idx].y * h)
            # cv.circle(frame, (x, y), 2, (0, 0, 255), -1)  # red
        
        # Key landmarks used for expression detection
        for idx in [61, 291, 13, 14]:
            x = int(landmarks[idx].x * w)
            y = int(landmarks[idx].y * h)
            # cv.circle(frame, (x, y), 5, (255, 0,0), -1)  # blue