import {useState} from "react";
import "./Drop.css";
function Drop(){

    const[open, setOpen] = useState(false);
    const [enabled, setEnabled] = useState(false);

    function toggleMenu(){
        setOpen(!open);
    }
    function toggleSetting(){
        setEnabled(!enabled);
    }

    return(
        <div className = "drop">
            <button onClick = {toggleMenu} className = "menu-button">
                ⚙️
            </button>

            <nav>
                <ul className = {`dropdown ${open ? "active" : ""}`}>
                    <li className = "setting-item">
                        <label className = "switch">
                            <input 
                                type="checkbox"
                                checked = {enabled}
                                onChange = {toggleSetting}
                            />
                            <span className = "slider"></span>
                        </label>
                        <span>blank 1</span>
                    </li>
                    <li>blank 2</li>
                    <li>blank 3</li>
                </ul>
            </nav>
            
        </div>
    );
}

export default Drop