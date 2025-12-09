# ollama.py
import json
import random

import numpy as np
import requests
import sounddevice as sd
from flask import Flask, jsonify
import whisper

app = Flask(__name__)

# ==============================
# 1. Whisper 모델 로드 (영어 전용)
# ==============================
print("Loading Whisper model (small.en)...")
# 영어만 쓸 거면 small.en 이 가볍고 빠름
whisper_model = whisper.load_model("small.en")   # 필요하면 "small" 등으로 변경 가능


# ==============================
# 2. 성격 관련 설정 (cute 제거, depressed 추가)
# ==============================
PERSONAS_EN = ["naive", "tsundere", "depressed"]
PERSONA_TO_DESC = {
    "naive": "naive, kind, a bit clumsy and innocent tone",
    "tsundere": "cold, blunt, a bit rude on the outside but actually caring, tsundere-like tone",
    "depressed": "very quiet, low energy, gloomy and slightly pessimistic but still gentle tone"
}

# 한 번 정해지면 서버가 꺼질 때까지 유지할 전역 변수
CURRENT_PERSONA = None


def choose_persona() -> str:
    """
    성격을 한 번만 랜덤으로 정하고, 이후 호출에서는 그대로 유지.
    """
    global CURRENT_PERSONA

    # 이미 한 번 정해졌다면 그대로 사용
    if CURRENT_PERSONA is not None:
        return CURRENT_PERSONA

    # 처음 호출일 때만 랜덤 선택
    CURRENT_PERSONA = random.choice(PERSONAS_EN)
    print(f"[Persona Init] Selected persona: {CURRENT_PERSONA}")
    return CURRENT_PERSONA


def build_prompt(persona_en: str, user_text_en: str) -> str:
    """
    LLM에 줄 프롬프트 생성.
    - 입력: 사용자 영어 질문, 성격
    - 출력: 한 문장 영어로 답하게 하는 지시문
    """
    style = PERSONA_TO_DESC[persona_en]
    prompt = f"""
You are a character AI.

- The user asks questions in English.
- You must always answer in **English**.
- Answer with **exactly ONE sentence**.
- Keep it short, under about 25 words.
- Your tone and style must follow this description: {style}

User question (English): "{user_text_en}"

Now answer the question in one sentence in English.
"""
    return prompt.strip()


# ==============================
# 3. Ollama 로컬 LLM 호출
# ==============================
def ask_llm_ollama(prompt: str) -> str:
    """
    Ollama의 로컬 LLM (llama3.2:1b) 호출.
    - 사전에: `ollama pull llama3.2:1b` 를 해둬야 함
    - Ollama 서비스가 떠 있어야 함
    """
    resp = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3.2:1b",   # 2GB 이하 모델, 필요시 "llama3.2"로 교체 가능
            "prompt": prompt,
            "stream": True
        },
        stream=True,
        timeout=300
    )

    full_text = ""
    for line in resp.iter_lines():
        if not line:
            continue
        data = json.loads(line.decode("utf-8"))
        full_text += data.get("response", "")

    # 첫 문장만 남기기
    for end in [".", "?", "!", "…"]:
        if end in full_text:
            full_text = full_text.split(end)[0] + end
            break

    return full_text.strip()


# ==============================
# 4. 마이크에서 4초 녹음 (numpy 배열로)
# ==============================
def record_4sec_audio(sr: int = 16000, duration: int = 4) -> np.ndarray:
    """
    기본 마이크에서 4초 동안 녹음하여 (N,) 형태의 float32 numpy 배열로 반환.
    """
    print("Recording 4 seconds...")
    audio = sd.rec(int(duration * sr), samplerate=sr, channels=1, dtype="float32")
    sd.wait()
    print("Recording done.")

    # (N, 1) -> (N,) 으로 변환
    audio = audio.squeeze(-1)
    return audio


# ==============================
# 5. Whisper로 음성 → 텍스트
# ==============================
def transcribe_whisper_from_audio(audio: np.ndarray) -> str:
    """
    numpy 배열 audio 를 Whisper에 직접 넣어서 텍스트로 변환.
    CPU 환경이므로 fp16=False 권장.
    """
    result = whisper_model.transcribe(audio, language="en", fp16=False)
    text = result.get("text", "").strip()
    return text


# ==============================
# 6. Flask 엔드포인트
# ==============================
@app.route("/qa_from_mic", methods=["POST"])
def qa_from_mic():
    try:
        # 1) 마이크에서 4초 녹음
        audio = record_4sec_audio()

        # 2) Whisper로 영어 인식
        question_text = transcribe_whisper_from_audio(audio)
        print("Recognized text:", question_text)

        if not question_text:
            return jsonify({
                "ok": False,
                "error": "no_speech_detected"
            })

        # 3) 성격 (처음 한 번만 랜덤, 이후 고정)
        persona = choose_persona()
        print("Current persona:", persona)

        # 4) LLM 호출
        prompt = build_prompt(persona, question_text)
        answer_text = ask_llm_ollama(prompt)
        print("AI answer:", answer_text)

        # 5) Unity로 반환
        return jsonify({
            "ok": True,
            "question": question_text,
            "answer": answer_text,
            "persona": persona
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "ok": False,
            "error": f"server_exception: {str(e)}"
        }), 500


# ==============================
# 7. 메인 실행
# ==============================
if __name__ == "__main__":
    # 예: conda activate play2 후 python ollama.py
    app.run(host="0.0.0.0", port=5000)
