// import { useState, useEffect, useRef } from "react";
 
// const API_BASE_URL = "http://localhost:8000";
 
// export default function DorasMap({ onBack }) {
//   const [phase, setPhase] = useState("setup"); // setup | playing | done
//   const [numItems, setNumItems] = useState(5);
//   const [duration, setDuration] = useState(60);
//   const [targets, setTargets] = useState([]);
//   const [timeLeft, setTimeLeft] = useState(0);
//   const [allFound, setAllFound] = useState(false);
//   const [error, setError] = useState(null);
//   const pollRef = useRef(null);
 
//   // Start the game
//   const startGame = async () => {
//     setError(null);
//     try {
//       const res = await fetch(`${API_BASE_URL}/api/scavenger/start`, {
//         method: "POST",
//         headers: { "Content-Type": "application/json" },
//         credentials: "include",
//         body: JSON.stringify({ num_items: numItems, duration }),
//       });
//       if (!res.ok) throw new Error("Failed to start game");
//       const data = await res.json();
//       setTargets(data.targets);
//       setTimeLeft(duration);
//       setAllFound(false);
//       setPhase("playing");
//     } catch (err) {
//       setError(err.message);
//     }
//   };
 
//   // Poll status every second while playing
//   useEffect(() => {
//     if (phase !== "playing") return;
 
//     pollRef.current = setInterval(async () => {
//       try {
//         const res = await fetch(`${API_BASE_URL}/api/scavenger/status`, {
//           credentials: "include",
//         });
//         const data = await res.json();
 
//         if (!data.active && phase === "playing") {
//           setTargets(data.targets || targets);
//           setTimeLeft(data.time_left ?? 0);
//           setAllFound(data.all_found ?? false);
//           setPhase("done");
//           clearInterval(pollRef.current);
//         } else {
//           setTargets(data.targets || []);
//           setTimeLeft(data.time_left ?? 0);
//           if (data.all_found) {
//             setAllFound(true);
//             setPhase("done");
//             clearInterval(pollRef.current);
//           }
//         }
//       } catch (err) {
//         console.error("Poll error:", err);
//       }
//     }, 1000);
 
//     return () => clearInterval(pollRef.current);
//   }, [phase]);
 
//   const stopGame = async () => {
//     clearInterval(pollRef.current);
//     await fetch(`${API_BASE_URL}/api/scavenger/stop`, {
//       method: "POST",
//       credentials: "include",
//     });
//     setPhase("done");
//   };
 
//   const foundCount = targets.filter((t) => t.found).length;
//   const timerColor =
//     timeLeft > 30 ? "text-green-500" : timeLeft > 10 ? "text-yellow-500" : "text-red-500";
 
//   // ── SETUP SCREEN ──
//   if (phase === "setup") {
//     return (
//       <div className="flex flex-col items-center justify-center h-screen bg-gradient-to-b from-yellow-50 to-orange-100">
//         <h1 className="text-5xl font-bold text-orange-600 mb-2">🗺️ Dora's Map</h1>
//         <p className="text-gray-500 mb-10 text-lg">Find objects around the room!</p>
 
//         <div className="bg-white rounded-2xl shadow-xl p-8 flex flex-col gap-6 w-80">
//           <div>
//             <label className="block text-gray-600 font-semibold mb-1">
//               Number of objects
//             </label>
//             <input
//               type="range" min={3} max={10} value={numItems}
//               onChange={(e) => setNumItems(Number(e.target.value))}
//               className="w-full accent-orange-500"
//             />
//             <span className="text-orange-500 font-bold text-xl">{numItems}</span>
//           </div>
 
//           <div>
//             <label className="block text-gray-600 font-semibold mb-1">
//               Time limit (seconds)
//             </label>
//             <input
//               type="range" min={20} max={180} step={10} value={duration}
//               onChange={(e) => setDuration(Number(e.target.value))}
//               className="w-full accent-orange-500"
//             />
//             <span className="text-orange-500 font-bold text-xl">{duration}s</span>
//           </div>
 
//           {error && <p className="text-red-500 text-sm">{error}</p>}
 
//           <button
//             onClick={startGame}
//             className="bg-orange-500 hover:bg-orange-600 text-white font-bold py-3 rounded-xl text-lg transition"
//           >
//             Let's Go! 🌟
//           </button>
 
//           {onBack && (
//             <button onClick={onBack} className="text-gray-400 hover:text-gray-600 text-sm">
//               ← Back
//             </button>
//           )}
//         </div>
//       </div>
//     );
//   }
 
//   // ── PLAYING SCREEN ──
//   if (phase === "playing") {
//     return (
//       <div className="flex flex-col items-center justify-center min-h-screen bg-gradient-to-b from-yellow-50 to-orange-100 p-6">
//         <h1 className="text-4xl font-bold text-orange-600 mb-1">🗺️ Dora's Map</h1>
 
//         <div className={`text-6xl font-mono font-bold my-4 ${timerColor}`}>
//           {timeLeft}s
//         </div>
 
//         <p className="text-gray-500 mb-4">
//           Found {foundCount} / {targets.length} — point your webcam at objects!
//         </p>
 
