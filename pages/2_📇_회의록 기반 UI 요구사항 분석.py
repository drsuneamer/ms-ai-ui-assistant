from dotenv import load_dotenv
import os
import streamlit as st
from langchain_openai import AzureChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import json
import tempfile
from utils.speech_utils import init_speech_config, speech_to_text_safe, validate_wav_file_only
from utils.langchain_utils import init_langchain_client
from utils.langfuse_monitor import langfuse_monitor, log_user_action, log_generation


# 사용자의 회의록을 분석하여 UI/UX 개선 요구사항을 도출하는 기능 제공 페이지
# txt, md 파일 업로드, WAV 음성 파일 업로드 또는 직접 입력 가능
# 회의록 내용은 LangChain LLM을 통해 분석되며, 
# UI/UX 관련 요구사항과 사용자 피드백을 JSON/MARKDOWN 형식으로 출력
# Azure Speech Service는 WAV 형식에서 가장 안정적인 성능을 제공합니다.


# 환경변수 로드
load_dotenv()
llm_name = os.getenv("AZURE_OPENAI_LLM_MINI")


# 시스템 프롬프트 정의
SYSTEM_PROMPT = """
당신은 회의록을 분석하여 UI/UX 개선 요구사항을 파악하는 전문가입니다.

**분석 목표:**
1. 회의록에서 UI/UX 관련 개선사항을 추출
2. 사용자 피드백과 개발 요구사항 구분
3. 구체적이고 실행 가능한 개선안 도출

**출력 형식 (JSON):**
{
  "ui_requirements": [
    {
      "category": "버튼/인터페이스/레이아웃/색상/텍스트 중 하나",
      "current_issue": "현재 문제점",
      "improvement_request": "개선 요구사항",
      "priority": "high/medium/low",
      "technical_detail": "구체적인 구현 방향"
    }
  ],
  "user_feedback": [
    {
      "feedback": "사용자가 제기한 구체적 피드백",
      "pain_point": "사용자 불편사항",
      "suggested_solution": "제안된 해결방안"
    }
  ],
  "summary": {
    "total_requirements": "총 요구사항 수",
    "high_priority_count": "고우선순위 항목 수",
    "main_focus_areas": ["주요 개선 영역들"]
  }
}

**분석 시 고려사항:**
- 명확하지 않은 요구사항은 합리적으로 해석
- 사용자 경험 관점에서 우선순위 설정
- 개발 복잡도와 사용자 임팩트 고려
"""

@langfuse_monitor(name="회의록_분석")  
def analyze_meeting_content(llm, system_prompt, content, focus_area):
    """회의록 내용을 LangChain LLM으로 분석"""
    try:
        # LangChain 메시지 구성
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"다음 회의록을 분석해주세요:\n\n{content}\n\n분석 집중 영역: {focus_area}")
        ]
        
        # LLM 호출 - 입력/출력이 자동으로 Langfuse에 기록됨
        response = llm.invoke(messages)
        
        # JSON 파싱 시도
        try:
            analysis_result = json.loads(response.content)
            return {"success": True, "data": analysis_result, "raw": response.content}
        except json.JSONDecodeError:
            return {"success": True, "data": None, "raw": response.content}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def display_analysis_results(result):
    """분석 결과 표시"""
    if result["data"]:  # JSON 파싱 성공
        data = result["data"]
        
        # 요약 정보
        st.subheader("📊 분석 요약")
        if "summary" in data:
            summary = data["summary"]
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("총 요구사항", summary.get("total_requirements", "N/A"))
            with col2:
                st.metric("고우선순위", summary.get("high_priority_count", "N/A"))
            with col3:
                focus_areas = summary.get("main_focus_areas", [])
                st.metric("주요 영역", len(focus_areas) if focus_areas else "N/A")
        
        # UI 요구사항
        if "ui_requirements" in data and data["ui_requirements"]:
            st.subheader("🎯 UI 개선 요구사항")
            
            for i, req in enumerate(data["ui_requirements"]):
                with st.expander(f"{req.get('category', 'UI')} - {req.get('current_issue', 'Issue')[:50]}..."):
                    st.write(f"**카테고리:** {req.get('category', 'N/A')}")
                    st.write(f"**현재 문제:** {req.get('current_issue', 'N/A')}")
                    st.write(f"**개선 요청:** {req.get('improvement_request', 'N/A')}")
                    st.write(f"**우선순위:** {req.get('priority', 'N/A')}")
                    st.write(f"**구현 방향:** {req.get('technical_detail', 'N/A')}")
        
        # 사용자 피드백
        if "user_feedback" in data and data["user_feedback"]:
            st.subheader("👥 사용자 피드백")
            
            for i, feedback in enumerate(data["user_feedback"]):
                with st.container():
                    st.write(f"**피드백 {i+1}:**")
                    st.info(feedback.get('feedback', 'N/A'))
                    st.write(f"**불편사항:** {feedback.get('pain_point', 'N/A')}")
                    st.write(f"**제안 해결책:** {feedback.get('suggested_solution', 'N/A')}")
                    st.divider()
    
    else:  # JSON 파싱 실패, raw text 표시
        st.subheader("📝 분석 결과")
        st.markdown(result["raw"])

