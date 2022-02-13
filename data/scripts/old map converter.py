from tkinter.filedialog import askopenfilename, asksaveasfile
from tkinter import Tk
import json

Tk().withdraw()


def openfile():
    try:
        file_name = askopenfilename(initialdir="data/maps",
                                    filetypes=[("jpeg files", "*.json")],
                                    defaultextension=[("jpeg files", "*.json")])
        f = open(file_name)
        data = json.load(f)
        return data
    except FileNotFoundError:
        openfile()


file = openfile()
new_file = {}
for chunk in file.keys():
    new_file[chunk] = {}
    for i in file[chunk]:
        new_file[chunk][str(i[0][0]) + ";" + str(i[0][1])] = [i[1]]#instead of [0][0][0] put like [i][0][0] or something

file_name = asksaveasfile(initialdir="data/maps",
                          defaultextension=".json",
                          filetypes=[("jpeg files", "*.json")])
f = open(file_name.name, "w")
json.dump(new_file, f)
f.close()
