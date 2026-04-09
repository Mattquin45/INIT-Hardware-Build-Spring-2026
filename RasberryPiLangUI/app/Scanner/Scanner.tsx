import './ScannerEffect.css'
import { useState, useEffect } from "react";

interface Scanning{
    active: boolean;
    onFinish?: (result: "SUCCESS" | "FAILURE") => void;
}

const Scanner: React.FC<Scanning> = ({active, onFinish}) => {
    const [status, setStatus] = useState< "IDLE" | "SCANNING" | "DONE" >("IDLE");
    const [result, setResult] = useState<"SUCCESS" | "FAILURE" | null>(null) 

    if (!active) return null;

    useEffect (() => {
        if(active){
            setStatus("IDLE");
        }
    }, [active]);

    useEffect(() => {
        if (status !== "SCANNING") return;

        const timer = setTimeout(() => {
            const result = Math.random() > 0.5 ? "SUCCESS" : "FAILURE";
            setResult(result);
            setStatus("DONE");
        }, 4000);

        return () => clearTimeout(timer);
    }, [status, onFinish])

    //Logic above is temporary until AI model is implemented.

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