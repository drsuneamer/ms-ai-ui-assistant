from dotenv import load_dotenv
import os, json, re
import streamlit as st
from langchain_openai import AzureChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from utils.langfuse_monitor import langfuse_monitor
from utils.langchain_utils import init_langchain_client

# 회의록에서 도출된 요구사항과 현재 코드를 입력받아 개선된 코드를 제공하는 페이지
# JSON 형태의 요구사항과 HTML/React/JavaScript/JSP 코드를 분석하여 개선안 제시

# 환경변수 로드
load_dotenv()
llm_name = os.getenv("AZURE_OPENAI_LLM_MINI")
# llm_name = os.getenv("AZURE_OPENAI_LLM_GPT4")


# 요구사항 파싱 함수
def parse_requirements(requirements_text):
    """다양한 형태의 요구사항을 파싱하여 구조화"""
    requirements_text = requirements_text.strip()
    
    # JSON 형태인지 확인
    if requirements_text.startswith('{') and requirements_text.endswith('}'):
        try:
            return json.loads(requirements_text), "json"
        except json.JSONDecodeError:
            pass
    
    # 마크다운 형태인지 확인 (# ## ### 포함)
    if '##' in requirements_text or '###' in requirements_text:
        return requirements_text, "markdown"
    
    # 일반 텍스트
    return requirements_text, "text"

def format_requirements_for_ai(requirements, format_type):
    """AI에게 전달할 요구사항 형태로 포맷"""
    if format_type == "json":
        return f"**구조화된 요구사항 (JSON):**\n```json\n{json.dumps(requirements, ensure_ascii=False, indent=2)}\n```"
    elif format_type == "markdown":
        return f"**마크다운 형태 요구사항:**\n{requirements}"
    else:
        return f"**텍스트 요구사항:**\n{requirements}"
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
        return 'html'  # 기본값

# 시스템 프롬프트 생성 함수
def create_system_prompt(code_language, focus_area):
    base_prompt = f"""
당신은 {code_language.upper()} 코드 개선 전문가입니다.

**역할:**
이미 분석된 UI/UX 요구사항을 바탕으로 기존 코드를 직접 개선합니다.

**개선 절차:**
1. 제공된 요구사항을 현재 코드에 직접 반영
2. 요구사항별로 구체적인 코드 수정 적용
3. 개선된 완전한 코드 작성

**출력 형식:**
```json
{{
  "applied_changes": [
    {{
      "requirement": "적용된 요구사항",
      "change_description": "구체적인 변경 내용",
      "code_section": "수정된 코드 부분"
    }}
  ],
  "improved_code": "개선된 완전한 코드",
  "summary": "주요 개선사항 요약"
}}
```

**개선 시 고려사항:**
- {code_language.upper()}의 모범 사례 적용
- 요구사항을 정확히 코드에 반영
- 기존 기능은 유지하면서 개선
- 실행 가능한 완전한 코드 제공
"""
    
    if focus_area != "전체 개선":
        base_prompt += f"\n**특별 집중 영역:** {focus_area}에 특히 집중하여 개선하세요."
    
    return base_prompt

@langfuse_monitor(name="개선된 코드 제공")  
def analyze_and_improve_code(llm, requirements, current_code, code_language, focus_area):
    """요구사항과 현재 코드를 분석하여 개선된 코드 제공"""
    try:
        # 요구사항 파싱
        parsed_requirements, req_format = parse_requirements(requirements)
        formatted_requirements = format_requirements_for_ai(parsed_requirements, req_format)
        
        system_prompt = create_system_prompt(code_language, focus_area)
        
        user_message = f"""
{formatted_requirements}

**현재 코드 ({code_language.upper()}):**
```{code_language}
{current_code}
```

위 요구사항을 반영하여 현재 코드를 개선해주세요.
요구사항 형태가 {req_format}이므로 이를 고려하여 적절히 해석하고 적용해주세요.
"""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ]
        
        response = llm.invoke(messages)
        
        # JSON 파싱 시도
        try:
            # JSON 블록 추출
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response.content, re.DOTALL)
            if json_match:
                json_content = json_match.group(1)
                improvement_result = json.loads(json_content)
                return {"success": True, "data": improvement_result, "raw": response.content}
            else:
                # JSON 블록이 없으면 전체 응답에서 JSON 찾기
                improvement_result = json.loads(response.content)
                return {"success": True, "data": improvement_result, "raw": response.content}
        except json.JSONDecodeError:
            return {"success": True, "data": None, "raw": response.content}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def display_improvement_results(result, code_language):
    """코드 개선 결과 표시"""
    if result["data"]:
        data = result["data"]
        
        # 적용된 변경사항
        if "applied_changes" in data:
            st.subheader("✅ 적용된 개선사항")
            
            for i, change in enumerate(data["applied_changes"]):
                with st.expander(f"개선사항 {i+1}: {change.get('requirement', 'Improvement')[:50]}..."):
                    st.write(f"**요구사항:** {change.get('requirement', 'N/A')}")
                    st.write(f"**변경내용:** {change.get('change_description', 'N/A')}")
                    if change.get('code_section'):
                        st.code(change['code_section'], language=code_language)
        
        # 개선 요약
        if "summary" in data:
            st.subheader("📊 개선 요약")
            st.info(data["summary"])
        
        # 개선된 코드
        if "improved_code" in data:
            st.subheader("💻 개선된 코드")
            improved_code = data["improved_code"]
            
            # 개선된 코드가 길면 접혀있는 expander로 표시
            with st.expander("전체 개선 코드 보기 ---", expanded=False):
                st.code(improved_code, language=code_language)
            
            # 다운로드 버튼
            file_extension = {
                'react': 'jsx',
                'html': 'html',
                'javascript': 'js',
                'jsp': 'jsp',
                'vue': 'vue',
                'angular': 'ts'
            }.get(code_language, 'txt')
            
            st.download_button(
                label=f"📥 개선된 코드 다운로드 (.{file_extension})",
                data=improved_code,
                file_name=f"improved_code.{file_extension}",
                mime="text/plain"
            )
    
    else:
        st.subheader("📋 개선 결과")
        st.markdown(result["raw"])

