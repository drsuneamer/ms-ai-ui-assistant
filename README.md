# MS AI UI Assistant
> (2025. 08. 06 ~ 07)
AI 기반 UI/UX 개선 자동화 시스템

### 🖐️ 프로젝트 소개
MS AI UI Assistant는 회의록, 사용자 피드백 등 다양한 입력을 기반으로 UI/UX 개선 요구사항을 자동으로 도출하고, HTML, js 등 다양한 코드의 개선안을 빠르게 확인해볼 수 있는 플랫폼입니다.
주요 목표는 누구나 쉽고 빠르게 UI/UX를 개선할 수 있도록 지원하는 것입니다.

프로젝트 릴리즈 주소: https://sahara-web-001.azurewebsites.net (avaliable ~25-08-08)<br>
전체 기능 demo: https://youtu.be/QLup92paS9Y

### 📌 주요 기능
- 회의록/피드백/요구사항 입력 → UI/UX 개선사항 자동 추출
- 음성 녹음, txt/md 파일, 텍스트 직접 입력 등 다양한 형태의 회의록 요약 및 핵심 UI 변경 기능 리포트
- 개선된 UI/UX 코드 및 개선 보고서 문서화
- 반응형 디자인, 접근성 개선, 시각적 디자인 등 집중 영역 선택 가능
- 개선 효과 요약 및 다운로드 기능(원본/분석/코드)
- Streamlit 기반 웹 UI 제공

### 🛠️ 기술 스택

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

<img width="723" height="227" alt="image" src="https://github.com/user-attachments/assets/8cd25f24-cc1e-4a39-9bf8-c9a8586c668e" />

<img width="723" height="265" alt="image" src="https://github.com/user-attachments/assets/1964b8a0-48c3-4145-9aa9-df4bcc4abb12" />


### 📊 프로젝트 구조
ms-ai-ui-assistant/<br>
├── pages/    _하위에 streamlit 사이드바 페이지 구성_<br>
├── result_docs/<br>
├── test_data/<br>
├── utils/    _langchain openai 설정, langfuse monitor, ai speech 관련 함수 등 여러 곳에서 쓰이는 함수 정의_<br>
├── .deployment<br>
├── .gitignore<br>
├── Home.py    _streamlit 메인 구동 페이지_<br>
├── README.md<br>
├── requirements.txt<br>
├── streamlit.sh    _azure app 배포 설정_<br>
└── test_scenario.md<br>

---

### 🧰 개발환경 세팅

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

### 🐾 세부 기능

#### 1. 🚀 통합 UI 개선 시스템

- 텍스트, 음성(wav) 등 다양한 형태로 입력되는 회의록에 등장한 UI 개선 내용을 요약한다.
- 기존 코드(html, react 등 여러 형태 지원)을 입력하면 파악한 개선 내용을 반영한 새로운 코드를 제시한다.
- HTML 코드를 개선하는 경우에는 화면에서 바로 전후 비교가 가능하다.
- 요약부터 전체 코드까지 정리된 보고서 파일(markdown) 다운로드가 가능하다.
- 전체 개선, 사용자 경험, 접근성, 반응형 디자인 등 개선 집중 영역을 선택할 수 있다.

![ezgif-8bd73ba992a59a](https://github.com/user-attachments/assets/8b84723c-6036-4102-9582-5ef5a904bf30)
![ezgif-33d2aced1402bc](https://github.com/user-attachments/assets/0010bd35-3edc-495d-affa-8048e5a98c0b)
![ezgif-368fdf2ecfd357](https://github.com/user-attachments/assets/3e84a44b-4549-4516-8c71-e7f7a129e090)


#### 2. 📇 회의록 기반 UI 요구사항 분석

- txt, md 등 여러 형태의 회의록 파일을 받아 UI 개선 요구사항을 분석한다.
- 사용자 피드백별 해결책을 제안한다.
- 분석 결과를 json, markdown 파일로 다운로드 가능하다.
- 정해진 시스템 프롬프트가 있지만, 사용자가 직접 화면에서 프롬프트 수정도 가능하다.

  
![ezgif-1b33ad3f72b925](https://github.com/user-attachments/assets/0413d11d-fe6e-482d-9f8a-51347d82f556)
![ezgif-1a88439846a227](https://github.com/user-attachments/assets/319b2610-1624-48da-b17e-15a17b53f974)



#### 3. 🛠️ 회의 결과 기반 UI 개선

- 요구사항이 담긴 파일을 입력하고, 기존 프론트엔드 코드를 입력하면 개선 결과 코드를 받을 수 있다.
- HTML 코드인 경우에는 화면에서 미리보기도 가능하다.
  
![ezgif-1d39768cc46cab](https://github.com/user-attachments/assets/3c553832-0e7c-4801-8d05-1d78d3908308)



#### 4. 💡 AI에게 질문하기

- AI agent가 질문에 적합한 tool을 선택하도록 한다.
- UI/UX 관련 질문의 경우에는, Azure AI Search로 사전에 정의된 검색 인덱스를 참조하도록 한다. 이때 Azure Blob Storage를 통해 보편적인 UI 관련 가이드 문서를 indexing에 사용했다.
- 핵심 문구 등 마이크로카피 관련 질문에는 prompt를 통해 마이크로카피 작성 가이드라인을 제시하여 적합한 답변을 낼 수 있도록 설정했다.

![ezgif-36666b510d4821](https://github.com/user-attachments/assets/e4c6cd97-9403-41d1-a20a-1b9c5a5e7087)

![ezgif-3dd52fc8619793](https://github.com/user-attachments/assets/a89f47f6-20b1-4a94-8da0-e12d6ec4989e)


#### 5. 💿 회의 녹음 기반 요약

- WAV 파일을 업로드하면 내용을 인식하여 회의 내용을 요약해준다.

![ezgif-167d9aabeaa9d7](https://github.com/user-attachments/assets/72573122-e58b-436e-8efe-d20892c30516)



#### 6. ⚠️ 관리자 기능 - 모니터링 상태 확인

- 특정 링크로 들어가서 .streamlit/secrets.toml로 설정한 비밀번호를 맞게 입력하면 langfuse 사이트로 연결되는 관리자 페이지 접속이 가능하다.
- langfuse와의 연결 상태도 확인 가능하다.

![ezgif-17fee65a8cd4b4](https://github.com/user-attachments/assets/5d74b869-4484-436f-9ecf-701955741741)
<img width="1671" height="680" alt="image" src="https://github.com/user-attachments/assets/7037981f-fc54-407e-81fe-c82745ee266f" />


---

### 😌 추가 개선 사항

- 오디오 연속 인식 기능 개선
- 속도 개선 및 기능 안정화


