# 개선 제안
from dotenv import load_dotenv
import os
import streamlit as st


load_dotenv()

# txt 파일 업로드
uploaded_file = st.file_uploader("회의 전문을 올려보세요", type="txt")
if uploaded_file is not None:
    # Read the file
    content = uploaded_file.read().decode("utf-8")
    st.text_area("File Content", content, height=300)
    
    print(content)
    
