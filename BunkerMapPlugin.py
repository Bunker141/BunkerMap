from phBot import *
from time import sleep
import threading
from threading import Timer
import QtBind
import os
import struct
import signal
import urllib.request
import urllib.parse
import json

name = 'BunkerMap'
version = '1.0'

Online = False
Username = ""
EnableCommands = False

UpdateDelay = 2000
DelayCounter = 0
		
PreviousData = None		


def joined_game():
	global Online
	Online = "Joined"

	
def teleported():
	global Online, Username
	CharData = get_character_data()
	if Online == "Joined":
		Online = True
		Username = f"{CharData['name']}_{CharData['server']}"
		SendData()


def HandleResponse(jsonresponse):
	print(jsonresponse)
	global EnableCommands
	EnableCommands = jsonresponse["EnableCommands"]
	if not EnableCommands:
		return
	Commands = jsonresponse["Commands"]
	for command in Commands:
		if command.lower() == "start":
			start_bot()
			log(f"[{name}] Starting Bot")
			
		if command.lower() == "stop":
			stop_bot()
			log(f"[{name}] Stopping Bot")
			
		if command.lower().startswith("starttrace"):
			Player = command.split(":")[1]
			if start_trace(Player):
				log(f"[{name}] Starting to Trace [{Player}]")
				
		if command.lower() == "stoptrace":
			if stop_trace():
				log(f"[{name}] Stopping Trace")
				
		if command.lower().startswith("setprofile"):
			Profile = command.split(":")[1]
			if set_profile(Profile):
				log(f"[{name}] Setting Profile to [{Profile}]")
				
		if command.lower() == "usereturnscroll":
			use_return_scroll()
			log(f"[{name}] Using a Return Scroll")
			
		if command.lower() == "goclientless":
			GoClientless()
			log(f"[{name}] Closing the Client")
			
		if command.lower() == "closebot":
			Terminate()

		if command.lower().startswith("setposition"):
			Cords = command.split(":")[1].split(",")
			Region = int(Cords[2])
			if set_training_position(int(Cords[2]),float(Cords[0]),float(Cords[1]),0):
				log(f"[{name}] Setting Postion to [{Cords[0]},{Cords[1]}]")	

		if command.lower().startswith("moveto"):
			Cords = command.split(":")[1].split(",")
			if move_to_region(int(Cords[3]),float(Cords[0]),float(Cords[1]),float(Cords[2])):
				log(f"[{name}] Moving to Postion [{Cords[0]},{Cords[1]}]")				

def GoClientless():
	pid = get_client()['pid']
	if pid:
		os.kill(pid, signal.SIGTERM)
	log('Plugin: Client is not open!')
	
def Terminate():
	global Online
	Online = False
	SendData()
	log("Plugin: Closing bot...")
	os.kill(os.getpid(),9)
	
def CheckOnline():
	global Online, Username
	CharData = get_character_data()
	if CharData['name']:
		Online = True
		Username = f"{CharData['name']}_{CharData['server']}"
	
def disconnected():
	global Online
	Online = False
	SendData()

PreviousData = None
def SendData():
	global PreviousData
	if Username == None or Username == "":
		return
		
	CharData = get_character_data()
	CharData.update({"z": get_position()['z'], "online": Online, "status": get_status()})
	#log(CharData)
	if CharData == PreviousData and not EnableCommands:
		return
	data = {Username: CharData}
	
	if CharData == PreviousData and EnableCommands:
		data = {Username: {"Ping": True}}
	PreviousData = CharData
	try:
		data = json.dumps(data).encode()
		req = urllib.request.Request("http://127.0.0.1:8888",data=data,headers={'content-type':'application/json'})
		with urllib.request.urlopen(req) as f:
			response = f.read().decode()
			jsonresponse = json.loads(response)
			HandleResponse(jsonresponse)
			return
	except Exception as ex:
		#log(str(ex))
		pass


def event_loop():
	global DelayCounter
	DelayCounter += 500
	if DelayCounter >= UpdateDelay and Online:
		DelayCounter = 0
		SendData()
		
		
log('Plugin: [%s] Version %s Loaded' % (name,version))
CheckOnline()