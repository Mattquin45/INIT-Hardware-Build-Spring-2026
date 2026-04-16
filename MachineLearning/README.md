# How to step up project

In the terminal, make sure you are in the Machine Learning Folder:

```bash 
cd /Documents/Github/INIT-Hardware-Build-Spring-2026/MachineLearning
``` 

Using a virtual environment:

In the command line, run the following commands:

```bash
python -m venv venv (you may need to use python3 instead if you are using python3)
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