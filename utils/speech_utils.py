from dotenv import load_dotenv
import os
import streamlit as st
import azure.cognitiveservices.speech as speechsdk
from langchain_openai import AzureChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import tempfile
import wave
import io

# 회의록을 WAV 음성 파일로 업로드할 수 있도록 하는 speech 관련 함수를 모아 놓은 모듈
# Azure Speech Service는 WAV 형식에서 가장 안정적인 성능을 제공합니다.

llm_name = os.getenv("AZURE_OPENAI_LLM_4o")

# Azure Speech SDK 설정 (WAV 전용 최적화)
@st.cache_resource
def init_speech_config():
    """Azure Speech Service 설정 초기화 - WAV 파일 전용"""
    speech_key = os.getenv("AZURE_SPEECH_KEY")
    service_region = os.getenv("AZURE_SPEECH_REGION")
    
    if not speech_key or not service_region:
        st.error("❌ Azure Speech 서비스 키 또는 지역이 설정되지 않았습니다.")
        st.info("""
        **환경변수 설정 필요:**
        - AZURE_SPEECH_KEY: Azure Speech 서비스 키
        - AZURE_SPEECH_REGION: Azure 리전 (예: koreacentral)
        """)
        return None
    
    # 환경변수 정리 및 검증
    speech_key = str(speech_key).strip()
    service_region = str(service_region).strip().lower()
    
    try:
        # Azure Speech SDK 설정 (WAV 최적화)
        speech_config = speechsdk.SpeechConfig(
            subscription=speech_key, 
            region=service_region
        )
        
        # WAV 파일 처리를 위한 최적 설정
        speech_config.speech_recognition_language = "ko-KR"        
        return speech_config
        
    except Exception as e:
        error_msg = str(e)
        st.error(f"❌ Azure Speech Config 초기화 실패: {error_msg}")
        
        # Azure 특화 오류 진단
        if "authentication" in error_msg.lower() or "unauthorized" in error_msg.lower():
            st.error("""
            🔐 **Azure 인증 문제:**
            - Azure Speech 서비스 키가 올바른지 확인
            - Azure Portal에서 키가 활성화되어 있는지 확인
            - 구독이 유효한지 확인
            """)
        elif "region" in error_msg.lower():
            st.error(f"""
            🌍 **Azure 리전 문제:**
            - 현재 리전: {service_region}
            - Azure Portal에서 정확한 리전명 확인 필요
            - 예시: koreacentral, eastus, westeurope
            """)
        
        return None

def validate_wav_file_only(file_data, file_name):
    """WAV 파일 전용 검증 및 Azure Speech SDK 호환성 확인"""
    try:
        file_extension = os.path.splitext(file_name)[1].lower()
        
        # WAV 파일만 허용
        if file_extension != '.wav':
            st.error(f"""
            ❌ **지원하지 않는 파일 형식: {file_extension.upper()}**
            
            이 서비스는 WAV 파일만 지원합니다.
            
            **WAV로 변환 방법:**
            - [Online Audio Converter](https://online-audio-converter.com/)
            - [Convertio](https://convertio.co/mp3-wav/)
            - FFmpeg: `ffmpeg -i input.{file_extension[1:]} -acodec pcm_s16le -ar 16000 -ac 1 output.wav`
            """)
            return None, False
        
        # 임시 WAV 파일 생성
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            tmp_file.write(file_data)
            tmp_file_path = tmp_file.name
        
        # WAV 파일 상세 검증 및 Azure Speech SDK 호환성 확인
        try:
            with wave.open(tmp_file_path, 'rb') as wav_file:
                channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()
                frame_rate = wav_file.getframerate()
                frames = wav_file.getnframes()
                duration = frames / frame_rate
                
                
                # Azure Speech Service 최적화 권장사항
                optimization_warnings = []
                if channels > 2:
                    optimization_warnings.append("채널 수가 많습니다. 모노(1채널) 또는 스테레오(2채널)를 권장합니다.")
                if sample_width != 2:
                    optimization_warnings.append("16-bit PCM을 권장합니다.")
                if frame_rate < 16000:
                    optimization_warnings.append("16kHz 이상의 샘플링 레이트를 권장합니다.")
                elif frame_rate > 48000:
                    optimization_warnings.append("48kHz 이하의 샘플링 레이트를 권장합니다.")
                
                if optimization_warnings:
                    st.warning("**🔧 Azure Speech Service 최적화 권장사항:**")
                    for warning in optimization_warnings:
                        st.warning(f"- {warning}")
                    
                    st.info("""
                    **최적 WAV 설정으로 변환:**
                    ```bash
                    ffmpeg -i input.wav -acodec pcm_s16le -ar 16000 -ac 1 optimized.wav
                    ```
                    """)
                
                return tmp_file_path, True
                    
        except wave.Error as e:
            st.error(f"❌ WAV 파일 오류: {e}")
            st.error("""
            **WAV 파일 문제 해결:**
            1. 파일이 손상되지 않았는지 확인
            2. 압축된 WAV가 아닌 PCM WAV 사용
            3. 오디오 편집 프로그램으로 재저장
            """)
            os.unlink(tmp_file_path)
            return None, False
            
    except Exception as e:
        st.error(f"❌ WAV 파일 준비 중 오류: {e}")
        return None, False

