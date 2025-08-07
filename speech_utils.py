from dotenv import load_dotenv
import os
import streamlit as st
import azure.cognitiveservices.speech as speechsdk
from langchain_openai import AzureChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import tempfile
import wave
import io

# 회의록을 음성 파일로 업로드할 수 있도록 하는 speech 관련 함수를 모아 놓은 모듈

# Azure Speech SDK 설정 (강화된 오류 처리)
@st.cache_resource
def init_speech_config():
    speech_key = os.getenv("AZURE_SPEECH_KEY")
    service_region = os.getenv("AZURE_SPEECH_REGION")
    
    if not speech_key or not service_region:
        st.error("Azure Speech 서비스 키 또는 지역이 설정되지 않았습니다.")
        return None
    
    # 환경변수 정리 및 검증
    speech_key = str(speech_key).strip()
    service_region = str(service_region).strip().lower()
    
    # 빈 값 체크
    if not speech_key or not service_region:
        st.error("Azure Speech 키 또는 리전이 비어있습니다.")
        return None
    
    # 키 형식 검증 (Azure 키는 보통 32자)
    if len(speech_key) < 20:
        st.error("Azure Speech 키가 너무 짧습니다. 올바른 키인지 확인하세요.")
        return None
    
    try:
        # 가장 기본적인 방식으로 config 생성
        speech_config = speechsdk.SpeechConfig(
            subscription=speech_key, 
            region=service_region
        )
        
        # 연결 테스트를 위한 기본 설정만
        speech_config.speech_recognition_language = "ko-KR"
        
        st.success(f"✅ Speech Config 생성 성공 (리전: {service_region})")
        return speech_config
        
    except Exception as e:
        error_msg = str(e)
        st.error(f"❌ Speech Config 초기화 실패: {error_msg}")
        
        # 구체적인 문제 진단
        if "authentication" in error_msg.lower():
            st.error("""
            🔐 **인증 문제:**
            - Azure Speech 키가 올바른지 확인
            - 키가 활성화되어 있는지 확인
            - Azure Portal에서 키 재생성 시도
            """)
        elif "region" in error_msg.lower():
            st.error(f"""
            🌍 **리전 문제:**
            - 현재 리전: {service_region}
            - Azure Portal에서 정확한 리전명 확인
            - 예: koreacentral, eastus, westeurope
            """)
        elif "invalid" in error_msg.lower():
            st.error("""
            ⚠️ **설정 문제:**
            - 환경변수에 특수문자나 공백 확인
            - .env 파일 형식 확인
            - 따옴표 없이 값만 입력했는지 확인
            """)
        
        return None

