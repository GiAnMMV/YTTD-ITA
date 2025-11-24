import tkinter as tk
from tkinter import ttk as ttk
import tkinter.messagebox
from PIL import ImageTk, Image
import json
import lzstring
import re
from program import decrypter
from io import BytesIO
import pyglet
import os.path
import sys
import win32clipboard as w32cb

GAMEDIR = 'C:\\Program Files (x86)\\Steam\\steamapps\\common\\yttd\\www\\'

if not os.path.isfile('www\\languages\\EN.json'):
    f = open('www\\languages\\EN.json', 'w', encoding = 'utf-8')
    g = open(GAMEDIR + 'languages\\EN.cte', 'r')
    f.write(lzstring.LZString().decompressFromBase64(g.read()))
    f.close()
    g.close()
with open('www\\languages\\EN.json', 'r', encoding = 'utf-8') as f:
    JSON = json.loads(f.read())
    f.close()
with open('www\\languages\\IT.json', 'r', encoding='utf-8') as f:
    JSON_IT = json.loads(f.read())
    f.close()

colors = ('#ffffff', '#20a0d6', '#ff784c', '#66cc40', '#99ccff', '#ccc0ff', '#ffffa0', '#808080', '#c0c0c0', '#2080cc', '#ff3810', '#00a010', '#3e9ade', '#a098ff', '#ffcc20', '#000000', '#84aaff', '#ffff40', '#ff2020', '#202040', '#e08040', '#f0c040', '#4080c0', '#40c0f0', '#80ff80', '#c08080', '#8080ff', '#ff80ff', '#00a040', '#00e060', '#a060e0', '#c080ff')
negative_colors = ('#000000', '#000000', '#000000', '#000000', '#000000', '#000000', '#000000', '#ffffff', '#000000', '#ffffff', '#ffffff', '#ffffff', '#000000', '#000000', '#000000', '#ffffff', '#000000', '#000000', '#ffffff', '#ffffff', '#000000', '#000000', '#ffffff', '#000000', '#000000', '#000000', '#000000', '#000000', '#ffffff', '#000000', '#ffffff', '#000000')
hidden = {}
edited = False

pyglet.options['win32_gdi_font'] = True
pyglet.font.add_file(GAMEDIR + 'fonts\\mplus-1m-regular.ttf')

def edit(b):
    global edited
    if b and not edited:
        root.title('*'+root.title())
    elif not b and edited:
        root.title(root.title()[1:])
    edited = b


CUSTOM_FORMAT_ID = 9999
def get_clipboard(formatted=True):
    clipboard_dict = {}
    
    w32cb.OpenClipboard()
    
    cf = [w32cb.EnumClipboardFormats(0)]
    while cf[-1]:
        cf.append(w32cb.EnumClipboardFormats(cf[-1]))
    cf.pop()
    
    res = ''
    if CUSTOM_FORMAT_ID in cf and formatted:
        res = w32cb.GetClipboardData(CUSTOM_FORMAT_ID).decode('utf-8')
    elif w32cb.CF_UNICODETEXT in cf:
        res = w32cb.GetClipboardData(w32cb.CF_UNICODETEXT)
    elif w32cb.CF_TEXT in cf:
        res = w32cb.GetClipboardData(w32cb.CF_TEXT).decode('utf-8')

    w32cb.CloseClipboard()
    return res

def set_clipboard(txt_rich, txt_plain):
	w32cb.OpenClipboard()
	w32cb.EmptyClipboard()
	w32cb.SetClipboardData(w32cb.CF_TEXT, txt_plain.encode('utf-8'))
	w32cb.SetClipboardData(w32cb.CF_UNICODETEXT, txt_plain)
	w32cb.SetClipboardData(CUSTOM_FORMAT_ID, txt_rich.encode('utf-8'))
	w32cb.CloseClipboard()

root = tk.Tk()
root.title('Text Editor')
root.minsize(800, 600)
root.resizable(False, False)

#ttk.Style().theme_use('default')

