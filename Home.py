import streamlit as st
from utils.langfuse_monitor import is_monitoring_enabled

def show_admin_page():
    st.title("🔒 관리자 페이지")
    
    if is_monitoring_enabled():
        # Langfuse 대시보드 링크
        import os
        host = os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com")
        st.markdown(f"[Langfuse 대시보드 열기]({host})")
        st.success("✅ 모니터링이 활성화되어 있습니다")
    else:
        st.warning("⚠️ Langfuse 모니터링이 비활성화되어 있습니다")

def login_form():
    st.title("🔐 관리자 로그인")
    password = st.text_input("비밀번호를 입력하세요", type="password")
    
    if password == st.secrets["admin"]["password"]:
        st.session_state["authenticated"] = True
        st.rerun()
    elif password:
        st.error("비밀번호가 틀렸습니다.")

# URL 쿼리 파라미터 확인
query_params = st.query_params
admin_flag = query_params.get("admin")


# 인증 상태 초기화
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# admin 페이지 접근 여부 확인
if admin_flag and admin_flag == "true":
    if st.session_state["authenticated"]:
        show_admin_page()
    else:
        login_form()
else:
    # 일반 사용자 화면

    st.set_page_config(
        page_title="HELP_MEET",
        page_icon="📑"
    )

    st.title("HELP_MEET")
    with st.sidebar:
        st.markdown("🚀 필요한 기능이 있는 페이지를 선택해보세요")

    st.markdown("""
### 📚 기능 소개

<br>\n
###### 🎨 통합 UI 개선 시스템
- 회의록 업로드부터 UI 개선 코드 생성까지, 모든 과정을 AI가 도와주는 통합 시스템이에요.

<br>\n
###### 📇 회의록 기반 UI 요구사항 분석  
- 정리된 회의록을 올리거나, 회의 내용을 그대로 업로드하면 AI가 회의에서 언급된 UI 요구사항을 분석해줍니다.<br>
- 분석 결과는 JSON, Markdown 형식으로 다운로드 할 수 있어요.

<br>
\n

###### 🛠️ 회의 결과 기반 코드 개선
- 사용 중인 코드를 업로드하면, AI가 해당 요구사항을 반영하여 코드를 개선해줘요.
- 요구사항은 직접 입력해도 되고, 회의록을 업로드하면 AI가 요구사항을 직접 추출해줘요.
- html, react, vue.js 등 다양한 프론트엔드 코드에 적용할 수 있어요.
- html 코드의 경우 개선 결과를 바로 화면에서 확인할 수 있어요.

\n
<br>
\n
###### 💡 AI에게 질문하기
- 요약된 회의록이나, 회의 전문을 바탕으로 추가적으로 개선할 사항을 질문할 수 있어요.
- UI 개선 제안, 마이크로카피 작성이나 유사한 사례 등 질문에 맞는 로직을 선택해 AI가 답변해요.
""", unsafe_allow_html=True)