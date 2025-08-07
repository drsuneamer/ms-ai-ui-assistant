from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.retrievers import AzureAISearchRetriever
from langchain_community.tools import TavilySearchResults
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.tools import tool
from langchain_core.callbacks import BaseCallbackHandler
import os
import streamlit as st

# 환경변수 로드
load_dotenv()

st.set_page_config(
    page_title="AI에게 질문하기",
    page_icon="💡",
    layout="wide"
)

st.title("💡 고민이 될 때 AI에게 질문하기")
st.markdown("UI/UX, 마이크로카피, 기타 사례 등 궁금한 점을 AI에게 자유롭게 질문하거나, 회의록을 입력해 조언을 받아보세요.")

col1, col2 = st.columns([1, 1])

llm_gpt4 = os.getenv("AZURE_OPENAI_LLM_GPT4")   # Agent를 위한 gpt-4 모델 사용
llm_mini = os.getenv("AZURE_OPENAI_LLM_MINI")
search_index_name = os.getenv("AZURE_AI_SEARCH_INDEX_NAME") # rag-uiux

# Tool 사용을 추적하는 콜백 클래스
class ToolTracker(BaseCallbackHandler):
    def __init__(self):
        self.used_tools = []
        
    def on_tool_start(self, serialized, input_str, **kwargs):
        tool_name = serialized.get("name", "Unknown")
        if tool_name not in self.used_tools:
            self.used_tools.append(tool_name)
    
    def reset(self):
        self.used_tools = []

# 전역 tool tracker 인스턴스
if 'tool_tracker' not in st.session_state:
    st.session_state.tool_tracker = ToolTracker()

def format_docs(docs):
    return "\n\n".join([doc.page_content for doc in docs])

@tool   # tool임을 명시
def help_uiux(query: str) -> str: # 들어오고 나가는 형식 str로 지정
    """
    AI에게 UI/UX 관련 질문을 던져 답변을 받는 기능입니다.
    """
    try:
        # chain이 독자적으로 실행될 수 있도록 하위에 다 넣어줌
        retriever = AzureAISearchRetriever(
                    index_name=search_index_name,
                    top_k=3,  # 검색 결과로 가져올 문서 수
                    content_key="chunk" # "content"로 하지 않게 주의! index 생성할 때 확인하자
        )
        
        prompt = ChatPromptTemplate.from_template(  # 이 prompt 이용해서 search
        """
        가이드라인: {context}
        질문: {question}
        
        당신은 UI/UX 전문 AI 어시스턴트입니다. 가이드라인과 본인의 창의적 역량을 결합하여 사용자에게 최적의 디자인 솔루션을 제공합니다.
        핵심 원칙
        1. 지식 기반 활용

        Azure AI Search에서 검색된 UI/UX 가이드라인을 우선 참고하되, 맹목적으로 따르지 마세요. 검색된 내용이 사용자 요구사항과 완전히 맞지 않을 경우, 적절히 해석하고 응용하세요. 가이드라인에 명시되지 않은 부분은 창의적으로 보완하세요

        2. 창의적 사고

        기존 가이드를 출발점으로 하되, 혁신적인 아이디어를 제안하세요. 트렌드와 새로운 기술을 고려한 미래지향적 솔루션을 제시하세요. 사용자의 특수한 상황이나 제약조건에 맞는 맞춤형 접근을 시도하세요

        3. 응답 구조
        다음 구조로 답변하세요:
        📚 가이드라인 기반 분석

        검색된 가이드라인에서 관련된 내용 요약
        해당 가이드라인이 현재 상황에 어떻게 적용되는지 설명

        💡 창의적 제안

        가이드라인을 넘어선 혁신적 아이디어
        최신 트렌드나 기술을 활용한 접근법
        사용자 맥락에 특화된 독창적 솔루션

        ⚖️ 종합 권장사항

        가이드라인과 창의적 아이디어를 결합한 최종 제안
        구현 우선순위와 단계별 접근법
        예상되는 효과와 주의사항

        4. 응답 스타일: 전문성과 친근함의 균형, 구체적이고 실행 가능한 조언

        전문 용어를 사용하되, 명확한 설명을 병행하세요.
        이론적 근거와 실용적 조언을 함께 제공하세요.
        사용자의 수준에 맞춰 설명의 깊이를 조절하세요.
        추상적 개념보다는 구체적인 실행 방안을 제시하세요.
        가능한 한 예시나 사례를 들어 설명하세요.
        단계별 가이드나 체크리스트를 제공하세요.

        5. 검색 결과 활용법

        검색된 내용이 부족하거나 구체적이지 않을 때: "가이드라인을 바탕으로 다음과 같이 확장해보겠습니다"
        검색된 내용과 다른 의견을 제시할 때: "일반적인 가이드라인과는 다르지만, 귀하의 상황을 고려할 때..."
        가이드라인에 없는 새로운 영역: "기존 원칙을 응용하여 새로운 접근을 제안드립니다"

        6. 창의성 발휘 영역

        인터랙션 패턴: 기존 패턴의 혁신적 변형
        비주얼 디자인: 트렌드를 반영한 현대적 접근
        사용자 경험: 개인화와 맞춤화 전략
        기술 활용: AI, AR/VR 등 신기술 통합 아이디어
        접근성: 포용적 디자인의 창의적 해결책

        7. 품질 기준

        가이드라인 준수도: 70% (기본 원칙은 지키되)
        창의성과 혁신: 30% (차별화된 가치 제공)
        실현 가능성과 사용자 중심성을 항상 고려

        8. 금지사항

        검색된 가이드라인을 단순 복사하여 제시하지 마세요
        창의성을 핑계로 기본적인 UX 원칙을 무시하지 마세요
        근거 없는 주장이나 검증되지 않은 방법론은 피하세요
        사용자의 실제 제약조건(예산, 기술, 시간)을 무시한 제안은 자제하세요

        기억하세요: 당신은 가이드라인의 해석자이자 창의적 파트너입니다. 기존 지식을 존중하면서도, 사용자만의 독특한 솔루션을 만들어내는 것이 목표입니다.
        """
        )
        
        llm = AzureChatOpenAI(deployment_name=llm_mini)

        chain = (
            {
                "context": retriever | format_docs,
                "question": RunnablePassthrough()
            }
            | prompt
            | llm   # prompt 실행할 LLM
            | StrOutputParser() # 결과를 원하는 형태로
        )
        
        result = chain.invoke(query)  # query를 실제로 사용하도록 수정
        return result
    except Exception as e:
        return f"UI/UX 검색 중 오류가 발생했습니다: {str(e)}"

