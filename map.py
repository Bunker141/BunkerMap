import PySimpleGUI as sg
from PIL import Image, ImageDraw, ImageFont
import PIL
import io
import base64
from io import BytesIO
import os
from os import listdir
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
import sqlite3

defaultsettings = {'botpath': '', 'theme': 'DarkGray4', 'enable_commands': 'True', 'show_npcs': 'True', 'show_teleporters': 'True', 'server': ''}

#create ini file if it doesnt exist 
config = configparser.ConfigParser()
if not os.path.exists("BunkerMap.ini"):
	config.add_section('Settings')
	for item in defaultsettings:
		config['Settings'][item] = defaultsettings[item]
	with open("BunkerMap.ini", 'w') as f:
		config.write(f)

config.read('BunkerMap.ini')

#check to make sure all settings exist
for item in defaultsettings:
	try:
		config.get("Settings",item)
	except configparser.NoOptionError:
		config['Settings'][item] = defaultsettings[item]
		with open("BunkerMap.ini", 'w') as f:
			config.write(f)
			
version = 1.1

#each minimap is 192 x 192 in game cords
#0,0 in game is on tile 135x92
graph = None
window = None
ZoomThread = None
ImageThread = None

ZoomLevels = {1: {"ImageWidth": 50, "Padding": 200, "PointSize": 3.5, "TextSize": 15, "PopupXOffset": 55, "PopupYOffset": 20}, 2: {"ImageWidth": 100, "Padding": 200, "PointSize": 1.5, "TextSize": 15, "PopupXOffset": 28, "PopupYOffset": 10}, 3: {"ImageWidth": 200, "Padding": 100, "PointSize": 0.75, "TextSize": 12, "PopupXOffset": 14, "PopupYOffset": 5}, 4: {"ImageWidth": 300, "Padding": 100, "PointSize": 0.5, "TextSize": 10, "PopupXOffset": 10, "PopupYOffset": 3}, 5: {"ImageWidth": 500, "Padding": 50, "PointSize": 0.35, "TextSize": 10, "PopupXOffset": 6.5, "PopupYOffset": 1}, 6: {"ImageWidth": 1000, "Padding": 40, "PointSize": 0.2, "TextSize": 10, "PopupXOffset": 4, "PopupYOffset": 0}}
ZoomLevel = 1
FocusArea = "World"

CanvasSize = 700,600
Ratio = (ZoomLevels[ZoomLevel]['ImageWidth']/10) / 2
GraphDims = CanvasSize[0]/2.5, CanvasSize[1]/2.5
GlobalCenter = GraphDims[0] / 2, GraphDims[1] / 2
GlobalZero = 0,0
ImageSize = 20

#dont change
XOffset = 2700 
YOffset = 1820


LoadedImages = []
LoadedScripts = []
LineIDs = []

BotPath = config.get("Settings","BotPath")

