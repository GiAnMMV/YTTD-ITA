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

undo_stack = []
redo_stack = []
undo_lastaction = ''

pyglet.options['win32_gdi_font'] = True
pyglet.font.add_file(GAMEDIR + 'fonts\\mplus-1m-regular.ttf')

def edit(b):
    global edited
    if b and not edited:
        root.title('*'+root.title())
    elif not b and edited:
        root.title(root.title()[1:])
    edited = b

root = tk.Tk()
root.title('Text Editor')
root.minsize(800, 600)
root.resizable(False, False)

icons = Image.open(BytesIO(decrypter(GAMEDIR + 'img\\system\\IconSet.rpgmvp')))
iconsW, iconsH = (i//32 for i in icons.size)
iconImages = {}

text = tk.Text(root, width=56, height=4, wrap='none', name='text')
text.config(font=('M+ 1m regular', -28), bg='black', fg='white', insertbackground='white')
text.bindtags(('.text', 'Text', 'cursor', '.', 'all'))
text.pack()

text.tag_config('hidden', elide=1)

color = tk.IntVar(root, 0, 'color')
size = tk.IntVar(root, 28, 'size')

hidden_box = ttk.Entry(root, name='hidden_box')
hidden_box.config(font=('Courier', -20), width=5)
hidden_box.pack()

hidden_box_2 = ttk.Spinbox(root, name='hidden_box_2')
hidden_box_2.config(font=('Courier', -20), width=5)
hidden_box_2.pack()

def hidden_box_enter(event):
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


for c in range(len(colors)):
    text.tag_config('C'+str(c), foreground=colors[c])

sizes = []
def set_size(s):
    if not s in sizes:
        text.tag_config('size'+str(s), font=('M+ 1m regular', -s))
        sizes.append(s)
    size.set(s)
    return s

def change_text(dialog):
    global undo_stack
    global redo_stack
    global undo_lastaction
    for h in list(hidden):
        del hidden[h]
    text.delete('1.0', 'end')
    color.set(0)
    size.set(28)
    undo_stack = []
    redo_stack = []
    undo_lastaction = ''
    set_text(dialog, tk.END)

reg = re.compile(r'([\$\.\|\^!><\{\}\\]|([A-Z]+))(?(2)\[([^\[\]]+)\]|)', re.I)
def insert_hidden(code, param='', index=tk.INSERT):
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

def set_text(dialog, index):
    dialog = dialog.replace('\\', '\x1b');
    dialog = dialog.replace('\x1b\x1b', '\\');

    l = 0
    while l < len(dialog):
        if dialog[l] == '\x1b':
            l += 1
            code, _, param = reg.findall(dialog, l)[0]
            l += len(reg.match(dialog, l)[0])
            insert_hidden(code, param, index)
        else:
            text.insert(index, dialog[l], ('C'+str(color.get()), 'size'+str(size.get())))
            l += 1

change_text('\\.Ciao, come \\C[10]stai\\C[0]?\\!\\!\nIo \\fs[40]benone\\}, grazie!\\I[16]')
def get_text(beg = '1.0', end = 'end-1c', tags = True):
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

def update_tags():
    global color
    global size
    
    for i in text.tag_names('insert-1displayindices'):
        if i[0] == 'C':
            color.set(i[1:])
        elif i[:4] == 'size':
            size.set(i[4:])

def update_hidden():
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
text.bind_class('cursor', '<<CursorMoved>>', update_all)

def text_copy(event):
    if text.tag_nextrange('sel', '1.0'):
        root.clipboard_clear()
        root.clipboard_append(get_text('sel.first', 'sel.last'))
text.bind_class('Text', '<<Copy>>', text_copy)

def text_paste(event):
    global undo_stack
    color.set(0)
    size.set(28)
    if text.tag_nextrange('sel', '1.0'):
        text_removed()

    undo_new('inserted')
    beg = text.index('insert')
    set_text(root.clipboard_get(), 'insert')
    text.tag_add('inserted', beg, 'insert')
    cursor_moved()
text.bind_class('Text', '<<Paste>>', text_paste)

def text_cut(event):
    if text.tag_nextrange('sel', '1.0'):
        root.clipboard_clear()
        root.clipboard_append(get_text('sel.first', 'sel.last'))
        text_removed()
        cursor_moved()
text.bind_class('Text', '<<Cut>>', text_cut)

def text_backspace(event):
    global undo_stack
    undo_new('backspaced')
    if text.tag_nextrange('sel', '1.0'):
        text_removed()
        cursor_moved()
    else:
        text.tag_add('removed', 'insert-1displayindices', 'insert')
    update_all()
text.bind_class('Text', '<BackSpace>', text_backspace)

def text_delete(event):
    if text.tag_nextrange('sel', '1.0'):
        text_removed()
        cursor_moved()
    else:
        undo_new('deleted')
        text.tag_add('removed', 'insert', 'insert+1displayindices')
        text.mark_set('insert', 'removed.last')
text.bind_class('Text', '<Delete>', text_delete)

def add_hidden_1(event):
    hidden_box.delete('@0', tk.END)
    hidden_box.focus_set()
text.bind_class('Text', '<\\>', add_hidden_1)

text.unbind_class('Text', '<<PasteSelection>>')
text.unbind_class('Text', '<Control-Button-1>')

text.tag_config('removed', elide=1)
text.tag_config('inserted')
def undo_new(action):
    global undo_stack
    global undo_lastaction
    global redo_stack
    res = undo_lastaction != action
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
            undo_stack.append((last0, last1))
            if redo_stack:
                redo_stack = []
        undo_lastaction = action
    return res

def cursor_moved(*event):
    undo_new('moved')
text.bind_class('Text', '<<CursorMoved>>', cursor_moved)

def text_removed(*event):
    undo_new('inserted')
    beg = text.index('sel.first')
    end = text.index('sel.last')
    text.tag_remove('sel', '1.0', tk.END)
    if text.compare(end, '==', 'end'):
        end += '-1c'
    text.tag_add('removed', beg, end)
    text.tag_add('sel2', beg, end)
    text.mark_set('insert', end)
text.bind_class('Text', '<<TextRemoved>>', text_removed)

def text_inserted(*event):
    undo_new('inserted')
    text.tag_add('inserted', 'insert-1displayindices', 'insert')
text.bind_class('Text', '<<TextInserted>>', text_inserted)


def text_undo_redo(action):
    #Undo: True
    #Redo: False
    global undo_stack
    global redo_stack
    cursor_moved()
    if action:
        stack = undo_stack
        stack2 = redo_stack
        n0, n1 = 0, 1
    else:
        stack = redo_stack
        stack2 = undo_stack
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
text.bind_class('Text', '<<Undo>>', lambda i=1: text_undo_redo(True))
text.bind_class('Text', '<<Redo>>', lambda i=1: text_undo_redo(False))


text.bind('<Alt-q>', lambda i=0: text.tag_config('removed', elide = 0, underline = 1))
text.bind('<Alt-KeyRelease-q>', lambda i=0: text.tag_config('removed', elide = 1, underline = 0))

text.tk.eval('''
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

def change_size(n):
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

    def __delchildren(self):
        for a in dict(self.item2):
            if type(self[a]) is Tree:
                self[a].__delchildren()
            del self.item2[a]
            self.update(a)
    
    def __delitem__(self, i):
        if i in self.item2:
            if type(self[i]) is Tree:
                self[i].__delchildren()
            obj = self
            ind = i
            while obj:
                if (type(obj[ind]) is Tree and not obj[ind].item2) or type(obj[ind]) is str:
                    del obj.item2[ind]
                obj.update(ind)
                try: ind = list(obj.parent.item1.keys())[list(obj.parent.item1.values()).index(obj)]
                except: pass
                obj = obj.parent
            self.update(i)
    
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
                        (lang[a].lower().find(s.lower()) + 1 and not search_case_var.get())):
                        res += 1
                    else:
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
        
tree = ttk.Treeview(root, selectmode='extended', columns=['value', 'search'], name='tree', height=32)
tree.yview_scroll = True
tree.column('value', width=600)
tree.column('search', width=30)
tree['displaycolumns'] = 'value'
tree.tag_configure('completed', background='light green')
tree.tag_configure('translated', background='gold')
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
search_lang = tk.IntVar()
def create_search_window(event):
    global search_window
    if not search_window:
        search_window = tk.Toplevel(root)
        
        search_entry = tk.Entry(search_window)
        search_entry.pack()
        search_entry.bind('<Return>', search_binding)

        global search_case_var
        search_case = tk.Checkbutton(search_window, text='Match case', variable = search_case_var)
        search_case.pack()
        
        global search_lang
        search_radio1 = tk.Radiobutton(search_window, text='Translated', variable = search_lang, value = 0)
        search_radio1.pack(side = tk.LEFT)
        search_radio2 = tk.Radiobutton(search_window, text='Original', variable = search_lang, value = 1)
        search_radio2.pack(side = tk.LEFT)
        
        search_entry.focus_set()
        
        search_window.bind('<Destroy>', destroy_search_window)
tree.bind_class('Treeview', '<Control-f>', create_search_window)

def open_dialog(event):
    change_text(Tree.__getitem__(*Tree.focus()))
tree.tag_bind('string', '<Return>', open_dialog)
tree.tag_bind('string', '<Double-Button-1>', open_dialog)

def set_dialog(event):
    cursor_moved()
    for a in Tree.selection():
        Tree.__setitem__(*a, get_text())
    tree.focus_set()
    edit(True)
text.bind_class('Text', '<Control-Return>', set_dialog)

def del_dialog(event):
    for a in Tree.selection():
        Tree.__delitem__(*a)
    edit(True)
tree.tag_bind('string', '<BackSpace>', del_dialog)
tree.tag_bind('string', '<Delete>', del_dialog)
tree.bind_class('Treeview', '<BackSpace>', del_dialog)

def select_down(event):
    if tree.next(tree.focus()) in tree.selection():
        tree.selection_toggle(tree.focus())
    tree.selection_add(tree.next(tree.focus()))
    tree.focus(tree.next(tree.focus()) or tree.focus())
    tree.see(tree.focus())
tree.bind_class('Treeview', '<<SelectNextLine>>', select_down)

def select_up(event):
    if tree.prev(tree.focus()) in tree.selection():
        tree.selection_toggle(tree.focus())
    tree.selection_add(tree.prev(tree.focus()))
    tree.focus(tree.prev(tree.focus()) or tree.focus())
    tree.see(tree.focus())
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


def save(*event):
    d = t.extract()
    with open('www\\languages\\IT.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(d, indent=2, ensure_ascii=False))
        f.close()
    edit(False)
root.bind('<Control-s>', save)

def exported_save(*event):
    save()
    with open(GAMEDIR + 'languages\\IT.cte', 'w') as f:
        f.write(lzstring.LZString().compressToBase64(json.dumps(t.extract_merged())))
        f.close()
root.bind('<Control-S>', exported_save)

def on_close():
    if edited:
        m = tk.messagebox.askyesnocancel('Save On Close','Do you want to save before closing?')
    else:
        m = False
    if m is not None:
        if m is True:
            exported_save()
        root.destroy()
root.protocol('WM_DELETE_WINDOW',on_close)

root.mainloop()
