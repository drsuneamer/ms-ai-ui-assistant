import { useState } from "react";

export default function UIMockPage() {
  const [isModalOpen, setIsModalOpen] = useState(false);

  return (
    <div className="min-h-screen bg-orange-50 text-gray-800">
      {/* Header */}
      <header className="flex items-center justify-between px-4 py-3 bg-orange-300">
        <div className="text-xl font-bold">AppLogo</div>
        <nav className="flex gap-4 items-center">
          <button className="text-sm">Login</button>
          <button className="text-xl">&#9776;</button>
        </nav>
      </header>

      {/* Banner */}
      <div className="bg-gray-200 text-center p-4 m-4 rounded">
        <p className="mb-2">This is a promotional banner. Limited time offer!</p>
        <img src="promo.png" alt="Promotional Banner Image" className="mx-auto w-48" />
      </div>

      {/* Main Content */}
      <main className="text-center px-4 py-8">
        <h1 className="text-2xl font-semibold mb-2">Welcome to Our Service</h1>
        <p className="mb-4">Find what you need, fast and easily.</p>
        <button className="bg-orange-400 text-white px-6 py-3 rounded hover:bg-orange-500 min-w-[48px] min-h-[48px]">
          Get Started
        </button>
      </main>

      {/* Feedback Modal Trigger */}
      <div className="text-center mb-20">
        <button
          onClick={() => setIsModalOpen(true)}
          className="bg-orange-400 text-white px-4 py-2 rounded hover:bg-orange-500"
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
          ></div>
          <div className="fixed top-1/4 left-1/2 transform -translate-x-1/2 z-50 bg-white p-6 rounded shadow-lg">
            <p className="mb-4">This is a feedback modal window.</p>
            <button
              onClick={() => setIsModalOpen(false)}
              className="bg-orange-400 text-white px-4 py-2 rounded hover:bg-orange-500"
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
          className="flex-1 px-2 py-1 rounded border"
        />
        <button className="bg-orange-400 text-white px-4 py-2 rounded hover:bg-orange-500">
          Send
        </button>
      </footer>
    </div>
  );
}
