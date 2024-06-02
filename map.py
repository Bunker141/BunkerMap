import PySimpleGUI as sg
from PIL import Image
import PIL
import io
import base64
import os
import sys
import asyncio
import math
from threading import Timer
from threading import Thread
import time
import queue
from flask import Flask
from flask import request
import json
import configparser
import urllib.request

config = configparser.ConfigParser()
if not os.path.exists("BunkerMap.ini"):
	config.add_section('Settings')
	config['Settings']['BotPath'] = ""
	config['Settings']['Theme'] = "DarkGray4"
	config['Settings']['enable_commands'] = "True"
	with open("BunkerMap.ini", 'w') as f:
		config.write(f)

config.read('BunkerMap.ini')	

#each minimap is 192 x 192 in game cords
#0,0 in game is on tile 135x92
graph = None
window = None
ZoomThread = None
ImageThread = None

ImageWidth = 50
CanvasSize = 700,600
Ratio = (ImageWidth/10) / 2
GraphDims = CanvasSize[0]/2.5, CanvasSize[1]/2.5
GlobalCenter = GraphDims[0] / 2, GraphDims[1] / 2
GlobalZero = 0,0
ImageSize = 20
Padding = 200
PointSize = 3.5
TextSize = 15

#dont change
XOffset = 2700 
YOffset = 1820

ImageData = {}

ZoomLevel = 1
FocusArea = "World"

LoadedImages = []
LoadedScripts = []
LineIDs = []

BotPath = config.get("Settings","BotPath")

IconPath = b"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"

Towns = {"Jangan": (6430,1035), "Donwhang": (3545,2110), "Hotan": (105,48), "Samarkand": (-5185,2880), "Constantinople": (-10685,2575), "Alexandria (North)": (-16155,67), "Alexandria (South)": (-16645,-278), "Baghdad": (-8535,-730)}
Areas = {"Bandit Camp": (4875,-40), "Tarim Basin": (2590,-20), "Karakoram": (-1400,-265), "Taklamakan": (-500,2000), "Mountain Roc": (-4400,-175), "Central Asia": (-4100,2500), "Asia Minor": (-6900,2100), "Eastern Europe": (-11900,2800), "Storm and Cloud Desert": (-12365,-1335), "King's Valley": (-13235,-3285), "Kirk Field": (-9292,-775), "Phantom Desert": (-10355,-2820), "Flaming Tree": (-8840,-2340), "Sky Temple": (17365,-100), "Mirror Dimension": (12875,-40), "Forgotten World": (19475,3570), "Stryia Arena": (20540,6325)}
Caves = {"Donwhang Dungeon B1": -32767, "Donwhang Dungeon B2": -32767, "Donwhang Dungeon B3": -32767, "Donwhang Dungeon B4": -32767, "Qin-Shi Tomb B1": -32761, "Qin-Shi Tomb B2": -32762, "Qin-Shi Tomb B3": -32763, "Qin-Shi Tomb B4": -32764, "Qin-Shi Tomb B5": -32765, "Qin-Shi Tomb B6": -32766, "Job Temple": -32752, "Flame Mountain": -32750, "Cave of Meditation": -1, }
Characters = {}
CommandsToSend = {}

SelectedUsername = ""

def SettingsPopup():
	sg.theme(config.get("Settings","Theme"))
	SettingCol = sg.Column([
	[sg.Text('Bot Path')],
	[sg.Text('Theme')],
	[sg.Text('Enable Commands')],
	])

	SettingCol2 = sg.Column([
	[sg.Input(config.get("Settings","BotPath"), k='botpath')],
	[sg.Combo(values=(sg.theme_list()), default_value=config.get("Settings","Theme"), readonly=True, k='theme')],
	[sg.Checkbox('Enable Bot Commands', default= True if config.get("Settings","enable_commands") == "True" else False, k='enable_commands', tooltip="enables communication to bots, may increase useage")],
	])


	SettingCol3 = sg.Column([
	[sg.Button("...", key="Botpath", enable_events=True,s=(2,1))],
	[sg.Text('')],
	[sg.Text('')],
	])


	layout = [[SettingCol, SettingCol2 , SettingCol3],[sg.Button("Save", key="setting-save", enable_events=True), sg.Button("Cancel", key="setting-cancel", enable_events=True)]]

	win = sg.Window("Settings", layout, modal=True, grab_anywhere=True, enable_close_attempted_event=True, icon=IconPath)

	event, values = win.read()
	win.close()
	window.write_event_value(event, values)


def UpdateCharacterData(data):
	global Characters
	for key, values in data.items():
		if key not in Characters:
			Characters.update(data)
			return
		for value in values:
			Characters[key][value] = data[key][value]


def CharInList(character):
	for char in Chars:
		if char['character'] == character:
			return True
	return False

