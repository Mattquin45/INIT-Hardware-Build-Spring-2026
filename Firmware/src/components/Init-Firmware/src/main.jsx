import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { Welcome } from "./welcome.tsx"
import Drop from "./Drop.jsx"
import  Home  from "./Home.jsx"
import './index.css'              

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <div style={{ position: "relative", width: "100vw", height: "100vh" }}>
      
      {/* Background layer */}
      <Welcome />
      
      {/* Home sits on top of Welcome */}
      <div style={{
        position: "absolute",
        top: 0,
        left: 0,
        width: "100%",
        height: "100%",
        zIndex: 5          // above Welcome (z:0) but below Drop/waves (z:10)
      }}>
        <Home />
      </div>

      {/* Drop floats above everything */}
      <Drop />

    </div>
  </StrictMode>
)
