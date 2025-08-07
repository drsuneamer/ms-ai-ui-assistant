# 🚀 UI/UX 개선 보고서

**대상 언어:** HTML
**개선 일시:** 2025-08-07 10:27:49

## 📊 개선 요약

- **총 변경사항:** 3
- **주요 개선사항:**
  - 메인 CTA 버튼 위치를 중앙 하단 고정으로 변경
  - 로그인 버튼 위치 유지 및 UI 간섭 최소화
  - 메인 컬러를 연한 오렌지 계열로 변경하여 친근한 분위기 조성
- **예상 효과:** 사용자가 주요 행동을 쉽게 인지하고 접근할 수 있으며, 친근하고 편안한 UI로 사용자 만족도 및 초기 진입 장벽이 감소하여 서비스 이용 경험이 향상됩니다.

## ✅ 적용된 개선사항

### 1. 메인 CTA 버튼을 오른쪽 상단에서 중앙 하단 쪽으로 이동하여 명확한 위치 제공
**변경내용:** 기존 메인 CTA 버튼을 main 영역 중앙 하단에서 고정된 footer 위쪽 중앙으로 위치 변경, 반응형 고려하여 화면 크기에 따라 위치 유지 및 충분한 여백 확보

**변경 전후:** 변경 전: <button class="cta">Get Started</button> (main 내부 중앙)
변경 후: <button class="cta fixed-cta" aria-label="Get Started">Get Started</button> (footer 위쪽 중앙 고정)

### 2. 로그인 버튼 위치는 유지하되 메인 CTA 버튼과 겹치지 않도록 배치 조정
**변경내용:** 로그인 버튼은 header 오른쪽 상단에 고정 유지, nav 내부 간격 조정 및 버튼 크기 유지로 CTA 버튼과 시각적 간섭 방지

**변경 전후:** 변경 전: header padding 1rem, nav gap 1rem
변경 후: header padding 1rem 1.5rem, nav gap 유지, 로그인 버튼 위치 및 크기 유지

### 3. 따뜻하고 편안한 느낌을 주는 연한 오렌지 톤 등으로 메인 컬러 변경 검토
**변경내용:** 기존 파란색 계열 대신 연한 오렌지 계열(#ffb74d, #ff8a65, #ffcc80)로 배경, 버튼, 헤더, 푸터 색상 변경하여 따뜻한 분위기 조성, WCAG 명도 대비 고려

**변경 전후:** 변경 전: 파란색 계열 (없음, 기존 코드에 파란색 없음)
변경 후: 연한 오렌지 계열 색상 적용

## 🔧 기술적 개선사항

- 메인 CTA 버튼을 화면 하단 중앙에 고정하여 사용자가 주요 행동을 쉽게 인지하고 접근 가능하도록 개선
- 로그인 버튼은 기존 위치인 오른쪽 상단에 유지하면서 시각적 간섭을 최소화하여 사용자 혼란 방지
- 전체 UI 색상을 연한 오렌지 계열로 변경하여 따뜻하고 친근한 느낌 제공, WCAG 명도 대비를 고려해 가독성 유지
- 반응형 디자인 적용으로 모바일 및 다양한 화면 크기에서 버튼 위치 및 크기 적절히 조정
- 접근성 향상을 위해 aria-label, role, aria-haspopup, aria-controls 등 ARIA 속성 추가 및 키보드 접근성(ESC 키로 모달 닫기) 지원
- 시각장애인용 숨김 텍스트 추가로 폼 요소 접근성 강화
- 고정된 요소들에 적절한 z-index 부여로 UI 요소 간 충돌 방지
- 버튼 및 인터랙티브 요소에 포커스 스타일 및 호버 스타일 추가하여 사용성 향상

## 💻 개선된 코드

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>UI Test Mock Page</title>
  <style>
    body {
      font-family: sans-serif;
      margin: 0;
      padding: 0;
      background-color: #fffaf5; /* 연한 오렌지 배경 */
      color: #4e342e; /* 다크 브라운 텍스트로 가독성 확보 */
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }

    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 1rem 1.5rem;
      background-color: #ffb74d; /* 연한 오렌지 헤더 */
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      position: sticky;
      top: 0;
      z-index: 100;
    }

    .logo {
      font-size: 1.5rem;
      font-weight: bold;
      color: #4e342e;
    }

    nav {
      display: flex;
      gap: 1rem;
    }

    .login-btn {
      background: transparent;
      border: none;
      font-size: 1rem;
      cursor: pointer;
      color: #4e342e;
      padding: 0.5rem 1rem;
      border-radius: 4px;
      transition: background-color 0.3s ease;
    }

    .login-btn:hover,
    .login-btn:focus {
      background-color: rgba(255, 183, 77, 0.3);
      outline: none;
    }

    .banner {
      background-color: #fbe9e7; /* 연한 오렌지 계열 밝은 배경 */
      padding: 2rem 1rem;
      margin: 1rem;
      text-align: center;
      font-size: 1rem;
      border-radius: 8px;
      color: #4e342e;
    }

    main {
      flex: 1 0 auto;
      padding: 1rem;
      text-align: center;
      max-width: 600px;
      margin: 0 auto 6rem auto; /* footer 위 공간 확보 */
    }

    main h1 {
      font-size: 2rem;
      margin-bottom: 0.5rem;
    }

    main p {
      font-size: 1.125rem;
      margin-bottom: 2rem;
      color: #6d4c41;
    }

    .cta {
      display: inline-block;
      padding: 1rem 2rem;
      background-color: #ff8a65; /* 연한 오렌지 버튼 */
      color: white;
      border: none;
      border-radius: 8px;
      font-size: 1.2rem;
      cursor: pointer;
      min-width: 48px;
      min-height: 48px;
      box-shadow: 0 4px 6px rgba(255, 138, 101, 0.5);
      transition: background-color 0.3s ease, box-shadow 0.3s ease;
    }

    .cta:hover,
    .cta:focus {
      background-color: #ff7043;
      box-shadow: 0 6px 12px rgba(255, 112, 67, 0.7);
      outline: none;
    }

    /* 고정된 메인 CTA 버튼 - 중앙 하단, footer 바로 위 */
    .fixed-cta {
      position: fixed;
      bottom: 4.5rem; /* footer 높이 + 여유 */
      left: 50%;
      transform: translateX(-50%);
      z-index: 1100;
      box-shadow: 0 6px 12px rgba(255, 138, 101, 0.8);
    }

    /* 반응형 조정 */
    @media (max-width: 480px) {
      .fixed-cta {
        bottom: 5.5rem;
        padding: 0.75rem 1.5rem;
        font-size: 1rem;
      }

      header {
        padding: 1rem;
      }

      main {
        margin-bottom: 7rem;
        padding: 1rem 0.5rem;
      }
    }

    .modal {
      display: none;
      position: fixed;
      top: 20%;
      left: 50%;
      transform: translateX(-50%);
      background: white;
      padding: 2rem;
      box-shadow: 0 4px 12px rgba(0,0,0,0.3);
      z-index: 1200;
      max-width: 90%;
      border-radius: 8px;
    }

    .modal.active {
      display: block;
    }

    .modal-overlay {
      display: none;
      position: fixed;
      inset: 0;
      background-color: rgba(0,0,0,0.5);
      z-index: 1190;
    }

    .modal-overlay.active {
      display: block;
    }

    footer {
      position: fixed;
      bottom: 0;
      width: 100%;
      padding: 0.5rem 1rem;
      background-color: #ffcc80; /* 연한 오렌지 푸터 */
      display: flex;
      gap: 0.5rem;
      align-items: center;
      justify-content: center;
      box-shadow: 0 -2px 6px rgba(0,0,0,0.1);
      z-index: 100;
    }

    input[type="text"] {
      padding: 0.5rem;
      flex: 1;
      border: 1px solid #d7ccc8;
      border-radius: 4px;
      font-size: 1rem;
      color: #4e342e;
    }

    input[type="text"]:focus {
      outline: 2px solid #ff8a65;
      outline-offset: 2px;
    }

    button {
      min-width: 48px;
      min-height: 48px;
      border-radius: 4px;
      border: none;
      cursor: pointer;
      font-size: 1rem;
      background-color: #ff8a65;
      color: white;
      transition: background-color 0.3s ease;
    }

    button:hover,
    button:focus {
      background-color: #ff7043;
      outline: none;
    }

  </style>