@tool
def help_microcopy(query: str) -> str:
    """
    AI에게 마이크로카피 작성 요청을 던져 답변을 받는 기능입니다.
    """
    try:
        prompt = ChatPromptTemplate.from_template(
            """
            당신은 UI/UX 전문 AI 어시스턴트입니다. 사용자의 요구에 맞는 마이크로카피를 작성합니다.
            
            질문: {question}
            
            마이크로카피 작성 가이드라인:
            1. 간결하고 명확하게 전달
            2. 사용자 친화적인 언어 사용
            3. 브랜드 톤과 일치하도록 작성
            4. 상황에 맞는 적절한 감정 표현
            
            예시:
            - 버튼 텍스트: "지금 시작하기"
            - 오류 메시지: "입력한 정보를 확인해주세요."
            
            위의 가이드라인을 참고하여, 다음 질문에 대한 마이크로카피를 작성해주세요.
            """
        )
        
        llm = AzureChatOpenAI(deployment_name=llm_mini)
        
        chain = (
            {
                "question": RunnablePassthrough()
            }
            | prompt
            | llm
            | StrOutputParser()
        )
        
        result = chain.invoke(query)
        return result
    except Exception as e:
        return f"마이크로카피 작성 중 오류가 발생했습니다: {str(e)}"

@tool
def web_search(query: str) -> str:   
    """직접적인 UI 관련 질문이 아닌 경우 웹 검색을 통해 답변을 제공하는 기능입니다."""
    try:
        tavilyRetriever = TavilySearchResults(
            max_results=3,  # 반환할 결과의 수
            search_depth="basic",  # 검색 깊이: basic 또는 advanced
            include_answer=True,  # 결과에 직접적인 답변 포함
            include_raw_content=True,  # 페이지의 원시 콘텐츠 포함
            include_images=True,  # 결과에 이미지 포함
        )
        
        result = tavilyRetriever.invoke(query)
        return str(result)  # 결과를 문자열로 변환
    except Exception as e:
        return f"웹 검색 중 오류가 발생했습니다: {str(e)}"

