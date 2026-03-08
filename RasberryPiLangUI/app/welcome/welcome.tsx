import waveBottom from "./WaveTileBottom.png";
import waveTop from "./WaveTileTop.png"

export function Welcome() {
  return (
    <>
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
    </>
  );
}
