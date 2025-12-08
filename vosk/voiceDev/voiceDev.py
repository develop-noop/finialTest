import sounddevice as sd
import queue
import json
from vosk import Model, KaldiRecognizer
import socket

UNITY_IP = "127.0.0.1"   # Unity랑 같은 PC면 이렇게
UNITY_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# 1. 모델 경로 (stt_test.py와 같은 폴더에 model 폴더가 있다고 가정)
MODEL_PATH = r"D:\university\2nd2th\openSW\finial_test\vosk\vosk-model-small-ko-0.22"

# 2. 오디오 설정
SAMPLE_RATE = 16000      # Vosk가 잘 쓰는 샘플레이트
BLOCK_SIZE = 8000

q = queue.Queue()

def audio_callback(indata, frames, time, status):
    if status:
        print(status)
    q.put(bytes(indata))
    
def classify_command(text: str):
    text = text.replace(" ", "")  # 띄어쓰기 제거해서 비교하기 쉽게
    if "안녕" in text or "안녕하세요" in text:
        return "HELLO"
    if "식사하자" in text or "밥먹자" in text or "밥먹자" in text:
        return "EAT"
    if "아이예뻐" in text or "아이이뻐" in text or "예쁘다" in text:
        return "CUTE"
    return None


def main():
    print("모델 로딩 중...")
    model = Model(MODEL_PATH)
    rec = KaldiRecognizer(model, SAMPLE_RATE)

    print("말해보세요! (Ctrl+C로 종료)")
    with sd.RawInputStream(samplerate=SAMPLE_RATE,
                           blocksize=BLOCK_SIZE,
                           dtype='int16',
                           channels=1,
                           callback=audio_callback):

        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                result = rec.Result()
                text = json.loads(result).get("text", "")
                if text:
                    print("인식:", text)
                    cmd = classify_command(text)
                    if cmd:
                        print("→ 명령어:", cmd)
                        # Unity로 UDP 전송
                        sock.sendto(cmd.encode('utf-8'), (UNITY_IP, UNITY_PORT))



if __name__ == "__main__":
    main()
