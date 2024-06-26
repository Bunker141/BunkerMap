BunkerMap is an interactive map of the Silkroad Online world, to be used with phBot. The map is written in python using pysimplegui because well... its simple. It's fairly basic but designed to be able to be expanded on by anyone to fit their needs. You must have the `BunkerMapPlugin` loaded into your bots in order for this to work. Its fully resizeable to whatever size you'd like.

It also allows communication with bots to execute commands, I have added a few examples. You can also right click on the map to change the training area of a character and move to where you clicked... pretty cool. 

![alt text](https://d.phx-cdn.com/original/2X/8/809b635e12f5e5d6c86941b9296f10075e642cfe.jpeg)
![alt text](https://d.phx-cdn.com/original/2X/a/a9fb62be65f203898f1301bcd8106d4b439e296f.jpeg)

Plugin Download: [[Link] ](https://raw.githubusercontent.com/Bunker141/BunkerMap/main/BunkerMapPlugin.py) Right click > save as .py

Libraries Used: pysimplegui, pillow, flask
```
python pip install pysimplegui==4.60.5 pillow flask
```
You can complied into an exe by using a complier, i used pyinstaller with the following command
```
pyinstaller --noconfirm --onefile --windowed --icon "E:/BunkerMap/icon.ico" --name "BunkerMap"  "E:/BunkerMap/map.py"
```

Known Issues:
- Memory leaks.. I have patched a couple of these but there is still some in the GUI lib (FIXED)
- Stange behaviour when moving the map around sometimes.. the GUI doesnt register the mouse up event but i really dont know why. (FIXED)

If you're look into to just use the program and not make any changes. I have complied a verison in python 3.8 so it can be used on windows 7 without any issues. It can be found here.

 **NOTE: The map will not load until you have set your bot folder in the settings and you MUST have the map installed in the phBot folder you select, it gets the images from this folder.**

[https://mega.nz/file/CTYg3TpD#9rqFwGviOGZeWZlf3QFhV1p7dB2eusTVP3Wttt7fEBg](https://mega.nz/file/GCQimZiS#N8aIDRFKl3eKuTh1B9N92oXOh5B_F7PUei17Uc98HXg)

Forum Link:
https://forum.projecthax.com/t/bunkermap/26077
