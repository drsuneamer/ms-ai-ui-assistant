import streamlit as st

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
###### 📇 회의록 기반 UI 요구사항 분석  
- 정리된 회의록을 올리거나, 회의 내용을 그대로 업로드해 AI가 회의에서 언급된 UI 요구사항을 분석해보세요.<br><br>

\n

###### 🛠️ 회의 결과 기반 코드 개선
- 회의에서 언급된 요구사항이나, 직접 요구사항을 입력하고 사용 중인 코드를 업로드하면, AI가 해당 요구사항을 반영하여 코드를 개선해줘요.
- html, react, vue.js 등 다양한 프론트엔드 코드에 적용할 수 있어요.

\n
<br>
\n
###### 💡 AI에게 질문하기
- 요약된 회의록이나, 회의 전문을 바탕으로 추가적으로 개선할 사항을 질문할 수 있어요.
- UI 개선 제안, 마이크로카피 작성이나 유사한 사례 등 질문에 맞는 로직을 선택해 AI가 답변해요.
""", unsafe_allow_html=True)