# Azure Speech Service 전용 안전한 음성 인식 함수
def speech_to_text_safe(wav_file_path, speech_config):
    """Azure Speech Service를 이용한 WAV 파일 전용 안전한 음성 인식"""
    
    # 1단계: WAV 파일 존재 및 접근성 확인
    if not os.path.exists(wav_file_path):
        st.error("❌ WAV 파일이 존재하지 않습니다.")
        return None
    
    # 파일 확장자 재확인
    if not wav_file_path.lower().endswith('.wav'):
        st.error("❌ WAV 파일이 아닙니다.")
        return None
    
    try:
        # 파일 크기 및 유효성 확인
        file_size = os.path.getsize(wav_file_path)
        if file_size == 0:
            st.error("❌ 빈 WAV 파일입니다.")
            return None
        if file_size > 100 * 1024 * 1024:  # 100MB Azure 제한
            st.error("❌ WAV 파일이 Azure 제한(100MB)을 초과합니다.")
            return None

        st.info(f"📁 WAV 파일 크기: {file_size / (1024 * 1024):.2f} MB")

    except Exception as e:
        st.error(f"❌ WAV 파일 정보 확인 실패: {e}")
        return None
    
    # 2단계: Azure AudioConfig 생성 (WAV 전용)
    audio_config = None
    try:        
        # 절대 경로로 변환 (Azure SDK 요구사항)
        abs_path = os.path.abspath(wav_file_path)
        
        # WAV 파일용 AudioConfig 생성
        audio_config = speechsdk.AudioConfig(filename=abs_path)
        
    except Exception as e:
        st.error(f"❌ Azure AudioConfig 생성 실패: {e}")
        st.error("""
        **Azure AudioConfig 문제 해결:**
        - WAV 파일 경로에 특수문자가 없는지 확인
        - 파일에 읽기 권한이 있는지 확인
        - 다른 프로그램에서 파일을 사용 중이지 않은지 확인
        """)
        return None
    
    # 3단계: Azure SpeechRecognizer 생성
    speech_recognizer = None
    try:     
        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            audio_config=audio_config
        )
        
    except Exception as e:
        error_msg = str(e)
        st.error(f"❌ Azure SpeechRecognizer 생성 실패: {error_msg}")
        
        if "SPXERR_INVALID_HEADER" in error_msg:
            st.error("""
            **WAV 헤더 오류 해결:**
            - WAV 파일이 표준 PCM 형식인지 확인
            - 압축된 WAV 대신 비압축 WAV 사용
            - 오디오 편집기로 WAV 재저장
            """)
        
        return None
    
    # 4단계: Azure Speech Service 음성 인식 실행
    try:
        st.info("🎯 Azure Speech Service로 음성 인식 시작...")
        
        # 단일 음성 인식 시도
        result = speech_recognizer.recognize_once_async().get()
        
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            recognized_text = result.text.strip()
            if len(recognized_text) > 1:
                st.success(f"✅ 음성 인식 성공 (길이: {len(recognized_text)}자)")
                return recognized_text
            else:
                st.info("ℹ️ 짧은 텍스트 인식됨, 연속 인식 시도...")
                return continuous_recognition_wav_safe(speech_recognizer)
                
        elif result.reason == speechsdk.ResultReason.NoMatch:
            st.warning("⚠️ Azure Speech Service에서 음성을 인식하지 못했습니다. 연속 인식 시도...")
            return continuous_recognition_wav_safe(speech_recognizer)
            
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation = result.cancellation_details
            st.error(f"❌ Azure Speech Service 인식 취소: {cancellation.reason}")
            
            if cancellation.reason == speechsdk.CancellationReason.Error:
                st.error(f"🔍 Azure 오류 세부사항: {cancellation.error_details}")
                
                # Azure 특화 오류 해결 가이드
                if "authentication" in cancellation.error_details.lower():
                    st.error("🔑 Azure 인증 오류: Speech Service 키를 확인하세요.")
                elif "quota" in cancellation.error_details.lower():
                    st.error("📊 Azure 할당량 초과: 사용량을 확인하세요.")
            
            return None
    
    except Exception as e:
        st.error(f"❌ Azure Speech Service 음성 인식 오류: {e}")
        return None
    
    finally:
        # Azure 리소스 정리
        if speech_recognizer:
            try:
                speech_recognizer = None
            except:
                pass

