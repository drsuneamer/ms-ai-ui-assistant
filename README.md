# MS-PJT

> 25-08-05 (화)

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
pip install streamlit openai python-dotenv
```

requirements.txt 만드는 법
```bash
pip freeze > requirements.txt
```

requirements.txt 기반 설치
```bash
pip install -r requirements.txt
```

Streamlit 메인 페이지 생성 (Home.py)