# How to step up project

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
Install all the requirements for the project to run
```bash
pip install opencv-python
```

For development for this project, ensure to install the dependencies
```bash
pip install -r requirements.txt
```