def continuous_recognition_wav_safe(speech_recognizer):
    """Azure Speech Service WAV 파일 전용 안전한 연속 음성 인식"""
    try:
        results = []
        done = False
        error_occurred = False
        
        def result_handler(evt):
            if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                text = evt.result.text.strip()
                if text:
                    results.append(text)
                    st.info(f"✅ 조각 #{len(results)}: {text[:50]}...")
        
        def stop_handler(evt):
            nonlocal done
            done = True
            st.info("🏁 Azure Speech Service 연속 인식 완료")
        
        def error_handler(evt):
            nonlocal error_occurred, done
            error_occurred = True
            done = True
            st.error(f"❌ Azure Speech Service 연속 인식 오류: {evt}")
        
        # Azure Speech Service 이벤트 핸들러 연결
        speech_recognizer.recognized.connect(result_handler)
        speech_recognizer.session_stopped.connect(stop_handler)
        speech_recognizer.canceled.connect(error_handler)
        
        # Azure 연속 인식 시작
        speech_recognizer.start_continuous_recognition()
        
        # 진행 상황 표시 (최대 3분 - WAV 파일은 더 오래 걸릴 수 있음)
        import time
        max_wait = 180  # 3분
        elapsed = 0
        
        progress = st.progress(0)
        status_text = st.empty()
        
        while not done and elapsed < max_wait:
            time.sleep(1)
            elapsed += 1
            progress.progress(elapsed / max_wait)
            status_text.text(f"Azure Speech Service 처리 중... {elapsed}/{max_wait}초")
        
        # Azure 연속 인식 정리
        speech_recognizer.stop_continuous_recognition()
        progress.progress(1.0)
        status_text.text("처리 완료")
        
        if error_occurred:
            st.error("❌ Azure Speech Service 연속 인식 중 오류 발생")
            return None
        
        if results:
            full_text = " ".join(results)
            st.success(f"✅ Azure Speech Service로 총 {len(results)}개 조각 인식 완료")
            st.info(f"📝 총 텍스트 길이: {len(full_text)}자")
            return full_text
        else:
            st.warning("⚠️ Azure Speech Service에서 인식된 텍스트가 없습니다.")
            st.info("""
            **음성 인식 개선 방법:**
            - 더 선명한 음질의 WAV 파일 사용
            - 배경 소음이 적은 녹음 사용
            - 16kHz, 16-bit, 모노 WAV로 변환
            """)
            return None
            
    except Exception as e:
        st.error(f"❌ Azure Speech Service 연속 인식 처리 오류: {e}")
        return None

# WAV 파일 품질 검사 함수
def check_wav_quality_for_azure(wav_file_path):
    """Azure Speech Service 최적화를 위한 WAV 파일 품질 검사"""
    try:
        with wave.open(wav_file_path, 'rb') as wav_file:
            params = wav_file.getparams()
            
            quality_score = 100
            recommendations = []
            
            # Azure Speech Service 최적 설정 기준으로 점수 계산
            if params.nchannels > 2:
                quality_score -= 20
                recommendations.append("채널을 1-2개로 줄이세요")
            elif params.nchannels == 1:
                quality_score += 10  # 모노 채널 보너스
            
            if params.sampwidth != 2:  # 16-bit
                quality_score -= 30
                recommendations.append("16-bit로 변환하세요")
            
            if params.framerate < 16000:
                quality_score -= 25
                recommendations.append("16kHz 이상으로 업샘플링하세요")
            elif params.framerate == 16000:
                quality_score += 15  # 16kHz 보너스
            elif params.framerate > 48000:
                quality_score -= 10
                recommendations.append("48kHz 이하로 다운샘플링하세요")
            
            return {
                "quality_score": max(0, quality_score),
                "recommendations": recommendations,
                "azure_optimized": quality_score >= 90
            }
            
    except Exception as e:
        return {
            "quality_score": 0,
            "recommendations": [f"파일 분석 실패: {e}"],
            "azure_optimized": False
        }

# 레거시 함수명 호환성 유지 (WAV 전용으로 변경)
def validate_and_prepare_audio(file_data, file_name):
    """레거시 호환성을 위한 함수 - WAV 파일만 지원"""
    return validate_wav_file_only(file_data, file_name)