def SetZoom(Type):
	global ImageWidth, GraphDims, Padding, LoadedImages, GlobalCenter, PointSize, TextSize, Ratio, ZoomThread
	ZoomThread = None
	PreviousDims = GraphDims
	ClearMap()
	if ZoomLevel == 1:
		ImageWidth = 50
		Padding = 200
		PointSize = 3.5
		TextSize = 15
	if ZoomLevel == 2:
		ImageWidth = 100
		Padding = 200
		PointSize = 1.5
		TextSize = 15
	if ZoomLevel == 3:
		ImageWidth = 200
		Padding = 200   
		PointSize = .75
		TextSize = 12
	if ZoomLevel == 4: 
		ImageWidth = 300
		Padding = 100  
		PointSize = .5
		TextSize = 10
	if ZoomLevel == 5: 
		ImageWidth = 500
		Padding = 50   
		PointSize = .35
		TextSize = 10
	if ZoomLevel == 6:  
		ImageWidth = 1000
		Padding = 40
		PointSize = .2
		TextSize = 10
	Ratio = (ImageWidth/10) / 2
	GraphDims = CanvasSize[0]/Ratio, CanvasSize[1]/Ratio
	graph.change_coordinates(graph_bottom_left=(0,0), graph_top_right=(GraphDims))
	if Type == "IN":
		GlobalCenter = GlobalCenter[0] - ((PreviousDims[0] - GraphDims[0]) / 2), GlobalCenter[1] - ((PreviousDims[1] - GraphDims[1]) / 2)
	if Type == "OUT":
		GlobalCenter = GlobalCenter[0] + (abs((PreviousDims[0] - GraphDims[0]) / 2)), GlobalCenter[1] + (abs((PreviousDims[1] - GraphDims[1]) / 2))
	Timer(0.1, AddImages, ()).start()
	LoadAllChars()
	for script in LoadedScripts:
		DrawScript(script)
	
def convert_to_bytes(file_or_bytes, resize=None):
	if isinstance(file_or_bytes, str):
		img = PIL.Image.open(file_or_bytes)
	else:
		img = PIL.Image.open(io.BytesIO(base64.b64decode(file_or_bytes)))

	cur_width, cur_height = img.size
	if resize:
		new_width, new_height = resize
		scale = min(new_height/cur_height, new_width/cur_width)
		img = img.resize((int(cur_width*scale), int(cur_height*scale)), PIL.Image.LANCZOS)
	bio = io.BytesIO()
	img.save(bio, format="PNG")
	del img
	return bio.getvalue()

def GetImageLocation(filename):
	filename = filename.split('.')[0]
	cords = filename.split('x')
	x = int(cords[0]) * ImageSize
	y = int(cords[1]) * ImageSize
	return (x - XOffset) - GlobalZero[0], (y - YOffset) - GlobalZero[1]
	
def AddImages():
	global LoadedImages, ImageCount
	if FocusArea == "World":
		folder = BotPath + f"/minimap"
	else:
		folder = BotPath + f"/minimap/d"
	Loaded = []
	ToBeLoaded = []
	ToBeDeleted = []
	files = GetCurrentImages()
	for Image in LoadedImages:
		Img = Image.split(',')[1]
		Loaded.append(Img)
		if Img not in files:
			ToBeDeleted.append(Image)
	for Image in files:
		if Image not in Loaded:
			ToBeLoaded.append(Image)
			
	for DelImage in ToBeDeleted:
		if DelImage in LoadedImages:
			LoadedImages.remove(DelImage)
			graph.delete_figure(DelImage.split(',')[0])
			try:
				window['-GRAPH-'].Images.pop(int(DelImage.split(',')[0]))
			except Exception as ex:
				print(f"error deleting image from memory {ex}")
			#print(f"deleting [{DelImage.split(',')[0]}] [{DelImage}]")

	num_files = len(ToBeLoaded)
	for slot, image in enumerate(ToBeLoaded):
		try:
			Timer(0.0, AddImage, [ToBeLoaded[slot],folder]).start()
		except Exception as ex:
			print(f'error loading images1 {ex}')
	CheckLoadedImages()   
	#print(LoadedImages)  
	print(f"Loaded Images {len(LoadedImages)}")
	print("======================")
	
	
def AddImage(Image, folder):
	global LoadedImages, ImageCount
	location = GetImageLocation(Image)
	if FocusArea == "World":
		file_to_display = os.path.join(folder, Image)
	else:
		file_to_display = os.path.join(folder, f"{GetCaveFilename()}{Image}")
	if os.path.isfile(file_to_display):
		img_data = convert_to_bytes(file_to_display,resize=(ImageWidth,ImageWidth))
		ID = graph.draw_image(data=img_data, location=(location))
		LoadedImages.append(f"{ID},{Image},{ZoomLevel}")
		try:
			graph.send_figure_to_back(ID)
		except Exception as ex:
			print(f"[{ID}] has error [{ex}]")
			pass

