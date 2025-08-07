from dotenv import load_dotenv
import os, tempfile, wave
import streamlit as st
import azure.cognitiveservices.speech as speechsdk
from langchain.schema import HumanMessage, SystemMessage
from utils.speech_utils import init_speech_config, speech_to_text_safe
from utils.langchain_utils import init_langchain_client

# 환경변수 로드
load_dotenv()
llm_name = os.getenv("AZURE_OPENAI_LLM_4o")  # 음성 처리 위해 mini 대신 GPT-4o 사용

# 페이지 설정
st.set_page_config(page_title="회의 녹음 기반 요약", page_icon="💿")
st.title("💿 회의 녹음 기반 요약")
st.markdown("WAV 형식의 음성 파일을 업로드하면 AI가 자동으로 텍스트 변환 후 회의 내용을 요약해드립니다.")

# WAV 파일 검증 및 준비 함수
def validate_and_prepare_wav_audio(file_data, file_name):
    """WAV 파일 검증 및 Azure Speech SDK 호환 형식으로 준비"""
    try:
        file_extension = os.path.splitext(file_name)[1].lower()
        
        # WAV 파일만 허용
        if file_extension != '.wav':
            st.error(f"❌ {file_extension.upper()} 파일은 지원하지 않습니다. WAV 파일만 업로드해주세요.")
            return None, False
        
        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            tmp_file.write(file_data)
            tmp_file_path = tmp_file.name
        
        # WAV 파일 상세 검증
        try:
            with wave.open(tmp_file_path, 'rb') as wav_file:
                channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()
                frame_rate = wav_file.getframerate()
                frames = wav_file.getnframes()
                duration = frames / frame_rate

                # Azure Speech SDK 호환성 경고
                warnings = []
                if channels > 2:
                    warnings.append("⚠️ 채널 수가 많습니다. 모노(1채널) 또는 스테레오(2채널)를 권장합니다.")
                if sample_width != 2:
                    warnings.append("⚠️ 16-bit PCM을 권장합니다.")
                if frame_rate < 8000 or frame_rate > 48000:
                    warnings.append("⚠️ 샘플링 레이트가 권장 범위(8-48kHz)를 벗어납니다.")
                
                if warnings:
                    for warning in warnings:
                        st.warning(warning)
                    st.info("💡 파일이 제대로 인식되지 않으면 권장 설정으로 변환해보세요.")
                
                return tmp_file_path, True
                
        except wave.Error as e:
            st.error(f"❌ WAV 파일이 손상되었거나 지원하지 않는 형식입니다: {e}")
            os.unlink(tmp_file_path)
            return None, False
            
    except Exception as e:
        st.error(f"❌ 파일 준비 중 오류 발생: {e}")
        return None, False

# 회의 내용 요약 함수
def summarize_meeting(llm, transcript):
    """회의 텍스트를 요약하는 함수"""
    system_prompt = """
    당신은 회의 내용을 전문적으로 요약하는 AI 어시스턴트입니다.
    음성에서 변환된 텍스트이므로 일부 불완전한 부분이 있을 수 있습니다.
    맥락을 파악하여 의미를 정확히 전달하도록 요약해주세요.

    **요약 형식:**
    ## 📋 회의 요약

    ### 🎯 주요 안건
    - 논의된 핵심 주제들을 명확하게 정리

    ### 💡 주요 결정사항
    - 회의에서 결정된 구체적인 사항들
    - 합의된 내용과 반대 의견 구분

    ### 📝 액션 아이템
    - 담당자: 구체적인 업무 내용
    - 기한: 명시된 또는 추정되는 완료 시점

    ### 🔍 핵심 키워드
    - 회의에서 중요하게 다뤄진 주요 개념들

    ### 📊 회의 분석
    - 참석자들의 주요 의견과 분위기
    - 향후 진행 방향 및 우려사항

    **주의사항:**
    - 음성 변환 시 발생할 수 있는 오타나 어색한 표현은 자연스럽게 교정
    - 불분명한 부분은 앞뒤 맥락으로 추정하여 명확히 표현
    - 중요한 수치나 날짜는 특별히 주의하여 정확히 기록
    """
    
    try:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"""다음은 음성에서 변환된 회의 녹취록입니다:

{transcript}

위 내용을 체계적으로 요약하고, 음성 변환 과정에서 발생한 불완전한 부분들을 맥락에 맞게 보완해주세요.""")
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
    llm = init_langchain_client(llm_name, 0.1)
    
    if not speech_config or not llm:
        st.stop()
    
    # 컬럼 레이아웃
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("🎤 WAV 음성 파일 업로드")
        
        # WAV 전용 안내
        st.info("""
        **📁 지원 파일 형식: WAV만 허용**
        
        **✅ 권장 WAV 설정:**
        - 형식: PCM (압축되지 않은 WAV)
        - 비트 깊이: 16-bit
        - 샘플링 레이트: 16kHz 또는 48kHz
        - 채널: 모노(1채널) 권장, 스테레오(2채널) 가능
        """)
        
        # WAV 파일만 허용하는 업로더
        uploaded_file = st.file_uploader(
            "WAV 회의 녹음 파일을 업로드하세요",
            type=["wav"],  # WAV만 허용
            help="WAV 형식만 지원합니다. 다른 형식은 WAV로 변환 후 업로드해주세요."
        )
        
        if uploaded_file is not None:
            st.success(f"✅ WAV 파일 업로드 완료: {uploaded_file.name}")
            
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
                # WAV 파일 검증 및 준비
                with st.spinner("📋 WAV 파일 검증 및 준비 중..."):
                    tmp_file_path, is_valid = validate_and_prepare_wav_audio(
                        uploaded_file.getvalue(), 
                        uploaded_file.name
                    )
                
                if not is_valid or not tmp_file_path:
                    st.error("❌ WAV 파일 준비에 실패했습니다.")
                    return
                
                try:
                    # 음성을 텍스트로 변환
                    with st.spinner("🎯 음성을 텍스트로 변환 중... (WAV 파일 처리 중)"):
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
                        st.error("""
                        ❌ 음성 인식에 실패했습니다.
                        
                        **해결 방법:**
                        1. WAV 파일이 손상되지 않았는지 확인
                        2. 권장 설정(16-bit PCM, 16kHz)으로 변환
                        3. 배경 소음이 적은 깨끗한 녹음 사용
                        4. 파일 크기가 너무 크지 않은지 확인
                        """)
                
                except Exception as e:
                    st.error(f"❌ 음성 변환 중 오류 발생: {e}")
                    st.error("""
                    **WAV 파일 오류 해결 방법:**
                    1. 다른 WAV 파일로 테스트
                    2. 오디오 편집 프로그램으로 파일 재저장
                    3. 권장 설정으로 변환:
                       `ffmpeg -i input.wav -acodec pcm_s16le -ar 16000 -ac 1 output.wav`
                    """)
                
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
            st.info("👆 WAV 음성 파일을 업로드하고 '변환 및 요약' 버튼을 눌러주세요.")

if __name__ == "__main__":
    main()