IconPath = b"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"
NPCIcon = b"iVBORw0KGgoAAAANSUhEUgAAAAYAAAAGCAYAAADgzO9IAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsIAAA7CARUoSoAAAAA4SURBVBhXY2QAg4r/EBoGOhhZQIIODQ1QAQg40MDwnwnKZsiIgGAYgEugA7jEjBUQDAM4LO9gBABFaQ0DGXi6nAAAAABJRU5ErkJggg=="
NPCPopupStartBG = b"iVBORw0KGgoAAAANSUhEUgAAAFAAAAArCAMAAADYKv+dAAAAAXNSR0IB2cksfwAAAAlwSFlzAAALEwAACxMBAJqcGAAAAa1QTFRFAAAAqqqqkJCQqqqql5eXYGBgmZmZqqqqmJiYS0tLNDQ0ZGRknJyclpaWTExMZ2dnm5ubmpqaXl5ebGxsm5ubmpqaampqbm5unJycn5+fcnJyNjY2enp6oKCgo6OjkZGRmJiYmZmZhYWFNzc3g4ODmJiYmpqaampqOjo6jY2Njo6Oj4+PAAAAAAAAj4+PAAAAjo6OAAAAAAAAjo6ONTU1AAAAAAAAjY2NAAAAAAAAjY2NAAAAAAAAjIyMODg4AAAAAAAAOTk5AAAAAAAAAAAAjY2NPDw8Ozs7PT09AAAAPz8/Pj4+jo6OQEBAQUFBQ0NDQkJCj4+PREREjY2NRkZGRUVFiYmJR0dHcnJyb29vTU1NSEhICgoKXV1dbm5ufHx8fHx8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAJWoGGQAAAI90Uk5TAAxSCc33kgS4/f/zhKP58IKP9OxrY+3mT0vm/+RJSKXP0ub/5dFn6//O4+cBA+gH6QYO6v8KFusFHuwSJO3/FCj/CCor7v///xf//+7/////7v/q///b/5Xy//9HmMfb3kRbbnl+f0NtQFhrd3x9JTtRZHB1DzJGVmJnaWomNk5TVQIZLzw9FRsgIwkMEQTfpHwSAAABbElEQVR4nM3Vy07CQBQG4PkptUisirEGFrIyJmhZ6YINa9cudOHj+DguNPEZfApj4gWNElkQwwILqEOd1qQOl2l/E2fTtM18c86ZG0SiAR/JT0YNiXcLQEAEHYxbjwe6GApho8sCS+iPH4vocEAvStbFCwOsxKmWgFZGsBrOxvOPPcpnAreBh5Qh6cHaPYeLwZ07Mrh7+79BH7ihgvUcrpmgb8slyATrBeDRoE9lFtgIHLT1v/sG48Sgbxf1KT8Zawq0Vqfu3JExuNFzg1eDPrNqKMFlTcop5z0CLcN+E6/GEHQGsFkLUYGFeby5ZicCcxkDi9pnBE6roVE1FOhmLWFcDgWu/ALTjqDANcP+k+dHgeu0A0yBZbBEtVM2wRL/CHS3BgtDHijPwxo1Qru4H3rm570eFI3mVfM7QkKM6tY7QKtKS1mcXuCw4wVvHkMML3p43SOZ8eUeCZRi/gTtsjhngZI8XjoT7wRPfAHNnkmYkzcq6gAAAABJRU5ErkJggg=="
NPCPopupEndBG = b"iVBORw0KGgoAAAANSUhEUgAAAA8AAAArCAMAAACQNSJYAAAAAXNSR0IB2cksfwAAAAlwSFlzAAALEwAACxMBAJqcGAAAAWtQTFRFAAAAmJiYmZmZmJiYmZmZqqqqNDQ0NTU1U1NTk5OTampqqqqqV1dXqqqqVlZWqqqqqKiopaWlAAAAm5ubAAAAkJCQAAAAAAAAV1dXhISEAAAAAAAAe3t7AAAAAAAANjY2dXV1AAAANzc3WFhYcnJyAAAAAAAAAAAAODg4WVlZcHBwAAAAOjo6WlpaOzs7W1tbb29vAAAAPDw8XFxcPj4+XV1dPz8/Xl5eQUFBQEBAX19fQkJCYGBgQ0NDYGBgampqRUVFcHBwQkJCRkZGR0dHhoaGAAAAfHx8fHx8eHh4Z2dnIiIiAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA+8rYrQAAAHl0Uk5TANHRxGwH///5t+oc+T/8RUZHAUwEUQgD/VkOBV8TB/9kF//9ZxkKAv/9aRv//f/9aQv//f/9//3///3//f/7Zf/wSP//zTLe3dSuWH98c2JLMXthSn15cF9IL3d2cmlYQitqaGRbTDgkVVRQOz08KB0SCSUiEBENBnvAe4gAAAEKSURBVHictdExT8JAGAbg7wXaMjBo+AEmTJoYB0OIiTExcWBxlInNzcHBuPh/jLNhYGeGX6CLEwPRVIi0Wq5U7+77zvTYuaHN07d3uXsP5A9s27APQIlD/orvsolqSDyH+PJcx8J3Ze67ithzgCIuOwJmxhF7V29hWnYNWOoJ2GNndSS5ccudQ48X/d7/t7I+FK/FRy5XYWp87HJxW6zEHXEmPpHpqfhU8qX4zK3/wT53nrEvrFYRpuyu6198KU43jFfev3GYB1iLey6f8Pn7Qoy4n+ucAush93dj8riZjD+531tCod4O9A9Ptv97oqSRD64GMd/PHQX0W3n+SQu+vweiR8qqO++W9AecYG0sLsZD3gAAAABJRU5ErkJggg=="
NPCPopupMiddleBG = b"iVBORw0KGgoAAAANSUhEUgAAAAoAAAArCAMAAAB2HOkcAAAAAXNSR0IB2cksfwAAAAlwSFlzAAALEwAACxMBAJqcGAAAAFdQTFRFAAAAmJiYNDQ0NTU1NjY2Nzc3ODg4OTk5Ozs7PDw8PT09Pz8/QEBAQkJCQ0NDRUVFRERERkZGR0dHfHx8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAnM/CngAAAB10Uk5TANH//////////////////////95/fXdqVT0lEga1k0zvAAAATUlEQVR4nK3IOw6AIBAAUdY/KhJU/N//nHQ7jYmFTPUyYjT5TyxFTpavrGANG9jCDlrYwwGO0MEJepUE7gwXuH4xwg3u8IAnvOANH2UC/3oB6m75gfkAAAAASUVORK5CYII="
MobIcon = b"iVBORw0KGgoAAAANSUhEUgAAAAYAAAAGAgMAAACdogfbAAAAAXNSR0IB2cksfwAAAAlwSFlzAAAOxAAADsQBlSsOGwAAAAxQTFRFAAAAcwAA1yws6IOD3seumAAAAAR0Uk5TAP///7MtQIgAAAAWSURBVHicYxTVZsxSY8xXBCEgQ1QbABmNAsfiB/KcAAAAAElFTkSuQmCC"
PartyIcon = b"iVBORw0KGgoAAAANSUhEUgAAAAYAAAAGAgMAAACdogfbAAAAAXNSR0IB2cksfwAAAAlwSFlzAAAOxAAADsQBlSsOGwAAAAxQTFRFAAAABWxHPOOohvbONgcJVwAAAAR0Uk5TAP///7MtQIgAAAAWSURBVHicYxTVZsxSY8xXBCEgQ1QbABmNAsfiB/KcAAAAAElFTkSuQmCC"
TeleportIcon = b"iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAACXBIWXMAAAsTAAALEwEAmpwYAAAAIGNIUk0AAHolAACAgwAA+f8AAIDpAAB1MAAA6mAAADqYAAAXb5JfxUYAAAU6SURBVHjarJZBaBzXGcd/K9fSNzVlZxBhZ8lh86qWziwJHamGTtUe1sI9KKKU1MnBEYYS2wfj+hJ8KCW9hNJDcHuxQ6FuenHjHFT5EiJdzNoUKu9B7IoiNEtgmZoiZpciZhSszluc7OthZGlT95gHA483733/7/u///e9r2SMAeCML8XkKxoPIl0C+Noz46t/vQrkgIVgc+9Bk6rrM+s/f1iwACGzFDYa8hSATGuSDBxJOVs/Ze7vHJRoeFNmt3fT9DbfM3vbN8325nsGOPrCMDCAWVwMj9Ya/7PWaHgGMLvbN01v847pbd4x6385bwAzASB5DLrP9MvXcATK5SmCoEKtUsZxbMrlMhsbEWEYEoYhcZJSLpexbYcg8NBaANBamDl9AUTzTfUtjiiCHBGH3uavqP/w14jY2OIQ64SdnYj9/X0AWq3Wl6hqNtsMBgNee20R2GLm9GW2N28XP08cbmp4U+Zg+4oBjOd5plYpm8VGYGoVTK1WKWj6eGTO3x+ZdzdH5t3tYu6tjI7OjNMVBJ6p1crmH3/75TFFz4ZtQ91XbHQilPLIsgxvZUTr3kU+ar+DU4WqAx81r9O9u0Tlzohut0ujEbK+3mJxsUG16hYymHg6TpEFQBwnxAAMiZMUuZXTXVsG3wdfcS1aLYQ260PVZXBvCW4e8PDaKTzPY6f9sLAmoPXnxwAaCEMPAaI4RQSsGwmPm9cJFt5kS2mYn4MkBm1D7oCzQWC/RdS8hNwZ0b0wQa1WQSmFZYF1cgRAoSKEVqtLP0txHEH9KSVZW4Y5VRivOlQQ9uwF9ty5ImB3ni0lDOdm2V87R2WlMBh1OrTbnSPaJ45iApTrkCQZygLtK3BdsB1whY28ynTnQ6YfrdJzVQFia7At8BVzDmgNyneRsXv90iW3OzGzvo3vwq3l3xTAFvSYZ6azSjivYAFmdJtdVxWHqi9x++INfBv8ny0TR300IDJ6HgCR5+uCLeQFj3QoSgJxjAawnMMEO5RK1EREELGZLP0fAF9V6WeaqA+/+PA65BpizctZk55/juEOBPkcPf8cM1kTUignmmvvv8NGAnE/pe4rsITSidK4TAsX4iRH64xOCkQJWDE4QOowQ5O9+hIA00kTkhwyi/2kD1EHzkCaZiRJhohm9ZO/HwNkqcbzaiilaLf7pJcs7Fs5g7tLBLbPVjWFPkynnxz7k1lMtWOGD1bx3mrS+d1FRMPCgo8gTMoX43kgdLuPyXONCGhsBhcm4PaIrbtL8OqZQk3YBUCiIfsnw7VVpi426b5R5EBfa9bWOgyHQ37y49fHKSpGve6Tphmt1haNRsjDyxN4KyO6d5dAvcTt+fdB4HLzOsQx3tXCeBB4pEnOD2bdQw30Ofv9F8YBCvW02xGDwYDFxQbr60Xad9+YIPy4UESSFlvPL9wgziG+VKgoTXOUXyWKOoCN1sKoYOg4gt3NK4DFi6d/z/r6QzzPI00TqtUqndcthsMh48U6CAKyTFOr1ajXFe32I0RcNlaX0Vqzm54Yk6nOECmM31+5cuhVgu8r0CkiQq1WIQwDwjA4BE9xXRfHcRCxEHFpfvAqL57+LWg40GPVNNXQfhSzt/02WkO5XLxknShG0NgCSvnEcQI6Q/mKLAMRIctSms34MEcttu+/TQ6c5D8AlIwxnK2fMn/481VOThSNxcETjf31EZOThqlJ+GBliy8Qfv7T7/D0aYnBkxLdTx/zvVdm+PTxv/mu/23Szz7nXwPNC2WY/sYTZn70R4wxpdKztqVUKn2lbYsxpgTw3wEAbhJX2my7m10AAAAASUVORK5CYII="
FortIcon = b"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"


