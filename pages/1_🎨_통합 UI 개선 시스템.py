from dotenv import load_dotenv
import os
import streamlit as st
from langchain_openai import AzureChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import json
import re
import datetime
import tempfile
from utils.speech_utils import init_speech_config, speech_to_text_safe
from utils.langchain_utils import init_langchain_client


# 회의록에서 도출된 요구사항과 현재 코드를 입력받아 개선된 코드를 제공하는 페이지
# JSON 형태의 요구사항과 HTML/React/JavaScript/JSP 코드를 분석하여 개선안 제시

# 환경변수 로드
load_dotenv()
llm_name = os.getenv("AZURE_OPENAI_LLM_MINI")

# 회의록 분석 시스템 프롬프트
MEETING_ANALYSIS_PROMPT = """
당신은 회의록을 분석하여 UI/UX 개선 요구사항을 파악하는 전문가입니다.

**분석 목표:**
1. 회의록에서 UI/UX 관련 개선사항을 추출
2. 사용자 피드백과 개발 요구사항 구분
3. 구체적이고 실행 가능한 개선안 도출

**출력 형식 (JSON):**
```json
{
  "ui_requirements": [
    {
      "category": "버튼/인터페이스/레이아웃/색상/텍스트/폼/네비게이션 중 하나",
      "current_issue": "현재 문제점",
      "improvement_request": "개선 요구사항",
      "priority": "high/medium/low",
      "technical_detail": "구체적인 구현 방향",
      "user_impact": "사용자에게 미치는 영향"
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
    "main_focus_areas": ["주요 개선 영역들"],
    "expected_outcome": "예상되는 개선 효과"
  }
}
```

**분석 시 고려사항:**
- 명확하지 않은 요구사항은 합리적으로 해석
- 사용자 경험 관점에서 우선순위 설정
- 개발 복잡도와 사용자 임팩트 고려
- 실행 가능한 구체적 개선안 제시
"""

# 코드 개선 시스템 프롬프트 생성 함수
def create_code_improvement_prompt(code_language, focus_area):
    return f"""
당신은 {code_language.upper()} 코드 개선 전문가입니다.

**역할:**
회의록에서 분석된 UI/UX 요구사항을 바탕으로 기존 코드를 직접 개선합니다.

**개선 절차:**
1. JSON 형태의 요구사항을 현재 코드에 직접 반영
2. 요구사항별로 구체적인 코드 수정 적용
3. 접근성, 반응형, 사용성을 고려한 완전한 코드 작성

**출력 형식:**
```json
{{
  "applied_changes": [
    {{
      "requirement": "적용된 요구사항",
      "change_description": "구체적인 변경 내용",
      "code_section": "수정된 핵심 코드 부분",
      "before_after": "변경 전후 비교"
    }}
  ],
  "improved_code": "개선된 완전한 실행 가능한 코드",
  "technical_improvements": [
    "성능 개선사항",
    "접근성 개선사항", 
    "코드 품질 개선사항"
  ],
  "summary": {{
    "total_changes": "총 변경사항 수",
    "main_improvements": ["주요 개선사항들"],
    "expected_benefits": "예상되는 사용자 경험 개선 효과"
  }}
}}
```

**개선 시 고려사항:**
- {code_language.upper()}의 최신 모범 사례 적용
- 요구사항을 정확히 코드에 반영
- 기존 기능은 유지하면서 개선
- 크로스 브라우저 호환성 고려
- 접근성 (WCAG) 가이드라인 준수
- 반응형 디자인 적용
- 실행 가능한 완전한 코드 제공

**특별 집중 영역:** {focus_area}에 특히 집중하여 개선하세요.
"""

def parse_requirements(requirements_text):
    """다양한 형태의 요구사항을 파싱하여 구조화"""
    requirements_text = requirements_text.strip()
    
    if requirements_text.startswith('{') and requirements_text.endswith('}'):
        try:
            return json.loads(requirements_text), "json"
        except json.JSONDecodeError:
            pass
    
    if '##' in requirements_text or '###' in requirements_text:
        return requirements_text, "markdown"
    
    return requirements_text, "text"

