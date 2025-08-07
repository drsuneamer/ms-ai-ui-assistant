# MS-PJT

### 프로젝트 정보

프로젝트 릴리즈 주소: sahara-web-001.azurewebsites.net (expired in 25-08-08)

---


### 개발환경 세팅

venv 생성
```bash
python -m venv venv
```

가상환경 실행 (powershell 일반모드 X)
```bash
.\venv\Scripts\activate
```

패키지 설치
```bash
pip install streamlit openai python-dotenv langchain langchain-openai langchain-community azure-cognitiveservices-speech langfuse
```

requirements.txt 만드는 법
```bash
pip freeze > requirements.txt
```

requirements.txt 기반 설치
```bash
pip install -r requirements.txt
```

streamlit 메인 페이지 실행
```bash
streamlit run Home.py
```

---

### 프로젝트 구조