</head>
<body>

  <header>
    <div class="logo">AppLogo</div>
    <nav aria-label="Primary navigation">
      <button class="login-btn" aria-label="Login to your account">Login</button>
      <button class="login-btn" aria-label="Open menu">&#9776;</button> <!-- hamburger -->
    </nav>
  </header>

  <div class="banner" role="region" aria-label="Promotional banner">
    <p>This is a promotional banner. Limited time offer!</p>
    <img src="promo.png" alt="Promotional Banner Image" width="200" />
  </div>

  <main>
    <h1>Welcome to Our Service</h1>
    <p>Find what you need, fast and easily.</p>
  </main>

  <!-- 메인 CTA 버튼: 중앙 하단 고정 -->
  <button class="cta fixed-cta" aria-label="Get Started">Get Started</button>

  <button onclick="openModal()" class="cta" style="margin-bottom: 5rem;" aria-haspopup="dialog" aria-controls="modal">Open Feedback Modal</button>

  <div class="modal-overlay" id="overlay" tabindex="-1" onclick="closeModal()"></div>
  <div class="modal" id="modal" role="dialog" aria-modal="true" aria-labelledby="modalTitle" tabindex="-1">
    <h2 id="modalTitle">Feedback</h2>
    <p>This is a feedback modal window.</p>
    <button onclick="closeModal()" aria-label="Close feedback modal">Close</button>
  </div>

  <footer>
    <label for="message" class="visually-hidden">Type your message</label>
    <input type="text" id="message" placeholder="Type your message..." aria-label="Type your message" />
    <button aria-label="Send message">Send</button>
  </footer>

  <script>
    function openModal() {
      const modal = document.getElementById('modal');
      const overlay = document.getElementById('overlay');
      modal.classList.add('active');
      overlay.classList.add('active');
      modal.focus();
    }

    function closeModal() {
      const modal = document.getElementById('modal');
      const overlay = document.getElementById('overlay');
      modal.classList.remove('active');
      overlay.classList.remove('active');
    }

    // 키보드 접근성: ESC 키로 모달 닫기
    document.addEventListener('keydown', function(event) {
      const modal = document.getElementById('modal');
      if(event.key === 'Escape' && modal.classList.contains('active')) {
        closeModal();
      }
    });
  </script>

  <style>
    /* 시각장애인용 숨김 텍스트 */
    .visually-hidden {
      position: absolute !important;
      width: 1px !important;
      height: 1px !important;
      padding: 0 !important;
      margin: -1px !important;
      overflow: hidden !important;
      clip: rect(0, 0, 0, 0) !important;
      white-space: nowrap !important;
      border: 0 !important;
    }
  </style>

</body>
</html>
```

