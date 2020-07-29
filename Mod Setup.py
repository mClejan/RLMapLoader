import os
from shutil import copyfile
import tkinter as tk
import tkinter.messagebox as msg
import json
from functools import partial



def getdrive():
    return os.getcwd()[:2]


def getfilename(files_l, ext):
    # get name of first file ending in ext if one exists, else None
    for s in files_l:
        if s[-len(ext):] == ext:
            return s
    return None


def getdirs():
    global MODS_DIR
    global WORKSHOP_DIR

    try:
        with open("dirs.txt", "r") as f:
            dirs_dict = json.load(f)
            if type(dirs_dict) != dict:
                raise json.JSONDecodeError
            print("dirs loaded from file")
    except (json.JSONDecodeError, FileNotFoundError):
        dirs_dict = default_dirs
        savedirs(mods=dirs_dict["MODS_DIR"], workshop=dirs_dict["WORKSHOP_DIR"])
        print("dirs loaded from defaults")

    MODS_DIR = dirs_dict["MODS_DIR"]
    WORKSHOP_DIR = dirs_dict["WORKSHOP_DIR"]


def savedirs(mods=None, workshop=None):
    dirs_dict = {
        "MODS_DIR": mods if mods != None else MODS_DIR,
        "WORKSHOP_DIR": workshop if workshop != None else WORKSHOP_DIR,
    }

    with open("dirs.txt", "w") as f:
        json.dump(dirs_dict, f)

    print("dirs dict successfully saved")


def warnwrap(f):
    def func(*args, **kwargs):
        ans = msg.showwarning(
            title="Create folder",
            message="Do you want to continue?",
            type=msg.OKCANCEL,
            default=msg.CANCEL,
        )
        if ans == "ok":
            f(*args, **kwargs)
    return func

def multi(*funcs):
    def many_func(*args, **kwargs):
        for f in funcs:
            f(*args, **kwargs)

    return many_func


MODS_DIR = ""
WORKSHOP_DIR = ""


default_dirs = {
    "WORKSHOP_DIR": "C:\\Program Files (x86)\\Steam\\steamapps\\workshop\\content\\252950",
    "MODS_DIR": "C:\\Program Files (x86)\\Steam\\steamapps\\common\\rocketleague\\TAGame\\CookedPCConsole\\mods",
}


