import os
os.environ["HF_HOME"] = r"D:\university\2nd2th\openSW\llm" 
import socket
import json
import random

import numpy as np
import sounddevice as sd


from faster_whisper import WhisperModel
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import torch


       # 또는
# os.environ["TRANSFORMERS_CACHE"] = r"D:\hf_cache"  # 둘 중 하나만 써도 됨


# ==========================
# 설정
# ==========================

# Unity 쪽 UDP 수신 설정 (Unity의 VoiceUDPReceiver.listenPort와 맞춰야 함)
UNITY_IP = "127.0.0.1"
UNITY_PORT = 5005

# Unity -> Python 명령 수신 포트 (STTModeSender.pythonPort와 맞추기)
PYTHON_LISTEN_PORT = 6000

# 오디오 설정
SAMPLE_RATE = 16000
RECORD_SECONDS = 4  # 한 번에 녹음하는 길이(초)

# LLM 모델 이름 (경량 모델로 교체 가능)
# 실제로 설치 가능한 작은 한국어/다국어 Chat 모델로 바꿔도 됨
LLM_MODEL_NAME = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

# 모드 상수
MODE_NONE = 0
MODE_WHISPER_SIMPLE = 2
MODE_WHISPER_PERSONA = 3

current_mode = MODE_NONE

# 캐릭터 성격 목록 (모드 3)
PERSONAS = ["cute", "tsundere", "naive"]
current_persona = None


# ==========================
# UDP 소켓 준비
# ==========================

# Unity로 결과 보내는 소켓
sock_out = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Unity에서 명령 받는 소켓
sock_in = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_in.bind(("0.0.0.0", PYTHON_LISTEN_PORT))


# ==========================
# 모델 로딩
# ==========================

print("[로딩] Whisper 모델 로딩 중...")
whisper_model = WhisperModel("small", device="cpu", compute_type="int8")
print("[로딩] Whisper 완료")

print("[로딩] 감정 분석 모델 로딩 중...")
sentiment_pipe = pipeline(
    "text-classification",
    model="tabularisai/multilingual-sentiment-analysis",
    top_k=None
)
print("[로딩] 감정 분석 모델 완료")

print("[로딩] LLM 모델 로딩 중...")
llm_tokenizer = AutoTokenizer.from_pretrained(LLM_MODEL_NAME)
llm_model = AutoModelForCausalLM.from_pretrained(
    LLM_MODEL_NAME,
    torch_dtype=torch.float32,       # CPU 기준
    device_map="cpu"                # GPU 있으면 활용, 없으면 CPU
)
print("[로딩] LLM 완료")


# ==========================
# 공통: 오디오 녹음
# ==========================

