import {useState} from "react";
import "./index.css";

const languages = {
  en: "English",
    sp: "Spanish",
    ja: "Japanese",
    fr: "French",
    zh: "Chinese",
    ko: "Korean",
    it: "Italian",
    de: "German",
    el: "Greek",
    ru: "Russian",
    ar: "Arabic",
    ur: "Urdu",
    hi: "Hindi",
    ht: "Haitian Creole",
    pt: "Portuguese",
    ro: "Romanian",
    fa: "Persian",
};

function Drop() {
    
    const [targetLanguage, setTargetLanguage] = useState("en"); // default to English

    const selectLanguage = (langId) => {
     setTargetLanguage(langId); 
    };

    const[open, setOpen] = useState(false);
    const [settings, setSettings] = useState({
    online: false,
    en: false,
    sp: false,
  });

    function toggleMenu(){
        setOpen(!open);
    }
    const toggleSetting = (langId) => {
    setSettings((prev) => ({ ...prev, [langId]: !prev[langId] }));
  };


    return(
        <div className = "drop">
            <button onClick = {toggleMenu} className = "menu-button">
                ⚙️
            </button>

            <nav>
                <ul className={`dropdown ${open ? "active" : ""}`}>
                        <li className="setting-item">
                        <label className="switch">
                            <input 
                                type="checkbox"
                                checked={settings.online}
                                onChange={() => toggleSetting("online")}
                            />
                            <span className="slider"></span>
                        </label>
                        <span>{settings.online ? "Online" : "Offline"}</span>
                    </li>
                    {Object.entries(languages).map(([id, name]) => (
                    <li key={id} className="setting-item">
                        <label className="switch">
                        <input
                            type="radio"
                            name="language"
                            checked={targetLanguage === id}
                            onChange={() => selectLanguage(id)}
                        />
                        <span className="slider"></span>
                        </label>
                        <span>{name}</span>
                    </li>
                ))}
                     
                </ul>
            </nav>
            
        </div>
    );
}

export default Drop