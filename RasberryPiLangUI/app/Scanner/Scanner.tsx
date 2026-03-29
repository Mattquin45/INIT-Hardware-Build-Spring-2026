import './ScannerEffect.css'
import { useState, useEffect } from "react";

interface Scanning{
    active: boolean;
    onFinish?: (result: "SUCCESS" | "FAILURE") => void;
}
const Scanner: React.FC<Scanning> = ({active, onFinish}) => {
    const [progress, setProgress] = useState(0);
    const [status, setStatus] = useState< "IDLE" | "SCANNING" | "DONE" >("IDLE");
    const [result, setResult] = useState<"SUCCESS" | "FAILURE" | null>(null) 

    if (!active) return null;

    useEffect (() => {
        if(active){
            setStatus("SCANNING");
            setProgress(0);
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
                    <div className = "result"/>
                )}
                
            </div>

            <button className = "scannerButton"/>

            <div className = "scannerLabel">
                {status === "SCANNING" ? (
                    <>
                        <span className="pulsingDot"/>ANALYZING OBJECT...
                    </>
                ) : (
                    <>
                        <span className="pulsingDot"/>ANALYSIS COMPLETE...
                    </>
                )}
                
            </div>
        </div>
    )
};
export default Scanner