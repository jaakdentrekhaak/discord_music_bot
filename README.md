# How to run on raspberry pi
1. ssh into raspberry pi with terminal
2. change directory to this project (after cloning from github)
3. activate the virtual environment: `source venv/bin/activate`
4. run the main.py file with nohup in background: `nohup ./main.py &`

To see the process running in the background, type in the terminal:
`ps ax | grep main.py`

Kill the process with the PID: `kill {PID}`