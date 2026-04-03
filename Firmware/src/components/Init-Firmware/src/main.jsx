import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { Welcome } from "./welcome.tsx"
import Drop from "./Drop.jsx"
import { Home } from "./Home.jsx"
import './index.css'              

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <div style={{ position: "relative", }}>
      <Welcome />
      <Drop />
      <Home/>

    </div>
  </StrictMode>
)
