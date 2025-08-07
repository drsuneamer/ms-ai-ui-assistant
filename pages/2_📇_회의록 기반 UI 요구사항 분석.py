from dotenv import load_dotenv
import os
import streamlit as st
from langchain_openai import AzureChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import json


# 사용자의 회의록을 분석하여 UI/UX 개선 요구사항을 도출하는 기능 제공 페이지
# txt, md 파일 업로드 또는 직접 입력 가능
# 회의록 내용은 LangChain LLM을 통해 분석되며, 
# UI/UX 관련 요구사항과 사용자 피드백을 JSON/MARKDOWN 형식으로 출력


# 환경변수 로드
load_dotenv()
llm_name = os.getenv("AZURE_OPENAI_LLM_MINI")

# LangChain Azure OpenAI 클라이언트 설정
@st.cache_resource
def init_langchain_client():
    try:
        llm = AzureChatOpenAI(
            azure_deployment=llm_name,
            api_version=os.getenv("OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0.0  # 창의성 최소화
        )
        return llm
    except Exception as e:
        st.error(f"LangChain Azure OpenAI 연결 실패: {str(e)}")
        return None

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

def analyze_meeting_content(llm, content):
    """회의록 내용을 LangChain LLM으로 분석"""
    try:
        # LangChain 메시지 구성
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"다음 회의록을 분석해주세요:\n\n{content}")
        ]
        
        # LLM 호출
        response = llm.invoke(messages)
        
        # JSON 파싱 시도
        try:
            analysis_result = json.loads(response.content)
            return {"success": True, "data": analysis_result, "raw": response.content}
        except json.JSONDecodeError:
            # JSON 파싱 실패 시 raw text 반환
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
    st.set_page_config(
        page_title="회의록 요구사항 분석기",
        page_icon="📋",
        layout="wide"
    )
    
    st.title("📋 회의록 UI 요구사항 분석기")
    st.markdown("회의 전문을 업로드하면 AI가 UI/UX 개선 요구사항을 분석해드립니다.")
    
    # LangChain 클라이언트 초기화
    llm = init_langchain_client()
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
        st.subheader("📄 회의록 업로드")
        
        # 파일 업로드
        uploaded_file = st.file_uploader("회의 전문을 올려보세요", type=["txt", "md"])
        
        content = ""
        if uploaded_file is not None:
            content = uploaded_file.read().decode("utf-8")
            st.text_area("파일 내용 미리보기:", content, height=300, disabled=True)
        else:
            st.markdown("또는 직접 입력:")
            content = st.text_area("회의록 내용을 직접 입력하세요:", height=300, 
                                 placeholder="회의 내용을 입력해주세요.", key="meeting_input")
            
        # 입력 완료 버튼
        if st.button("📝 입력 완료", 
                    type="secondary", 
                    use_container_width=True):
            st.session_state["input_ready"] = True
            st.rerun()
    
    with col2:
        st.subheader("🤖 AI 분석 결과")
        
        # 입력이 준비되었거나 파일이 업로드된 경우
        is_ready = (uploaded_file is not None) or st.session_state.get("input_ready", False)
        
        # 분석 결과를 세션 상태에 저장
        if is_ready and content.strip():
            if st.button("🚀 요구사항 분석 시작", type="primary", use_container_width=True):
                with st.spinner("🤖 AI가 회의록을 분석 중입니다..."):
                    system_prompt = custom_prompt if 'custom_prompt' in locals() else SYSTEM_PROMPT
                    result = analyze_meeting_content(llm, content)
                    st.session_state["analysis_result"] = result  # 세션 상태에 저장

        # 세션 상태에 결과가 있으면 표시 및 다운로드
        if "analysis_result" in st.session_state:
            result = st.session_state["analysis_result"]
            if result["success"]:
                st.success("✅ 분석이 완료되었습니다!")
                display_analysis_results(result)
                st.download_button(
                    label="📥 분석 결과 다운로드 (JSON)",
                    data=result["raw"],
                    file_name="meeting_analysis_result.json",
                    mime="application/json"
                )
                if result["data"]:
                    md_data = result_to_markdown(result["data"])
                    st.download_button(
                        label="📥 분석 결과 다운로드 (Markdown)",
                        data=md_data,
                        file_name="meeting_analysis_result.md",
                        mime="text/markdown"
                    )
            else:
                st.error(f"❌ 분석 중 오류가 발생했습니다: {result['error']}")
        else:
            st.info("👆 회의록을 업로드하거나 직접 입력 후 '입력 완료' 버튼을 눌러주세요.")

if __name__ == "__main__":
    main()