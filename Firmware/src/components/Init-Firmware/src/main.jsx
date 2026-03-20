import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { Welcome } from "./welcome.tsx"
import Drop from "./Drop.jsx"
import './index.css'              

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <div style={{ position: "relative", }}>
      <Welcome />
      <Drop />
    </div>
  </StrictMode>
)
