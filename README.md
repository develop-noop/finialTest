<Anaconda 사용>
파이썬 버전: 3.10 
라이브러리 및 라이브러리 버전: requirements.txt(동작인식 및 음성인식 대부분), requirements2.txt(음성인식 키패드 4) 참고

<실행방법>
동시에 시연 가능합니다.(동작인식: 실시간 인식, 음성인식: 키패드 눌러 원할 때 인식)
동시에 python 4가지 파일을 실행중인채 유니티 실행
1. 동작 인식 실행방법
requirements.txt의 가상환경 라이브러리 다운 후, 가상환경에서 python hand.py 실행, unity 실행 버튼 눌러 게임 창의 결과 확인
2. 음성 인식 실행방법(키패드 1,2,3을 눌러 유니티에서 실행)- requirements.txt 가상환경 실행
2-1. 키패드 
vosk 이용한 기능으로 가상환경 외에 vosk 홈페이지에서 vosk-model-small-ko-0.22 다운 필요
가상환경 실행 후 python voiceDev.py -> unity 실행 -> 키패드 1번을 통해 확인
2-2 키패드 2, 3
whisper, Hugging Face 이용한 기능. 가상환경에서 다 깔릴 것이나, python stt_server_whisper_qa.py 최초실행시 hugging Face의 (TinyLlama/TinyLlama-1.1B-Chat-v1.0) LLM 모델이 자동으로 깔릴 것임. 경로설정 주의
->unity에서 키패드 2, 3을 눌러 기능 수행
3. 음성 인식 실행방법(키패드 4)-requirements2.txt 가상환경 실행
Ollama 다운로드 필요. ollama pull llama3.2:3b 사용
python ollama.py -> unity 실행 -> 숫자 4 키패드 눌러 확인