Towns = {"Jangan": (6430,1035), "Donwhang": (3545,2110), "Hotan": (105,48), "Samarkand": (-5185,2880), "Constantinople": (-10685,2575), "Alexandria (North)": (-16155,67), "Alexandria (South)": (-16645,-278), "Baghdad": (-8535,-730)}
Areas = {"Bandit Camp": (4875,-40), "Tarim Basin": (2590,-20), "Karakoram": (-1400,-265), "Taklamakan": (-500,2000), "Mountain Roc": (-4400,-175), "Central Asia": (-4100,2500), "Asia Minor": (-6900,2100), "Eastern Europe": (-11900,2800), "Storm and Cloud Desert": (-12365,-1335), "King's Valley": (-13235,-3285), "Kirk Field": (-9292,-775), "Phantom Desert": (-10355,-2820), "Flaming Tree": (-8840,-2340), "Sky Temple": (17365,-100), "Mirror Dimension": (12875,-40), "Forgotten World": (19475,3570), "Stryia Arena": (20540,6325)}
Caves = {"Donwhang Dungeon B1": -32767, "Donwhang Dungeon B2": -32767, "Donwhang Dungeon B3": -32767, "Donwhang Dungeon B4": -32767, "Qin-Shi Tomb B1": -32761, "Qin-Shi Tomb B2": -32762, "Qin-Shi Tomb B3": -32763, "Qin-Shi Tomb B4": -32764, "Qin-Shi Tomb B5": -32765, "Qin-Shi Tomb B6": -32766, "Job Temple": -32752, "Flame Mountain": -32750, "Cave of Meditation": -99999, }
NPCs = {}
Teleports = {}
Characters = {}
CommandsToSend = {}

SelectedUsername = ""

