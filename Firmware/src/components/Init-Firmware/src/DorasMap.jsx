
import { useState, useEffect, useRef } from "react";
 
const API_BASE_URL = "http://localhost:8000";
 
export default function DorasMap({ onBack }) {
  const [phase, setPhase] = useState("setup");
  const [numItems, setNumItems] = useState(5);
  const [duration, setDuration] = useState(60);
  const [targets, setTargets] = useState([]);
  const [timeLeft, setTimeLeft] = useState(0);
  const [allFound, setAllFound] = useState(false);
  const [error, setError] = useState(null);
  
  const pollIntervalRef = useRef(null);
 
  // Start the game
  const startGame = async () => {
    setError(null);
    setAllFound(false);
    
    try {
      const res = await fetch(`${API_BASE_URL}/api/scavenger/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ num_items: numItems, duration }),
      });
      
      if (!res.ok) throw new Error("Failed to start game");
      const data = await res.json();
      setTargets(data.targets);
      setTimeLeft(duration);
      setPhase("playing");
      
    } catch (err) {
      setError(err.message);
    }
  };
 
  // Poll for game status
  useEffect(() => {
    if (phase !== "playing") return;
 
    pollIntervalRef.current = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/scavenger/status`, {
          credentials: "include",
        });
        const data = await res.json();
        
        setTimeLeft(data.time_left ?? 0);
        setTargets(data.targets || []);
        
        // Check if game ended
        if (!data.active || data.time_left <= 0) {
          setAllFound(data.all_found || false);
          setPhase("done");
          clearInterval(pollIntervalRef.current);
        }
        
      } catch (err) {
        console.error("Poll error:", err);
      }
    }, 1000);
 
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, [phase]);
 
  const stopGame = async () => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
    }
    
    await fetch(`${API_BASE_URL}/api/scavenger/stop`, {
      method: "POST",
      credentials: "include",
    });
    
    setPhase("done");
  };
 
  const foundCount = targets.filter((t) => t.found).length;
  const timerColor =
    timeLeft > 30 ? "text-green-500" : timeLeft > 10 ? "text-yellow-500" : "text-red-500";
 
  // ── SETUP SCREEN ──
  if (phase === "setup") {
    return (
      <div className="flex flex-col items-center justify-center h-screen bg-gradient-to-b from-yellow-50 to-orange-100">
        <h1 className="text-5xl font-bold text-orange-600 mb-2">🗺️ Dora's Map</h1>
        <p className="text-gray-500 mb-10 text-lg">Find objects around the room!</p>
 
        <div className="bg-white rounded-2xl shadow-xl p-8 flex flex-col gap-6 w-80">
          <div>
            <label className="block text-gray-600 font-semibold mb-1">
              Number of objects
            </label>
            <input
              type="range" min={3} max={10} value={numItems}
              onChange={(e) => setNumItems(Number(e.target.value))}
              className="w-full accent-orange-500"
            />
            <span className="text-orange-500 font-bold text-xl">{numItems}</span>
          </div>
 
          <div>
            <label className="block text-gray-600 font-semibold mb-1">
              Time limit (seconds)
            </label>
            <input
              type="range" min={20} max={180} step={10} value={duration}
              onChange={(e) => setDuration(Number(e.target.value))}
              className="w-full accent-orange-500"
            />
            <span className="text-orange-500 font-bold text-xl">{duration}s</span>
          </div>
 
          {error && <p className="text-red-500 text-sm">{error}</p>}
 
          <button
            onClick={startGame}
            className="bg-orange-500 hover:bg-orange-600 text-white font-bold py-3 rounded-xl text-lg transition"
          >
            Let's Go! 🌟
          </button>
 
          {onBack && (
            <button onClick={onBack} className="text-gray-400 hover:text-gray-600 text-sm">
              ← Back
            </button>
          )}
        </div>
      </div>
    );
  }
 
  // ── PLAYING SCREEN ──
  if (phase === "playing") {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-gradient-to-b from-yellow-50 to-orange-100 p-6">
        <h1 className="text-4xl font-bold text-orange-600 mb-1">🗺️ Dora's Map</h1>
 
        <div className={`text-6xl font-mono font-bold my-4 ${timerColor}`}>
          {timeLeft}s
        </div>
 
        <p className="text-gray-500 mb-4 text-center">
          The webcam is now running in the background!<br/>
          Point your camera at the objects below.<br/>
          Press 'q' in the webcam window to quit.
        </p>
 
        <div className="grid grid-cols-2 gap-3 w-full max-w-sm mb-6">
          {targets.map((t, i) => (
            <div
              key={i}
              className={`
                flex items-center gap-2 p-3 rounded-xl font-semibold text-lg
                transition-all duration-500
                ${t.found
                  ? "bg-green-400 text-white scale-105 shadow-lg"
                  : "bg-white text-gray-700 shadow"}
              `}
            >
              <span>{t.found ? "✅" : "⬜"}</span>
              <span>{t.translated}</span>
            </div>
          ))}
        </div>
 
        <button
          onClick={stopGame}
          className="text-gray-400 hover:text-red-400 text-sm transition"
        >
          Give up
        </button>
      </div>
    );
  }
 
  // ── DONE SCREEN ──
  return (
    <div className="flex flex-col items-center justify-center h-screen bg-gradient-to-b from-yellow-50 to-orange-100">
      <div className="text-7xl mb-4">{allFound ? "🎉" : "⏰"}</div>
      <h1 className="text-4xl font-bold text-orange-600 mb-2">
        {allFound ? "You found them all!" : "Time's up!"}
      </h1>
      <p className="text-gray-500 text-xl mb-8">
        {foundCount} / {targets.length} objects found
      </p>
 
      <div className="grid grid-cols-2 gap-3 w-full max-w-sm mb-8">
        {targets.map((t, i) => (
          <div
            key={i}
            className={`
              flex items-center gap-2 p-3 rounded-xl font-semibold text-lg
              ${t.found ? "bg-green-400 text-white" : "bg-gray-200 text-gray-500 line-through"}
            `}
          >
            <span>{t.found ? "✅" : "❌"}</span>
            <span>{t.translated}</span>
          </div>
        ))}
      </div>
 
      <button
        onClick={() => {
          setPhase("setup");
          setTargets([]);
          setAllFound(false);
        }}
        className="bg-orange-500 hover:bg-orange-600 text-white font-bold py-3 px-8 rounded-xl text-lg transition mb-3"
      >
        Play Again 🗺️
      </button>
 
      {onBack && (
        <button onClick={onBack} className="text-gray-400 hover:text-gray-600 text-sm">
          ← Back to Home
        </button>
      )}
    </div>
  );
}