class MainApp(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.pack()
        self.mods_dir = tk.StringVar()
        self.mods_dir.set(MODS_DIR)
        self.workshop_dir = tk.StringVar()
        self.workshop_dir.set(WORKSHOP_DIR)
        self.wkfiles = self.getwkfiles()
        self.modfiles = {}
        self.frames = {}
        self.widgets = {}
        self._initwidgets()

    @staticmethod
    def checkdir(widget, *args):
        exists = os.path.isdir(widget.get())
        if exists:
            widget.config(fg="Black")
        else:
            widget.config(fg="Red")

    def copytolabs(self):
        index = self.widgets["lb_wkfiles"].curselection()[0]
        name, path = list(self.wkfiles.items())[index]
        src = os.path.join(path, name)
        dest = self.mods_dir.get()
        if os.path.isdir(dest):
            copyfile(
                src,
                os.path.join(dest, "Labs_Underpass_P.upk")
            )
            msg.showinfo("Copied!", "Map successfully copied to mods")
            return
        msg.showerror("Invalid path", "Mods path is not a directory")

    def getwkfiles(self):
        udks = {}
        walk = os.walk(self.workshop_dir.get())
        try:
            next(walk)
        except StopIteration:
            return udks
        for t in walk:
            name = getfilename(t[2], ".udk")
            if name:
                udks[name] = t[0]
        return udks

    def fillwslist(self, *args):
        self.wkfiles = self.getwkfiles()
        widget = self.widgets["lb_wkfiles"]
        widget.delete(0, tk.END)
        widget.insert(tk.END, *self.wkfiles.keys())

    def getmodfiles(self):
        walk = os.walk(self.mods_dir.get())
        udks = []
        for t in walk:
            name = getfilename(t[2], ".udk")
            if name:
                udks.append({"path": t[0], "name": name})
        return udks

    def savedirs(self, *args):
        savedirs(
            self.mods_dir.get(),
            self.workshop_dir.get(),
        )

    def setdefaults(self, *args):
        self.mods_dir.set(default_dirs["MODS_DIR"])
        self.workshop_dir.set(default_dirs["WORKSHOP_DIR"])

    def makemods(self, *args):
        basename, split = os.path.basename, os.path.split
        path = self.mods_dir.get()
        path = path if basename(path) else split(path)[0]
        if basename(path) != "CookedPCConsole":
            msg.showerror(
                "Can't create folder",
                "Can't create mods folder. Must be located within \\CookedPCConsole"
            )
            return
        try:
            os.mkdir(os.path.join(path, "mods"))
            print("mods directory created")
        except FileNotFoundError as exception:
            msg.showerror("No such directory", exception)
        except FileExistsError:
            msg.showinfo("Already exists", "Mods folder already exists")
            self.mods_dir.set(
                os.path.join(self.mods_dir.get(), "mods")
            )

    def _initwidgets(self):
        self.widgets = {}

        widget = tk.Label(self, text="Workshop dir:")
        widget.grid(row=0, sticky="e")
        self.widgets["l_wkdir"] = widget


        widget = tk.Entry(
            self,
            textvariable=self.workshop_dir,
            width = 60,
        )
        self.workshop_dir.trace("w", multi(
            partial(self.checkdir, widget),
            self.savedirs,
            self.fillwslist,
        ))
        widget.grid(row=0, column=1)
        self.checkdir(widget)
        self.widgets["e_wkdir"] = widget


        widget = tk.Label(self, text="Mods dir:")
        widget.grid(row=1, sticky="e")
        self.widgets["l_mdir"] = widget


        widget = tk.Entry(
            self,
            textvariable=self.mods_dir,
            width = 60,
        )
        self.mods_dir.trace("w", multi(
            partial(self.checkdir, widget),
            self.savedirs,
        ))
        widget.grid(row=1, column=1)
        self.checkdir(widget)
        self.widgets["e_mdir"] = widget


        widget = tk.Button(
            self,
            text="Defaults",
            command=self.setdefaults
        )
        widget.grid(row=0, column=2, rowspan=1, sticky="we")
        self.widgets["b_defaults"] = widget


        widget = tk.Button(
            self,
            text="Make mods folder",
            command=warnwrap(self.makemods)
        )
        widget.grid(row=1, column=2, rowspan=1)
        self.widgets["b_mkmods"] = widget


        frame = tk.Frame(self)
        frame.grid(row=2, columnspan=3)
        self.frames["middle"] = frame
        widget = tk.Label(frame, text="Workshop Files")
        widget.grid(row=0, column=0)
        self.widgets["l_wkfiles"] = widget
        widget = tk.Scrollbar(frame)
        widget.grid(row=1, column=1, sticky="ns")
        self.widgets["s_wkfiles"] = widget
        widget = tk.Listbox(
            frame,
            width = 30,
            selectmode = tk.SINGLE,
            yscrollcommand = self.widgets["s_wkfiles"].set,
        )
        self.widgets["s_wkfiles"].config(command=widget.yview)
        widget.insert(tk.END, *self.wkfiles.keys())
        widget.grid(row=1, column=0)
        self.widgets["lb_wkfiles"] = widget


        widget = tk.Button(
            frame,
            text="Activate",
            command=self.copytolabs,
        )
        widget.grid(row=1, column=2)
        self.widgets["b_tolabs"] = widget



if __name__ == "__main__":
    getdirs()
    root = tk.Tk()
    root.title("RL Mods Setup")
    app = MainApp(root)
    root.mainloop()
