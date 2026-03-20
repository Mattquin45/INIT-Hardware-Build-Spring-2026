import React from "react";
import './ScannerEffect.css'
interface Scanning{
    active: boolean;
}
const Scanner: React.FC<Scanning> = ({active}) => {
    if (!active) return null;

    return(
        <div className = "scannerContainer">
            <div className = "viewFinder">
                <div className = "Corner BottomLeft"/>
                <div className = "Corner BottomRight"/>
                <div className = "Corner TopLeft"/>
                <div className = "Corner TopRight"/>

                <div className = "scanningLine"/>
            </div>
            <div className = "scannerLabel">
                <span className="pulsingDot"/>ANALYZING OBJECT...
            </div>
        </div>
    )
};
export default Scanner