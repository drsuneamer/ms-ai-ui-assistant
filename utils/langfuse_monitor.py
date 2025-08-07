# utils/monitoring.py
import os
import streamlit as st
from dotenv import load_dotenv
import requests

load_dotenv()

# 환경변수 설정
os.environ["LANGFUSE_SECRET_KEY"] = os.getenv("LANGFUSE_SECRET_KEY", "")
os.environ["LANGFUSE_PUBLIC_KEY"] = os.getenv("LANGFUSE_PUBLIC_KEY", "")
os.environ["LANGFUSE_HOST"] = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

try:
    from langfuse import observe
    LANGFUSE_AVAILABLE = True
    
    # 환경변수 체크
    if not all([os.environ["LANGFUSE_SECRET_KEY"], os.environ["LANGFUSE_PUBLIC_KEY"]]):
        st.warning("⚠️ Langfuse 환경변수가 설정되지 않았습니다. 모니터링이 비활성화됩니다.")
        LANGFUSE_AVAILABLE = False
        
except ImportError:
    LANGFUSE_AVAILABLE = False
    st.info("📊 Langfuse가 설치되지 않았습니다. `pip install langfuse`로 설치하면 모니터링을 사용할 수 있습니다.")

# 데코레이터 정의
if LANGFUSE_AVAILABLE:
    # Langfuse가 사용 가능할 때
    langfuse_monitor = observe
else:
    # Langfuse가 사용 불가능할 때 - 아무것도 하지 않는 데코레이터
    def langfuse_monitor(func=None, *, name=None, **kwargs):
        if func is None:
            # 파라미터가 있는 경우 @langfuse_monitor(name="...")
            def decorator(f):
                return f
            return decorator
        else:
            # 파라미터가 없는 경우 @langfuse_monitor
            return func

# 편의 함수들
def log_user_action(action_name, metadata=None):
    """사용자 액션 로깅 (수동) - v3 호환"""
    if LANGFUSE_AVAILABLE:
        try:
            # v3에서는 간단한 trace 생성 방식 사용
            @observe(name=f"user_action_{action_name}")
            def _log_action():
                return {"action": action_name, "metadata": metadata or {}}
            
            _log_action()
            
        except Exception as e:
            print(f"Langfuse 로깅 실패: {e}")

def log_generation(name, input_text, output_text, model=None, metadata=None):
    """생성 로깅 (수동) - v3 호환, @observe 데코레이터와 중복 가능성 있음"""
    if LANGFUSE_AVAILABLE:
        try:
            # v3에서는 observe 데코레이터로 generation 생성
            @observe(name=name, as_type="generation")
            def _log_generation(input_data):
                # 실제 LLM 호출이 없으므로 단순 반환
                return output_text
            
            _log_generation(input_text)
            
        except Exception as e:
            print(f"Langfuse 생성 로깅 실패: {e}")

# 상태 확인 함수
def is_monitoring_enabled():
    """모니터링 활성화 상태 확인"""
    return LANGFUSE_AVAILABLE

