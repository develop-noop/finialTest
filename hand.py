import cv2
import mediapipe as mp
import socket
import base64

# 통신 설정
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
serverAddressPort = ("127.0.0.1", 5065)

mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands

cap = cv2.VideoCapture(0)
cap.set(3, 320)
cap.set(4, 240)

print("=== 업그레이드 AR 펫 ===")
print("1. 주먹: 공격")
print("2. 검지 하나만: 쓰다듬기")
print("3. 손 쫙 핌: 대기 (Idle)")

with mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.5, min_tracking_confidence=0.5) as hands:
    while cap.isOpened():
        success, image = cap.read()
        if not success: continue

        image.flags.writeable = False
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = hands.process(image_rgb)
        image.flags.writeable = True

        command = "palm" # 기본값은 대기
        index_x = 0.0
        index_y = 0.0

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                
                # 좌표 계산
                index_x = 1 - hand_landmarks.landmark[8].x 
                index_y = 1 - hand_landmarks.landmark[8].y

                # 손가락 개수 세기 (엄지 제외 4개만 체크)
                fingers = []
                for id in [8, 12, 16, 20]:
                    if hand_landmarks.landmark[id].y > hand_landmarks.landmark[id-2].y:
                        fingers.append(0) # 접힘
                    else:
                        fingers.append(1) # 펴짐
                
                total_fingers = sum(fingers)

                # --- ★ 핵심 로직 수정 ★ ---
                if total_fingers == 0:
                    command = "fist" # 주먹 (공격)
                    cv2.putText(image, "ATTACK!", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                
                elif total_fingers >= 3:
                    command = "palm" # 손가락 3개 이상 펴면 무조건 대기!
                    cv2.putText(image, "IDLE (Stop)", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                else: 
                    command = "pet" # 손가락 1~2개일 때만 쓰다듬기
                    # 검지 위치 표시
                    h, w, c = image.shape
                    cx, cy = int((1-index_x)*w), int((1-index_y)*h)
                    cv2.circle(image, (cx, cy), 15, (255, 255, 0), cv2.FILLED)

        # 전송
        try:
            _, buffer = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 50])
            img_str = base64.b64encode(buffer).decode('utf-8')
            
            # "명령어,x,y|이미지"
            final_data = f"{command},{index_x},{index_y}|{img_str}"
            sock.sendto(final_data.encode(), serverAddressPort)
        except:
            pass

        cv2.imshow('Python Cam', image)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()