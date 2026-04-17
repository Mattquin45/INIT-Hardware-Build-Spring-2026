import camera from "./assets/Camera.png";
import hotpotato from "./assets/HotPotato.png";
import map from "./assets/Map.png";
import { useState, useEffect } from "react";
import Drop from "./Drop";

useEffect(() => {
  const startScan = async () => {
    try {
      await fetch(`http://localhost:8000/start-scan?lang=${language}`);
    } catch (err) {
      console.log("Server error");
    }
  };

  startScan();
}, [language]); 


export default function Home() {
  //Use state change is hardcoded language change
   const [language, setLanguage] = useState("es");

  const handleScan = async () => {
    try {
      await fetch(`http://localhost:8000/start-scan?lang=${language}`);
    } catch (err) {
      alert("Could not reach the ML server. Is uvicorn running?");
    }
  };
  return (
    <div className="flex flex-col items-center justify-center h-screen">
      <Drop onLanguageChange={setLanguage} />

      <h1 className="text-4xl font-bold mb-20 text-gray-700 -translate-y-16">
        
      </h1>

      <div className="flex gap-10 items-end">

        <button
          onClick={handleScan}
          className="
            w-60 h-60 rounded-full
            bg-gradient-to-br from-blue-200 to-blue-700
            shadow-xl
            float
            flex flex-col items-center justify-center
            hover:scale-110 hover:shadow-red-300 
            transition duration-300
          "
        >
          <img src={camera} className="w-32 h-32 mb-3" />
          <span className="text-xl font-semibold text-gray-700">
            Take a pic
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
    </div>
  );
}