import {useState} from "react";
import "./index.css";

const languages = {
  en: "English",
  es: "Spanish",
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

function Drop({ onLanguageChange }) {
  const [targetLanguage, setTargetLanguage] = useState("en");
  const [open, setOpen] = useState(false);          // ← was missing
  const [settings, setSettings] = useState({        // ← was missing
    online: false,
  });

  const selectLanguage = (langId) => {
  setTargetLanguage(langId);
  onLanguageChange(langId);
};

  function toggleMenu() {
    setOpen(!open);
  }

  const toggleSetting = (langId) => {
    setSettings((prev) => ({ ...prev, [langId]: !prev[langId] }));
  };

  return (
    <div className="drop">
      <button onClick={toggleMenu} className="menu-button">⚙️</button>
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
        type="checkbox"
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

export default Drop;