def GetCaveFilename():
	if FocusArea == "Donwhang Dungeon B1":
		return "dh_a01_floor01_"
	if FocusArea == "Donwhang Dungeon B2":
		return "dh_a01_floor02_"
	if FocusArea == "Donwhang Dungeon B3":
		return "dh_a01_floor03_" 
	if FocusArea == "Donwhang Dungeon B4":
		return "dh_a01_floor04_"
		
	if FocusArea == "Qin-Shi Tomb B1":
		return "qt_a01_floor01_"		
	if FocusArea == "Qin-Shi Tomb B2":
		return "qt_a01_floor02_"		
	if FocusArea == "Qin-Shi Tomb B3":
		return "qt_a01_floor03_"		
	if FocusArea == "Qin-Shi Tomb B4":
		return "qt_a01_floor04_"	   
	if FocusArea == "Qin-Shi Tomb B5":
		return "qt_a01_floor05_"	   
	if FocusArea == "Qin-Shi Tomb B6":
		return "qt_a01_floor06_"	  
		
	if FocusArea == "Job Temple":
		return "rn_sd_egypt1_01_"  
		
	if FocusArea == "Flame Mountain":
		return "flame_dungeon01_"	   
		
	if FocusArea == "Cave of Meditation":
		return "fort_dungeon01_"

		
def GetCurrentImages():
	Images = []
	Buffer = (GraphDims[0] / 2) + Padding
	TopLimit = (GlobalCenter[1]) + Buffer
	BottomLimit = GlobalCenter[1] - Buffer
	RightLimit = (GlobalCenter[0]) + Buffer
	LeftLimit = GlobalCenter[0] - Buffer
	
	TopRow = round((TopLimit + YOffset) / ImageSize)
	BottomRow = round((BottomLimit + YOffset) / ImageSize)
	RightRow = round((RightLimit + XOffset) / ImageSize)
	LeftRow = round((LeftLimit + XOffset) / ImageSize)
	XDist = abs(LeftRow - RightRow)
	YDist = abs(BottomRow - TopRow)
	for y in range(YDist):
		for x in range(XDist):
			Images.append(f"{LeftRow+x}x{BottomRow+y}.jpg")
	return Images

#in game x,y
def AddCharacterToMap(Username):
	window["-CHARCOMBO-"].update(values=GetChars())
	global Characters
	CharInfo = Characters[Username]
	try:
		graph.delete_figure(CharInfo['PointID'])
		graph.delete_figure(CharInfo['TextID'])
	except Exception as ex:
		pass
	
	if not CharInfo['online']:
		return
	
	AddPoint = False
	TextID = 0
	PointX = (CharInfo['x'] / (192/ImageSize)) - GlobalZero[0]
	PointY = (CharInfo['y'] / (192/ImageSize)) - GlobalZero[1]
	region = CharInfo['region']
	z = CharInfo['z']
	if region > 0 and FocusArea == "World":
		AddPoint = True
		
	if FocusArea == "Donwhang Dungeon B1":
		if z < 25:
			AddPoint = True
	if FocusArea == "Donwhang Dungeon B2":
		if z > 25 and z < 150:
			AddPoint = True			   
	if FocusArea == "Donwhang Dungeon B3":
		if z > 150 and z < 300:
			AddPoint = True   
	if FocusArea == "Donwhang Dungeon B4":
		if z > 300:
			AddPoint = True   
	#dont add DW cave because Z matters there, region is all the same for all levels
	if region == GetRegionFromName(FocusArea) and region != GetRegionFromName('Donwhang Dungeon B1'):	 
		AddPoint = True
	
	if "PointID" not in CharInfo or "TextID" not in CharInfo:
		data = {Username: {"PointID": 0, "TextID": 0}}
		UpdateCharacterData(data)
	
	if AddPoint:
		if CharInfo['dead']:
			fill_color = "red"
		else:
			fill_color = "teal"
		print(f"Adding Point [{PointX}][{PointY}]")
		ID = graph.draw_circle((PointX,PointY),PointSize,fill_color = fill_color,line_color = "black",line_width = 4)
		if ZoomLevel >= 3:
			TextID = graph.draw_text(CharInfo['name'],(PointX,PointY-2/ZoomLevel),color = "white",font = ("Impact", TextSize),angle = 0,text_location = "center")	
		data = {Username: {"PointID": ID, "TextID": TextID}}
		UpdateCharacterData(data)
		
def GetNameFromRegion(Region):
	for cave in Caves:
		if Caves[cave] == Region:
			return cave
			
def GetRegionFromName(Name):
	for cave in Caves:
		if cave == Name:
			return Caves[cave]
			