def SettingsPopup():
	sg.theme(config.get("Settings","Theme"))
	SettingCol = sg.Column([
	[sg.Text('Bot Path')],
	[sg.Text('Theme')],
	[sg.Text('Enable Commands')],
	[sg.Checkbox("Show NPC's", default= True if config.get("Settings","show_npcs") == "True" else False, k='show_npcs', tooltip="shows NPC's for the selected server.. bot folder must be set")],
	[sg.Checkbox("Show Teleporters", default= True if config.get("Settings","show_teleporters") == "True" else False, k='show_teleporters', tooltip="shows teleporters for the selected server.. bot folder must be set")],
	])

	SettingCol2 = sg.Column([
	[sg.Input(config.get("Settings","BotPath"), k='botpath')],
	[sg.Combo(values=(sg.theme_list()), default_value=config.get("Settings","Theme"), readonly=True, k='theme')],
	[sg.Checkbox('Enable Bot Commands', default= True if config.get("Settings","enable_commands") == "True" else False, k='enable_commands', tooltip="enables communication to bots, may increase useage")],
	[sg.Combo(values=GetServerList(), size = (45,10), k='-SERVERCOMBO-', default_value=config.get("Settings","server"), readonly=True)],
	[sg.Text('')],
	])


	SettingCol3 = sg.Column([
	[sg.Button("...", key="Botpath", enable_events=True,s=(2,1))],
	[sg.Text('')],
	[sg.Text('')],
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
	global GraphDims, LoadedImages, GlobalCenter, Ratio, ZoomThread
	ZoomThread = None
	PreviousDims = GraphDims
	ClearMap()
	
	Ratio = (ZoomLevels[ZoomLevel]['ImageWidth']/10) / 2
	GraphDims = CanvasSize[0]/Ratio, CanvasSize[1]/Ratio
	graph.change_coordinates(graph_bottom_left=(0,0), graph_top_right=(GraphDims))
	if Type == "IN":
		GlobalCenter = GlobalCenter[0] - ((PreviousDims[0] - GraphDims[0]) / 2), GlobalCenter[1] - ((PreviousDims[1] - GraphDims[1]) / 2)
	if Type == "OUT":
		GlobalCenter = GlobalCenter[0] + (abs((PreviousDims[0] - GraphDims[0]) / 2)), GlobalCenter[1] + (abs((PreviousDims[1] - GraphDims[1]) / 2))
	Timer(0.1, AddImages, ()).start()
	LoadAllChars()
	LoadNPCs = True if config.get("Settings","show_npcs") == "True" else False
	if LoadNPCs:
		AddAllNPCs()
	LoadTeleporters = True if config.get("Settings","show_teleporters") == "True" else False
	if LoadTeleporters:
		AddAllTeleports()
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
	img.save(bio, format="PNG", optimize=True)
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
		ID = int(Image.split(',')[0])
		Location = GetImageLocation(Img)
		if not dragging:
			try:
				graph.relocate_figure(ID, Location[0], Location[1])
				graph.send_figure_to_back(window['-GRAPH-'].Images[ID]["obj"])
			except Exception as ex:
				pass
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
	ClearBullshit()	
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
		img_data = convert_to_bytes(file_to_display,resize=(ZoomLevels[ZoomLevel]['ImageWidth'],ZoomLevels[ZoomLevel]['ImageWidth']))
		ID = graph.draw_image(data=img_data, location=(location))
		window['-GRAPH-'].Images[ID] = {"obj": window['-GRAPH-'].Images[ID], "filename": Image}
		LoadedImages.append(f"{ID},{Image},{ZoomLevel}")
		try:
			graph.send_figure_to_back(ID)
		except Exception as ex:
			print(f"[{ID}] has error [{ex}]")
			pass
			
#deletes shit from memory that doesnt need to be there.. like the same image twice
def ClearBullshit():
	try:
		seen = set()
		dupes = []
		for key, img in window['-GRAPH-'].Images.copy().items():
			if str(img).startswith('pyimage'):
				continue
			if img['filename'] in seen:
				dupes.append(key)
			else:
				seen.add(img['filename'])
		for key in dupes:
			del window['-GRAPH-'].Images[key]
		delete = []
		for Image in LoadedImages:
			ID = int(Image.split(',')[0])
			if ID in dupes:
				delete.append(Image)
		for img in delete:
			LoadedImages.remove(img)
	except Exception as ex:
		print(f" BS {ex}")


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
	Buffer = (GraphDims[0] / 2) + ZoomLevels[ZoomLevel]['Padding']
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

def NPCInView(x,y):
	#map coordinates
	Buffer = (GraphDims[0] / 2) + ZoomLevels[ZoomLevel]['Padding']
	BottomLeft = (GlobalCenter[0] - Buffer, GlobalCenter[1] - Buffer)
	TopRight = (GlobalCenter[0] + Buffer, GlobalCenter[1] + Buffer)
	
	#translate to game coordinates
	BottomLeft = round((BottomLeft[0]) * (192/ImageSize),1), round((BottomLeft[1]) * (192/ImageSize),1)
	TopRight = round((TopRight[0]) * (192/ImageSize),1), round((TopRight[1]) * (192/ImageSize),1)
	
	if (x > BottomLeft[0] and x < TopRight[0] and y > BottomLeft[1] and y < TopRight[1]):
		return True
	else:
		return False
		
#have to do it like this because the GUI doesnt do well with clicking on the small icon images
def GetNPCsNearClick(X, Y, size):
	global NPCPopup
	Figures = []
	coords = []
	for key, npc in NPCs.items():
		npcX, npcY = npc['x'], npc['y']
		if npcX != None or npcY != None:
			if Inside(X, Y, size, npc['x'], npc['y']):
				Figures.append(npc)
				coords.append((npc['x'],npc['y']))
	if coords:
		cloest_x, cloest_y = min(coords, key=lambda point: math.hypot(X-point[0], Y-point[1]))
	for fig in Figures:
		if fig['x'] == cloest_x and fig['y'] == cloest_y:
			PointX = ((fig['x']-ZoomLevels[ZoomLevel]['PopupXOffset']) / (192/ImageSize)) - GlobalZero[0]
			PointY = ((fig['y']-ZoomLevels[ZoomLevel]['PopupYOffset']) / (192/ImageSize)) - GlobalZero[1]
			ID = graph.draw_image(data=BuildNPCPopup(fig['name']), location=(PointX,PointY))
			return ID
	return None
	
def Inside(clicked_x, clicked_y, radius, x, y):
	if ((x - clicked_x) * (x - clicked_x) + (y - clicked_y) * (y - clicked_y) <= radius * radius):
		return True
	else:
		return False
	
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
		ID = graph.draw_circle((PointX,PointY),ZoomLevels[ZoomLevel]['PointSize'],fill_color = fill_color,line_color = "black",line_width = 4)
		if ZoomLevel >= 3:
			TextID = graph.draw_text(CharInfo['name'],(PointX,PointY-3/ZoomLevel),color = "white",font = ("Impact", ZoomLevels[ZoomLevel]['TextSize']),angle = 0,text_location = "center")	
		data = {Username: {"PointID": ID, "TextID": TextID}}
		UpdateCharacterData(data)

def AddAllNPCs():
	global NPCs
	Loaded = []
	ToBeLoaded = []
	ToBeDeleted = []
		
	for key, npc in NPCs.items():
		if npc['PointID'] > 0:
			Loaded.append(key)
		if npc['x'] != None and npc['y'] != None:
			if NPCInView(int(npc['x']), int(npc['y'])) and npc['region'] > 0:
				ToBeLoaded.append(key)

	if FocusArea != "World":
		ToBeLoaded = []
		region = GetRegionFromName(FocusArea)
		for key, npc in NPCs.items():
			if npc['region'] == region:
				ToBeLoaded.append(key)
		
	for npc in ToBeLoaded:
		if npc not in Loaded:
			AddNPCToMap(npc)
			
	for npc in Loaded:
		if npc not in ToBeLoaded:
			ToBeDeleted.append(npc)
	
	for npc in ToBeDeleted:
		try:
			del window['-GRAPH-'].Images[NPCs[npc]['PointID']]
			NPCs[npc]['PointID'] = 0
		except Exception as ex:
			pass
		
def GetNPCNameFromID(ID):
	for key, npc in NPCs.items():
		if npc['PointID'] == ID:
			return npc['name']
	
def AddNPCToMap(id):
	global NPCs
	NPCInfo = NPCs[id]
	#print(NPCInfo)
	X, Y = NPCInfo['x'], NPCInfo['y']
	if X == None or Y == None:
		return
	PointX = ((X-1) / (192/ImageSize)) - GlobalZero[0]
	PointY = ((Y+1) / (192/ImageSize)) - GlobalZero[1]
	ID = graph.draw_image(data=NPCIcon, location=(PointX,PointY))
	graph.bring_figure_to_front(ID)
	NPCs[id]["PointID"] = ID
	
#start = 80px wide
#end = 15px wide
#middle = 10px wide
def BuildNPCPopup(name):
	textXoffset, textYoffset = 10, 8
	font = ImageFont.truetype("impact.ttf", 17)
	width = font.getbbox(name)[2] + textXoffset*2
	PopupImg = Image.new(mode='RGBA', size=(width, 43))
	Start = Image.open(BytesIO(base64.b64decode(NPCPopupStartBG)))
	Middle = Image.open(BytesIO(base64.b64decode(NPCPopupMiddleBG)))
	End = Image.open(BytesIO(base64.b64decode(NPCPopupEndBG)))
	PopupImg.paste(Start, (0,0))
	for x in range(int((width-70)/10)):
		PopupImg.paste(Middle, (80+(x*10),0))
	PopupImg.paste(End, (width-15,0))
	d1 = ImageDraw.Draw(PopupImg)
	d1.text((textXoffset, textYoffset), f"{name}", font=font)
	img_byte_arr = io.BytesIO()
	PopupImg.save(img_byte_arr, format='PNG')
	return img_byte_arr.getvalue()

#XSector = X / 1920 + 128
#YSector Y  / 1920 + 128
def ConvertCoords(X,Y,Region):
	#world coordinates
	if Region > 0:
		PosX = ((Region & 0xFF) - 135) * 192 + X / 10
		PosY = ((Region >> 8) - 92) * 192 + Y / 10
	else:
		PosX = ((Region & 255) - 128) * 192 + X / 10
		PosY = (((Region >> 8) & 0xFF) - 128) * 192 + Y / 10
	return PosX, PosY
	
def GetServerList():
	if BotPath == "" or BotPath == None:
		print('yes')
		return []
	Servers = []
	files = [f for f in listdir(BotPath + f"/Data/") if os.path.isfile(os.path.join(BotPath + f"/Data/", f))]
	for file in files:
		if file.endswith(".db3"):
			try:
				conn = sqlite3.connect(BotPath + f"/Data/{file}")
				if conn:
					result = conn.cursor().execute('SELECT * FROM data WHERE k="path"').fetchone()
					conn.close()
					Servers.append(result[2])
			except Exception as ex:
				print(ex)
	return Servers
	
def ConnectToDatabase():
	files = [f for f in listdir(BotPath + f"/Data/") if os.path.isfile(os.path.join(BotPath + f"/Data/", f))]
	for file in files:
		if file.endswith(".db3"):
			try:
				conn = sqlite3.connect(BotPath + f"/Data/{file}")
				if conn:
					result = conn.cursor().execute('SELECT * FROM data WHERE k="path"').fetchone()
					if result[2] == config.get("Settings","server"):
						return conn
					else:
						conn.close()
			except Exception as ex:
				print(ex)
	return None

def GetNPCsFromdb3():
	global NPCs
	NPCs = {}
	if BotPath == "" or BotPath == None or config.get("Settings","server") == "" or config.get("Settings","server") == None:
		return 
	try:
		conn = ConnectToDatabase()
		if conn:
			result = conn.cursor().execute('SELECT * FROM npcpos')
			for row in result:
				name = conn.cursor().execute('SELECT * FROM monsters WHERE id=?',(int(row[0]),)).fetchone()[2]
				X, Y = ConvertCoords(float(row[2]),float(row[4]),row[1])
				data = {row[0]: {"name": name, "region": row[1], "x": X, "y": Y, "z": int(row[3]), "PointID": 0}}
				NPCs.update(data)
			conn.close()
	except Exception as ex:
		print(ex)
GetNPCsFromdb3()

def GetTeleportsFromdb3():
	global Teleports
	Teleports = {}
	if BotPath == "" or BotPath == None or config.get("Settings","server") == "" or config.get("Settings","server") == None:
		return 
	try:
		conn = ConnectToDatabase()
		if conn:
			result = conn.cursor().execute('SELECT * FROM teleport')
			for row in result:
				#if destination is 0 its not a real teleport
				if row[4] == 0:
					continue
				Destinations = conn.cursor().execute('SELECT * FROM teleport WHERE id=?',(int(row[4]),))
				for dest in Destinations:
					X, Y = int(dest[10]), int(dest[11])
					if X == 0 and Y == 0:
						X, Y = int(dest[8]), int(dest[9])
					DestData = {"name": dest[3], "servername": dest[2], "region": dest[7], "x": X, "y": Y}
					break
				if row[0] in Teleports:
					Teleports[row[0]]["destinations"].append(DestData)
				else:
					X, Y = int(row[10]), int(row[11])
					if X == 0 and Y == 0:
						X, Y = int(row[8]), int(row[9])
					data = {row[0]: {"name": row[3], "servername": row[2], "region": row[7], "x": X, "y": Y, "destinations": [DestData], "PointID": 0}}
					Teleports.update(data)
			conn.close()
	except Exception as ex:
		print(ex)
GetTeleportsFromdb3()

def AddAllTeleports():
	global Teleports
	Loaded = []
	ToBeLoaded = []
	ToBeDeleted = []

	for key, tp in Teleports.items():
		if tp['PointID'] > 0:
			Loaded.append(key)
		if tp['x'] != None and tp['y'] != None:
			if NPCInView(int(tp['x']), int(tp['y'])) and tp['x'] != 0 and tp['y'] != 0 and tp['region'] > 0:
				ToBeLoaded.append(key)
				
	if FocusArea != "World":
		ToBeLoaded = []
		region = GetRegionFromName(FocusArea)
		for key, tp in Teleports.items():
			if tp['region'] == region:
				ToBeLoaded.append(key)
		
	for tp in ToBeLoaded:
		if tp not in Loaded:
			AddTeleportToMap(tp)
			
	for tp in Loaded:
		if tp not in ToBeLoaded:
			ToBeDeleted.append(tp)
	
	for tp in ToBeDeleted:
		try:
			del window['-GRAPH-'].Images[Teleports[tp]['PointID']]
			Teleports[tp]['PointID'] = 0
		except Exception as ex:
			pass		
		
def AddTeleportToMap(id):
	global Teleports
	TeleportInfo = Teleports[id]
	if "fort" in TeleportInfo['servername'].lower():
		icon = FortIcon
	else:
		icon = TeleportIcon
	X, Y = TeleportInfo['x'], TeleportInfo['y']
	if X == None or Y == None:
		return
	PointX = ((X-90 / 2**ZoomLevel) / (192/ImageSize)) - GlobalZero[0]
	PointY = ((Y+90 / 2**ZoomLevel) / (192/ImageSize)) - GlobalZero[1]
	ID = graph.draw_image(data=icon, location=(PointX,PointY))
	graph.bring_figure_to_front(ID)
	Teleports[id]["PointID"] = ID

	
def GetTPsNearClick(X, Y, size):
	Figures = []
	coords = []
	for key, npc in Teleports.items():
		npcX, npcY = npc['x'], npc['y']
		if npcX != None or npcY != None:
			if Inside(X, Y, size, npc['x'], npc['y']):
				Figures.append(npc)
				coords.append((npc['x'],npc['y']))

	if coords:
		cloest_x, cloest_y = min(coords, key=lambda point: math.hypot(X-point[0], Y-point[1]))
	for fig in Figures:
		if fig['x'] == cloest_x and fig['y'] == cloest_y:
			return fig
	return None	
	
def GetTeleportDestinationNames():
	names = []
	for tp in destinations:
		names.append(tp['name'])
	return names	
	
TrainingAreaID = 0
def AddTrainingArea():
	global TrainingAreaID
	try:
		graph.delete_figure(TrainingAreaID)
	except Exception as ex:
		print(ex)
	TrainingArea = Characters[SelectedUsername]['trainingarea']
	PointX = (TrainingArea['x'] / (192/ImageSize)) - GlobalZero[0]
	PointY = (TrainingArea['y'] / (192/ImageSize)) - GlobalZero[1]
	Radius = (TrainingArea['radius'] / (192/ImageSize))
	TrainingAreaID = graph.draw_circle(center_location=(PointX,PointY), radius=Radius, fill_color=None, line_color="blue", line_width=1)
	graph.bring_figure_to_front(TrainingAreaID)
	
Mobs = []
def AddMonsters():
	global Mobs
	for ID in Mobs:
		try:
			del window['-GRAPH-'].Images[ID]
			Mobs.remove(ID)
		except Exception as ex:
			print(ex)
	Monsters = Characters[SelectedUsername]['monsters']
	for key, mob in Monsters.items():
		PointX = ((mob['x']) / (192/ImageSize)) - GlobalZero[0]
		PointY = ((mob['y']) / (192/ImageSize)) - GlobalZero[1]
		ID = graph.draw_image(data=MobIcon, location=(PointX,PointY))
		Mobs.append(ID)
		graph.bring_figure_to_front(ID)

PartyIDs = []
def AddParty():
	global PartyIDs
	for ID in PartyIDs:
		try:
			del window['-GRAPH-'].Images[ID]
			PartyIDs.remove(ID)
		except Exception as ex:
			print(f"party {ex}")
	Party = Characters[SelectedUsername]['party']
	Chars = [char['name'] for key, char in Characters.items()]
	for key, char in Party.items():
		if char['name'] not in Chars: 
			PointX = ((char['x']) / (192/ImageSize)) - GlobalZero[0]
			PointY = ((char['y']) / (192/ImageSize)) - GlobalZero[1]
			ID = graph.draw_image(data=PartyIcon, location=(PointX,PointY))
			PartyIDs.append(ID)
			graph.bring_figure_to_front(ID)
	
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
	if region <= -32750:
		FocusArea = GetNameFromRegion(region)
		XOffset = 5100
		YOffset = 2540
		#job temple
		if region == -32752:
			XOffset = 4800
		#flame mountain
		if region == -32750:
			XOffset = 4760
		#jangan cave
		if region == -32761:
			XOffset = 4980
		if region == -32762:
			XOffset = 5000
		if region == -32763:
			XOffset = 5020		
		if region == -32764:
			XOffset = 5040				
		if region == -32765:
			XOffset = 5060		
		if region == -32766:
			XOffset = 5080	
			
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
	LoadNPCs = True if config.get("Settings","show_npcs") == "True" else False
	if LoadNPCs:
		AddAllNPCs()
	LoadTeleporters = True if config.get("Settings","show_teleporters") == "True" else False
	if LoadTeleporters:
		AddAllTeleports()

def ClearMap():
	global LoadedImages, NPCs, Mobs, PartyIDs, TrainingAreaID
	LoadedImages = []
	graph.erase()
	window['-GRAPH-'].Images = {}
	for key, npc in NPCs.items():
		NPCs[key]['PointID'] = 0
	for key, tp in Teleports.items():
		Teleports[key]['PointID'] = 0	
	TrainingAreaID = 0	
	Mobs = []
	PartyIDs = []
	print(PartyIDs)
	
	
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
	
def GetNPCs():
	list = []
	for key, npc in NPCs.items():
		list.append(npc['name'])
	return sorted(list)

def GetCharsCords(Username):
	for key, char in Characters.items():
		if key == Username:
			return char['x'], char['y'], char['z'], char['region']
			
def GetNPCCords(name):
	for key, npc in NPCs.items():
		if npc['name'] == name:
			return npc['x'], npc['y'], npc['z'], npc['region']
 
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
		if key not in ['monsters', 'party']: #too long to display
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
	AddTrainingArea()
	AddMonsters()
	AddParty()
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
	

dragging = False
NPCPopup = None
graph_right_click_menu = ["",["Set Position", "Move To (Selected Char)"]]
destinations = []
def main():
	global graph, window, CanvasSize, GraphDims, XOffset, YOffset, LoadedScripts, LineIDs, dragging, NPCPopup, destinations, BotPath
	sg.theme(config.get("Settings","Theme"))

	layout2 = sg.Column([
			   [sg.T('Zoom to Town', enable_events=True)],
			   [sg.Combo(values=GetTowns(), size = (30,10), enable_events = True, k='-TOWNCOMBO-' )],
			   [sg.T('Zoom to Area', enable_events=True)],
			   [sg.Combo(values=GetAreas(), size = (30,10), enable_events = True, k='-AREACOMBO-' )],
			   [sg.T('Zoom to Cave', enable_events=True)],
			   [sg.Combo(values=GetCaves(), size = (30,10), enable_events = True, k='-CAVECOMBO-' )],
			   [sg.T('Zoom to NPC/Monster', enable_events=True)],
			   [sg.Combo(values="", size = (30,10), enable_events = True, k='-NPCSCOMBO-' )],
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
				right_click_menu=graph_right_click_menu,
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
	window = sg.Window(f"BunkerMap - v{version}", Layout, keep_on_top=False, finalize=True, return_keyboard_events=True, resizable=True, icon=IconPath)
	graph = window["-GRAPH-"]

	Timer(0.0, AddImages, ()).start()  
	
	LoadNPCs = True if config.get("Settings","show_npcs") == "True" else False
	if LoadNPCs:
		AddAllNPCs()
	LoadTeleporters = True if config.get("Settings","show_teleporters") == "True" else False
	if LoadTeleporters:
		AddAllTeleports()
	
	dragging = False
	start_point = end_point = prior_rect = None
	graph.bind("<Button-3>", "+RIGHT")
	window.bind('<Configure>', "Configure")

	OriginalWindow = window.size
	window["-NPCSCOMBO-"].update(values=GetNPCs())

	while True:
		global GlobalCenter, GlobalZero, LoadedImages, ZoomLevel, FocusArea, ZoomThread, ImageThread, BotPath, SelectedUsername
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
				graph.motion_events = False
				if ImageThread:
					ImageThread.cancel()
					ImageThread = None
				print('dragging')
				start_point = (x, y)
				dragging = True
				lastxy = x, y
				drag_figures = graph.get_figures_at_location((x,y))
				#print(drag_figures)
				for fig in drag_figures:
					Username = GetCharFromFigureId(fig)
					if Username and Username != SelectedUsername:
						SelectedUsername = Username
						UpdateDisplayedChar()
						AddTrainingArea()
				LoadNPCs = True if config.get("Settings","show_npcs") == "True" else False
				if LoadNPCs:
					ID = GetNPCsNearClick(GameCords[0],GameCords[1],55/ZoomLevel)
					if ID != None:
						if NPCPopup != None:
							try:
								window['-GRAPH-'].Images.pop(NPCPopup)
							except Exception as ex:
								pass
						NPCPopup = ID

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
			graph.motion_events = True
			start_point, end_point = None, None 
			dragging = False
			prior_rect = None
			ImageThread = Timer(0.01, AddImages)
			ImageThread.start()
			LoadNPCs = True if config.get("Settings","show_npcs") == "True" else False
			if LoadNPCs:
				AddAllNPCs()
			LoadTeleporters = True if config.get("Settings","show_teleporters") == "True" else False
			if LoadTeleporters:
				AddAllTeleports()
					
		if event.endswith('+RIGHT'):
			x, y = values["-GRAPH-"]
			GameCords = round((GlobalZero[0] + x) * (192/ImageSize),1), round((GlobalZero[1] + y) * (192/ImageSize),1) 
			window["mousepos"].update(value=f"Game Cordinates {GameCords}")
			
			destinations = []
			window['-GRAPH-'].set_right_click_menu(graph_right_click_menu)
			Teleporter = GetTPsNearClick(GameCords[0],GameCords[1],70/ZoomLevel)
			if Teleporter:
				destinations = Teleporter['destinations']
				menu = [f"{Teleporter['name']}", "---",]
				for dest in Teleporter['destinations']:
					menu.append(dest['name'])
				print(menu)
				window['-GRAPH-'].set_right_click_menu(["",menu])
		
		if event in GetTeleportDestinationNames():
			for tp in destinations:
				if tp['name'] == event:
					print(tp)
					ZoomTo(tp['x'],tp['y'],0,tp['region'])
			#print(TpData)
		
		
		
		
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
			x, y = -24200, -90
			z = 0
			if Cave == "Donwhang Dungeon B1":
				z = 25
			if Cave == "Donwhang Dungeon B2":
				z = 30			
			if Cave == "Donwhang Dungeon B3":
				z = 160
			if Cave == "Donwhang Dungeon B4":
				z = 310
			if Cave == "Job Temple":
				x = -21200	  	
			if Cave == "Flame Mountain":
				x = -21200	  
			ZoomTo(x, y, z, Caves[values['-CAVECOMBO-']])
			
		elif event == '-CHARCOMBO-':
			Cords = GetCharsCords(values['-CHARCOMBO-'])
			ZoomTo(Cords[0],Cords[1],Cords[2],Cords[3])

		elif event == '-NPCSCOMBO-':
			Cords = GetNPCCords(values['-NPCSCOMBO-'])
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
				try:
					DetailsPopup(SelectedUsername)
				except Exception as ex:
					print(ex)
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
			LoadNPCs = True if config.get("Settings","show_npcs") == "True" else False
			if LoadNPCs:
				AddAllNPCs()
			LoadTeleporters = True if config.get("Settings","show_teleporters") == "True" else False
			if LoadTeleporters:
				AddAllTeleports()
			
		elif event == 'setting-save':
			BotPath = values['setting-save']['botpath']
			config['Settings']['BotPath'] = values['setting-save']['botpath']
			config['Settings']['Theme'] = values['setting-save']['theme']
			config['Settings']['enable_commands'] = str(values['setting-save']['enable_commands'])
			config['Settings']['show_npcs'] = str(values['setting-save']['show_npcs'])
			config['Settings']['show_teleporters'] = str(values['setting-save']['show_teleporters'])
			config['Settings']['server'] = str(values['setting-save']['-SERVERCOMBO-'])
			with open("BunkerMap.ini", 'w') as f:
				config.write(f)
			LoadNPCs = True if config.get("Settings","show_npcs") == "True" else False
			if LoadNPCs:
				GetNPCsFromdb3()
				window["-NPCSCOMBO-"].update(values=GetNPCs())
			LoadTeleporters = True if config.get("Settings","show_teleporters") == "True" else False
			if LoadTeleporters:
				GetTeleportsFromdb3()
				
		elif event == 'Botpath':
			try:
				path = sg.popup_get_folder('Choose your phBot Folder',icon=IconPath)
				if path != None and path != '':
					config['Settings']['BotPath'] = str(path)
					BotPath = str(path)
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
				print('yes1')
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
				print('yes2')
				CanvasSize = CurrentWindowSize[0]-300,graph.CanvasSize[1]
				GraphDims = CanvasSize[0]/Ratio, CanvasSize[1]/Ratio
				window['-GRAPH-'].set_size(size=(CanvasSize))
				graph.change_coordinates(graph_bottom_left=(0,0), graph_top_right=(GraphDims))
				DeltaX = GraphDims[0] - CurrentGraphSize[0]
				GlobalCenter = GlobalCenter[0] + (DeltaX/2), GlobalCenter[1]
				OriginalWindow = window.size

			#resize y direction only	
			if OriginalWindow[1] != CurrentWindowSize[1]:
				print('yes3')
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
				req = urllib.request.Request('https://raw.githubusercontent.com/Bunker141/BunkerMap/main/BunkerMapPlugin.py', headers={'User-Agent': 'Mozilla/5.0'})
				with urllib.request.urlopen(req) as f:
					lines = str(f.read().decode("utf-8"))
					with open("BunkerMap.py", "w+") as f:
						f.write(lines)
			except Exception as ex:
				print('Error Updating [%s] Please Update Manually or Try Again Later' %ex)
					
		elif event == "About":
			os.startfile("https://www.youtube.com/watch?v=wnedkVrgFF0")

		elif event == '-test-':
			print(len(window['-GRAPH-'].Images))
			
	window.close()

main()
