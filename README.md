BunkerMap is an interactive map of the Silkroad Online world, to be used with phBot. The map is written in python using pysimplegui because well... its simple. It's fairly basic but designed to be able to be expanded on by anyone to fit their needs. You must have the `BunkerMapPlugin` laoded into your bots in order for this to work. 


Libraries Used: pysimplegui, pillow, flask
```
python pip install pysimplegui==4.60.5 pillow flask
```
You can complied into an exe by using a complier, i used pyinstaller with the following command
```
pyinstaller --noconfirm --onefile --windowed --icon "E:/BunkerMap/icon.ico" --name "BunkerMap"  "E:/BunkerMap/map.py"
```

Known Issues:
- Memory leaks.. I have patched a couple of these but there is still some in the GUI lib
- Stange behaviour when moving the map around sometimes.. the GUI doesnt register the mouse up event but i really dont know why. 