#in game x,y  
def ZoomTo(x, y, z=0, region=0):
	global GlobalZero, GlobalCenter, FocusArea, XOffset, YOffset
	ClearMap()
	XOffset = 2700 
	YOffset = 1820
	PointX = (x / 9.6) - GlobalZero[0]
	PointY = (y / 9.6) - GlobalZero[1]

	MoveX = PointX - (GraphDims[0]/2)
	MoveY = PointY - (GraphDims[1]/2)
	FocusArea = "World"
	if region < 0:
		FocusArea = GetNameFromRegion(region)
		XOffset = 5100
		YOffset = 2540
		if FocusArea.startswith('Donwhang'):
			if z < 25:
				FocusArea = "Donwhang Dungeon B1"
			if z > 25 and z < 150:
				FocusArea = "Donwhang Dungeon B2"		  
			if z > 150 and z < 300:
				FocusArea = "Donwhang Dungeon B3"
			if z > 300:
				FocusArea = "Donwhang Dungeon B4"

	print((f"MOVE Distance {MoveX},{MoveY}"))
	count = 0
	#fix for move API, using total in API isnt always accuurate.. moving larger than it should
	for i in range(int(abs(MoveX))):
		if MoveX > 0:
			GlobalCenter = GlobalCenter[0] + 1, GlobalCenter[1] - 0
			GlobalZero = GlobalZero[0] + 1, GlobalZero[1] - 0
			graph.move(1, 0)
		else:
			GlobalCenter = GlobalCenter[0] - 1, GlobalCenter[1] - 0
			GlobalZero = GlobalZero[0] - 1, GlobalZero[1] - 0
			graph.move(-1, 0)
	
	for i in range(int(abs(MoveY))):
		if MoveY > 0:
			GlobalCenter = GlobalCenter[0] - 0, GlobalCenter[1] + 1
			GlobalZero = GlobalZero[0] - 0, GlobalZero[1] + 1
			graph.move(0, 1)
		else:
			GlobalCenter = GlobalCenter[0] - 0, GlobalCenter[1] - 1
			GlobalZero = GlobalZero[0] - 0, GlobalZero[1] - 1
			graph.move(0, -1)
	Timer(0.1, AddImages, ()).start()
	LoadAllChars()
	for script in LoadedScripts:
		DrawScript(script)

def ClearMap():
	global LoadedImages
	LoadedImages = []
	graph.erase()
	window['-GRAPH-'].Images = {}
	
def Terminate():
	os.kill(os.getpid(),9)  

def GetTowns():
	towns = []
	for town in Towns:
		towns.append(town)
	return towns
  
def GetAreas():
	areas = []
	for area in Areas:
		areas.append(area)
	return areas
	
def GetCaves():
	caves = []
	for cave in Caves:
		caves.append(cave)
	return caves
	
def GetChars():
	chars = []
	for key, char in Characters.items():
		chars.append(key)
	return chars   

def GetCharsCords(Username):
	for key, char in Characters.items():
		if key == Username:
			return char['x'], char['y'], char['z'], char['region']
 
#redundancy 
def CheckLoadedImages():
	global LoadedImages
	for image in LoadedImages:
		Zoom = int(image.split(',')[2])
		ID = int(image.split(',')[0])
		if Zoom != ZoomLevel:
			LoadedImages.remove(image)
			graph.delete_figure(ZoomLevel)
 
def LoadAllChars():
	Chars = GetChars()
	for char in Chars:
		AddCharacterToMap(char)

def GetCharFromFigureId(ID):
	for key, char in Characters.items():
		if char['PointID'] == ID:
			return key

		
def DrawScript(ScriptFile):
	global LineIDs
	Lines = []
	if os.path.exists(ScriptFile):
		with open(ScriptFile,"r") as f:
			rawlines = f.readlines()
			for line in rawlines:
				if line.startswith("walk"):
					Lines.append(line.strip("\n"))
			try:	
				for index, line in enumerate(Lines):
					if index == (len(Lines) - 1):
						break
					if line.startswith("walk"):
						startpoint = Lines[index].split(",")
						endpoint = Lines[index+1].split(",")
						StartPointX = (float(startpoint[1]) / (192/ImageSize)) - GlobalZero[0]
						StartPointY = (float(startpoint[2]) / (192/ImageSize)) - GlobalZero[1]
						
						EndPointX = (float(endpoint[1]) / (192/ImageSize)) - GlobalZero[0]
						EndPointY = (float(endpoint[2]) / (192/ImageSize)) - GlobalZero[1]
						LineIDs.append(graph.draw_line((StartPointX,StartPointY), (EndPointX, EndPointY), color="blue", width=3))
			except Exception as ex:
				print(ex)
				
def PositionPopup(cords):
	Char = ""
	sg.theme(config.get("Settings","Theme"))
	layout = [[sg.Text('Select a Character')],[sg.Combo(values=GetChars(), size = (30,10), enable_events = True, k='-SETPOS-' )],[sg.Button("Set", key="setposok", enable_events=True), sg.Button("Cancel", key="btnclosecancel", enable_events=True)]]

	win = sg.Window("Set Position", layout, modal=True, grab_anywhere=True, enable_close_attempted_event=True, icon=IconPath)
	while True:
		event, values = win.read()
		if event == sg.WIN_CLOSED or event == '-WINDOW CLOSE ATTEMPTED-':
			break
			
		if event == "-SETPOS-":
			for key, char in Characters.items():
				if key == values['-SETPOS-']:
					Char = key
		
		if event == 'setposok':
			Region = 0
			if FocusArea != "World":
				Region = GetRegionFromName(FocusArea)
			UpdateCommandsToSend(Char, f"setposition:{cords[0]},{cords[1]},{Region}")
			break
				
		if event == 'btnclosecancel':
			break
	win.close()

