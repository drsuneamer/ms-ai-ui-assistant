from dotenv import load_dotenv
import os
import streamlit as st
import azure.cognitiveservices.speech as speechsdk
from langchain_openai import AzureChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import tempfile
import wave
import io
from speech_utils import init_speech_config, speech_to_text_safe


# 환경변수 로드
load_dotenv()

# 페이지 설정
st.set_page_config(page_title="회의 녹음 기반 요약", page_icon="💿")
st.title("💿 회의 녹음 기반 요약")
st.markdown("음성 파일을 업로드하면 AI가 자동으로 텍스트 변환 후 회의 내용을 요약해드립니다.")


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


# 회의 내용 요약 함수
def summarize_meeting(llm, transcript):
    """회의 텍스트를 요약하는 함수"""
    system_prompt = """
    당신은 회의 내용을 전문적으로 요약하는 AI 어시스턴트입니다.
    다음 회의 녹취록을 분석하여 체계적으로 요약해주세요:

    **요약 형식:**
    ## 📋 회의 요약

    ### 🎯 주요 안건
    - 논의된 핵심 주제들을 나열

    ### 💡 주요 결정사항
    - 회의에서 결정된 중요한 사항들

    ### 📝 액션 아이템
    - 담당자: 해야 할 일
    - 기한: 언제까지

    ### 🔍 핵심 키워드
    - 회의에서 자주 언급된 키워드들

    ### 📊 회의 분석
    - 회의 분위기, 참석자 의견 등 전반적인 분석

    명확하고 간결하게 요약하되, 중요한 정보는 빠뜨리지 마세요.
    """
    
    try:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"다음 회의 녹취록을 요약해주세요:\n\n{transcript}")
        ]
        
        response = llm.invoke(messages)
        return response.content
    
    except Exception as e:
        st.error(f"요약 생성 중 오류 발생: {e}")
        return None