def record_audio(seconds=RECORD_SECONDS, sample_rate=SAMPLE_RATE):
    """마이크에서 seconds초 만큼 녹음해서 (sr, float32 ndarray) 반환"""
    print(f"[녹음] {seconds}초 동안 녹음합니다...")
    audio = sd.rec(
        int(seconds * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype="float32"
    )
    sd.wait()
    print("[녹음] 완료")
    audio = audio.flatten()
    return sample_rate, audio


# ==========================
# Whisper: STT
# ==========================

def recognize_with_whisper():
    """Whisper로 한 번 인식 (모드 2, 3에서 사용)"""
    sr, audio = record_audio()
    print("[Whisper] 음성 인식 중...")
    segments, info = whisper_model.transcribe(audio, language="ko")
    text = "".join(seg.text for seg in segments).strip()
    print("[Whisper] 인식 결과:", text)
    return text


# ==========================
# 감정 분석 + 키워드
# ==========================

POSITIVE_KEYWORDS = ["좋아", "좋다", "사랑", "고마워", "행복", "멋있", "예쁘", "귀엽", "최고"]
NEGATIVE_KEYWORDS = ["싫", "싫다", "짜증", "화나", "불편", "최악", "별로", "미워"]

def extract_sentiment_keywords(text: str):
    """텍스트에서 호/불호 관련 키워드 추출"""
    found_pos = [w for w in POSITIVE_KEYWORDS if w in text]
    found_neg = [w for w in NEGATIVE_KEYWORDS if w in text]
    return found_pos, found_neg

def classify_sentiment(text: str):
    """
    Hugging Face로 전체 감정을 판단하고,
    그와 관련된 키워드를 함께 반환.
    return: sentiment("호/중립/불호"), keywords(list[str])
    """
    if not text.strip():
        return "중립", []

    pos_kw, neg_kw = extract_sentiment_keywords(text)

    results = sentiment_pipe(text)[0]  # top_k=None 이라서 [ [ {label,score}, ... ] ]
    best = max(results, key=lambda x: x["score"])
    label = best["label"].lower()

    if "positive" in label or "4" in label or "3" in label:
        sentiment = "호"
        keywords = pos_kw or neg_kw
    elif "negative" in label or "0" in label or "1" in label:
        sentiment = "불호"
        keywords = neg_kw or pos_kw
    else:
        sentiment = "중립"
        keywords = pos_kw + neg_kw

    # 중복 제거
    keywords = list(dict.fromkeys(keywords))
    return sentiment, keywords


# ==========================
# 모드 2: Whisper + 감정 + 규칙 기반 QA
# ==========================

def generate_answer_basic(text: str, sentiment: str, keywords: list[str]) -> str:
    """모드 2에서 사용할 가벼운 규칙 기반 답변"""
    kw_text = ", ".join(keywords) if keywords else "없음"

    if sentiment == "호":
        return f"좋게 말해줘서 고마워요. 당신의 말에서 [{kw_text}] 같은 포근한 느낌이 전해져요."
    elif sentiment == "불호":
        return f"많이 속상하셨겠어요. [{kw_text}] 같은 말에서 그런 마음이 느껴져요. 그래도 저는 곁에 있을게요."
    else:
        return "그렇게 느끼셨군요. 더 이야기해 주면 제가 조금 더 잘 이해할 수 있을 것 같아요."

def run_whisper_simple_mode():
    """모드 2 실행: Whisper + 감정 + 규칙 기반 QA"""
    global current_mode
    current_mode = MODE_WHISPER_SIMPLE
    print("[모드] 2번: WHISPER_SIMPLE (기본 QA)")

    text = recognize_with_whisper()
    if not text:
        print("[Whisper] 인식된 텍스트 없음")
        return

    sentiment, keywords = classify_sentiment(text)
    print("[감정] 판단 결과:", sentiment, "/ 키워드:", keywords)

    answer = generate_answer_basic(text, sentiment, keywords)
    print("[대답] 생성:", answer)

    payload = {
        "type": "qa",
        "mode": 2,
        "q": text,
        "sentiment": sentiment,
        "keywords": keywords,
        "a": answer,
        "persona": None,
    }
    msg = json.dumps(payload, ensure_ascii=False)
    sock_out.sendto(msg.encode("utf-8"), (UNITY_IP, UNITY_PORT))
    print("[전송] Unity로 Q&A(모드2) 전송 완료")


# ==========================
# 모드 3: Whisper + 감정 + LLM + 성격 QA
# ==========================

def init_persona_if_needed():
    """모드 3에서 처음 실행할 때 성격을 랜덤으로 한 번 정함"""
    global current_persona
    if current_persona is None:
        current_persona = random.choice(PERSONAS)
        print(f"[성격] 이번 플레이 캐릭터 성격: {current_persona}")

def get_persona_description(persona: str) -> str:
    """LLM 프롬프트에 넣을 성격 설명 문장"""
    if persona == "cute":
        return (
            "귀엽고 애교가 많으며, 말투가 상냥하다. "
            "가끔 말 끝에 '메에' 같은 소리를 붙이기도 한다."
        )
    elif persona == "tsundere":
        return (
            "겉으로는 까칠하고 퉁명스럽게 말하지만, 실제로는 상대를 많이 걱정한다. "
            "솔직하지 못해서 돌려 말하고, 가끔 '흥' 같은 말을 쓴다."
        )
    elif persona == "naive":
        return (
            "순진하고 세상 물정을 잘 모르지만, 상대의 말을 진지하게 듣고 솔직하게 느낀 대로 말한다. "
            "모르는 것은 모른다고 말하고, 단순하지만 따뜻한 성격이다."
        )
    else:
        return (
            "따뜻하고 부드러운 성격으로, 상대의 감정을 존중하며 조심스럽게 말한다."
        )

def build_llm_prompt(text: str, sentiment: str, keywords: list[str], persona: str) -> str:
    persona_desc = get_persona_description(persona)
    keyword_text = ", ".join(keywords) if keywords else "없음"

    prompt = f"""
너는 게임 속에서 플레이어와 대화하는 캐릭터다.
너의 성격은 다음과 같다: {persona_desc}

지금부터 플레이어가 말한 문장과 그에 대한 감정 분석 결과, 감정 키워드를 줄 것이다.
그 정보를 바탕으로, 플레이어에게 한국어로 자연스럽게 한두 문장 정도로 대답해라.

[플레이어 발화]
"{text}"

[감정 분석 결과]
- 전반적인 감정: {sentiment}  (호/중립/불호 중 하나)
- 감정과 관련된 키워드: {keyword_text}

[답변 규칙]
1. 플레이어의 감정을 존중하고, 상황에 맞게 공감하거나 부드럽게 반응해라.
2. 답변은 1~2문장 이내로 짧고 자연스럽게 말해라.
3. 캐릭터의 성격에 맞는 말투와 표현을 사용해라.
4. 너무 설명조가 아니라, 대화하는 말투로 대답해라.

[출력 형식]
- 오직 캐릭터의 대답만 출력하고, 설명이나 다른 표시는 하지 마라.

대답:
""".strip()

    return prompt

def generate_answer_llm_persona(text: str, sentiment: str, keywords: list[str], persona: str) -> str:
    """모드 3: LLM + 성격 프롬프트로 답변 생성"""
    prompt = build_llm_prompt(text, sentiment, keywords, persona)

    inputs = llm_tokenizer(prompt, return_tensors="pt")
    inputs = {k: v.to(llm_model.device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = llm_model.generate(
            **inputs,
            max_new_tokens=80,
            do_sample=True,
            top_p=0.9,
            temperature=0.8,
        )

    full = llm_tokenizer.decode(outputs[0], skip_special_tokens=True)

    if "대답:" in full:
        answer = full.split("대답:")[-1].strip()
    else:
        # 혹시 모델이 형식을 안 지켰을 경우, prompt 이후 부분만 사용
        answer = full[len(prompt):].strip()

    # 너무 길면 잘라주기 (안전)
    if len(answer) > 300:
        answer = answer[:300]

    return answer

def run_whisper_persona_mode():
    """모드 3 실행: Whisper + 감정 + LLM + 성격 QA"""
    global current_mode
    current_mode = MODE_WHISPER_PERSONA
    print("[모드] 3번: WHISPER_PERSONA (LLM 성격 QA)")

    init_persona_if_needed()

    text = recognize_with_whisper()
    if not text:
        print("[Whisper] 인식된 텍스트 없음")
        return

    sentiment, keywords = classify_sentiment(text)
    print("[감정] 판단 결과:", sentiment, "/ 키워드:", keywords)
    print("[성격] 현재 캐릭터 성격:", current_persona)

    answer = generate_answer_llm_persona(text, sentiment, keywords, current_persona)
    print("[대답] 생성:", answer)

    payload = {
        "type": "qa",
        "mode": 3,
        "q": text,
        "sentiment": sentiment,
        "keywords": keywords,
        "a": answer,
        "persona": current_persona,
    }
    msg = json.dumps(payload, ensure_ascii=False)
    sock_out.sendto(msg.encode("utf-8"), (UNITY_IP, UNITY_PORT))
    print("[전송] Unity로 Q&A(모드3) 전송 완료")


# ==========================
# Unity 명령 수신 루프
# ==========================

def listen_commands():
    print(f"[서버] STT 서버가 포트 {PYTHON_LISTEN_PORT}에서 대기 중...")
    while True:
        data, addr = sock_in.recvfrom(1024)
        cmd = data.decode("utf-8").strip()
        print("[서버] Unity로부터 명령 수신:", cmd)

        if cmd == "MODE_WHISPER_SIMPLE":
            run_whisper_simple_mode()
        elif cmd == "MODE_WHISPER_PERSONA":
            run_whisper_persona_mode()
        else:
            print("[서버] 알 수 없는 명령:", cmd)


# ==========================
# 메인
# ==========================

if __name__ == "__main__":
    listen_commands()