def chunks(lst, n):
	for i in range(0, len(lst), n):
		yield lst[i:i + n]

def DetailsPopup(Username):
	CharInfo = Characters[Username]
	text = []
	columns = []
	for key in CharInfo:
		text.append([sg.Text(f"{key} - {CharInfo[key]}")])
	
	lists = list(chunks(text, 10))
	for item in lists:
		columns.append(sg.Column(item))

	layout = [columns,[sg.Button("Cancel", key="details-cancel", enable_events=True)]]

	win = sg.Window(f"Character Details [{Username}]", layout, modal=True, enable_close_attempted_event=True, icon=IconPath)

	event, values = win.read()
	win.close()
	window.write_event_value(event, values)
			
def RestartApp():
	try:
		os.startfile(sys.executable)
	except Exception as ex:
		pass
	Terminate()
	
def UpdateCommandsToSend(name,command):
	global CommandsToSend
	CurrentCommands = []
	for Name in CommandsToSend:
		if Name == name:
			CurrentCommands = CommandsToSend[name]
			if command in CurrentCommands:
				CurrentCommands.remove(command)
	data = {name:[command] + CurrentCommands}
	CommandsToSend.update(data)
			
def GetCommands(Username):
	global CommandsToSend
	commands = []
	for key, Name in enumerate(CommandsToSend):
		if Name == Username:
			CurrentCommands = CommandsToSend[Name]
			for cmd in CurrentCommands:
				if cmd not in commands:
					commands.append(cmd)
					CommandsToSend[Name] = []
	return commands
	
def UpdateDisplayedChar():
	CharInfo = Characters[SelectedUsername]
	window["-username-"].update(value=f"{CharInfo['name']} - {CharInfo['server']}")
	window["-charlevel-"].update(value=f"Level: {CharInfo['level']}")
	window["-postion-"].update(value=f"Postion: {round(CharInfo['x'],1)}, {round(CharInfo['y'],1)}, {round(CharInfo['z'],1)}")
	window["-deadstate-"].update(value=f"Dead: {CharInfo['dead']}")
	window["-status-"].update(value=f"State: {CharInfo['status']}")
	window['-HP_BAR-'].update(max=CharInfo['hp_max'], current_count=CharInfo['hp'])
	window['-MP_BAR-'].update(max=CharInfo['mp_max'], current_count=CharInfo['mp'])
	window['-EXP_BAR-'].update(max=CharInfo['max_exp'], current_count=CharInfo['current_exp'])

app = Flask(__name__)
q = queue.Queue()

def asyncloop(loop):
	asyncio.set_event_loop(loop)  
	loop.run_forever()

loop = asyncio.new_event_loop()
t = Thread(target=asyncloop, args=(loop,))
t.start()

async def UpdateTask():
	global q, Chars
	try:
		while not q.empty():
			item = q.get()
			Username = list(item.keys())[0]
			if not "Ping" in item[Username]:
				UpdateCharacterData(item)
				AddCharacterToMap(Username)
				if Username == SelectedUsername:
					UpdateDisplayedChar()
	except Exception as e:
		print(e)
		 
@app.route('/', methods=['POST'])
def index():
	global q
	try:
		if request.method == 'POST':
			q.put(request.json)
			asyncio.run_coroutine_threadsafe(UpdateTask(), loop)
			Cmds = True if config.get("Settings","enable_commands") == "True" else False
			if Cmds:
				Username = list(request.json.keys())[0]
				return {"EnableCommands": True, "Commands": GetCommands(Username)}
			return {"EnableCommands": False}
	except Exception as e:
		print(e)
		pass
	return 'error'

def flask_thread():
	app.run(debug=False, host='0.0.0.0', port=8888)
 
Timer(2.0, flask_thread,()).start()  