# 메인 함수
def main():
    # 클라이언트 초기화
    speech_config = init_speech_config()
    llm = init_langchain_client()
    
    if not speech_config or not llm:
        st.stop()
    
    # 컬럼 레이아웃
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("🎤 음성 파일 업로드")
        
        # 개선된 파일 형식 안내
        st.info("""
        **📁 권장 파일 형식 (안정성 순):**
        1. **MP3**: 가장 안정적이고 호환성 좋음 ⭐⭐⭐
        2. **M4A**: 일반적으로 잘 작동함 ⭐⭐
        3. **WAV**: PCM 16bit만 권장, 헤더 오류 가능 ⭐
        
        **🚫 피해야 할 것:**
        - 손상된 파일, 비표준 인코딩
        - 100MB 초과 파일 (나누어서 업로드)
        """)
        
        # 파일 업로더
        uploaded_file = st.file_uploader(
            "회의 녹음 파일을 업로드하세요",
            type=["wav", "mp3", "m4a"],
            help="MP3 파일을 가장 권장합니다"
        )
        
        if uploaded_file is not None:
            st.success(f"✅ 파일 업로드 완료: {uploaded_file.name}")
            
            # 파일 정보 표시
            file_size = len(uploaded_file.getvalue()) / (1024 * 1024)  # MB
            st.info(f"📁 파일 크기: {file_size:.2f} MB")
            
            # 파일 크기 제한 확인
            if file_size > 100:
                st.error("❌ 파일이 100MB를 초과합니다. 더 작은 파일로 나누어 업로드해주세요.")
                st.stop()
            elif file_size > 50:
                st.warning("⚠️ 파일이 50MB를 초과합니다. 처리 시간이 오래 걸릴 수 있습니다.")
            
            # 오디오 플레이어
            st.audio(uploaded_file.getvalue())
            
            # 변환 시작 버튼
            if st.button("🚀 음성 → 텍스트 변환 및 요약", type="primary", use_container_width=True):
                # 파일 검증 및 준비
                with st.spinner("📋 파일 검증 및 준비 중..."):
                    tmp_file_path, is_valid = validate_and_prepare_audio(
                        uploaded_file.getvalue(), 
                        uploaded_file.name
                    )
                
                if not is_valid or not tmp_file_path:
                    st.error("❌ 파일 준비에 실패했습니다.")
                    return
                
                try:
                    # 음성을 텍스트로 변환
                    transcript = speech_to_text_safe(tmp_file_path, speech_config)
                    
                    if transcript and transcript.strip():
                        st.session_state["transcript"] = transcript
                        st.success(f"✅ 음성 인식 완료! (인식된 텍스트 길이: {len(transcript)}자)")
                        
                        # 요약 생성
                        with st.spinner("📝 AI가 회의 내용을 요약 중입니다..."):
                            summary = summarize_meeting(llm, transcript)
                            if summary:
                                st.session_state["summary"] = summary
                                st.balloons()  # 성공 애니메이션
                                st.success("🎉 변환 및 요약이 완료되었습니다!")
                    else:
                        st.error("❌ 음성 인식에 실패했습니다. 파일 형식을 확인하거나 MP3로 변환해보세요.")
                
                finally:
                    # 임시 파일 삭제
                    try:
                        if tmp_file_path and os.path.exists(tmp_file_path):
                            os.unlink(tmp_file_path)
                    except:
                        pass
    
    with col2:
        st.subheader("📝 변환 및 요약 결과")
        
        # 요약 결과 표시
        if "summary" in st.session_state:
            st.markdown("#### 🎯 AI 요약 결과")
            st.markdown(st.session_state["summary"])
            
            # 다운로드 버튼
            col_a, col_b = st.columns(2)
            with col_a:
                st.download_button(
                    label="📥 요약 다운로드 (MD)",
                    data=st.session_state["summary"],
                    file_name="meeting_summary.md",
                    mime="text/markdown",
                    use_container_width=True,
                    key="download_summary_btn"
                )
            with col_b:
                if "transcript" in st.session_state:
                    st.download_button(
                        label="📄 전문 다운로드 (TXT)",
                        data=st.session_state["transcript"],
                        file_name="meeting_transcript.txt",
                        mime="text/plain",
                        use_container_width=True,
                        key="download_transcript_btn"
                    )
            
            # 전문 보기 (접히는 형태)
            if "transcript" in st.session_state:
                with st.expander("📖 전체 녹취록 보기"):
                    st.text_area("변환된 텍스트", st.session_state["transcript"], height=300, disabled=True, key="transcript_display")
        
        else:
            st.info("👆 음성 파일을 업로드하고 '변환 및 요약' 버튼을 눌러주세요.")
            
            # 상세 문제 해결 가이드
            st.markdown("""
            **🚨 SPXERR_INVALID_HEADER 문제 진단:**
            
            **🔍 단계별 체크리스트:**
            
            **1️⃣ 환경변수 확인**
            ```
            AZURE_SPEECH_KEY=당신의32자키 (따옴표없이)
            AZURE_SPEECH_REGION=koreacentral (소문자)
            ```
            
            **2️⃣ Azure Portal 확인**
            - Speech 서비스가 활성화되어 있는가?
            - 올바른 구독에서 키를 가져왔는가?
            - 키를 재생성해볼 수 있는가?
            
            **3️⃣ 네트워크 & 권한**
            - 방화벽이 Azure 접속을 차단하고 있는가?
            - 프록시 설정이 있는가?
            - 임시 폴더 쓰기 권한이 있는가?
            
            **4️⃣ 파일 문제**
            - 다른 미디어 플레이어에서 재생되는가?
            - MP3로 변환했는가?
            - 파일 크기가 적당한가? (<50MB 권장)
            
            **🆘 긴급 해결책:**
            - `.env` 파일 재생성
            - Azure Speech 키 새로 발급
            - 다른 리전으로 시도 (예: eastus)
            - 작은 테스트 파일로 시도
            """)
            
            # 환경변수 디버깅 도구 추가
            with st.expander("🔧 환경변수 디버깅 도구"):
                if st.button("환경변수 체크", type="secondary"):
                    key = os.getenv("AZURE_SPEECH_KEY", "")
                    region = os.getenv("AZURE_SPEECH_REGION", "")
                    
                    st.write("**환경변수 상태:**")
                    st.write(f"- AZURE_SPEECH_KEY: {'설정됨' if key else '❌ 미설정'} (길이: {len(key)})")
                    st.write(f"- AZURE_SPEECH_REGION: {region if region else '❌ 미설정'}")
                    
                    if key and region:
                        st.write("**기본 검증:**")
                        if len(key) >= 30:
                            st.write("✅ 키 길이 적절")
                        else:
                            st.write("⚠️ 키가 너무 짧을 수 있음")
                            
                        if region.lower() in ['koreacentral', 'eastus', 'westus2']:
                            st.write("✅ 일반적인 리전")
                        else:
                            st.write(f"⚠️ 리전 확인 필요: {region}")
                    
                    # 간단한 연결 테스트 (실제 API 호출 없이)
                    try:
                        test_config = speechsdk.SpeechConfig(subscription=key, region=region)
                        st.write("✅ SpeechConfig 생성 가능")
                    except Exception as e:
                        st.write(f"❌ SpeechConfig 생성 실패: {e}")

if __name__ == "__main__":
    main()