# LangChain Azure OpenAI 클라이언트 설정
@st.cache_resource
def init_langchain_client():
    try:
        llm = AzureChatOpenAI(
            azure_deployment=os.getenv("AZURE_OPENAI_LLM_GPT4"),
            api_version=os.getenv("OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0.1
        )
        return llm
    except Exception as e:
        st.error(f"LangChain 클라이언트 초기화 실패: {e}")
        return None

# 오디오 파일 검증 및 변환 함수 (강화됨)
def validate_and_prepare_audio(file_data, file_name):
    """오디오 파일 검증 및 Azure Speech SDK 호환 형식으로 준비"""
    try:
        file_extension = os.path.splitext(file_name)[1].lower()
        
        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
            tmp_file.write(file_data)
            tmp_file_path = tmp_file.name
        
        # WAV 파일의 경우 상세 검증
        if file_extension == '.wav':
            try:
                with wave.open(tmp_file_path, 'rb') as wav_file:
                    channels = wav_file.getnchannels()
                    sample_width = wav_file.getsampwidth()
                    frame_rate = wav_file.getframerate()
                    frames = wav_file.getnframes()
                    duration = frames / frame_rate
                    
                    st.info(f"📊 WAV 파일 정보: {channels}채널, {sample_width*8}bit, {frame_rate}Hz, {duration:.1f}초")
                    
                    # Azure Speech SDK 호환성 확인
                    if channels > 2:
                        st.warning("⚠️ 채널 수가 많습니다. 1-2채널을 권장합니다.")
                    if sample_width not in [1, 2, 3, 4]:
                        st.warning("⚠️ 지원하지 않는 비트 깊이입니다.")
                    if frame_rate < 8000 or frame_rate > 48000:
                        st.warning("⚠️ 샘플링 레이트가 권장 범위(8-48kHz)를 벗어납니다.")
                        
                    return tmp_file_path, True
                    
            except wave.Error as e:
                st.error(f"WAV 파일이 손상되었거나 지원하지 않는 형식입니다: {e}")
                os.unlink(tmp_file_path)
                return None, False
                
        else:
            # MP3, M4A 등 다른 형식
            file_size_mb = len(file_data) / (1024 * 1024)
            st.info(f"📊 {file_extension.upper()} 파일 크기: {file_size_mb:.2f} MB")
            return tmp_file_path, True
            
    except Exception as e:
        st.error(f"파일 준비 중 오류 발생: {e}")
        return None, False

# 단계별 안전한 음성 인식 함수
def speech_to_text_safe(audio_file_path, speech_config):
    """단계별 안전한 음성 인식 (SPXERR_INVALID_HEADER 방지)"""
    
    # 1단계: 파일 존재 및 접근 가능성 확인
    if not os.path.exists(audio_file_path):
        st.error("❌ 오디오 파일이 존재하지 않습니다.")
        return None
    
    try:
        # 파일 크기 확인
        file_size = os.path.getsize(audio_file_path)
        if file_size == 0:
            st.error("❌ 빈 파일입니다.")
            return None
        if file_size > 100 * 1024 * 1024:  # 100MB
            st.error("❌ 파일이 너무 큽니다 (100MB 제한).")
            return None
            
        st.info(f"📁 파일 크기: {file_size / 1024 / 1024:.2f} MB")
        
    except Exception as e:
        st.error(f"파일 정보 확인 실패: {e}")
        return None
    
    # 2단계: AudioConfig 생성 (가장 안전한 방식)
    audio_config = None
    try:
        st.info("🎵 AudioConfig 생성 중...")
        
        # 절대 경로로 변환
        abs_path = os.path.abspath(audio_file_path)
        st.info(f"📂 파일 경로: {abs_path}")
        
        # 기본 AudioConfig 생성
        audio_config = speechsdk.AudioConfig(filename=abs_path)
        st.success("✅ AudioConfig 생성 성공")
        
    except Exception as e:
        st.error(f"❌ AudioConfig 생성 실패: {e}")
        
        # 대체 방법: 스트림 방식으로 시도
        try:
            st.info("🔄 스트림 방식으로 재시도...")
            
            # 파일을 바이너리로 읽어서 처리
            with open(audio_file_path, 'rb') as audio_file:
                audio_data = audio_file.read()
            
            # 메모리 스트림 생성
            import io
            stream = io.BytesIO(audio_data)
            
            # PushAudioInputStream 사용
            push_stream = speechsdk.audio.PushAudioInputStream()
            audio_config = speechsdk.AudioConfig(stream=push_stream)
            
            # 데이터 푸시
            push_stream.write(audio_data)
            push_stream.close()
            
            st.success("✅ 스트림 AudioConfig 생성 성공")
            
        except Exception as e2:
            st.error(f"❌ 스트림 방식도 실패: {e2}")
            return None
    
    # 3단계: SpeechRecognizer 생성 (매우 신중하게)
    speech_recognizer = None
    try:
        st.info("🤖 SpeechRecognizer 생성 중...")
        
        # 최소한의 설정으로 생성
        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            audio_config=audio_config
        )
        
        st.success("✅ SpeechRecognizer 생성 성공!")
        
    except Exception as e:
        error_msg = str(e)
        st.error(f"❌ SpeechRecognizer 생성 실패: {error_msg}")
        
        # 상세한 오류 분석
        if "0xa" in error_msg or "SPXERR_INVALID_HEADER" in error_msg:
            st.error("""
            🔧 **헤더 오류 해결 방법:**
            
            **즉시 시도할 수 있는 방법:**
            1. **환경변수 재확인**
               - AZURE_SPEECH_KEY: 32자리 문자열
               - AZURE_SPEECH_REGION: 소문자 (예: koreacentral)
               
            2. **Azure Portal 확인**
               - Speech 서비스가 활성화되어 있는지
               - 키를 새로 생성해보기
               - 올바른 리전 확인
               
            3. **파일 형식**
               - MP3 파일로 변환 시도
               - 파일 재생 테스트 (미디어 플레이어에서)
               
            4. **권한 문제**
               - 임시 디렉토리 접근 권한
               - 방화벽/보안 소프트웨어 확인
            """)
        
        return None
    
    # 4단계: 실제 음성 인식
    try:
        st.info("🎯 음성 인식 시작...")
        
        # 단순한 한 번 인식부터 시작
        result = speech_recognizer.recognize_once_async().get()
        
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            if len(result.text.strip()) > 5:  # 최소 길이 확인
                st.success(f"✅ 인식 성공! (길이: {len(result.text)}자)")
                return result.text
            else:
                st.info("ℹ️ 짧은 텍스트 인식됨, 연속 인식 시도...")
                return continuous_recognition_safe(speech_recognizer)
                
        elif result.reason == speechsdk.ResultReason.NoMatch:
            st.warning("⚠️ 음성 미인식, 연속 인식 시도...")
            return continuous_recognition_safe(speech_recognizer)
            
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation = result.cancellation_details
            st.error(f"❌ 인식 취소: {cancellation.reason}")
            
            if cancellation.reason == speechsdk.CancellationReason.Error:
                st.error(f"🔍 상세 오류: {cancellation.error_details}")
            
            return None
    
    except Exception as e:
        st.error(f"음성 인식 과정 오류: {e}")
        return None
    
    finally:
        # 리소스 정리
        if speech_recognizer:
            try:
                speech_recognizer = None
            except:
                pass
            
            