def main():
	global graph, window, CanvasSize, GraphDims, XOffset, YOffset, LoadedScripts, LineIDs
	sg.theme(config.get("Settings","Theme"))

	layout2 = sg.Column([
			   [sg.T('Zoom to Town', enable_events=True)],
			   [sg.Combo(values=GetTowns(), size = (30,10), enable_events = True, k='-TOWNCOMBO-' )],
			   [sg.T('Zoom to Area', enable_events=True)],
			   [sg.Combo(values=GetAreas(), size = (30,10), enable_events = True, k='-AREACOMBO-' )],
			   [sg.T('Zoom to Cave', enable_events=True)],
			   [sg.Combo(values=GetCaves(), size = (30,10), enable_events = True, k='-CAVECOMBO-' )],
			   [sg.T('Zoom to Character', enable_events=True)],
			   [sg.Combo(values=[], size = (30,10), enable_events = True, k='-CHARCOMBO-' )],
			   [sg.T('')],
			   [sg.T('N/A', enable_events=True, k='-username-', font=("impact", 20))],
			   [sg.ProgressBar(100, orientation='h', size=(20, 5), border_width=4, key='-HP_BAR-', bar_color=("red","pink"))],
			   [sg.ProgressBar(100, orientation='h', size=(20, 5), border_width=4, key='-MP_BAR-', bar_color=("blue","lightblue"))],
			   [sg.T('Level: ', enable_events=True, k='-charlevel-')],
			   [sg.T('Postion: ', enable_events=True, k='-postion-')],
			   [sg.T('Dead: ', enable_events=True, k='-deadstate-')],
			   [sg.T('Status: ', enable_events=True, k='-status-')],
			   [sg.ProgressBar(100, orientation='h', size=(20, 5), border_width=4, key='-EXP_BAR-', bar_color=("green","lightgreen"))],
			   [sg.B('Start Bot', key='-startbot-'), sg.B('Stop Bot', key='-stopbot-')],
			   [sg.B('Start Trace', key='-starttrace-'), sg.B('Stop Trace', key='-stoptrace-')],
			   [sg.B('Use Return Scroll', key='-usereturnscroll-'), sg.B('Change Profile', key='-changeprofile-')],
			   [sg.B('Go Clientless', key='-goclientless-'), sg.B('Close Bot', key='-closebot-')],
			   [sg.B('See All Details', key='-seechardetails-')],
			   #[sg.B('test', key='-test-')]
			   ], vertical_alignment='top')

			   
	layout1 = sg.Column([
				[sg.Graph(
				canvas_size=(CanvasSize),
				graph_bottom_left=(0, 0),
				graph_top_right=(GraphDims),
				key="-GRAPH-",
				enable_events=True,
				motion_events=True,
				right_click_menu=["",["Set Position", "Move To (Selected Char)"]],
				background_color='black',
				drag_submits=True,
				expand_x=True, 
				expand_y=True)]])
				
			  
	layout3 = [[
				sg.Text(key='mousepos', size=(40, 1)),
				sg.Slider(range=(1,6), default_value=1, orientation='h', key='-ZOOMSLIDER-',enable_events=True, disabled=True, pad=(100,10))],
				#sg.Text(key='info', size=(80, 1))
				]

	layout4 = [[sg.B('Reload Map', key='ReloadMap', expand_x=True)]]	
	
	menu_def = [['&Application', ["Load Script", "Clear Scripts", "---", "Restart App","Settings"]],['Help',["Download Plugin", "About"]] ]
	
	Layout = [[sg.Menu(menu_def, key='-MAPMENU-')],[layout1,layout2],[layout3],[layout4]]
	window = sg.Window("BunkerMap", Layout, keep_on_top=False, finalize=True, return_keyboard_events=True, resizable=True, icon=IconPath)
	graph = window["-GRAPH-"]

	Timer(0.0, AddImages, ()).start()   
	
	dragging = False
	start_point = end_point = prior_rect = None
	window['-ZOOMSLIDER-'].bind('<ButtonRelease-1>', ' Release')
	window.bind('<Configure>', "Configure")

	OriginalWindow = window.size
	while True:
		global GlobalCenter, GlobalZero, LoadedImages, ZoomLevel, FocusArea, ZoomThread, ImageThread, BotPath, SelectedUsername
		#window, event, values = sg.read_all_windows() #use this line instead of the one below to fix werid map movement.. but close button and other shit will break, no clue why
		event, values = window.read() 
		#print(event, values)
		if event in (sg.WIN_CLOSED, 'Cancel'):
			Terminate()
			break  # exit

		if event in ('-MOVE-', '-MOVEALL-'):
			graph.set_cursor(cursor='fleur')
		if not event.startswith('-GRAPH-'):
			graph.set_cursor(cursor='left_ptr')	

		if event == "-GRAPH-": 
			x, y = values["-GRAPH-"]
			if not dragging:
				if ImageThread:
					ImageThread.cancel()
					ImageThread = None
				print('dragging')
				start_point = (x, y)
				dragging = True
				lastxy = x, y
				drag_figures = graph.get_figures_at_location((x,y))
				for fig in drag_figures:
					Username = GetCharFromFigureId(fig)
					if Username and Username != SelectedUsername:
						SelectedUsername = Username
						UpdateDisplayedChar()
						
			else:
				end_point = (x, y)
			delta_x, delta_y = x - lastxy[0], y - lastxy[1]
			GlobalCenter = GlobalCenter[0] - delta_x, GlobalCenter[1] - delta_y
			GlobalZero = GlobalZero[0] - delta_x, GlobalZero[1] - delta_y
			lastxy = x,y
			graph.move(delta_x, delta_y)

		if event.endswith('+UP'):
			#print('up....')
			#window["info"].update(value=f"grabbed {start_point} to {end_point} Center {GlobalCenter} Zero {GlobalZero}") #for debugging
			start_point, end_point = None, None 
			dragging = False
			prior_rect = None
			ImageThread = Timer(0.01, AddImages)
			ImageThread.start()
			
		elif event == "-GRAPH-+MOVE":
			x, y = values["-GRAPH-"]
			GameCords = round((GlobalZero[0] + x) * (192/ImageSize),1), round((GlobalZero[1] + y) * (192/ImageSize),1) 
			window["mousepos"].update(value=f"Game Cordinates {GameCords}")
				
		#zoom in with mouse wheel
		elif event == "MouseWheel:Up":
			if ZoomLevel == 6:
				print(f'Max Zoom Reached[{ZoomLevel}]')
				
			elif ZoomLevel <= 6:
				if ZoomThread:
					ZoomThread.cancel()
					ZoomThread = None
				ZoomLevel += 1
				window['-ZOOMSLIDER-'].update(value = ZoomLevel)
				
				ZoomThread = Timer(1.0, SetZoom, ["IN"])
				ZoomThread.start()
		#zoom out with mouse wheel	
		elif event == "MouseWheel:Down":
			if ZoomLevel == 1:
				print(f'Min Zoom Reached[{ZoomLevel}]')
				
			elif ZoomLevel >= 1:
				if ZoomThread:
					ZoomThread.cancel()
					ZoomThread = None
				ZoomLevel -= 1
				window['-ZOOMSLIDER-'].update(value = ZoomLevel)
				
				ZoomThread = Timer(1.0, SetZoom, ["OUT"])
				ZoomThread.start()
				
		elif event == '-TOWNCOMBO-':
			FocusArea = "World"
			Cords = Towns[values['-TOWNCOMBO-']]
			ZoomTo(Cords[0],Cords[1])
			
		elif event == '-AREACOMBO-':
			FocusArea = "World"
			Cords = Areas[values['-AREACOMBO-']]
			ZoomTo(Cords[0],Cords[1])
			
		elif event == '-CAVECOMBO-':
			Cave = values['-CAVECOMBO-']
			z = 0
			if Cave == "Donwhang Dungeon B1":
				z = 25
			if Cave == "Donwhang Dungeon B2":
				z = 30			
			if Cave == "Donwhang Dungeon B3":
				z = 160
			if Cave == "Donwhang Dungeon B4":
				z = 310	   
			ZoomTo(-24200,-90, z, Caves[values['-CAVECOMBO-']])
			
		elif event == '-CHARCOMBO-':
			Cords = GetCharsCords(values['-CHARCOMBO-'])
			ZoomTo(Cords[0],Cords[1],Cords[2],Cords[3])  
						
		elif event == "Load Script":
			ScriptFile = sg.popup_get_file('Choose your Walking Script',icon=IconPath)
			if ScriptFile != None and ScriptFile != '':
				LoadedScripts.append(ScriptFile)
				DrawScript(ScriptFile)
		
		elif event == "Clear Scripts":
			LoadedScripts = []
			for ID in LineIDs:
				graph.delete_figure(ID)
			LineIDs = []

		# bot return commands			
		elif event == "Set Position":
			PositionPopup(GameCords)
			
		elif event == "Move To (Selected Char)":
			if SelectedUsername and Characters[SelectedUsername]["online"]:
				Region = 0
				if FocusArea != "World":
					Region = GetRegionFromName(FocusArea)
				UpdateCommandsToSend(SelectedUsername, f"moveto:{GameCords[0]},{GameCords[1]},{Characters[SelectedUsername]['z']},{Region}")
			
		elif event == '-startbot-':
			if SelectedUsername and Characters[SelectedUsername]["online"]:
				UpdateCommandsToSend(SelectedUsername, "start")
			else:
				print(f"[{SelectedUsername}] is not online")
				
		elif event == '-stopbot-':
			if SelectedUsername and Characters[SelectedUsername]["online"]:
				UpdateCommandsToSend(SelectedUsername, "stop")
			else:
				print(f"[{SelectedUsername}] is not online")
				
		elif event == '-starttrace-':
			Player = sg.popup_get_text("Enter player name to start tracing", icon=IconPath)
			if SelectedUsername and Characters[SelectedUsername]["online"]:
				UpdateCommandsToSend(SelectedUsername, f"starttrace:{Player}")
			else:
				print(f"[{SelectedUsername}] is not online")
				
		elif event == '-stoptrace-':
			if SelectedUsername and Characters[SelectedUsername]["online"]:
				UpdateCommandsToSend(SelectedUsername, "stoptrace")
			else:
				print(f"[{SelectedUsername}] is not online")
				
		elif event == '-changeprofile-':
			Profile = sg.popup_get_text("Enter the profile name", icon=IconPath)
			if SelectedUsername and Characters[SelectedUsername]["online"]:
				UpdateCommandsToSend(SelectedUsername, f"setprofile:{Profile}")
			else:
				print(f"[{SelectedUsername}] is not online")
				
		elif event == '-usereturnscroll-':
			if SelectedUsername and Characters[SelectedUsername]["online"]:
				UpdateCommandsToSend(SelectedUsername, f"usereturnscroll")
			else:
				print(f"[{SelectedUsername}] is not online")
				
		elif event == '-goclientless-':
			if SelectedUsername and Characters[SelectedUsername]["online"]:
				UpdateCommandsToSend(SelectedUsername, "goclientless")
			else:
				print(f"[{SelectedUsername}] is not online")
					
		elif event == '-closebot-':
			if SelectedUsername and Characters[SelectedUsername]["online"]:
				UpdateCommandsToSend(SelectedUsername, "closebot")
			else:
				print(f"[{SelectedUsername}] is not online")
				
		elif event == '-seechardetails-':
			if SelectedUsername and Characters[SelectedUsername]["online"]:
				DetailsPopup(SelectedUsername)
			else:
				print(f"[{SelectedUsername}] is not online")
			
		elif event == "Settings":
			SettingsPopup()		
			
		elif event == "Restart App":
			RestartApp()
			
		elif event == "ReloadMap":
			ClearMap()
			Timer(0.1, AddImages, ()).start()
			LoadAllChars()
			
		elif event == 'setting-save':
			BotPath = values['setting-save']['botpath']
			config['Settings']['BotPath'] = values['setting-save']['botpath']
			config['Settings']['Theme'] = values['setting-save']['theme']
			config['Settings']['enable_commands'] = str(values['setting-save']['enable_commands'])
			print(values['setting-save']['theme'])
			with open("BunkerMap.ini", 'w') as f:
				config.write(f)

		elif event == 'Botpath':
			try:
				path = sg.popup_get_folder('Choose your phBot Folder',icon=IconPath)
				if path != None and path != '':
					config['Settings']['BotPath'] = str(path)
					SettingsPopup()
			except Exception as ex:
				print(ex)
				pass

		#reszing of window
		elif event == 'Configure':
			CurrentWindowSize = window.size
			CurrentGraphSize = GraphDims
			#resize both directions
			if OriginalWindow[0] != CurrentWindowSize[0] and OriginalWindow[1] != CurrentWindowSize[1]:
				CanvasSize = CurrentWindowSize[0]-300,CurrentWindowSize[1]-140
				GraphDims = CanvasSize[0]/Ratio, CanvasSize[1]/Ratio
				window['-GRAPH-'].set_size(size=(CanvasSize))
				graph.change_coordinates(graph_bottom_left=(0,0), graph_top_right=(GraphDims))
				DeltaX = GraphDims[0] - CurrentGraphSize[0]
				DeltaY = GraphDims[1] - CurrentGraphSize[1]
				GlobalCenter = GlobalCenter[0] + (DeltaX/2), GlobalCenter[1]  - (DeltaY/2)
				GlobalZero = GlobalZero[0], GlobalZero[1] - (DeltaY)
				OriginalWindow = window.size
				
			#resize x direction only
			if OriginalWindow[0] != CurrentWindowSize[0]:
				CanvasSize = CurrentWindowSize[0]-300,graph.CanvasSize[1]
				GraphDims = CanvasSize[0]/Ratio, CanvasSize[1]/Ratio
				window['-GRAPH-'].set_size(size=(CanvasSize))
				graph.change_coordinates(graph_bottom_left=(0,0), graph_top_right=(GraphDims))
				DeltaX = GraphDims[0] - CurrentGraphSize[0]
				GlobalCenter = GlobalCenter[0] + (DeltaX/2), GlobalCenter[1]
				OriginalWindow = window.size

			#resize y direction only	
			if OriginalWindow[1] != CurrentWindowSize[1]:
				CanvasSize = graph.CanvasSize[0],CurrentWindowSize[1]-140
				GraphDims = CanvasSize[0]/Ratio, CanvasSize[1]/Ratio
				window['-GRAPH-'].set_size(size=(CanvasSize))
				graph.change_coordinates(graph_bottom_left=(0,0), graph_top_right=(GraphDims))
				DeltaY = GraphDims[1] - CurrentGraphSize[1]
				GlobalCenter = GlobalCenter[0], GlobalCenter[1] - (DeltaY/2)
				GlobalZero = GlobalZero[0], GlobalZero[1] - (DeltaY)
				OriginalWindow = window.size
				
		elif event == "Download Plugin":
			try:
				req = urllib.request.Request('https://raw.githubusercontent.com/Bunker141/Phbot-Plugins/master/RewardsCollector.py', headers={'User-Agent': 'Mozilla/5.0'})
				with urllib.request.urlopen(req) as f:
					lines = str(f.read().decode("utf-8"))
					with open("BunkerMap.py", "w+") as f:
						f.write(lines)
			except Exception as ex:
				print('Error Updating [%s] Please Update Manually or Try Again Later' %ex)
					
		elif event == "About":
			os.startfile("https://www.youtube.com/watch?v=wnedkVrgFF0")

		elif event == '-test-':
			pass
			
	window.close()

main()