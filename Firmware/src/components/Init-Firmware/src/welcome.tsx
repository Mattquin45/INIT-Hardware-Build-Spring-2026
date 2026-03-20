import waveBottom from "./assets/WaveTileBottom.png"
import waveTop from "./assets/WaveTileTop.png"
import waves from "./assets/Waves.png"

export function Welcome() {
  return (
    // ONE container that fills the screen
    <div
      style={{
        width: "100vw",
        height: "100vh",
        backgroundImage: `url(${waves})`,
        backgroundRepeat: "repeat",
        backgroundPosition: "center",
        backgroundSize: "auto",
        position: "relative"   // ✅ needed so fixed children work
      }}
    >

      {/* WAVE TOP - fixed to top of screen */}
      <div
        style={{
          position: "fixed",
          top: 0,
          left: 0,
          width: "100%",
          height: "90px",
          backgroundImage: `url(${waveTop})`,
          backgroundRepeat: "repeat-x",
          backgroundPosition: "top",
          backgroundSize: "contain",
          zIndex: 10            // ✅ makes sure it shows on top
        }}
      />

      {/* WAVE BOTTOM - fixed to bottom of screen */}
      <div
        style={{
          position: "fixed",
          bottom: 0,
          left: 0,
          width: "100%",
          height: "90px",
          backgroundImage: `url(${waveBottom})`,
          backgroundRepeat: "repeat-x",
          backgroundPosition: "bottom",
          backgroundSize: "contain",
          zIndex: 10            // ✅ makes sure it shows on top
        }}
      />

    </div>
  )
}