import cv2
import mediapipe as mp
import socket
import base64

# 1. 통신 설정
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
serverAddressPort = ("127.0.0.1", 5052)

# 2. 미디어파이프 설정
mpHands = mp.solutions.hands
hands = mpHands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5)
cap = cv2.VideoCapture(0)

# 해상도를 낮춰야 전송이 빠릅니다 (320x240 추천)
cap.set(3, 320)
cap.set(4, 240)

print("AR 모드 시작! 유니티를 켜세요.")

while True:
    success, img = cap.read()
    if not success: break

    # (1) 손 좌표 찾기
    imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(imgRGB)
    
    lmList = []
    data_coords = "0,0" # 손 없으면 기본값

    if results.multi_hand_landmarks:
        for handLms in results.multi_hand_landmarks:
            index_finger = handLms.landmark[8]
            h, w, c = img.shape
            # 좌표 보정
            x = 1 - index_finger.x 
            y = index_finger.y
            data_coords = f"{x},{y}"

    # (2) 이미지 압축 및 전송
    # 이미지를 JPG로 압축 (화질 50%)
    _, buffer = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 50])
    # 문자로 변환 (Base64)
    img_str = base64.b64encode(buffer).decode('utf-8')

    # (3) 데이터 합치기: "좌표|이미지데이터"
    # 좌표와 이미지를 '|' 기호로 구분해서 보냄
    final_data = f"{data_coords}|{img_str}"
    
    # 데이터가 너무 크면 잘릴 수 있으니 예외처리
    try:
        sock.sendto(str.encode(final_data), serverAddressPort)
    except:
        pass # 너무 큰 프레임은 버림

    cv2.imshow("Python Cam", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()