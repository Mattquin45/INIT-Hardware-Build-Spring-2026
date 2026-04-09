import { resolve } from 'path';
import './ScannerEffect.css'
import { useState, useEffect } from "react";

interface Scanning{
    active: boolean;
    onFinish?: (result: "SUCCESS" | "FAILURE") => void;
}

const Scanner: React.FC<Scanning> = ({active, onFinish}) => {
    const [status, setStatus] = useState< "IDLE" | "SCANNING" | "DONE" >("IDLE");
    const [result, setResult] = useState<"SUCCESS" | "FAILURE" | "null" >("null") 

    if (!active) return null;

    const aiResult = async () => {
        try{
            const aiResponse = await fetch('http://http://127.0.0.1:8000/confidence');
            const aiData = await aiResponse.json();

            return aiData.confidence >= 0.55 ? "SUCCESS" : "FAILURE";
        } catch (error){
            console.error("AI failed");
            return "null";
        }
    }

    const beginScan = async () => {
        const promise = aiResult();
        const delayResult = new Promise(resolve => setTimeout(resolve, 4000));

        const [result] = await Promise.all([promise, delayResult]);

        setResult(result);
        setStatus("DONE");
    }

    useEffect (() => {
        if(active){
            setStatus("IDLE");
        }
    }, [active]);

    useEffect(() => {
        if (status !== "SCANNING") return;

        beginScan();

    }, [status, onFinish])

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

            <button className = "scannerButton" onClick={() => {setStatus("SCANNING");}}> </button>

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