def result_to_markdown(data):
    """분석 결과(JSON)를 Markdown 형식으로 변환"""
    md = "# 📋 회의록 UI 요구사항 분석 결과\n\n"
    if "summary" in data:
        md += "## 📊 요약\n"
        summary = data["summary"]
        md += f"- **총 요구사항:** {summary.get('total_requirements', 'N/A')}\n"
        md += f"- **고우선순위:** {summary.get('high_priority_count', 'N/A')}\n"
        focus_areas = summary.get("main_focus_areas", [])
        md += f"- **주요 영역:** {', '.join(focus_areas) if focus_areas else 'N/A'}\n\n"
    if "ui_requirements" in data and data["ui_requirements"]:
        md += "## 🎯 UI 개선 요구사항\n"
        for req in data["ui_requirements"]:
            md += f"- **카테고리:** {req.get('category', 'N/A')}\n"
            md += f"  - **현재 문제:** {req.get('current_issue', 'N/A')}\n"
            md += f"  - **개선 요청:** {req.get('improvement_request', 'N/A')}\n"
            md += f"  - **우선순위:** {req.get('priority', 'N/A')}\n"
            md += f"  - **구현 방향:** {req.get('technical_detail', 'N/A')}\n\n"
    if "user_feedback" in data and data["user_feedback"]:
        md += "## 👥 사용자 피드백\n"
        for feedback in data["user_feedback"]:
            md += f"- **피드백:** {feedback.get('feedback', 'N/A')}\n"
            md += f"  - **불편사항:** {feedback.get('pain_point', 'N/A')}\n"
            md += f"  - **제안 해결책:** {feedback.get('suggested_solution', 'N/A')}\n\n"
    return md