def detect_code_language(code):
    """코드 내용을 분석하여 언어를 자동 감지"""
    code_lower = code.lower()
    
    if 'import react' in code_lower or 'from react' in code_lower or 'jsx' in code_lower:
        return 'react'
    elif '<%' in code and '%>' in code:
        return 'jsp'
    elif '<html' in code_lower or '<!doctype html' in code_lower:
        return 'html'
    elif 'function' in code_lower and ('document.' in code_lower or 'window.' in code_lower):
        return 'javascript'
    elif '<template>' in code_lower and '<script>' in code_lower:
        return 'vue'
    elif 'component' in code_lower and '@' in code:
        return 'angular'
    else:
        return 'html'

def analyze_meeting_notes(llm, meeting_content):
    """회의록을 분석하여 요구사항 도출"""
    try:
        messages = [
            SystemMessage(content=MEETING_ANALYSIS_PROMPT),
            HumanMessage(content=f"다음 회의록을 분석하여 UI/UX 개선 요구사항을 도출해주세요:\n\n{meeting_content}")
        ]
        
        response = llm.invoke(messages)
        
        # JSON 파싱 시도
        try:
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response.content, re.DOTALL)
            if json_match:
                json_content = json_match.group(1)
                analysis_result = json.loads(json_content)
                return {"success": True, "data": analysis_result, "raw": response.content}
            else:
                analysis_result = json.loads(response.content)
                return {"success": True, "data": analysis_result, "raw": response.content}
        except json.JSONDecodeError:
            return {"success": True, "data": None, "raw": response.content}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def improve_code_with_requirements(llm, requirements, current_code, code_language, focus_area):
    """요구사항을 바탕으로 코드 개선"""
    try:
        system_prompt = create_code_improvement_prompt(code_language, focus_area)
        
        user_message = f"""
**분석된 요구사항 (JSON):**
```json
{json.dumps(requirements, ensure_ascii=False, indent=2)}
```

**현재 코드 ({code_language.upper()}):**
```{code_language}
{current_code}
```

위 요구사항을 반영하여 현재 코드를 개선해주세요.
특히 JSON에 포함된 ui_requirements의 각 항목들을 구체적으로 코드에 반영해주세요.
"""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ]
        
        response = llm.invoke(messages)
        
        # JSON 파싱 시도
        try:
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response.content, re.DOTALL)
            if json_match:
                json_content = json_match.group(1)
                improvement_result = json.loads(json_content)
                return {"success": True, "data": improvement_result, "raw": response.content}
            else:
                improvement_result = json.loads(response.content)
                return {"success": True, "data": improvement_result, "raw": response.content}
        except json.JSONDecodeError:
            return {"success": True, "data": None, "raw": response.content}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def display_requirements_analysis(result):
    """요구사항 분석 결과 표시"""
    if result["data"]:
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
            
            if summary.get("expected_outcome"):
                st.info(f"**예상 효과:** {summary['expected_outcome']}")
        
        # UI 요구사항
        if "ui_requirements" in data and data["ui_requirements"]:
            st.subheader("🎯 UI/UX 개선 요구사항")
            
            for i, req in enumerate(data["ui_requirements"]):
                priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}
                priority = req.get('priority', 'medium')
                
                with st.expander(f"{priority_emoji.get(priority, '⚪')} {req.get('category', 'UI')} - {req.get('current_issue', 'Issue')[:50]}..."):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.write(f"**카테고리:** {req.get('category', 'N/A')}")
                        st.write(f"**우선순위:** {req.get('priority', 'N/A')}")
                        st.write(f"**현재 문제:** {req.get('current_issue', 'N/A')}")
                    with col_b:
                        st.write(f"**개선 요청:** {req.get('improvement_request', 'N/A')}")
                        st.write(f"**구현 방향:** {req.get('technical_detail', 'N/A')}")
                        if req.get('user_impact'):
                            st.write(f"**사용자 영향:** {req['user_impact']}")
        
        # 사용자 피드백
        if "user_feedback" in data and data["user_feedback"]:
            st.subheader("👥 사용자 피드백")
            
            for i, feedback in enumerate(data["user_feedback"]):
                with st.container():
                    st.write(f"**피드백 {i+1}:**")
                    st.info(feedback.get('feedback', 'N/A'))
                    col_c, col_d = st.columns(2)
                    with col_c:
                        st.write(f"**불편사항:** {feedback.get('pain_point', 'N/A')}")
                    with col_d:
                        st.write(f"**제안 해결책:** {feedback.get('suggested_solution', 'N/A')}")
                    st.divider()
    
    else:
        st.subheader("📝 분석 결과")
        st.markdown(result["raw"])