icons = Image.open(BytesIO(decrypter(GAMEDIR + 'img\\system\\IconSet.rpgmvp')))
iconsW, iconsH = (i//32 for i in icons.size)
iconImages = {}

texts = [0,0]

for a in range(2):
    texts[a] = tk.Text(root, width=56, height=4, wrap='none', name=f'text{a}')
    texts[a].config(font=('M+ 1m regular', -28), bg='black', fg='white', insertbackground='white')
    texts[a].bindtags(('.text', 'Text', 'cursor', '.', 'all'))
    texts[a].pack()

    texts[a].tag_config('hidden', elide=1)

    for c in range(len(colors)):
        texts[a].tag_config('C'+str(c), foreground=colors[c])

    texts[a].tag_config('removed', elide=1)
    texts[a].tag_config('inserted')
    
    texts[a].undo_stack = []
    texts[a].redo_stack = []
    texts[a].undo_lastaction = ''

color = tk.IntVar(root, 0, 'color')
size = tk.IntVar(root, 28, 'size')

hidden_box = ttk.Entry(root, name='hidden_box')
hidden_box.config(font=('Courier', -20), width=5)
hidden_box.pack()

hidden_box_2 = ttk.Spinbox(root, name='hidden_box_2')
hidden_box_2.config(font=('Courier', -20), width=5)
hidden_box_2.pack()

def hidden_box_enter(event):
    text = texts[0]
    undo_new('inserted')
    beg = text.index('insert')
    
    code = hidden_box.get()
    param = hidden_box_2.get()
    if reg.fullmatch(f'{code}' + (param and F'[{param}]' or '')):
        insert_hidden(code, param)
    hidden_box.delete('@0', tk.END)
    hidden_box_2.delete('@0', tk.END)
    update_hidden()
    text.focus_set()
    
    text.tag_add('inserted', beg, 'insert')
    
hidden_box.bind('<Return>', hidden_box_enter)
hidden_box_2.bind('<Return>', hidden_box_enter)

sizes = []
def set_size(s):
    if not s in sizes:
        for text in texts:
            text.tag_config('size'+str(s), font=('M+ 1m regular', -s))
        sizes.append(s)
    size.set(s)
    return s

def change_text(dialog, text=texts[0]):
    for h in list(hidden):
        del hidden[h]
    text.delete('1.0', 'end')
    color.set(0)
    size.set(28)
    text.undo_stack = []
    text.redo_stack = []
    text.undo_lastaction = ''
    set_text(dialog, tk.END, text)

reg = re.compile(r'([\$\.\|\^!><\{\}\\]|([A-Z]+))(?(2)\[([^\[\]]+)\]|)', re.I)
def insert_hidden(code, param='', index=tk.INSERT, text=texts[0]):
    match code.upper():
        case '\\':
            text.insert(index, '\\', ('C'+str(color.get()), 'size'+str(size.get())))
        case '{':
            if size.get() <= 96:
                set_size(size.get() + 12)
        case '}':
            if size.get() >= 24:
                set_size(size.get() - 12)
        case 'C':
            try:
                if int(param) < len(colors):
                    color.set(int(param))
            except: pass
        case 'FS':
            if param:
                set_size(int(param))
        case 'I':
            p = int(param)
            if not p in iconImages:
                x = p % iconsW * 32
                y = p // iconsW * 32
                iconImages[p] = ImageTk.PhotoImage(icons.crop([x, y, x+32, y+32]), name=f'icon{p}')
            text.image_create(index, image = iconImages[p])
        case _:
            text.insert(index, '\u035C', ('C'+str(color.get()), 'size'+str(size.get())))
            text.insert(index, code, 'hidden')
            if param:
                text.insert(index, f'[{param}]', 'hidden')

def set_text(dialog, index, text=texts[0]):
    dialog = dialog.replace('\\', '\x1b');
    dialog = dialog.replace('\x1b\x1b', '\\');

    l = 0
    while l < len(dialog):
        if dialog[l] == '\x1b':
            l += 1
            code, _, param = reg.findall(dialog, l)[0]
            l += len(reg.match(dialog, l)[0])
            insert_hidden(code, param, index, text)
        else:
            text.insert(index, dialog[l], ('C'+str(color.get()), 'size'+str(size.get())))
            l += 1

change_text('\\.Ciao, come \\C[10]stai\\C[0]?\\!\\!\nIo \\fs[40]benone\\}, grazie!\\I[16]')
change_text('\\.Hi, how are you \\C[10]doin\'\\C[0]?\\!\\!\nI\'m \\fs[40]real\\} good, thanks!\\I[16]', texts[1])
texts[1].config(state="disabled")
def get_text(text, beg = '1.0', end = 'end-1c', tags = True):
    if text.compare(end, '==', 'end'):
        end += '-1c'
    
    dump = text.dump(beg, end)
    for t in text.tag_names(beg):
        if not ('tagon', t, beg) in dump:
            dump.insert(0, ('tagon', t, beg))
        
    if tags:
        col = 0
        size = 28
    else:
        for t in text.tag_names(beg):
            if t[0] == 'C':
                col = int(t[1:])
            elif t[:4] == 'size':
                size = int(t[4:])
    
    res = ''
    for a in dump:
        match a[0]:
            case 'tagon':
                if a[1][0] == 'C':
                    if int(a[1][1:]) != col:
                        col = int(a[1][1:])
                        res += '\\C[' + str(col) + ']'
                elif a[1][:4] == 'size':
                    s = int(a[1][4:])
                    if s != size:
                        if not (size-s) % 12:
                            if (size-s) // 12 > 0:
                                res += '\\}' * ((size-s) // 12)
                            else:
                                res += '\\{' * (-(size-s) // 12)
                        else:
                            res += '\\fs[' + str(s) + ']'
                        size = s
                elif a[1] == 'hidden':
                    res += '\\'
            case 'image':
                res += '\\I[' + a[1][4:] + ']'
            case 'text':
                res += a[1].replace('\u035C', '').replace('\\', '\\\\')
    return res

def update_tags(text=texts[0]):
    global color
    global size
    
    for i in text.tag_names('insert-1displayindices'):
        if i[0] == 'C':
            color.set(i[1:])
        elif i[:4] == 'size':
            size.set(i[4:])

def update_hidden(text=texts[0]):
    hidden_box.delete('@0', tk.END)
    hidden_box_2.delete('@0', tk.END)
    if text.get('insert-1displayindices') == '\u035C' and text.index('insert') != '1.0':
        beg, end = text.tag_nextrange('hidden', 'insert-1displayindices')
        code, _, param = reg.findall(text.get(beg, end))[0]
        hidden_box.insert('@0', code)
        hidden_box_2.insert('@0', param)

def update_all(*event):
    update_tags()
    update_hidden()
root.bind_class('cursor', '<<CursorMoved>>', update_all)

def text_copy(event):
    text = event.widget
    if text.tag_nextrange('sel', '1.0'):
        txt_rich = get_text(text, 'sel.first', 'sel.last')
        txt_plain = text.selection_get().replace('\u035C', '')
        set_clipboard(txt_rich, txt_plain)
root.bind_class('Text', '<<Copy>>', text_copy)

def text_paste(event):
    text = event.widget
    color.set(0)
    size.set(28)
    if text.tag_nextrange('sel', '1.0'):
        text_removed(event)

    undo_new('inserted')
    beg = text.index('insert')
    set_text(get_clipboard(not (event.state & 1)), 'insert', text)
    text.tag_add('inserted', beg, 'insert')
    cursor_moved(event)
root.bind_class('Text', '<<Paste>>', text_paste)
root.bind_class('Text', '<Control-V>', text_paste)

def text_cut(event):
    text_copy(event)
    text_delete(event)
root.bind_class('Text', '<<Cut>>', text_cut)

def text_backspace(event):
    text = event.widget
    undo_new('backspaced')
    if text.tag_nextrange('sel', '1.0'):
        text_removed(event)
        cursor_moved(event)
    else:
        text.tag_add('removed', 'insert-1displayindices', 'insert')
    update_all()
root.bind_class('Text', '<BackSpace>', text_backspace)

def text_delete(event):
    text = event.widget
    if text.tag_nextrange('sel', '1.0'):
        text_removed(event)
        cursor_moved(event)
    else:
        undo_new('deleted')
        text.tag_add('removed', 'insert', 'insert+1displayindices')
        text.mark_set('insert', 'removed.last')
root.bind_class('Text', '<Delete>', text_delete)

def add_hidden_1(event):
    hidden_box.delete('@0', tk.END)
    hidden_box.focus_set()
root.bind_class('Text', '<\\>', add_hidden_1)

root.unbind_class('Text', '<<PasteSelection>>')
root.unbind_class('Text', '<Control-Button-1>')

def undo_new(action, text=texts[0]):
    res = text.undo_lastaction != action
    if res:
        last0 = last1 = None
        if text.tag_nextrange('removed', '1.0'):
            beg, end = text.index('removed.first'), text.index('removed.last')
            text.tag_remove('removed', beg, end)
            last0 = (beg, end, text.dump(beg, end), text.tag_names(beg))
            text.delete(beg, end)
        if text.tag_nextrange('inserted', '1.0'):
            beg, end = text.index('inserted.first'), text.index('inserted.last')
            text.tag_remove('inserted', beg, end)
            last1 = (beg, end, text.dump(beg, end), text.tag_names(beg))
        if last0 or last1:
            text.undo_stack.append((last0, last1))
            if text.redo_stack:
                text.redo_stack = []
        text.undo_lastaction = action
    return res

def cursor_moved(event):
    text = event.widget
    undo_new('moved', text)
root.bind_class('Text', '<<CursorMoved>>', cursor_moved)

def text_removed(event):
    text = event.widget
    undo_new('inserted')
    beg = text.index('sel.first')
    end = text.index('sel.last')
    text.tag_remove('sel', '1.0', tk.END)
    if text.compare(end, '==', 'end'):
        end += '-1c'
    text.tag_add('removed', beg, end)
    text.tag_add('sel2', beg, end)
    text.mark_set('insert', end)
root.bind_class('Text', '<<TextRemoved>>', text_removed)

def text_inserted(event):
    undo_new('inserted')
    event.widget.tag_add('inserted', 'insert-1displayindices', 'insert')
root.bind_class('Text', '<<TextInserted>>', text_inserted)


def text_undo_redo(action, event):
    #Undo: True
    #Redo: False
    text = event.widget
    cursor_moved(event)
    if action:
        stack = text.undo_stack
        stack2 = text.redo_stack
        n0, n1 = 0, 1
    else:
        stack = text.redo_stack
        stack2 = text.undo_stack
        n0, n1 = 1, 0
    
    if len(stack):
        last = stack[-1]
        l0 = last[n0]
        l1 = last[n1]
        stack2.append(last)
        del stack[-1]

        if l1:
            text.delete(l1[0], l1[1])

        if l0:
            tags = list(l0[3])
            for t in l0[2]:
                match t[0]:
                    case 'tagon':
                        tags.append(t[1].replace('sel2', 'sel'))
                    case 'tagoff':
                        try: tags.remove(t[1].replace('sel2', 'sel'))
                        except: pass
                    case 'text':
                        text.insert(t[2], t[1], tuple(tags))
    update_all()

def text_undo(event):
    text_undo_redo(True, event)
root.bind_class('Text', '<<Undo>>', text_undo)

def text_redo(event):
    text_undo_redo(False, event)
root.bind_class('Text', '<<Redo>>', text_redo)


def show_hide_elided_text(event):
    if event.type == tk.EventType.KeyPress:
        event.widget.tag_config('hidden', elide = 0, underline = 1)
    elif event.type == tk.EventType.KeyRelease:
        event.widget.tag_config('hidden', elide = 1, underline = 0)
root.bind_class('Text', '<Alt-q>', show_hide_elided_text)
root.bind_class('Text', '<Alt-KeyRelease-q>', show_hide_elided_text)

root.tk.eval('''
proc ::tk::TextInsert {w s} {
    if {$s eq "" || [$w cget -state] eq "disabled"} {
	return
    }
    global color
    global size
    set compound 0
    if {[TextCursorInSelection $w]} {
	set oldSeparator [$w cget -autoseparators]
	if {$oldSeparator} {
	    $w configure -autoseparators 0
	    $w edit separator
	    set compound 1
	}
	event generate $w <<TextRemoved>>
    }
    $w insert insert $s [list C$color size$size]
    event generate $w <<TextInserted>>
    $w see insert
    if {$compound && $oldSeparator} {
	$w edit separator
	$w configure -autoseparators 1
    }
}


proc ::tk::TextSetCursor {w pos} "
[info body tk::TextSetCursor]
event generate \$w <<CursorMoved>>
"

proc ::tk::TextKeySelect {w new} "
[info body tk::TextKeySelect]
event generate \$w <<CursorMoved>>
"

proc ::tk::TextButton1 {w x y} "
[info body tk::TextButton1]
event generate \$w <<CursorMoved>>
"

proc ::tk::TextSelectTo {w x y {extend 0}} [
    string map {"$w mark set insert $cur" "if {[$w compare $cur > $anchorname]} {$w mark set insert $last} else {$w mark set insert $first}"} [info body tk::TextSelectTo]
]


bind Text <ButtonRelease-1> {
    tk::CancelRepeat
    set anchorname [tk::TextAnchor %W]
    set cur [tk::TextClosestGap %W %x %y]
    if {[%W compare $cur > $anchorname]} {
        catch {%W mark set $anchorname sel.first}
    } else {
        catch {%W mark set $anchorname sel.last}
    }
}

bind Text <<SelectAll>> {
    %W tag add sel 1.0 end-1c
    %W mark set insert 1.0
    event generate %W <<CursorMoved>>

    tk::CancelRepeat
    set anchorname [tk::TextAnchor %W]
    set cur [tk::TextClosestGap %W %x %y]
    catch {%W mark set $anchorname sel.last}
}

bind Text <<PrevChar>> {
    if {[%W tag nextrange sel 1.0 end] eq ""} {
        tk::TextSetCursor %W insert-1displayindices
    } else {
        tk::TextSetCursor %W sel.first
    }
}
bind Text <<NextChar>> {
    if {[%W tag nextrange sel 1.0 end] eq ""} {
        tk::TextSetCursor %W insert+1displayindices
    } else {
        tk::TextSetCursor %W sel.last
    }
}

''')

def change_size(n, text=texts[0]):
    try:
        sel_start, sel_end = text.tag_ranges('sel')
        for t in text.tag_names():
            if t[:4] == 'size':
                text.tag_remove(t, sel_start, sel_end)
        text.tag_add('size'+str(set_size(n)), sel_start, sel_end)
    except:
        text.tk.call('set', 'size', str(set_size(n)))
    text.focus()


format_frame = tk.Frame(root, name = 'format_frame')
format_frame.pack()

color_button = tk.Button(format_frame, bg='white', name='colorbutton', width=2)
color_button.configure(textvariable = color)
def color_button_update(u0, u1, u2):
    color_button.configure(bg = colors[color.get()])
    color_button.configure(fg = negative_colors[color.get()])
color.trace('w', color_button_update)
color_button.pack(side = tk.LEFT, padx = 10)

sizebox = ttk.Combobox(format_frame, width=3, values = (28, 40, 52, 64, 76, 88), name='sizebox')
sizebox.set(28)
sizebox.configure(textvariable = size)
sizebox.bind('<<ComboboxSelected>>', lambda i=1: change_size(int(sizebox.cget("values")[sizebox.current()])))
sizebox.bind('<Return>', lambda i: change_size(int(sizebox.get())))
sizebox.pack(side = tk.LEFT, padx = 10)

def open_colorpicker():
    colorpicker = tk.Toplevel()
    colorpicker.transient(root)
    colorpicker.grab_set()
    root.attributes('-disabled', 1)
    colorpicker.title('Color Picker')
    colorpicker.resizable(False, False)
    colorpicker.focus()
    buttons = []
    for c in colors:
        buttons.append(tk.Button(colorpicker, text=str(len(buttons)), width=2, bg=c, fg=negative_colors[len(buttons)], command=lambda i=len(buttons): change_color(f'C{i}', colorpicker)))
        buttons[-1].grid(row=(len(buttons)-1)//8, column=(len(buttons)-1)%8)
    colorpicker.bind('<Destroy>', lambda i=0: root.attributes('-disabled', 0))
    colorpicker.update_idletasks()
    x = root.winfo_x() + root.winfo_width()//2 - colorpicker.winfo_width()//2
    y = root.winfo_y() + root.winfo_height()//2 - colorpicker.winfo_height()//2
    colorpicker.geometry(f'+{x}+{y}')
color_button.config(command = open_colorpicker)

def change_color(n, win=None):
    try:
        sel_start, sel_end = text.tag_ranges('sel')
        for t in text.tag_names():
            if t[0] == 'C':
                text.tag_remove(t, sel_start, sel_end)
        text.tag_add(n, sel_start, sel_end)
    except:
        color.set(n[1:])
        text.tk.call('set', 'color', n[1:])
    text.focus()
    win.destroy()

class Tree():
    ids = {}
    def __init__(self, item1, item2, iid, parent):
        self.parent = parent
        self.iid = iid
        self.children = {}
        self.type = type(item1)

        self.item1 = {}
        self.item2 = {}
        self.completed = set()
        if self.type == list: keys = range(len(item1))
        elif self.type == dict: keys = item1

        for i in keys:
            child = tree.insert(self.iid, 'end', text=str(i))
            self.children[i] = child
            self.ids[child] = (self, i)
            try: l = item2[i]
            except: l = None
            if isinstance(item1[i], (dict, list)):
                obj = Tree(item1[i], l, child, self)
                self.item1[i] = obj
                if obj.item2: self.item2[i] = obj
            else:
                self.item1[i] = item1[i]
                if l is not None: self.item2[i] = item2[i]
            self.update(i)
    
    def __getitem__(self, i):
        if i in self.item2:
            return self.item2[i]
        elif i in self.item1:
            return self.item1[i]

    def __delitem__(self, indexes):
        def __delchildren(self, i):
            if type(self[i]) is Tree:
                for a in dict(self[i].item2):
                    __delchildren(self[i], a)
            del self.item2[i]
            self.update(i)

        if type(indexes) is not list:
             indexes = (indexes,)

        for i in indexes:
            if i in self.item2:
                __delchildren(self, i)

        obj = self
        while obj.parent:
            ind = list(obj.parent.item1.keys())[list(obj.parent.item1.values()).index(obj)]
            obj = obj.parent
            if not obj[ind].item2 and ind in obj.item2:
                del obj.item2[ind]
            obj.update(ind)
    
    def __setitem__(self, i, v):
        obj = self
        ind = i
        while obj:
            if type(obj[ind]) is Tree:
                obj.item2[ind] = obj.item1[ind]
            elif type(obj[ind]) is str:
                obj.item2[ind] = v
            obj.update(ind)
            try: ind = list(obj.parent.item1.keys())[list(obj.parent.item1.values()).index(obj)]
            except: pass
            obj = obj.parent
        self.update(i)
    
    def __str__(self):
        return f'{self.item2}'
    
    def __repr__(self):
        return f'{self.item2}'
    
    def extract(self):
        if not self.item2:
            return None
        else:
            if self.type is list:
                res = [None] * len(self.item1)
            elif self.type is dict:
                res = {}
            for a in self.item1:
                if a in self.item2:
                    try:
                        b = self.item2[a].extract()
                        if b: res[a] = b
                    except: res[a] = self.item2[a]
            return res

    def extract_merged(self):
        if self.type is list:
            res = [None] * len(self.item1)
        elif self.type is dict:
            res = {}
        for a in self.item1:
            try: res[a] = self[a].extract_merged()
            except: res[a] = self[a]
        return res

    def update(self, i):
        tags = []
        if type(self[i]) is not Tree:
            values = '{'+self[i].replace('\n', '\u21b5')+'}'
            tags.append('string')
            if i in self.item2:
                tags.append('completed')
                self.completed.add(i)
            elif i in self.completed:
                self.completed.remove(i)
        else:
            l1 = len(self.item1[i].item1)
            try: l2 = len(self.item1[i].completed)
            except: l2 = 0
            if self[i].type is dict:
                values = f'{{{{{l2}/{l1}}}}}'
            elif self[i].type is list:
                values = f'[{l2}/{l1}]'
            if l2 == l1:
                tags.append('completed')
                self.completed.add(i)
            else:
                if i in self.completed:
                    self.completed.remove(i)
                if self[i].item2:
                    tags.append('translated')
                
        tree.item(self.children[i], values = values, tags = tags)
    
    def focus():
        return Tree.ids[tree.focus()]

    def selection():
        return (Tree.ids[a] for a in tree.selection())

    def search(self, s):
        if search_lang.get() == 0:
            lang = self.item2
        else:
            lang = self.item1
        tree['displaycolumns'] = ('search', 'value')
        res = 0
        for a in self.item1:
            if a in lang:
                if type(lang[a]) == Tree:
                    sub_search = lang[a].search(s)
                    res += sub_search
                    if not sub_search:
                        tree.detach(self.children[a])
                else:
                    if ((lang[a].find(s) + 1 and search_case_var.get()) or
                        (lang[a].lower().find(s.lower()) + 1 and not search_case_var.get()) or
                        (re.search(s, lang[a]) and search_regex_var.get() and search_case_var.get()) or
                        (re.search(s, lang[a], re.I)) and search_regex_var.get() and not search_case_var.get()):
                        res += 1
                    else:
                        #tree.selection_remove(self.children[a])
                        tree.detach(self.children[a])
            else:
                tree.detach(self.children[a])
        tree.set(self.iid, 'search', f'{res}')
        return res
    
    def cancel_search(self):
        if Tree.searching:
            tree['displaycolumns'] = 'value'
            keys = list(self.item1.keys())
            for a in keys:
                tree.move(self.children[a], self.iid, keys.index(a))
                if type(self[a]) == Tree:
                    self[a].cancel_search()

    searching = False
        
tree = ttk.Treeview(root, selectmode='browse', columns=['value', 'search'], name='tree', height=24)
tree.yview_scroll = True
tree.column('value', width=600)
tree.column('search', width=30)
tree['displaycolumns'] = 'value'
tree.tag_configure('completed', background='light green')
tree.tag_configure('translated', background='gold')
tree.editing = False
t = Tree(JSON, JSON_IT, '', None)
tree.pack()

def search_binding(event):
    t.cancel_search()
    s = event.widget.get()
    if s:
        t.search(s)
        Tree.searching = True
    else:
        Tree.searching = False

def destroy_search_window(event):
    global search_window
    search_window = None
    if event.widget == event.widget.winfo_toplevel():
        t.cancel_search()
        Tree.searching = False
    tree.see(tree.focus())


search_window = None
search_case_var = tk.BooleanVar()
search_regex_var = tk.BooleanVar()
search_lang = tk.IntVar()
def create_search_window(event):
    global search_window
    if not search_window:
        search_window = tk.Toplevel(root, name='search_window')
        search_window.title('Search...')
        search_window.resizable(False, False)
        search_window.wm_attributes('-toolwindow', True)
        
        search_entry = tk.Entry(search_window, name='search_entry')
        search_entry.pack()
        search_entry.bind('<Return>', search_binding)

        global search_case_var
        search_case = tk.Checkbutton(search_window, text='Case sensitive', variable = search_case_var)
        search_case.pack()

        global search_regex_var
        search_regex = tk.Checkbutton(search_window, text='Regular expression', variable = search_regex_var)
        search_regex.pack()
        
        global search_lang
        search_radio1 = tk.Radiobutton(search_window, text='Translated', variable = search_lang, value = 0)
        search_radio1.pack(side = tk.LEFT)
        search_radio2 = tk.Radiobutton(search_window, text='Original', variable = search_lang, value = 1)
        search_radio2.pack(side = tk.LEFT)
        
        search_window.bind('<Destroy>', destroy_search_window)
    search_window.tk.call('focus', '.search_window.search_entry')
tree.bind_class('Treeview', '<Control-f>', create_search_window)

def focus(event):
    if tree.editing and root.focus_get() == tree:
        cursor_moved(event)
        t, i = Tree.ids[tree.editing]
        t[i] = get_text(texts[0])
        tree.editing = False
        edit(True)
root.bind_class('Text', '<FocusOut>', focus)

def open_dialog(event):
    if tree.tag_has('string', tree.focus()):
        t, i = Tree.focus()
        texts[0].config(state="normal")
        change_text(t[i])
        texts[1].config(state="normal")
        change_text(t.item1[i], texts[1])
        texts[1].config(state="disabled")
        tree.editing = tree.focus()
    else:
        for a in range(2):
            texts[a].config(state="normal")
            change_text('', texts[a])
            texts[a].config(state="disabled")
        tree.editing = False
tree.bind('<<TreeviewSelect>>', open_dialog)

def edit_dialog(event):
    texts[0].focus_set()
    texts[0].event_generate('<<SelectAll>>')
tree.tag_bind('string', '<Return>', edit_dialog)
tree.tag_bind('string', '<Double-Button-1>', edit_dialog)

def set_dialog(event):
    if tree.editing:
        tree.focus(tree.next(tree.editing) or tree.editing)
        tree.see(tree.focus())
        tree.selection_set(tree.focus())
        text = texts[0]
        cursor_moved(event)
        tree.focus_set()
root.bind_class('Text', '<Control-Return>', set_dialog)

def esc_dialog(event):
    if tree.editing:
        tree.editing = False
        tree.selection_set(tree.focus())
        cursor_moved(event)
        tree.focus_set()
root.bind_class('Text', '<Escape>', esc_dialog)

def del_dialog(event):
    for a in Tree.selection():
        Tree.__delitem__(*a)
    edit(True)
    open_dialog(event)
tree.tag_bind('string', '<BackSpace>', del_dialog)
tree.tag_bind('string', '<Delete>', del_dialog)
tree.bind_class('Treeview', '<BackSpace>', del_dialog)


def select(f):
    selection = tree.selection()
    if len(selection) < 2:
        tree.cur_sel = tree.focus()
    new = f(tree.cur_sel)
    if new:
        tree.selection_add(new)
        if new in selection:
            tree.selection_remove(tree.cur_sel)
        tree.see(new)
        tree.cur_sel = new

def select_down(event):
    select(tree.next)
tree.bind_class('Treeview', '<<SelectNextLine>>', select_down)

def select_up(event):
    select(tree.prev)
tree.bind_class('Treeview', '<<SelectPrevLine>>', select_up)

def select_toggle(event):
    item = tree.identify('item', event.x, event.y)
    if tree.parent(item) == tree.parent(tree.focus()):
        tree.selection_add(item)
    else:
        tree.selection_set(item)
    tree.focus(item)
tree.bind_class('Treeview', '<<ToggleSelection>>', select_toggle)

def select_all(event):
    children = tree.get_children(tree.parent(tree.focus()))
    tree.selection_set(children)
    tree.focus(children[-1])
tree.bind_class('Treeview', '<<SelectAll>>', select_all)

#---------------------------#

def save(*event):
    d = t.extract()
    with open('www\\languages\\IT.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(d, indent=2, ensure_ascii=False))
        f.close()
    edit(False)
root.bind('<Control-s>', save)

def exported_save(*event):
    with open(GAMEDIR + 'languages\\IT.cte', 'w') as f:
        f.write(lzstring.LZString().compressToBase64(json.dumps(t.extract_merged())))
        f.close()
    save()
root.bind('<Control-S>', exported_save)

def on_close():
    if edited:
        m = tk.messagebox.askyesnocancel('Save On Close','Do you want to save before closing?')
    else:
        m = False
    if m is not None:
        if m is True:
            exported_save()

        if sys.platform == 'win32':
            from ctypes import windll
            u32 = windll.user32
            u32.OpenClipboard(0)
            u32.GetClipboardData(1)
            u32.CloseClipboard()

        root.destroy()
root.protocol('WM_DELETE_WINDOW',on_close)

root.mainloop()
