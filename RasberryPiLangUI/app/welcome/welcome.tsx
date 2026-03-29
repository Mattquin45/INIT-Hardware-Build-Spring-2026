import waveBottom from "./assets/WaveTileBottom.png"
import waveTop from "./assets/WaveTileTop.png"
import waves from "./assets/Waves.png"
import Scanner from "~/Scanner/Scanner";

export function Welcome() {
  return (
    <>
      <div>
        <Scanner active ={true}/>
      </div>

      <div 
        className = "fixed bottom-0 left-0 w-full h-[90px]"
        style={{
          backgroundImage: `url(${waveBottom})`, 
          backgroundRepeat: 'repeat-x',
          backgroundPosition: 'bottom',
          backgroundSize: 'contain'
        }}
      />
      <div 
        className = "fixed top-0 left-0 w-full h-[90px]"
        style={{
          backgroundImage: `url(${waveTop})`, 
          backgroundRepeat: 'repeat-x',
          backgroundPosition: 'bottom',
          backgroundSize: 'contain'
        }}
      />
      <div
      className = "grid h-screen w-full place-items-center"
      style = {{
        backgroundImage: `url(${waves})`,
        backgroundRepeat: `repeat`,
        backgroundPosition: 'bottom',
        backgroundSize: 'auto'
      }}
      />
    </>
  );
}