# 메인 앱
def main():
    st.session_state["current_page"] = "ui_requirements_analysis"

    
    st.set_page_config(
        page_title="회의록 요구사항 분석기",
        page_icon="📋",
        layout="wide"
    )
    
    st.title("📋 회의록 UI 요구사항 분석기")
    st.markdown("회의 전문을 업로드하거나 WAV 음성으로 입력하면 AI가 UI/UX 개선 요구사항을 분석해드립니다.")
    
    # 초기 사용자 액션 로깅
    log_user_action("page_loaded", {"page": "ui_requirements_analysis"})
    
    # LangChain 클라이언트 초기화
    llm = init_langchain_client(llm_name, 0.0)  # 창의력 최소화
    if not llm:
        st.error("❌ LangChain Azure OpenAI 연결에 실패했습니다. 환경변수를 확인해주세요.")
        st.code("""
        필요한 환경변수:
        - AZURE_OPENAI_API_KEY
        - AZURE_OPENAI_ENDPOINT  
        - AZURE_OPENAI_API_VERSION
        - AZURE_OPENAI_LLM_MINI
        """)
        return
    
    # 사이드바 설정
    with st.sidebar:
        st.subheader("⚙️ 분석 설정")
        
        # 프롬프트 커스터마이징
        with st.expander("시스템 프롬프트 수정"):
            custom_prompt = st.text_area(
                "시스템 프롬프트:",
                value=SYSTEM_PROMPT,
                height=200
            )
        
        # 분석 옵션
        analysis_focus = st.selectbox(
            "분석 집중 영역:",
            ["전체 분석", "UI 요구사항 중심", "사용자 피드백 중심", "기술적 구현 중심"]
        )
    
    # 메인 컨텐츠
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📄 회의록 입력")
        
        # 입력 방식 선택
        input_method = st.radio(
            "입력 방식 선택:",
            ["📁 텍스트 파일 업로드", "🎤 음성 파일 업로드", "📝 직접 입력"]
        )
        
        content = ""
        
        if input_method == "📁 텍스트 파일 업로드":
            # 텍스트 파일 업로드
            uploaded_file = st.file_uploader(
                "회의 전문 파일을 업로드하세요", 
                type=["txt", "md"],
                help="TXT, MD 파일을 지원합니다."
            )
            
            if uploaded_file is not None:
                content = uploaded_file.read().decode("utf-8")
                st.success("✅ 파일이 업로드되었습니다.")
                with st.expander("📄 파일 내용 미리보기"):
                    st.text_area("내용", content, height=200, disabled=True, key="file_preview")
        
        elif input_method == "🎤 WAV 음성 파일 업로드":
            # WAV 음성 파일 업로드 전용
            st.info("""
            🎵 **WAV 음성 파일 전용 서비스**
            
            Azure Speech Service 최적화를 위해 **WAV 파일만** 지원합니다.
            """)
            
            uploaded_audio_file = st.file_uploader(
                "회의 녹음 파일을 업로드하세요:",
                type=['wav'],  # WAV만 허용
                help="WAV 형식만 지원합니다. 다른 형식은 WAV로 변환 후 업로드해주세요."
            )
            
            if uploaded_audio_file is not None:
                st.success(f"✅ WAV 음성 파일이 업로드되었습니다: {uploaded_audio_file.name}")
                
                # 파일 정보 표시
                file_size = len(uploaded_audio_file.getvalue()) / (1024 * 1024)  # MB
                st.info(f"📁 파일 크기: {file_size:.2f} MB")
                
                # 파일 크기 제한 확인
                if file_size > 100:
                    st.error("❌ 파일이 100MB를 초과합니다. 더 작은 파일로 나누어 업로드해주세요.")
                    st.stop()
                elif file_size > 50:
                    st.warning("⚠️ 파일이 50MB를 초과합니다. 처리 시간이 오래 걸릴 수 있습니다.")
                
                # 오디오 플레이어
                st.audio(uploaded_audio_file.getvalue())
                
                # WAV 음성을 텍스트로 변환
                if st.button("🎯 음성을 텍스트로 변환", type="secondary", use_container_width=True):
                    # Azure Speech Service 초기화
                    speech_config = init_speech_config()
                    
                    if speech_config:
                        with st.spinner("🎯 음성을 텍스트로 변환 중입니다..."):
                            # WAV 파일 검증 및 준비
                            tmp_file_path, is_valid = validate_wav_file_only(
                                uploaded_audio_file.getvalue(), 
                                uploaded_audio_file.name
                            )
                            
                            if not is_valid or not tmp_file_path:
                                st.error("❌ WAV 파일 준비에 실패했습니다.")
                                return
                            
                            try:
                                # speech_utils의 WAV 전용 함수 사용
                                transcript = speech_to_text_safe(tmp_file_path, speech_config)
                                
                                if transcript and transcript.strip():
                                    content = transcript
                                    st.success("✅ WAV 음성 인식이 완료되었습니다!")
                                    
                                    # 변환된 텍스트 표시
                                    with st.expander("📄 변환된 텍스트 보기", expanded=True):
                                        st.text_area("변환된 회의록", content, height=200, disabled=True)
                                    
                                    # 세션에 저장
                                    st.session_state["converted_audio_content"] = content
                                    st.session_state["audio_input_ready"] = True
                                else:
                                    st.error("""
                                    ❌ WAV 음성 인식에 실패했습니다.
                                    
                                    **해결 방법:**
                                    1. WAV 파일이 손상되지 않았는지 확인
                                    2. 권장 설정(16-bit PCM, 16kHz)으로 변환
                                    3. 배경 소음이 적은 깨끗한 녹음 사용
                                    4. 파일 크기가 너무 크지 않은지 확인
                                    """)
                            
                            finally:
                                # 임시 파일 정리
                                try:
                                    if tmp_file_path and os.path.exists(tmp_file_path):
                                        os.unlink(tmp_file_path)
                                except:
                                    pass
                    else:
                        st.error("❌ Azure Speech 서비스 설정이 올바르지 않습니다.")
                        st.warning("""
                        **환경변수 확인이 필요합니다:**
                        - AZURE_SPEECH_KEY: Azure Speech 서비스 키
                        - AZURE_SPEECH_REGION: Azure Speech 서비스 지역 (예: koreacentral)
                        """)
                
                # 이전에 변환된 내용이 있으면 표시
                if "converted_audio_content" in st.session_state:
                    content = st.session_state["converted_audio_content"]
                    
                    st.success("✅ 변환된 WAV 텍스트를 사용합니다.")
                    with st.expander("📄 변환된 텍스트 확인"):
                        st.text_area("내용", content, height=200, disabled=True)
                    
                    # 텍스트 편집 옵션
                    if st.button("✏️ 변환된 텍스트 편집하기"):
                        st.session_state["edit_audio_mode"] = True
                    
                    # 편집 모드
                    if st.session_state.get("edit_audio_mode", False):
                        edited_content = st.text_area(
                            "변환된 텍스트를 수정하세요:",
                            value=content,
                            height=200,
                            key="edit_audio_area"
                        )
                        
                        col_edit1, col_edit2 = st.columns(2)
                        with col_edit1:
                            if st.button("💾 수정 완료", type="primary"):
                                st.session_state["converted_audio_content"] = edited_content
                                content = edited_content
                                st.session_state["edit_audio_mode"] = False
                                st.success("✅ 텍스트가 수정되었습니다!")
                                st.rerun()
                        with col_edit2:
                            if st.button("❌ 편집 취소"):
                                st.session_state["edit_audio_mode"] = False
                                st.rerun()
        
        else:  # 직접 입력
            st.markdown("📝 회의록 내용을 직접 입력하세요:")
            content = st.text_area(
                "회의록 내용:", 
                height=300,
                placeholder="""예시:

오늘 UI/UX 개선 회의에서 다음과 같은 의견이 나왔습니다:

1. 로그인 버튼이 너무 작아서 클릭하기 어렵다는 의견이 많음
2. 색상 대비가 낮아서 가독성이 떨어진다는 피드백
3. 모바일에서 폼이 잘려서 보인다는 문제 제기
4. 에러 메시지가 사용자 친화적이지 않다는 의견

개선 우선순위:
- 버튼 크기 확대 (고우선순위)
- 색상 접근성 개선 (고우선순위)  
- 반응형 개선 (중우선순위)
- UX 라이팅 개선 (중우선순위)""",
                key="direct_meeting_input"
            )
            
            # 직접 입력 시에만 입력 완료 버튼 표시
            if st.button("📝 입력 완료", 
                        type="secondary", 
                        use_container_width=True,
                        disabled=not content.strip()):
                st.session_state["direct_input_ready"] = True
                st.success("✅ 입력이 완료되었습니다!")
    
    with col2:
        st.subheader("🤖 AI 분석 결과")
        
        # 입력이 준비되었는지 확인
        is_ready = (
            (input_method == "📁 텍스트 파일 업로드" and content.strip()) or
            (input_method == "🎤 음성 파일 업로드" and st.session_state.get("audio_input_ready", False)) or
            (input_method == "📝 직접 입력" and st.session_state.get("direct_input_ready", False))
        )
        
        # 분석 실행
        if is_ready and content.strip():
            if st.button("🚀 요구사항 분석 시작", type="primary", use_container_width=True):
                with st.spinner("🤖 AI가 회의록을 분석 중입니다..."):
                    # 사용자가 화면에서 시스템 프롬프트를 수정한 경우 반영한다.
                    system_prompt = custom_prompt if 'custom_prompt' in locals() else SYSTEM_PROMPT
                    result = analyze_meeting_content(llm, system_prompt, content, focus_area=analysis_focus)
                    st.session_state["analysis_result"] = result  # 세션 상태에 저장
        
        # 세션 상태에 결과가 있으면 표시 및 다운로드
        if "analysis_result" in st.session_state:
            result = st.session_state["analysis_result"]
            if result["success"]:
                st.success("✅ 분석이 완료되었습니다!")
                display_analysis_results(result)
                
                # 다운로드 버튼
                col_download1, col_download2 = st.columns(2)
                with col_download1:
                    st.download_button(
                        label="📥 분석 결과 (JSON)",
                        data=result["raw"],
                        file_name="meeting_analysis_result.json",
                        mime="application/json",
                        use_container_width=True
                    )
                with col_download2:
                    if result["data"]:
                        md_data = result_to_markdown(result["data"])
                        st.download_button(
                            label="📥 분석 결과 (MD)",
                            data=md_data,
                            file_name="meeting_analysis_result.md",
                            mime="text/markdown",
                            use_container_width=True
                        )
            else:
                st.error(f"❌ 분석 중 오류가 발생했습니다: {result['error']}")
        else:
            st.info("👆 회의록을 입력하고 '분석 시작' 버튼을 눌러주세요.")
            
            # 입력 방식별 안내
            if input_method == "📁 텍스트 파일 업로드":
                st.markdown("""
                **📁 파일 업로드 팁:**
                - TXT, MD 파일을 지원합니다
                - UTF-8 인코딩을 권장합니다
                - 파일 크기는 10MB 이하를 권장합니다
                """)
            elif input_method == "🎤 음성 파일 업로드":
                st.markdown("""
                **🎵 WAV 음성 파일 팁:**
                - WAV 형식만 지원됩니다
                - 배경 소음이 적은 깨끗한 녹음 사용
                - 파일 크기는 100MB 이하로 제한
                """)
            else:
                st.markdown("""
                **📝 직접 입력 팁:**
                - 회의 내용을 자세히 입력할수록 정확한 분석이 가능합니다
                - UI/UX 관련 피드백을 구체적으로 작성해주세요
                - 우선순위나 중요도를 언급하면 더 좋습니다
                """)

if __name__ == "__main__":
    main()