def display_code_improvement_results(result, code_language):
    """코드 개선 결과 표시"""
    if result["data"]:
        data = result["data"]
        
        # 개선 요약
        if "summary" in data:
            summary = data["summary"]
            st.subheader("📊 개선 요약")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("총 변경사항", summary.get("total_changes", "N/A"))
                if summary.get("main_improvements"):
                    st.write("**주요 개선사항:**")
                    for improvement in summary["main_improvements"]:
                        st.write(f"• {improvement}")
            
            with col2:
                if summary.get("expected_benefits"):
                    st.info(f"**예상 효과:**\n{summary['expected_benefits']}")
        
        # 적용된 변경사항
        if "applied_changes" in data:
            st.subheader("✅ 적용된 개선사항")
            
            for i, change in enumerate(data["applied_changes"]):
                with st.expander(f"개선사항 {i+1}: {change.get('requirement', 'Improvement')[:60]}..."):
                    st.write(f"**요구사항:** {change.get('requirement', 'N/A')}")
                    st.write(f"**변경내용:** {change.get('change_description', 'N/A')}")
                    
                    if change.get('before_after'):
                        st.write(f"**변경 전후:** {change['before_after']}")
                    
                    if change.get('code_section'):
                        st.write("**핵심 변경 코드:**")
                        st.code(change['code_section'], language=code_language)
        
        # 기술적 개선사항
        if "technical_improvements" in data:
            st.subheader("🔧 기술적 개선사항")
            for improvement in data["technical_improvements"]:
                st.write(f"• {improvement}")
        
        # 개선된 코드
        if "improved_code" in data:
            st.subheader("💻 개선된 완전한 코드")
            improved_code = data["improved_code"]
            
            # 개선된 코드 표시
            with st.expander("전체 개선 코드 보기", expanded=False):
                st.code(improved_code, language=code_language)
            
            # 다운로드 버튼
            file_extension = {
                'react': 'jsx', 'html': 'html', 'javascript': 'js',
                'jsp': 'jsp', 'vue': 'vue', 'angular': 'ts'
            }.get(code_language, 'txt')
            
            col_dl1, col_dl2 = st.columns(2)
            with col_dl1:
                st.download_button(
                    label=f"📥 개선된 코드 다운로드 (.{file_extension})",
                    data=improved_code,
                    file_name=f"improved_code.{file_extension}",
                    mime="text/plain",
                    use_container_width=True
                )
            with col_dl2:
                # 개선 보고서 생성
                report = create_improvement_report(data, code_language)
                st.download_button(
                    label="📄 개선 보고서 (MD)",
                    data=report,
                    file_name="improvement_report.md",
                    mime="text/markdown",
                    use_container_width=True
                )
    
    else:
        st.subheader("📋 개선 결과")
        st.markdown(result["raw"])

def create_improvement_report(data, code_language):
    """개선 보고서를 마크다운으로 생성"""
    report = f"# 🚀 UI/UX 개선 보고서\n\n"
    report += f"**대상 언어:** {code_language.upper()}\n"
    report += f"**개선 일시:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    if "summary" in data:
        summary = data["summary"]
        report += "## 📊 개선 요약\n\n"
        report += f"- **총 변경사항:** {summary.get('total_changes', 'N/A')}\n"
        if summary.get("main_improvements"):
            report += "- **주요 개선사항:**\n"
            for improvement in summary["main_improvements"]:
                report += f"  - {improvement}\n"
        if summary.get("expected_benefits"):
            report += f"- **예상 효과:** {summary['expected_benefits']}\n"
        report += "\n"
    
    if "applied_changes" in data:
        report += "## ✅ 적용된 개선사항\n\n"
        for i, change in enumerate(data["applied_changes"]):
            report += f"### {i+1}. {change.get('requirement', 'Improvement')}\n"
            report += f"**변경내용:** {change.get('change_description', 'N/A')}\n\n"
            if change.get('before_after'):
                report += f"**변경 전후:** {change['before_after']}\n\n"
    
    if "technical_improvements" in data:
        report += "## 🔧 기술적 개선사항\n\n"
        for improvement in data["technical_improvements"]:
            report += f"- {improvement}\n"
        report += "\n"
    
    if "improved_code" in data:
        report += f"## 💻 개선된 코드\n\n"
        report += f"```{code_language}\n{data['improved_code']}\n```\n\n"
    
    return report

