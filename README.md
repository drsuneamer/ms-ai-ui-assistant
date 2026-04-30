# MS AI UI Assistant
> AI-Based UI/UX Improvement Automation System

### 🖐️ Project Overview
MS AI UI Assistant is a platform that automatically derives UI/UX improvement requirements from various types of input, such as meeting transcripts and user feedback, and generates improved versions of HTML, JavaScript, and other code.
The primary objective of this project is to enable users to quickly and easily enhance the usability and quality of user interfaces without requiring advanced technical expertise.
This system integrates natural language processing, retrieval-augmented generation (RAG), and automated code generation to support data-driven UI/UX decision-making.

🔗 Demo video:: [https://youtu.be/QLup92paS9Y](https://youtu.be/p88RRI0-BeI?si=S_1Bujfp5d5j_ZV3) <br>
🌐 Deployment: https://sahara-web-001.azurewebsites.net <br>
&emsp;&emsp;*Note: The system was deployed on Microsoft Azure App Service during the project period for demonstration and testing purposes.*

### 📌 Key Features
- Automatically extracts UI/UX improvement requirements from meeting transcripts, feedback, or requirement documents
- Supports multiple input formats, including voice recordings, text files (txt/md), and direct text input
- Generates improved UI/UX code based on identified requirements
- Provides responsive design, accessibility, and visual design improvement recommendations
- Allows users to select specific focus areas for improvement
- Produces structured improvement reports and downloadable results (original input, analysis output, and generated code)
- Offers a web-based interface implemented using Streamlit

### 🛠️ Technology Stack

**Programming Language**<br>
- Python 3.13<br>

**Frameworks and Libraries**
- Streamlit (Web UI framework)
- LangChain (LLM orchestration framework)
- Langfuse (Monitoring and observability tool)<br>

**AI and Cloud Services**
- Azure OpenAI
  - GPT-4.1 (Agent model)<br>
  - GPT-4.1-mini<br>
  - GPT-4o (Speech processing)<br>
  - text-embedding-3-small (Vector embedding)
- Azure AI Search
- Azure Storage Account
- Azure Speech Services
- Azure App Service (Deployment)

<img width="723" height="227" alt="image" src="https://github.com/user-attachments/assets/8cd25f24-cc1e-4a39-9bf8-c9a8586c668e" />

<img width="723" height="265" alt="image" src="https://github.com/user-attachments/assets/1964b8a0-48c3-4145-9aa9-df4bcc4abb12" />


### 🗺️ Architecture

The system uses a multi-model AI pipeline where an AI agent routes each request to the appropriate tool:

- For UI/UX domain questions → RAG pipeline (Azure AI Search over indexed design guidelines)
- For code generation and requirement extraction → direct GPT-4.1 agent
- For audio input → GPT-4o speech processing → text → agent pipeline

<img width="723" height="1024" alt="image" src="https://github.com/user-attachments/assets/65c70fa2-cc52-40df-860b-901745adf809" />



### 📊 Project Structure
ms-ai-ui-assistant/<br>
├── pages/    _# Streamlit sidebar pages_<br>
├── result_docs/<br>
├── test_data/<br>
├── utils/    _# Shared utilities: LangChain/OpenAI setup, Langfuse monitor, Azure Speech helpers_<br>
├── .deployment<br>
├── .gitignore<br>
├── Home.py    _# Streamlit main entry point_<br>
├── README.md<br>
├── requirements.txt<br>
├── streamlit.sh    _# Azure App Service deployment config_<br>
└── test_scenario.md<br>

---

### 🧰 Local Setup

```bash
# Create virtual environment
python -m venv venv

# Activate (PowerShell admin mode required)
.\venv\Scripts\activate

# install packages
pip install streamlit openai python-dotenv langchain langchain-openai langchain-community azure-cognitiveservices-speech langfuse

# Run
streamlit run Home.py

# Optional: Generate requirements.txt
pip freeze > requirements.txt

# Optional: Install from requirements.txt
pip install -r requirements.txt
```



### 🐾 Features in Detail

#### Main Page – Feature Overview

<img width="800" height="1081" alt="image" src="https://github.com/user-attachments/assets/f50c62ff-f784-4802-a82f-7a4c6d2ffeb4" />


#### 1. 🚀 Integrated UI Improvement System

- Summarizes UI improvement points from meeting notes (text or WAV audio)
- Generates improved code based on existing frontend code input (HTML, React, and more)
- HTML code: supports live before/after preview in browser
- Downloadable report (Markdown) covering full summary and revised code
- Selectable focus areas: overall, UX, accessibility, responsive design

<img width="800" height="1003" alt="image" src="https://github.com/user-attachments/assets/393134cf-c4a7-4678-b376-8c3ae3cc2fc2" />

![ezgif-8bd73ba992a59a](https://github.com/user-attachments/assets/8b84723c-6036-4102-9582-5ef5a904bf30)
![ezgif-18b42cb0146202](https://github.com/user-attachments/assets/3a960d64-b1d4-4333-a9c6-54bbcf040e76)
![ezgif-368fdf2ecfd357](https://github.com/user-attachments/assets/3e84a44b-4549-4516-8c71-e7f7a129e090)


#### 2. 📇 Meeting Transcript Analysis

This module processes meeting transcripts and extracts actionable UI requirements.

- Supports text and document-based input
- Identifies user feedback and usability problems
- Suggests possible solutions for each issue
- Exports results in JSON or Markdown format

<img width="800" height="1125" alt="image" src="https://github.com/user-attachments/assets/43c492dc-a5a3-4598-a012-19f0b5a99d01" />

![ezgif-1b33ad3f72b925](https://github.com/user-attachments/assets/0413d11d-fe6e-482d-9f8a-51347d82f556)
![ezgif-1a88439846a227](https://github.com/user-attachments/assets/319b2610-1624-48da-b17e-15a17b53f974)



#### 3. 🛠️  Code Improvement from Requirements

- Input a requirements file + existing frontend code → receive improved code output
- HTML output: live preview available

<img width="800" height="790" alt="image" src="https://github.com/user-attachments/assets/f8809111-6253-42c1-9e81-bd43448c7927" />
<img width="800" height="1125" alt="image" src="https://github.com/user-attachments/assets/9f5389f2-e2b2-4327-9450-c66c3c40d78e" />

![ezgif-1d39768cc46cab](https://github.com/user-attachments/assets/3c553832-0e7c-4801-8d05-1d78d3908308)



#### 4. 💡 AI Question and Recommendation System

- AI agent selects appropriate tool per query
- UI/UX questions: routed to Azure AI Search (RAG over pre-indexed design guideline documents)
- Microcopy questions: prompt-guided responses based on writing guidelines

<img width="800" height="917" alt="image" src="https://github.com/user-attachments/assets/548855d6-2ea0-4bf5-a97a-df085106f12e" />

![ezgif-36666b510d4821](https://github.com/user-attachments/assets/e4c6cd97-9403-41d1-a20a-1b9c5a5e7087)
![ezgif-3dd52fc8619793](https://github.com/user-attachments/assets/a89f47f6-20b1-4a94-8da0-e12d6ec4989e)


#### 5. 💿 Speech-Based Meeting Summary

- Accepts WAV audio files
- Performs speech recognition
- Generates summarized meeting content

![ezgif-167d9aabeaa9d7](https://github.com/user-attachments/assets/72573122-e58b-436e-8efe-d20892c30516)



#### 6. ⚠️ System Monitoring and Administration

- Password-protected admin page linking to Langfuse dashboard
- Langfuse connection status visible

![ezgif-17fee65a8cd4b4](https://github.com/user-attachments/assets/5d74b869-4484-436f-9ecf-701955741741)
<img width="800" height="680" alt="image" src="https://github.com/user-attachments/assets/7037981f-fc54-407e-81fe-c82745ee266f" />


---

### 🔦 Planned Improvements

- Continuous audio recognition enhancement
- Performance optimization and stability improvements


