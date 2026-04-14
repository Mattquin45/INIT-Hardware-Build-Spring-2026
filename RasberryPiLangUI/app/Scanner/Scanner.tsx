import './ScannerEffect.css'
import { useState, useEffect } from "react";

interface Scanning{
    active: boolean;
    onFinish?: (result: "SUCCESS" | "FAILURE") => void;
}

const Scanner: React.FC<Scanning> = ({active, onFinish}) => {
    const [status, setStatus] = useState< "IDLE" | "SCANNING" | "DONE" >("IDLE");
    const [result, setResult] = useState<"SUCCESS" | "FAILURE" | "null">("null");
    const [streamReady, setStreamReady] = useState(false);
    const [isTransitioning, setIsTransitioning] = useState(false); 

    const aiResult = async () => {
        try{
            const aiResponse = await fetch('http://127.0.0.1:8000/confidence');
            const aiData = await aiResponse.json();

            return aiData.confidence >= 0.55 ? "SUCCESS" : "FAILURE";
        } catch (error){
            console.error("AI failed");
            return "FAILURE";
        }
    }

    const beginCams = async () => {
        try{
            await fetch('http://127.0.0.1:8000/camUp', { method: 'POST' });
        }catch(error){
            console.error("Camera is not on");
        }
    }

    const endCams = async () => {
        try{
            await fetch('http://127.0.0.1:8000/camDown', { method: 'POST' }).catch(() => {});
        } catch(error){
            console.error("Camera is still on");
        }
    }

    const beginScan = async () => {
        const promise = aiResult();
        const delayResult = new Promise(resolve => setTimeout(resolve, 4000));

        const [result] = await Promise.all([promise, delayResult]);

        setResult(result);
        setStatus("DONE");
    }

    const backHandler = async () => {
        setIsTransitioning(true);
        setStreamReady(false);
        setResult("null");
        setStatus("IDLE");

        try{
            await endCams();
        } catch(e){
            console.error("Cleanup failed", e);
        }
        
        if (onFinish) onFinish("FAILURE");
    }

    useEffect (() => {
        if(active){
            setStatus("IDLE");
        }
    }, [active]);

    useEffect(() => {
        if (status !== "SCANNING") return;

        beginScan();

    }, [status, onFinish]);

    useEffect(() => {
        let isMounted = true;

        const autoStart = async () => {

            if(active){
                await beginCams();

                if (isMounted){
                    setTimeout(() => {
                        setStreamReady(true);
                    }, 1000);
                }
            } 
        };

        autoStart();
        
        return () => {
            endCams().then(() => {
                isMounted = false;
                setStreamReady(false);
                endCams();
            });
        };
    }, [active]);

    if (!active || isTransitioning){
        return null;
    }

    return(
        <div className = {`scannerContainer ${status === "DONE" ? `finished ${result?.toLowerCase()}` : ""}`}>
            <div className = "viewFinder">

                <div className = "Corner BottomLeft"/>
                <div className = "Corner BottomRight"/>
                <div className = "Corner TopLeft"/>
                <div className = "Corner TopRight"/>

                {status === "SCANNING" ? (
                    <div className = "scanningLine"/>
                ) : (
                    <div/>
                )}
                
            </div>
            
            {streamReady && (<img
                                src = "http://127.0.0.1:8000/camFeed"
                                alt = "Live Feed"
                                onError={(e) => console.log("Stream down: ", e)}
                                style={{
                                    position: 'absolute',
                                    top: 0,
                                    left: 0,
                                    width: '100%',
                                    height: '100%',
                                    objectFit: 'cover',
                                    zIndex: 49
                                }}
                            />)}
            <button className = "backButton" onClick={backHandler} disabled = {isTransitioning}> </button>
            <button className = "scannerButton" onClick={() => {setStatus("SCANNING");}} disabled = {isTransitioning}> </button>

            <div className = "scannerLabel">
                {status === "SCANNING" ? (
                    <>
                        <span className="pulsingDot"/>ANALYZING OBJECT...
                    </>
                ) : (
                    <>
                        {status === "IDLE" ? (
                            <>
                                <span className="pulsingDot"/>WAITING FOR INPUT...
                            </>
                        ) : (
                            <>
                                <span className="pulsingDot"/>ANALYSIS COMPLETE...
                            </>
                        )}
                    </>
                )}
                
            </div>
        </div>
    )
};
export default Scanner