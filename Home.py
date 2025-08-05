# Landing Page
import streamlit as st

st.set_page_config(
    page_title="HELP_MEET",
    page_icon="📑"
)

st.title("Landing Page 🛸")
with st.sidebar:
    st.markdown("🚀 Navigation")

# # 커스텀 CSS로 file_uploader 라벨 크기 조정
# st.markdown("""
#     <style>
#     /* 최신 Streamlit에서 file_uploader 라벨 스타일 변경 */
#     div[data-testid="stFileUploader"] label {
#         font-size: 100px !important;
#         color: grey !important;
#     }
#     </style>
# """, unsafe_allow_html=True)

# txt 파일 업로드
uploaded_file = st.file_uploader("회의 전문을 올려보세요", type="txt")
if uploaded_file is not None:
    # Read the file
    content = uploaded_file.read().decode("utf-8")
    st.text_area("File Content", content, height=300)
    
    print(content)
    
# pdf 파일 업로드
uploaded_pdf = st.file_uploader("회의록 PDF를 올려보세요", type="pdf")
if uploaded_pdf is not None:
    # Read the file
    content_pdf = uploaded_pdf.read()
    st.text_area("PDF Content", content_pdf, height=300)
    
    print(content_pdf)