def create_improvement_report(data, code_language):
    """개선 보고서를 마크다운으로 생성"""
    report = f"# 🚀 코드 개선 보고서\n\n"
    report += f"**대상 언어:** {code_language.upper()}\n"
    report += f"**개선 일시:** {st.session_state.get('analysis_time', 'Unknown')}\n\n"
    
    if "applied_changes" in data:
        report += "## ✅ 적용된 개선사항\n\n"
        for i, change in enumerate(data["applied_changes"]):
            report += f"### {i+1}. {change.get('requirement', 'Improvement')}\n"
            report += f"**변경내용:** {change.get('change_description', 'N/A')}\n\n"
    
    if "summary" in data:
        report += f"## 📊 개선 요약\n\n{data['summary']}\n\n"
    
    if "improved_code" in data:
        report += f"## 💻 개선된 코드\n\n"
        report += f"```{code_language}\n{data['improved_code']}\n```\n\n"
    
    return report

# 메인 앱
def main():
    st.set_page_config(
        page_title="코드 개선 도우미",
        page_icon="🛠️",
        layout="wide"
    )
    
    st.title("🛠️ 회의 결과 기반 UI 코드 개선 도우미")
    st.markdown("회의에서 도출된 요구사항을 바탕으로 UI 코드를 개선해드립니다. 직접 요구사항을 입력하는 것도 당연히 가능합니다!")
    
    # LangChain 클라이언트 초기화
    llm = init_langchain_client(llm_name, 0.1)  # 약간의 창의성 허용
    if not llm:
        st.error("❌ LangChain Azure OpenAI 연결에 실패했습니다.")
        return
    
    # 사이드바 설정
    with st.sidebar:
        st.subheader("⚙️ 개선 설정")
        
        # 코드 언어 선택
        code_language = st.selectbox(
            "코드 언어:",
            ["auto-detect", "html", "react", "javascript", "jsp", "vue", "angular"],
            help="auto-detect는 코드를 분석하여 자동으로 언어를 감지합니다."
        )
        
        # 개선 집중 영역
        focus_area = st.selectbox(
            "개선 집중 영역:",
            ["전체 개선", "UI 디자인", "사용자 경험", "성능 최적화", "접근성", "반응형 디자인"]
        )
        
        st.divider()
        
        # 지원하는 요구사항 형태 안내
        st.subheader("💡 지원하는 입력 형태")
        st.markdown("""
        **요구사항 입력:**
        - 📄 **파일 업로드**: JSON, MD, TXT
        - 📝 **직접 입력**: 자유 형태
        
        **코드 입력:**
        - 📁 **파일 업로드**: 모든 코드 파일
        - ⌨️ **직접 입력**: 복사&붙여넣기
        - ❔ **지원 언어**: HTML, React, JavaScript, JSP, Vue.js 등
        """)
        
        st.info("💡 **팁**: 요구사항은 JSON, 마크다운, 일반 텍스트 어떤 형태든 입력 가능합니다!")
    
    # 메인 컨텐츠
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📋 입력 정보")
        
        # 요구사항 입력
        st.write("**1. 요구사항**")
        
        # 세션 상태로 요구사항 관리
        if "requirements_input" not in st.session_state:
            st.session_state.requirements_input = ""
        
        # 탭으로 입력 방식 선택
        tab1, tab2 = st.tabs(["📄 파일 업로드", "📝 직접 입력"])
        
        with tab1:
            uploaded_req_file = st.file_uploader(
                "요구사항 파일을 업로드하세요:",
                type=["json", "md", "txt"],
                help="JSON, 마크다운, 또는 텍스트 파일을 업로드할 수 있습니다."
            )
            
            if uploaded_req_file is not None:
                requirements_from_file = uploaded_req_file.read().decode("utf-8")
                st.session_state.requirements_input = requirements_from_file
                
                # 파일 형태 감지 및 미리보기
                parsed_req, req_format = parse_requirements(requirements_from_file)
                st.success(f"✅ {req_format.upper()} 형태로 인식되었습니다.")
                
                # 파일 내용 미리보기
                with st.expander("📄 파일 내용 미리보기"):
                    if req_format == "json":
                        st.json(parsed_req)
                    else:
                        st.text_area("내용", requirements_from_file, height=200, disabled=True, key="file_preview_text_area")
        
        with tab2:
            st.write("다양한 형태로 입력 가능합니다:")
            st.info("""
            • **JSON**: {"ui_requirements": [...], "user_feedback": [...]}\n
            • **마크다운**: ## 요구사항, ### UI 개선사항\n
            • **일반 텍스트**: 자유로운 형태의 요구사항 설명\n
            """)
            
            requirements_text = st.text_area(
                "요구사항을 입력하세요:",
                value=st.session_state.requirements_input,
                height=300,
                placeholder="""예시:

JSON 형태:
{"ui_requirements": [{"category": "버튼", "improvement_request": "더 큰 버튼 필요"}]}

마크다운 형태:
## UI 개선사항
- 버튼 크기를 더 크게 만들어주세요
- 색상을 더 밝게 해주세요

일반 텍스트:
버튼이 너무 작아서 클릭하기 어렵습니다. 좀 더 크게 만들어주세요.""",
                key="requirements_text_input"
            )
            
            # 요구사항 입력 완료 버튼 (tab2용)
            if st.button("📝 요구사항 입력 완료", 
                        type="secondary", 
                        use_container_width=True,
                        key="requirements_tab2_complete_btn"):
                st.session_state.requirements_input = requirements_text
                st.session_state["requirements_tab2_ready"] = True
                st.rerun()

            
            # 입력 내용이 변경되면 세션 상태 업데이트
            if requirements_text != st.session_state.requirements_input:
                st.session_state.requirements_input = requirements_text
            
            if requirements_text.strip():
                parsed_req, req_format = parse_requirements(requirements_text)
                st.success(f"✅ {req_format.upper()} 형태로 인식되었습니다.")

        # 최종 요구사항 값 설정
        requirements = st.session_state.requirements_input
        
        st.divider()
        
        # 현재 코드 입력
        st.write("**2. 현재 코드**")
        uploaded_code_file = st.file_uploader(
            "코드 파일 업로드 (선택사항):",
            type=["html", "js", "jsx", "jsp", "vue", "ts", "txt"]
        )
        
        current_code = ""
        if uploaded_code_file is not None:
            current_code = uploaded_code_file.read().decode("utf-8")
            # 파일 업로드 시 자동으로 저장 및 완료 상태 설정
            st.session_state["saved_code"] = current_code
            st.session_state["code_input_ready"] = True
            # 언어 자동 감지
            if code_language == "auto-detect":
                detected_lang = detect_code_language(current_code)
                st.info(f"🔍 감지된 언어: {detected_lang.upper()}")
                code_language = detected_lang
            st.text_area("업로드된 코드 미리보기:", current_code, height=200, disabled=True, key="uploaded_code_preview")
        else:
            # 저장된 코드가 있으면 표시
            if st.session_state.get("saved_code", "") and st.session_state.get("code_input_ready", False):
                current_code = st.session_state["saved_code"]
                st.text_area("입력 완료된 코드:", current_code, height=200, disabled=True, key="saved_code_display")
                st.success("✅ 코드 입력이 완료되었습니다!")
                
                # 코드 재입력 버튼
                if st.button("🔄 코드 다시 입력", type="secondary", use_container_width=True, key="code_re_input_btn"):
                    st.session_state["saved_code"] = ""
                    st.session_state["code_input_ready"] = False
                    st.rerun()
            else:
                # 새로 입력
                current_code = st.text_area(
                    "코드를 직접 입력하세요:",
                    height=300,
                    placeholder="개선하고 싶은 HTML, React, JavaScript 등의 코드를 입력하세요.",
                    key="current_code_input"
                )
                
                # 코드 입력 완료 버튼
                if st.button("📝 코드 입력 완료", 
                            type="secondary", 
                            use_container_width=True,
                            key="code_input_complete_btn"):
                    st.session_state["saved_code"] = current_code  # 코드를 세션에 저장
                    st.session_state["code_input_ready"] = True
                    st.rerun()
                    
                    
                    
        # 언어 자동 감지
        if code_language == "auto-detect" and current_code.strip():
            if st.session_state.get("code_input_ready", False):
                detected_lang = detect_code_language(current_code)
                st.info(f"🔍 감지된 언어: {detected_lang.upper()}")
                code_language = detected_lang
    
    with col2:
        st.subheader("🎯 개선 결과")
        
        # 입력 상태 체크
        requirements_ready = (uploaded_req_file is not None) or st.session_state.get("requirements_tab2_ready", False)
        code_ready = st.session_state.get("code_input_ready", False)
        
        # 실제 데이터 체크
        has_requirements = requirements.strip() != ""
        has_code = st.session_state.get("saved_code", "").strip() != ""
        
        # 현재 코드 변수 업데이트
        if has_code:
            current_code = st.session_state["saved_code"]
        
        # 상태별 안내 메시지
        if requirements_ready and code_ready and has_requirements and has_code:
            st.success("✅ 요구사항과 코드 입력이 모두 완료되었습니다! 개선을 시작할 수 있습니다.")
        elif not requirements_ready or not has_requirements:
            if code_ready and has_code:
                st.info("✅ 코드 입력 완료! 이제 요구사항을 입력하고 '입력 완료' 버튼을 눌러주세요.")
            else:
                st.warning("⚠️ 요구사항과 코드를 모두 입력하고 각각 '입력 완료' 버튼을 눌러주세요.")
        elif not code_ready or not has_code:
            if requirements_ready and has_requirements:
                st.info("✅ 요구사항 입력 완료! 이제 코드를 입력하고 '입력 완료' 버튼을 눌러주세요.")
            else:
                st.warning("⚠️ 현재 코드를 입력하고 '입력 완료' 버튼을 눌러주세요.")

        
        # 기존 코드 화면 미리보기 (HTML만 지원 안내)
        if current_code.strip() and code_ready:
            st.markdown("#### 🖥️ 기존 코드 화면 미리보기")
            if code_language == "html":
                try:
                    st.components.v1.html(current_code, height=400, scrolling=True)
                except Exception as e:
                    st.warning(f"렌더링 오류: {e}")
            else:
                st.info("⚠️ 화면 미리보기는 HTML 코드에만 지원됩니다.")
            st.divider()

        # 개선 실행 버튼
        if st.button("🚀 코드 개선 시작", 
                    type="primary", 
                    use_container_width=True,
                    disabled=not (requirements_ready and code_ready and has_requirements and has_code),
                    key="improvement_start_btn"):
            
            with st.spinner("🤖 AI가 코드를 개선하는 중입니다..."):
                import datetime
                st.session_state["analysis_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                result = analyze_and_improve_code(
                    llm, requirements, current_code, code_language, focus_area
                )
                st.session_state["improvement_result"] = result

        
        st.divider()
        
        # 결과 표시
        if "improvement_result" in st.session_state:
            result = st.session_state["improvement_result"]
            if result["success"]:
                st.success("✅ 코드 개선이 완료되었습니다!")
                
                
                # 개선 화면 미리보기
                if result["data"] and "improved_code" in result["data"]:
                    st.markdown("#### 🖥️ 개선 결과 화면 미리보기")
                    improved_code = result["data"]["improved_code"]  # <--- 변수 정의 추가

                    if code_language == "html":
                        try:
                            st.components.v1.html(improved_code, height=400, scrolling=True)
                        except Exception as e:
                            st.warning(f"렌더링 오류: {e}")
                            
                display_improvement_results(result, code_language)


                # 보고서 다운로드
                if result["data"]:
                    col_a, col_b = st.columns(2)
                    with col_a:
                        report_md = create_improvement_report(result["data"], code_language)
                        st.download_button(
                            label="📄 개선 보고서 (MD)",
                            data=report_md,
                            file_name="code_improvement_report.md",
                            mime="text/markdown",
                            use_container_width=True
                        )
                    with col_b:
                        st.download_button(
                            label="📥 원본 응답 (TXT)",
                            data=result["raw"],
                            file_name="improvement_raw_result.txt",
                            mime="text/plain",
                            use_container_width=True
                        )
            else:
                st.error(f"❌ 개선 중 오류 발생: {result['error']}")

if __name__ == "__main__":
    main()