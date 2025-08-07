# MS AI UI Assistant
AI 기반 UI/UX 개선 자동화 시스템

### 프로젝트 소개
MS AI UI Assistant는 회의록, 사용자 피드백 등 다양한 입력을 기반으로 UI/UX 개선 요구사항을 자동으로 도출하고, HTML, js 등 다양한 코드의 개선안을 빠르게 확인해볼 수 있는 플랫폼입니다.
주요 목표는 누구나 쉽고 빠르게 UI/UX를 개선할 수 있도록 지원하는 것입니다.

프로젝트 릴리즈 주소: https://sahara-web-001.azurewebsites.net (avaliable ~25-08-08)<br>
전체 기능 demo: https://youtu.be/QLup92paS9Y

### 주요 기능
- 회의록/피드백/요구사항 입력 → UI/UX 개선사항 자동 추출
- 음성 녹음, txt/md 파일, 텍스트 직접 입력 등 다양한 형태의 회의록 요약 및 핵심 UI 변경 기능 리포트
- 개선된 UI/UX 코드 및 개선 보고서 문서화
- 반응형 디자인, 접근성 개선, 시각적 디자인 등 집중 영역 선택 가능
- 개선 효과 요약 및 다운로드 기능(원본/분석/코드)
- Streamlit 기반 웹 UI 제공

### 기술 스택

- Python 3.13
- Streamlit (web UI)
- Langfuse (AI monitoring)
- Azure OpenAI
  - GPT 4.1 (agent)
  - GPT 4.1-mini
  - GPT 4o (음성 처리)
  - text-embedding-3-small (RAG)
- Azure AI Search
- Azure Storage Account
- Azure Speech services (Azure Cognitive Services)
- Azure APP service (web deployment)

<img width="1144" height="227" alt="image" src="https://github.com/user-attachments/assets/8cd25f24-cc1e-4a39-9bf8-c9a8586c668e" />

<img width="723" height="265" alt="image" src="https://github.com/user-attachments/assets/1964b8a0-48c3-4145-9aa9-df4bcc4abb12" />


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

### 세부 기능

#### 1. 🚀 통합 UI 개선 시스템

[<img width="800" height="450" alt="image" src="https://github.com/user-attachments/assets/8627cccf-ba45-4975-8ec8-0fa096e33872" />](https://s8.ezgif.com/tmp/ezgif-8bd73ba992a59a.gif)


#### 2. 📇 회의록 기반 UI 요구사항 분석

#### 3. 🛠️ 회의 결과 기반 UI 개선

#### 4. 💡 AI에게 질문하기

#### 5. 💿 회의 녹음 기반 요약

#### 6. ⚠️ 관리자 기능 - 모니터링 상태 확인





