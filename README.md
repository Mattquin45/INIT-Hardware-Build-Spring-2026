# INIT-Hardware-Build-Spring-2026
INIT Build project about allowing learning languages be more interactive and efficient.

# How to step up project

In the terminal, make sure you are in the Machine Learning Folder:

```bash 
cd /Documents/Github/INIT-Hardware-Build-Spring-2026/MachineLearning
``` 

Using a virtual environment:

In the command line, run the following commands:

```bash
python3 -m venv venv 
```
If you have a Mac/Linus System you run this command to create your virtual environment
```bash
source venv/bin/activate 
```

If you have a Windows System you run this command to create your virtual environment
```bash
.\venv\Scripts\activate
```

For development for this project, ensure to install the dependencies
```bash
pip install -r requirements.txt
```

How to run the server
```bash
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

# Different approach for creating a virtual environment using conda

For creating a conda virtual environment
```bash
conda create -n init_project python=3.11 -y

conda activate init_project

pip install opencv-python ultralytics numpy google-cloud-translate fastapi uvicorn
```

to deactivate this virtual environment
```bash
conda  deactivate 
```

In another terminal for running the firmware, run the following commands
```bash
cd INIT-Hardware-Build-Spring-2026/Firmware/src/components/Init-Firmware
npm install
npm run dev
```