def continuous_recognition_safe(speech_recognizer):
    """안전한 연속 음성 인식"""
    try:
        results = []
        done = False
        error_occurred = False
        
        def result_handler(evt):
            if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                text = evt.result.text.strip()
                if text:
                    results.append(text)
                    st.info(f"✅ 조각 #{len(results)}: {text[:30]}...")
        
        def stop_handler(evt):
            nonlocal done
            done = True
        
        def error_handler(evt):
            nonlocal error_occurred, done
            error_occurred = True
            done = True
            st.error(f"❌ 연속 인식 오류: {evt}")
        
        # 핸들러 연결
        speech_recognizer.recognized.connect(result_handler)
        speech_recognizer.session_stopped.connect(stop_handler)
        speech_recognizer.canceled.connect(error_handler)
        
        # 인식 시작
        speech_recognizer.start_continuous_recognition()
        
        # 대기 (최대 2분)
        import time
        max_wait = 120
        elapsed = 0
        
        progress = st.progress(0)
        while not done and elapsed < max_wait:
            time.sleep(1)
            elapsed += 1
            progress.progress(elapsed / max_wait)
        
        # 정리
        speech_recognizer.stop_continuous_recognition()
        progress.progress(1.0)
        
        if error_occurred:
            return None
        
        if results:
            full_text = " ".join(results)
            st.success(f"✅ 총 {len(results)}개 조각 인식 완료")
            return full_text
        else:
            st.warning("⚠️ 인식된 텍스트가 없습니다")
            return None
            
    except Exception as e:
        st.error(f"연속 인식 오류: {e}")
        return None