def main():
    st.set_page_config(
        page_title="통합 UI 개선 시스템",
        page_icon="🎨",
        layout="wide"
    )
    
    st.title("🎨 통합 UI 개선 시스템")
    st.markdown("**회의록 → 요구사항 분석 → 코드 개선**까지 한 번에!")
    
    # LangChain 클라이언트 초기화
    llm = init_langchain_client(llm_name, 0.1)
    if not llm:
        st.error("❌ LangChain Azure OpenAI 연결에 실패했습니다.")
        return
    
    # 사이드바 설정
    with st.sidebar:
        st.subheader("⚙️ 시스템 설정")
        
        # 코드 언어 선택
        code_language = st.selectbox(
            "코드 언어:",
            ["auto-detect", "html", "react", "javascript", "jsp", "vue", "angular"],
            help="auto-detect는 코드를 분석하여 자동으로 언어를 감지합니다."
        )
        
        # 개선 집중 영역
        focus_area = st.selectbox(
            "개선 집중 영역:",
            ["전체 개선", "사용자 경험", "접근성", "반응형 디자인", "성능 최적화", "시각적 디자인"]
        )
        
        st.divider()
        
        # 프로세스 가이드
        st.subheader("📋 진행 단계")
        st.markdown("""
        **1단계:** 회의록 업로드/입력
        **2단계:** AI 요구사항 분석
        **3단계:** 현재 코드 입력
        **4단계:** 코드 개선 실행
        **5단계:** 결과 확인 및 다운로드
        """)
        
        st.info("💡 각 단계를 순서대로 진행해주세요!")
    
    # 메인 탭 구성
    tab1, tab2, tab3 = st.tabs(["📝 1-2단계: 회의록 & 요구사항 분석", "💻 3-4단계: 코드 입력 & 개선", "📊 5단계: 통합 결과"])
    
    # === TAB 1: 회의록 & 요구사항 분석 ===
    with tab1:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("📋 1단계: 회의록 입력")
            
            # 회의록 입력 방식
            input_method = st.radio(
                "입력 방식 선택:",
                ["📁 텍스트 파일 업로드", "🎤 음성 파일 업로드", "📝 직접 입력"]
            )
            
            
            meeting_content = ""
            if input_method == "📁 텍스트 파일 업로드":
                uploaded_meeting_file = st.file_uploader(
                    "회의록 텍스트 파일을 업로드하세요:",
                    type=['txt', 'md'],
                    help="TXT, MD 파일을 지원합니다.",
                    key="text_file_uploader"
                )
                
                if uploaded_meeting_file is not None:
                    if uploaded_meeting_file.type == "text/plain":
                        meeting_content = str(uploaded_meeting_file.read(), "utf-8")
                        st.success("✅ 파일이 업로드되었습니다.")
                        
                        with st.expander("📄 파일 내용 미리보기"):
                            st.text_area("내용", meeting_content, height=200, disabled=True)
                    else:
                        st.error("텍스트 파일(.txt)과 마크다운 파일(.md)만 지원됩니다.")
            
            elif input_method == "🎤 음성 파일 업로드":
                st.info("🎵 음성 파일을 업로드하면 자동으로 텍스트로 변환됩니다.")
                
                uploaded_audio_file = st.file_uploader(
                    "회의 녹음 파일을 업로드하세요:",
                    type=['wav', 'mp3', 'm4a', 'flac', 'aac'],
                    help="다양한 음성 파일 형식을 지원합니다. 자동으로 텍스트로 변환됩니다.",
                    key="audio_file_uploader"
                )
                
                if uploaded_audio_file is not None:
                    st.success(f"✅ 음성 파일이 업로드되었습니다: {uploaded_audio_file.name}")
                    
                    # 파일 정보 표시
                    file_size = len(uploaded_audio_file.getvalue()) / (1024 * 1024)  # MB
                    st.info(f"📁 파일 크기: {file_size:.2f} MB")
                    
                    # 파일 크기 제한 확인
                    if file_size > 100:
                        st.warning("⚠️ 파일이 100MB를 초과합니다. 처리 시간이 오래 걸릴 수 있습니다.")
                    
                    # 오디오 플레이어
                    st.audio(uploaded_audio_file.getvalue())
                    
                    # 음성을 텍스트로 변환
                    if st.button("🎯 음성을 텍스트로 변환", type="secondary", use_container_width=True, key="audio_convert_btn"):
                        # Azure Speech Service 초기화
                        speech_config = init_speech_config()
                        
                        if speech_config:
                            with st.spinner("🎯 음성을 텍스트로 변환 중입니다... (시간이 다소 걸릴 수 있습니다)"):
                                # 임시 파일로 저장
                                file_extension = os.path.splitext(uploaded_audio_file.name)[1]
                                with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
                                    tmp_file.write(uploaded_audio_file.getvalue())
                                    tmp_file_path = tmp_file.name
                                
                                try:
                                    # speech_utils의 함수 사용
                                    transcript = speech_to_text_safe(tmp_file_path, speech_config)
                                    
                                    if transcript and transcript.strip():
                                        meeting_content = transcript
                                        st.success("✅ 음성 인식이 완료되었습니다!")
                                        
                                        # 변환된 텍스트 표시
                                        with st.expander("📄 변환된 텍스트 보기", expanded=True):
                                            st.text_area("변환된 회의록", meeting_content, height=200, disabled=True, key="audio_transcript_preview")
                                        
                                        # 세션에 저장
                                        st.session_state["converted_meeting_content"] = meeting_content
                                    else:
                                        st.error("❌ 음성 인식에 실패했습니다. 파일을 확인하거나 다른 형식으로 시도해보세요.")
                                
                                finally:
                                    # 임시 파일 정리
                                    try:
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
                    if "converted_meeting_content" in st.session_state:
                        meeting_content = st.session_state["converted_meeting_content"]
                        
                        st.success("✅ 변환된 텍스트를 사용합니다.")
                        with st.expander("📄 변환된 텍스트 확인", expanded=False):
                            st.text_area("내용", meeting_content, height=200, disabled=True, key="saved_transcript_preview")
                        
                        # 텍스트 편집 옵션 제공
                        if st.button("✏️ 변환된 텍스트 편집하기", key="edit_transcript_btn"):
                            st.session_state["edit_mode"] = True
                        
                        # 편집 모드
                        if st.session_state.get("edit_mode", False):
                            edited_content = st.text_area(
                                "변환된 텍스트를 수정하세요:",
                                value=meeting_content,
                                height=200,
                                key="edit_transcript_area"
                            )
                            
                            col_edit1, col_edit2 = st.columns(2)
                            with col_edit1:
                                if st.button("💾 수정 완료", type="primary", key="save_edit_btn"):
                                    st.session_state["converted_meeting_content"] = edited_content
                                    meeting_content = edited_content
                                    st.session_state["edit_mode"] = False
                                    st.success("✅ 텍스트가 수정되었습니다!")
                                    st.rerun()
                            with col_edit2:
                                if st.button("❌ 편집 취소", key="cancel_edit_btn"):
                                    st.session_state["edit_mode"] = False
                                    st.rerun()
            
            
            else:  # 직접 입력
                meeting_content = st.text_area(
                    "회의록 내용을 입력하세요:",
                    height=300,
                    placeholder="""예시:
                    
오늘 사용자 피드백 리뷰 회의에서 다음과 같은 의견이 나왔습니다:

1. 로그인 버튼이 너무 작아서 클릭하기 어렵다는 의견이 많음
2. 색상 대비가 낮아서 가독성이 떨어진다는 피드백
3. 모바일에서 폼이 잘려서 보인다는 문제 제기
4. 에러 메시지가 사용자 친화적이지 않다는 의견

개선 우선순위:
- 버튼 크기 확대 (고우선순위)
- 색상 접근성 개선 (고우선순위)  
- 반응형 개선 (중우선순위)
- UX 라이팅 개선 (중우선순위)"""
                )
            
            # 분석 실행 버튼
            if st.button("🔍 2단계: 요구사항 분석 실행", 
                        type="primary", 
                        use_container_width=True,
                        disabled=not meeting_content.strip()):
                
                with st.spinner("🤖 회의록을 분석하여 요구사항을 도출하는 중..."):
                    result = analyze_meeting_notes(llm, meeting_content)
                    st.session_state["requirements_analysis"] = result
                    st.session_state["meeting_content"] = meeting_content
                
                if result["success"]:
                    st.success("✅ 요구사항 분석이 완료되었습니다!")
                else:
                    st.error(f"❌ 분석 중 오류 발생: {result['error']}")
        
        with col2:
            st.subheader("🎯 2단계: 분석된 요구사항")
            
            if "requirements_analysis" in st.session_state:
                result = st.session_state["requirements_analysis"]
                if result["success"]:
                    display_requirements_analysis(result)
                    
                    # 요구사항을 다음 단계로 전달
                    if result["data"]:
                        st.session_state["structured_requirements"] = result["data"]
                else:
                    st.error("분석 중 오류가 발생했습니다.")
            else:
                st.info("👈 좌측에서 회의록을 입력하고 분석을 실행해주세요.")
    
    # === TAB 2: 코드 입력 & 개선 ===
    with tab2:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("💻 3단계: 현재 코드 입력")
            
            # 요구사항 확인
            if "structured_requirements" not in st.session_state:
                st.warning("⚠️ 먼저 1-2단계에서 요구사항 분석을 완료해주세요.")
                return
            
            # 코드 입력 방식
            code_input_method = st.radio(
                "코드 입력 방식:",
                ["📁 파일 업로드", "📝 직접 입력"]
            )
            
            current_code = ""
            if code_input_method == "📁 파일 업로드":
                uploaded_code_file = st.file_uploader(
                    "코드 파일 업로드:",
                    type=["html", "js", "jsx", "jsp", "vue", "ts", "txt"]
                )
                
                if uploaded_code_file is not None:
                    current_code = uploaded_code_file.read().decode("utf-8")
                    st.success("✅ 코드 파일이 업로드되었습니다.")
                    
                    # 언어 자동 감지
                    if code_language == "auto-detect":
                        detected_lang = detect_code_language(current_code)
                        st.info(f"🔍 감지된 언어: {detected_lang.upper()}")
                        code_language = detected_lang
                    
                    with st.expander("📄 코드 미리보기"):
                        st.code(current_code[:500] + "..." if len(current_code) > 500 else current_code, 
                               language=code_language)
            
            else:  # 직접 입력
                current_code = st.text_area(
                    "현재 코드를 입력하세요:",
                    height=300,
                    placeholder="""예시 HTML 코드:
                    
<!DOCTYPE html>
<html>
<head>
    <title>로그인 페이지</title>
    <style>
        .login-btn { 
            width: 80px; 
            height: 30px; 
            background: #ccc; 
            border: none; 
        }
    </style>
</head>
<body>
    <form>
        <input type="text" placeholder="사용자명">
        <input type="password" placeholder="비밀번호">
        <button class="login-btn">로그인</button>
    </form>
</body>
</html>"""
                )
                
                # 언어 자동 감지
                if code_language == "auto-detect" and current_code.strip():
                    detected_lang = detect_code_language(current_code)
                    st.info(f"🔍 감지된 언어: {detected_lang.upper()}")
                    code_language = detected_lang
            
            # 현재 코드 미리보기 (HTML만)
            if current_code.strip() and code_language == "html":
                st.markdown("#### 🖥️ 현재 코드 미리보기")
                try:
                    st.components.v1.html(current_code, height=300, scrolling=True)
                except Exception as e:
                    st.warning(f"미리보기 오류: {e}")
            
            # 개선 실행 버튼
            if st.button("🚀 4단계: 코드 개선 실행", 
                        type="primary", 
                        use_container_width=True,
                        disabled=not current_code.strip()):
                
                with st.spinner("🤖 요구사항을 바탕으로 코드를 개선하는 중..."):
                    requirements = st.session_state["structured_requirements"]
                    result = improve_code_with_requirements(
                        llm, requirements, current_code, code_language, focus_area
                    )
                    st.session_state["improvement_result"] = result
                    st.session_state["current_code"] = current_code
                    st.session_state["final_code_language"] = code_language
                
                if result["success"]:
                    st.success("✅ 코드 개선이 완료되었습니다!")
                else:
                    st.error(f"❌ 개선 중 오류 발생: {result['error']}")
        
        with col2:
            st.subheader("🎯 4단계: 개선 결과")
            
            if "improvement_result" in st.session_state:
                result = st.session_state["improvement_result"]
                if result["success"]:
                    # 개선된 코드 미리보기 (HTML만)
                    if result["data"] and "improved_code" in result["data"]:
                        improved_code = result["data"]["improved_code"]
                        final_lang = st.session_state.get("final_code_language", "html")
                        
                        if final_lang == "html":
                            st.markdown("#### 🖥️ 개선된 코드 미리보기")
                            try:
                                st.components.v1.html(improved_code, height=300, scrolling=True)
                            except Exception as e:
                                st.warning(f"미리보기 오류: {e}")
                    
                    display_code_improvement_results(result, st.session_state.get("final_code_language", "html"))
                else:
                    st.error("코드 개선 중 오류가 발생했습니다.")
            else:
                st.info("👈 좌측에서 현재 코드를 입력하고 개선을 실행해주세요.")
    
    # === TAB 3: 통합 결과 ===
    with tab3:
        st.subheader("📊 5단계: 전체 프로세스 결과")
        
        # 프로세스 진행 상황 체크
        steps_completed = 0
        if "meeting_content" in st.session_state:
            steps_completed += 1
        if "requirements_analysis" in st.session_state:
            steps_completed += 1
        if "current_code" in st.session_state:
            steps_completed += 1
        if "improvement_result" in st.session_state:
            steps_completed += 1
        
        # 진행 상황 표시
        progress = steps_completed / 4
        st.progress(progress, text=f"진행률: {steps_completed}/4 단계 완료")
        
        if steps_completed < 4:
            st.warning(f"⚠️ {4-steps_completed}개 단계가 남았습니다. 이전 탭에서 모든 단계를 완료해주세요.")
            return
        
        # 모든 단계 완료된 경우
        st.success("🎉 모든 단계가 완료되었습니다!")
        
        # 통합 결과 표시
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("📋 원본 회의록")
            with st.expander("회의록 내용 보기"):
                st.text_area("회의록", st.session_state["meeting_content"], height=200, disabled=True)
            
            st.subheader("🎯 분석된 요구사항 요약")
            requirements_result = st.session_state["requirements_analysis"]
            if requirements_result["data"] and "summary" in requirements_result["data"]:
                summary = requirements_result["data"]["summary"]
                st.info(f"""
                **총 요구사항:** {summary.get('total_requirements', 'N/A')}개
                **고우선순위:** {summary.get('high_priority_count', 'N/A')}개
                **주요 영역:** {', '.join(summary.get('main_focus_areas', []))}
                """)
        
        with col2:
            st.subheader("💻 Before / After 비교")
            
            # Before/After 코드 길이 비교
            original_code = st.session_state["current_code"]
            improved_result = st.session_state["improvement_result"]
            
            if improved_result["data"] and "improved_code" in improved_result["data"]:
                improved_code = improved_result["data"]["improved_code"]
                
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.metric("원본 코드", f"{len(original_code)} 글자")
                with col_b:
                    st.metric("개선된 코드", f"{len(improved_code)} 글자")
                with col_c:
                    change = len(improved_code) - len(original_code)
                    st.metric("변화량", f"{change:+} 글자")
                
                # 개선 효과 요약
                if improved_result["data"].get("summary", {}).get("expected_benefits"):
                    st.success(f"**예상 효과:** {improved_result['data']['summary']['expected_benefits']}")
        
        # 통합 다운로드 섹션
        st.divider()
        st.subheader("📥 통합 결과 다운로드")
        
        col_dl1, col_dl2, col_dl3, col_dl4 = st.columns(4)
        
        with col_dl1:
            # 원본 회의록
            st.download_button(
                label="📄 원본 회의록",
                data=st.session_state["meeting_content"],
                file_name="original_meeting_notes.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        with col_dl2:
            # 요구사항 분석 결과
            req_result = st.session_state["requirements_analysis"]
            st.download_button(
                label="🎯 요구사항 분석",
                data=req_result["raw"],
                file_name="requirements_analysis.json",
                mime="application/json",
                use_container_width=True
            )
        
        with col_dl3:
            # 원본 코드
            original_code = st.session_state["current_code"]
            file_ext = st.session_state.get("final_code_language", "html")
            st.download_button(
                label="💻 원본 코드",
                data=original_code,
                file_name=f"original_code.{file_ext}",
                mime="text/plain",
                use_container_width=True
            )
        
        with col_dl4:
            # 개선된 코드
            if improved_result["data"] and "improved_code" in improved_result["data"]:
                improved_code = improved_result["data"]["improved_code"]
                st.download_button(
                    label="🚀 개선된 코드",
                    data=improved_code,
                    file_name=f"improved_code.{file_ext}",
                    mime="text/plain",
                    use_container_width=True
                )
        
        # 최종 통합 보고서
        st.subheader("📊 최종 통합 보고서")
        if st.button("📋 통합 보고서 생성", use_container_width=True):
            # 통합 보고서 생성
            integrated_report = create_integrated_report(
                st.session_state["meeting_content"],
                st.session_state["requirements_analysis"]["data"],
                st.session_state["improvement_result"]["data"],
                st.session_state.get("final_code_language", "html")
            )
            
            st.download_button(
                label="📥 통합 보고서 다운로드 (MD)",
                data=integrated_report,
                file_name="integrated_ui_improvement_report.md",
                mime="text/markdown",
                use_container_width=True
            )
            
            with st.expander("📄 통합 보고서 미리보기"):
                st.markdown(integrated_report)

def create_integrated_report(meeting_content, requirements_data, improvement_data, code_language):
    """전체 프로세스의 통합 보고서 생성"""
    report = f"""# 🎨 UI/UX 통합 개선 보고서

## 📅 보고서 정보
- **생성 일시:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **대상 언어:** {code_language.upper()}
- **프로세스:** 회의록 분석 → 요구사항 도출 → 코드 개선

---

## 📋 1. 원본 회의록

```
{meeting_content}
```

---

## 🎯 2. 분석된 요구사항

"""
    
    if requirements_data:
        # 요약 정보
        if "summary" in requirements_data:
            summary = requirements_data["summary"]
            report += f"""
### 📊 요구사항 요약
- **총 요구사항:** {summary.get('total_requirements', 'N/A')}개
- **고우선순위:** {summary.get('high_priority_count', 'N/A')}개
- **주요 영역:** {', '.join(summary.get('main_focus_areas', []))}
- **예상 효과:** {summary.get('expected_outcome', 'N/A')}

"""
        
        # UI 요구사항
        if "ui_requirements" in requirements_data:
            report += "### 🎯 UI/UX 개선 요구사항\n\n"
            for i, req in enumerate(requirements_data["ui_requirements"]):
                report += f"""
**{i+1}. {req.get('category', 'UI')} - {req.get('priority', 'medium').upper()} 우선순위**
- **현재 문제:** {req.get('current_issue', 'N/A')}
- **개선 요청:** {req.get('improvement_request', 'N/A')}
- **구현 방향:** {req.get('technical_detail', 'N/A')}
- **사용자 영향:** {req.get('user_impact', 'N/A')}

"""
    
    report += "\n---\n\n## 🚀 3. 코드 개선 결과\n\n"
    
    if improvement_data:
        # 개선 요약
        if "summary" in improvement_data:
            summary = improvement_data["summary"]
            report += f"""
### 📊 개선 요약
- **총 변경사항:** {summary.get('total_changes', 'N/A')}
- **예상 효과:** {summary.get('expected_benefits', 'N/A')}

**주요 개선사항:**
"""
            for improvement in summary.get("main_improvements", []):
                report += f"- {improvement}\n"
            
            report += "\n"
        
        # 적용된 변경사항
        if "applied_changes" in improvement_data:
            report += "### ✅ 적용된 변경사항\n\n"
            for i, change in enumerate(improvement_data["applied_changes"]):
                report += f"""
**{i+1}. {change.get('requirement', 'Improvement')}**
- **변경내용:** {change.get('change_description', 'N/A')}
- **변경 전후:** {change.get('before_after', 'N/A')}

"""
        
        # 기술적 개선사항
        if "technical_improvements" in improvement_data:
            report += "### 🔧 기술적 개선사항\n\n"
            for improvement in improvement_data["technical_improvements"]:
                report += f"- {improvement}\n"
            report += "\n"
        
        # 최종 개선된 코드
        if "improved_code" in improvement_data:
            report += f"""
### 💻 최종 개선된 코드

```{code_language}
{improvement_data['improved_code']}
```

"""
    
    report += """
---

## 📈 4. 결론 및 권장사항

이번 개선을 통해 다음과 같은 효과를 기대할 수 있습니다:

1. **사용자 경험 개선**: 회의에서 제기된 사용자 불편사항 해결
2. **접근성 향상**: 웹 접근성 가이드라인 준수로 더 많은 사용자가 이용 가능
3. **코드 품질 향상**: 최신 모범 사례 적용으로 유지보수성 개선
4. **반응형 지원**: 다양한 디바이스에서 일관된 사용자 경험 제공

### 추후 개선 방향
- 사용자 테스트를 통한 개선 효과 검증
- A/B 테스트를 통한 성과 측정
- 지속적인 사용자 피드백 수집 및 반영

---

*본 보고서는 AI 기반 UI/UX 개선 시스템을 통해 자동 생성되었습니다.*
"""
    
    return report

if __name__ == "__main__":
    main()