//         <div className="grid grid-cols-2 gap-3 w-full max-w-sm mb-6">
//           {targets.map((t, i) => (
//             <div
//               key={i}
//               className={`
//                 flex items-center gap-2 p-3 rounded-xl font-semibold text-lg
//                 transition-all duration-500
//                 ${t.found
//                   ? "bg-green-400 text-white scale-105 shadow-lg"
//                   : "bg-white text-gray-700 shadow"}
//               `}
//             >
//               <span>{t.found ? "✅" : "⬜"}</span>
//               <span>{t.translated}</span>
//             </div>
//           ))}
//         </div>
 
//         <button
//           onClick={stopGame}
//           className="text-gray-400 hover:text-red-400 text-sm transition"
//         >
//           Give up
//         </button>
//       </div>
//     );
//   }
 
//   // ── DONE SCREEN ──
//   return (
//     <div className="flex flex-col items-center justify-center h-screen bg-gradient-to-b from-yellow-50 to-orange-100">
//       <div className="text-7xl mb-4">{allFound ? "🎉" : "⏰"}</div>
//       <h1 className="text-4xl font-bold text-orange-600 mb-2">
//         {allFound ? "You found them all!" : "Time's up!"}
//       </h1>
//       <p className="text-gray-500 text-xl mb-8">
//         {foundCount} / {targets.length} objects found
//       </p>
 
//       <div className="grid grid-cols-2 gap-3 w-full max-w-sm mb-8">
//         {targets.map((t, i) => (
//           <div
//             key={i}
//             className={`
//               flex items-center gap-2 p-3 rounded-xl font-semibold text-lg
//               ${t.found ? "bg-green-400 text-white" : "bg-gray-200 text-gray-500 line-through"}
//             `}
//           >
//             <span>{t.found ? "✅" : "❌"}</span>
//             <span>{t.translated}</span>
//           </div>
//         ))}
//       </div>
 
//       <button
//         onClick={() => setPhase("setup")}
//         className="bg-orange-500 hover:bg-orange-600 text-white font-bold py-3 px-8 rounded-xl text-lg transition mb-3"
//       >
//         Play Again 🗺️
//       </button>
 
//       {onBack && (
//         <button onClick={onBack} className="text-gray-400 hover:text-gray-600 text-sm">
//           ← Back to Home
//         </button>
//       )}
//     </div>
//   );
// }

import { useState, useEffect, useRef } from "react";
 
const API_BASE_URL = "http://localhost:8000";
 
export default function DorasMap({ onBack }) {
  const [phase, setPhase] = useState("setup"); // setup | playing | done
  const [numItems, setNumItems] = useState(5);
  const [duration, setDuration] = useState(60);
  const [targets, setTargets] = useState([]);
  const [timeLeft, setTimeLeft] = useState(0);
  const [allFound, setAllFound] = useState(false);
  const [error, setError] = useState(null);
  const [showVideo, setShowVideo] = useState(false);
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const pollRef = useRef(null);
 
  // Start video stream
  const startVideoStream = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        streamRef.current = stream;
        setShowVideo(true);
      }
    } catch (err) {
      console.error("Error accessing camera:", err);
      setError("Could not access camera. Please allow camera permissions.");
    }
  };

  // Stop video stream
  const stopVideoStream = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setShowVideo(false);
  };
 
  // Start the game
  const startGame = async () => {
    setError(null);
    try {
      // Start video stream first
      await startVideoStream();
      
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
      setAllFound(false);
      setPhase("playing");
    } catch (err) {
      setError(err.message);
      stopVideoStream();
    }
  };
 
  // Poll status every second while playing
  useEffect(() => {
    if (phase !== "playing") return;
 
    pollRef.current = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/scavenger/status`, {
          credentials: "include",
        });
        const data = await res.json();
 
        if (!data.active && phase === "playing") {
          setTargets(data.targets || targets);
          setTimeLeft(data.time_left ?? 0);
          setAllFound(data.all_found ?? false);
          setPhase("done");
          clearInterval(pollRef.current);
          stopVideoStream();
        } else {
          setTargets(data.targets || []);
          setTimeLeft(data.time_left ?? 0);
          if (data.all_found) {
            setAllFound(true);
            setPhase("done");
            clearInterval(pollRef.current);
            stopVideoStream();
          }
        }
      } catch (err) {
        console.error("Poll error:", err);
      }
    }, 1000);
 
    return () => {
      clearInterval(pollRef.current);
    };
  }, [phase]);
 
  const stopGame = async () => {
    clearInterval(pollRef.current);
    await fetch(`${API_BASE_URL}/api/scavenger/stop`, {
      method: "POST",
      credentials: "include",
    });
    stopVideoStream();
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
 
        {/* Video Feed */}
        {showVideo && (
          <div className="relative mb-4 rounded-xl overflow-hidden shadow-lg border-4 border-orange-400">
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className="w-96 h-72 object-cover"
            />
            <div className="absolute bottom-2 left-2 bg-black bg-opacity-50 text-white px-2 py-1 rounded text-sm">
              Point camera at objects!
            </div>
          </div>
        )}
 
        <div className={`text-6xl font-mono font-bold my-4 ${timerColor}`}>
          {timeLeft}s
        </div>
 
        <p className="text-gray-500 mb-4">
          Found {foundCount} / {targets.length} — point your webcam at objects!
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
          stopVideoStream();
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