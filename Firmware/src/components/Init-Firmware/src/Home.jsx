// import camera from "./assets/Camera.png";
// import hotpotato from "./assets/HotPotato.png";
// import map from "./assets/Map.png";

// export default function Home() {
//   return (
//     <div className="flex flex-col items-center justify-center h-screen">

//       <h1 className="text-4xl font-bold mb-20 text-gray-700 -translate-y-16">
        
//       </h1>

//       <div className="flex gap-10 items-end">

//         <button
//           onClick={() => alert("APP numero uno Scan translate thing")}
//           className="
//             w-60 h-60 rounded-full
//             bg-gradient-to-br from-blue-200 to-blue-700
//             shadow-xl
//             float
//             flex flex-col items-center justify-center
//             hover:scale-110 hover:shadow-red-300 
//             transition duration-300
//           "
//         >
//           <img src={camera} className="w-32 h-32 mb-3" />
//           <span className="text-xl font-semibold text-gray-700">
//             Take a pic
//           </span>
//         </button>

//         <button
//           onClick={() => alert("APPPP NUMBER TWOOO 🥔")}
//           className="
//             w-60 h-60 rounded-full
//             bg-gradient-to-br from-blue-700 to-blue-200
//             shadow-xl
//             float
//             -translate-y-32
//             flex flex-col items-center justify-center
//             hover:scale-110 hover:shadow-red-300 
//             transition duration-300
//           "
//         >
//           <img src={hotpotato} className="w-32 h-32 mb-3" />
//           <span className="text-xl font-semibold text-gray-700">
//             Potato Caliente
//           </span>
//         </button>

//         <button
//           onClick={() => alert("THREEE scavenger hunt 🐣")}
//           className="
//             w-60 h-60 rounded-full
//             bg-gradient-to-br from-blue-100 to-blue-600
//             shadow-xl
//             float
//             flex flex-col items-center justify-center
//             hover:scale-110 hover:shadow-red-300 
//             transition duration-300
//           "
//         >
//           <img src={map} className="w-32 h-32 mb-3" />
//           <span className="text-xl font-semibold text-gray-700">
//             Dora's map
//           </span>
//         </button>

//       </div>
//     </div>
//   );
// }

// Home.jsx
import camera from "./assets/Camera.png";
import hotpotato from "./assets/HotPotato.png";
import map from "./assets/Map.png";
import { useState } from "react";

const API_BASE_URL = 'http://localhost:8000';

export default function Home() {
  const [isStarting, setIsStarting] = useState(false);
  const [error, setError] = useState(null);

  const startWebcamTester = async () => {
    setIsStarting(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/webcam/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include', // Important for session cookies
        body: JSON.stringify({
          conf_threshold: 0.35  // You can adjust this
        })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to start webcam');
      }
      
      const data = await response.json();
      console.log('Webcam started:', data);
      
      // Show success message
      alert(`Webcam tester started!\nLanguage: ${data.language_name}\nPress 'q' in the webcam window to quit.`);
      
    } catch (err) {
      console.error('Error starting webcam:', err);
      setError(err.message);
      alert(`Failed to start webcam: ${err.message}`);
    } finally {
      setIsStarting(false);
    }
  };

  const stopWebcamTester = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/webcam/stop`, {
        method: 'POST',
        credentials: 'include'
      });
      
      const data = await response.json();
      console.log('Webcam stopped:', data);
      
      if (data.success) {
        alert('Webcam tester stopped');
      }
    } catch (err) {
      console.error('Error stopping webcam:', err);
    }
  };

  const checkWebcamStatus = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/webcam/status`, {
        credentials: 'include'
      });
      const data = await response.json();
      console.log('Webcam status:', data);
      return data.running;
    } catch (err) {
      console.error('Error checking status:', err);
      return false;
    }
  };

  return (
    <div className="flex flex-col items-center justify-center h-screen">

      <h1 className="text-4xl font-bold mb-20 text-gray-700 -translate-y-16">
        INIT Hardware Build
      </h1>

      <div className="flex gap-10 items-end">

        <button
          onClick={startWebcamTester}
          disabled={isStarting}
          className={`
            w-60 h-60 rounded-full
            bg-gradient-to-br from-blue-200 to-blue-700
            shadow-xl
            float
            flex flex-col items-center justify-center
            hover:scale-110 hover:shadow-red-300 
            transition duration-300
            ${isStarting ? 'opacity-50 cursor-not-allowed' : ''}
          `}
        >
          <img src={camera} className="w-32 h-32 mb-3" />
          <span className="text-xl font-semibold text-gray-700">
            {isStarting ? 'Starting...' : 'Take a pic'}
          </span>
        </button>

        <button
          onClick={() => alert("APPPP NUMBER TWOOO 🥔")}
          className="
            w-60 h-60 rounded-full
            bg-gradient-to-br from-blue-700 to-blue-200
            shadow-xl
            float
            -translate-y-32
            flex flex-col items-center justify-center
            hover:scale-110 hover:shadow-red-300 
            transition duration-300
          "
        >
          <img src={hotpotato} className="w-32 h-32 mb-3" />
          <span className="text-xl font-semibold text-gray-700">
            Potato Caliente
          </span>
        </button>

        <button
          onClick={() => alert("THREEE scavenger hunt 🐣")}
          className="
            w-60 h-60 rounded-full
            bg-gradient-to-br from-blue-100 to-blue-600
            shadow-xl
            float
            flex flex-col items-center justify-center
            hover:scale-110 hover:shadow-red-300 
            transition duration-300
          "
        >
          <img src={map} className="w-32 h-32 mb-3" />
          <span className="text-xl font-semibold text-gray-700">
            Dora's map
          </span>
        </button>

      </div>
      
      {error && (
        <div className="mt-8 text-red-600 bg-red-100 p-3 rounded-lg">
          Error: {error}
        </div>
      )}
    </div>
  );
}