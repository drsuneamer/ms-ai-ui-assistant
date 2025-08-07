import os
import streamlit as st
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI


load_dotenv()

# LangChain Azure OpenAI 클라이언트 설정
@st.cache_resource
def init_langchain_client(llm_name, temp):
    try:
        llm = AzureChatOpenAI(
            azure_deployment=llm_name,
            api_version=os.getenv("OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=temp
        )
        return llm
    except Exception as e:
        st.error(f"LangChain Azure OpenAI 연결 실패: {str(e)}")
        return None
