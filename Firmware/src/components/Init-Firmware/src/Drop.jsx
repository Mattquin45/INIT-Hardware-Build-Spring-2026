import {useState, useEffect} from "react";
import "./index.css";

const languages = {
  en: "English",
    es: "Spanish",
    // ja: "Japanese",
    fr: "French",
    // zh: "Chinese",
    // ko: "Korean",
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

// Change to work 
const API_BASE_URL = 'http://localhost:8000';

function Drop() {
    
//     const [targetLanguage, setTargetLanguage] = useState("en"); // default to English

//     const selectLanguage = (langId) => {
//      setTargetLanguage(langId); 
//     };

//     const[open, setOpen] = useState(false);
//     const [settings, setSettings] = useState({
//     online: false,
//     en: false,
//     es: false,
//   });

//     function toggleMenu(){
//         setOpen(!open);
//     }
//     const toggleSetting = (langId) => {
//     setSettings((prev) => ({ ...prev, [langId]: !prev[langId] }));
//   };

    const [targetLanguage, setTargetLanguage] = useState("en");
    const [open, setOpen] = useState(false);
    const [settings, setSettings] = useState({
      online: false,
      en: false,
      es: false,
    });
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);

    // Fetch current language and settings on component mount
    useEffect(() => {
      const fetchLanguageSettings = async () => {
        try {
          console.log('Fetching language settings from FastAPI...');
          const response = await fetch(`${API_BASE_URL}/api/language`, {
            credentials: 'include', // Important for cookies
          });
          
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          
          const data = await response.json();
          console.log('Received language data:', data);
          
          if (data.currentLanguage) {
            setTargetLanguage(data.currentLanguage);
          }
          if (data.settings) {
            setSettings(data.settings);
          }
        } catch (err) {
          console.error('Failed to fetch language settings:', err);
          setError('Could not connect to FastAPI server. Make sure it\'s running on port 8000');
        }
      };
      
      fetchLanguageSettings();
    }, []);

    const selectLanguage = async (langId) => {
      const previousLanguage = targetLanguage;
      setTargetLanguage(langId);
      setError(null);
      setIsLoading(true);
      
      try {
        const response = await fetch(`${API_BASE_URL}/api/language`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
          body: JSON.stringify({
            targetLanguage: langId,
            settings: settings
          }),
        });
        
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Language updated successfully:', data);
        
        // You can add a success indicator here
        // showToast(`Language changed to ${data.languageName}`, 'success');
        
      } catch (err) {
        console.error('Error updating language:', err);
        setError(err.message || 'Failed to update language. Please try again.');
        // Revert the language selection on error
        setTargetLanguage(previousLanguage);
      } finally {
        setIsLoading(false);
        // Auto-clear error after 3 seconds
        setTimeout(() => setError(null), 3000);
      }
    };

    function toggleMenu() {
      setOpen(!open);
    }

    const toggleSetting = async (langId) => {
      const newSettings = { ...settings, [langId]: !settings[langId] };
      setSettings(newSettings);
      
      // Update settings via API
      try {
        await fetch(`${API_BASE_URL}/api/settings`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
          body: JSON.stringify({ settings: newSettings }),
        });
      } catch (err) {
        console.error('Error updating settings:', err);
      }
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