# Azure OpenAI LLM을 사용하여 Agent 생성
agent_llm = AzureChatOpenAI(
    deployment_name=llm_gpt4,
)
tools = [help_uiux, help_microcopy, web_search]

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", """
        당신은 UI/UX 전문 AI 어시스턴트입니다. 사용자의 질문에 대해 최적의 답변을 제공하기 위해 다음 도구를 적절히 선택하여 사용해야 합니다:

        🔍 **help_uiux**: UI/UX 디자인, 사용자 경험, 인터페이스 설계, 사용성, 접근성 등과 관련된 질문일 때 사용
        - 예: "버튼 디자인을 어떻게 개선하면 좋을까요?", "사용자 경험을 향상시키려면?", "UI 가이드라인이 궁금해요"
        
        ✏️ **help_microcopy**: 버튼 텍스트, 오류 메시지, 안내 문구, 라벨링 등 UI 텍스트 작성 요청일 때 사용
        - 예: "로그인 버튼에 쓸 텍스트 추천해주세요", "오류 메시지를 어떻게 쓰면 좋을까요?", "메뉴명을 정해주세요"
        
        🌐 **web_search**: 최신 트렌드, 시장 동향, 특정 회사/제품 정보, 기술 동향 등 실시간 정보가 필요한 질문일 때 사용
        - 예: "2024년 UI 트렌드가 궁금해요", "구글의 최신 디자인 시스템은?", "요즘 인기있는 앱 UI는?"

        **중요한 판단 기준:**
        - UI/UX 관련 질문이면서 구체적인 디자인 조언이 필요하면 → help_uiux
        - 텍스트나 카피 작성 요청이면 → help_microcopy  
        - 최신 정보나 실시간 검색이 필요하면 → web_search
        - 회의록 분석이나 조언 요청이면 → help_uiux (UI/UX 맥락으로 해석)

        각 질문의 핵심 의도를 파악하여 가장 적합한 도구를 선택하세요.
         """),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

agent = create_tool_calling_agent(
    agent_llm,
    tools,
    prompt,
)

# AgentExecutor 생성 - return_intermediate_steps=True 추가!
agent_executor = AgentExecutor(
    agent=agent, 
    tools=tools, 
    verbose=True,
    handle_parsing_errors=True,  # 파싱 에러 처리
    max_iterations=3,  # 최대 반복 횟수 제한
    max_execution_time=60,  # 최대 실행 시간(초)
    return_intermediate_steps=True,  # 중간 단계 정보 반환
)

with col1:
    st.subheader("📝 질문 입력 또는 회의록 업로드")
    user_question = st.text_area(
        "AI에게 궁금한 점을 입력하세요:",
        height=200,
        placeholder="예시: 호텔 예약 UI에서 버튼 색상을 어떻게 개선하면 좋을까요?"
    )
    st.markdown("""
    - UI/UX 개선, 디자인 원칙, 마이크로카피, 사례 등 다양한 질문을 할 수 있습니다.
    - Azure AI Search 인덱스 기반 가이드라인을 참고하여 답변합니다.
    - 웹 검색도 활용합니다.
    """)
    
    # 질문 입력 완료 버튼 추가
    question_ready = st.button("📝 질문 입력 완료", 
                              type="secondary", 
                              use_container_width=True,
                              key="question_complete_btn")
    if question_ready:
        st.session_state["question_input_ready"] = True
        st.rerun()
    
    
    st.divider()
    uploaded_file = st.file_uploader("회의록 파일 업로드 (txt, md)", type=["txt", "md"])
    meeting_content = ""
    if uploaded_file is not None:
        meeting_content = uploaded_file.read().decode("utf-8")
        st.text_area("업로드된 회의록 미리보기", meeting_content, height=200, disabled=True)
    else:
        meeting_content = st.text_area(
            "회의록을 직접 입력하세요 (선택):",
            height=200,
            placeholder="회의에서 논의된 UI/UX 개선사항을 입력해주세요..."
        )
        
    # 회의록 입력 완료 버튼 추가
    meeting_ready = st.button("📝 회의록 입력 완료", 
                                type="secondary", 
                                use_container_width=True,
                                key="meeting_complete_btn")
    if meeting_ready:
        st.session_state["meeting_input_ready"] = True
        st.rerun()

with col2:
    # 질문 또는 회의록이 있을 때만 버튼 활성화
    if user_question.strip() or meeting_content.strip():
        if user_question.strip():
            btn_key = f"ask_ai_btn_question_{len(user_question)}"
        else:
            btn_key = f"ask_ai_btn_meeting_{len(meeting_content)}"
        if st.button("🚀 질문/조언 받기", type="primary", use_container_width=True, key=btn_key):
            with st.spinner("AI가 답변을 준비 중입니다..."):
                try:
                    # Tool tracker 리셋
                    st.session_state.tool_tracker.reset()
                    
                    if meeting_content.strip() and not user_question.strip():
                        advice_prompt = f"다음 회의록을 바탕으로 UI/UX 개선 조언을 해주세요:\n\n{meeting_content}"
                        # AgentExecutor의 invoke 메서드 사용 (콜백 포함)
                        result = agent_executor.invoke(
                            {"input": advice_prompt},
                            config={"callbacks": [st.session_state.tool_tracker]}
                        )
                    elif user_question.strip():
                        # AgentExecutor의 invoke 메서드 사용 (콜백 포함)
                        result = agent_executor.invoke(
                            {"input": user_question},
                            config={"callbacks": [st.session_state.tool_tracker]}
                        )
                    
                    # 답변만 추출해서 세션에 저장
                    answer = result.get("output", str(result))
                    st.session_state["ai_answer"] = answer
                    
                    # 사용된 tool 정보 저장 (콜백에서 수집된 정보 + intermediate_steps에서 추출)
                    used_tools = st.session_state.tool_tracker.used_tools.copy()
                    
                    # intermediate_steps에서도 추가로 확인
                    steps = result.get("intermediate_steps", [])
                    for step in steps:
                        if isinstance(step, tuple) and len(step) >= 1:
                            action = step[0]
                            if hasattr(action, 'tool') and action.tool not in used_tools:
                                used_tools.append(action.tool)
                    
                    # tool이 사용되지 않은 경우
                    if not used_tools:
                        used_tools = ["직접 답변"]
                    
                    st.session_state["used_tools"] = used_tools
                    
                except Exception as e:
                    st.error(f"AI 답변 생성 중 오류: {str(e)}")
                    # 디버깅을 위한 상세 에러 정보
                    import traceback
                    st.error(f"상세 에러: {traceback.format_exc()}")

    if "ai_answer" in st.session_state:
        st.markdown("#### 📝 AI의 답변")
        
        # 사용된 tool 정보 표시
        if "used_tools" in st.session_state:
            tool_name_map = {
                "help_uiux": "🔍 UI/UX 가이드라인 검색",
                "help_microcopy": "✏️ 마이크로카피 생성", 
                "web_search": "🌐 웹 검색",
                "직접 답변": "🤖 AI 직접 답변"
            }
            
            used_tools = st.session_state["used_tools"]
            tool_displays = []
            for tool in used_tools:
                display_name = tool_name_map.get(tool, f"🔧 {tool}")
                tool_displays.append(display_name)
            
            if len(tool_displays) == 1:
                st.info(f"**사용된 AI Tool:** {tool_displays[0]}")
            else:
                st.info(f"**사용된 AI Tools:** {' + '.join(tool_displays)}")
        
        
        st.write(st.session_state["ai_answer"])
        
        
        st.download_button(
            label="📥 답변 다운로드 (Markdown)",
            data=str(st.session_state["ai_answer"]),
            file_name="ai_answer.md",
            mime="text/markdown"
        )
    else:
        st.info("👆 질문을 입력하거나 회의록을 업로드/입력한 후 '질문/조언 받기' 버튼을 눌러주세요.")

# 사이드바 안내
with st.sidebar:
    st.markdown("### ℹ️ 사용법 안내")
    st.markdown("""
    - 질문을 입력하면 AI가 Azure AI Search 인덱스와 웹 검색을 참고해 답변합니다.
    - 회의록을 입력하거나 업로드하면, 회의 내용을 바탕으로 UI/UX 개선 조언을 받을 수 있습니다.
    - 답변은 Markdown 파일로 다운로드할 수 있습니다.
    - UI/UX, 마이크로카피, 사례 등 다양한 주제를 자유롭게 질문하세요.
    """)
    
    st.divider()
    st.markdown("### 🔧 AI Tools")
    st.markdown("""
    **🔍 UI/UX 가이드라인 검색**
    - 디자인 원칙과 사용자 경험 조언
    
    **✏️ 마이크로카피 생성**
    - 버튼, 메시지, 라벨 텍스트 작성
    
    **🌐 웹 검색**
    - 최신 트렌드와 실시간 정보 검색
    """)