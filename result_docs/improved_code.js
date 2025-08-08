import { useState, useEffect, useRef } from "react";

export default function UIMockPage() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const modalRef = useRef(null);

  // Focus modal when opened
  useEffect(() => {
    if (isModalOpen && modalRef.current) {
      modalRef.current.focus();
    }
  }, [isModalOpen]);

  return (
    <div className="min-h-screen bg-orange-50 text-orange-900 relative">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 flex items-center justify-between px-4 py-3 bg-orange-300 shadow-md z-50">
        <div className="text-xl font-bold">AppLogo</div>
        <nav className="flex gap-4 items-center">
          <button
            className="text-sm px-3 py-1 rounded hover:bg-orange-200 focus:outline-none focus:ring-2 focus:ring-orange-400"
            aria-label="Login"
          >
            Login
          </button>
          <button
            className="text-xl px-3 py-1 rounded hover:bg-orange-200 focus:outline-none focus:ring-2 focus:ring-orange-400"
            aria-label="Menu"
          >
            &#9776;
          </button>
        </nav>
      </header>

      {/* Banner */}
      <div className="bg-gray-200 text-center p-4 mt-16 mx-4 rounded shadow-sm">
        <p className="mb-2">This is a promotional banner. Limited time offer!</p>
        <img
          src="promo.png"
          alt="Promotional Banner Image"
          className="mx-auto w-48"
          width={192}
          height={108}
        />
      </div>

      {/* Main Content */}
      <main className="text-center px-4 py-8 max-w-xl mx-auto mt-4">
        <h1 className="text-2xl font-semibold mb-2">Welcome to Our Service</h1>
        <p className="mb-4">Find what you need, fast and easily.</p>

        {/* Main CTA Button - fixed bottom center */}
        <button
          className="fixed bottom-12 left-1/2 transform -translate-x-1/2 bg-orange-400 text-white px-6 py-3 rounded-lg shadow-lg min-w-[48px] min-h-[48px] hover:bg-orange-500 focus:outline-none focus:ring-2 focus:ring-orange-300 font-semibold"
          aria-label="Get Started"
          type="button"
        >
          Get Started
        </button>
      </main>

      {/* Feedback Modal Trigger */}
      <div className="text-center mb-20 mt-8">
        <button
          onClick={() => setIsModalOpen(true)}
          className="bg-orange-400 text-white px-4 py-2 rounded hover:bg-orange-500 focus:outline-none focus:ring-2 focus:ring-orange-300"
          aria-label="Open Feedback Modal"
          type="button"
        >
          Open Feedback Modal
        </button>
      </div>

      {/* Modal */}
      {isModalOpen && (
        <>
          <div
            className="fixed inset-0 bg-black/50 z-40"
            onClick={() => setIsModalOpen(false)}
            aria-hidden="true"
          ></div>
          <div
            ref={modalRef}
            role="dialog"
            aria-modal="true"
            tabIndex={-1}
            className="fixed top-1/4 left-1/2 transform -translate-x-1/2 z-50 bg-white p-6 rounded shadow-lg max-w-sm w-11/12"
          >
            <p className="mb-4">This is a feedback modal window.</p>
            <button
              onClick={() => setIsModalOpen(false)}
              className="bg-orange-400 text-white px-4 py-2 rounded hover:bg-orange-500 focus:outline-none focus:ring-2 focus:ring-orange-300"
              aria-label="Close Feedback Modal"
              type="button"
            >
              Close
            </button>
          </div>
        </>
      )}

      {/* Footer Input */}
      <footer className="fixed bottom-0 w-full bg-orange-200 p-2 flex gap-2 items-center">
        <input
          type="text"
          placeholder="Type your message..."
          aria-label="Message input"
          className="flex-1 px-2 py-1 rounded border border-orange-300 focus:outline-none focus:ring-2 focus:ring-orange-400"
        />
        <button
          className="bg-orange-400 text-white px-4 py-2 rounded hover:bg-orange-500 focus:outline-none focus:ring-2 focus:ring-orange-300"
          aria-label="Send message"
          type="button"
        >
          Send
        </button>
      </footer>
    </div>
  );
}
