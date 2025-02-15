import json
import lzstring
import os
import sys

HEADERLENGTH = 16
KEY = 0xd41d8cd98f00b204e9800998ecf8427e
SIGNATURE = b'RPGMV\x00\x00\x00'
VER = b'\x00\x03\x01'
GAMEDIR = 'C:\\Program Files (x86)\\Steam\\steamapps\\common\\yttd\\'

def decrypter(encImg):
    if encImg[:HEADERLENGTH] != (SIGNATURE+VER).ljust(16, b'\x00'):
        raise Exception('Header is wrong.')

    encImg = encImg[HEADERLENGTH:]

    return (int.from_bytes(encImg[:HEADERLENGTH]) ^ KEY).to_bytes(16) + encImg[HEADERLENGTH:]

def encrypter(Img):
    return (SIGNATURE+VER).ljust(16, b'\x00') + (int.from_bytes(Img[:HEADERLENGTH]) ^ KEY).to_bytes(16) + Img[HEADERLENGTH:]

def json2cte(file):
    return lzstring.LZString().compressToBase64(json.dumps(json.loads(file), separators=(',', ':')))

def cte2json(file):
    return json.dumps(json.loads(lzstring.LZString().decompressFromBase64(B64)), indent=2, ensure_ascii=False)

loop = True
while loop:
    os.system('cls' if os.name == 'nt' else 'clear')
    if len(sys.argv) <= 1:
        sel = input('[I] Compress images.\n[T] Compress text.\n[C] Close.\n').lower()
    else:
        sel = sys.argv[1]
        sys.argv.pop(1)
        loop = False
    
    if sel == 'c': break
    
    if 'i' in sel:
        for d in os.walk('www\\img'):
            for i in d[2]:
                if i.endswith('.png'):
                    path = os.path.join(d[0], i)
                    f = open(path, 'rb')
                    rpgmvp = encrypter(f.read())
                    f.close()

                    os.makedirs(GAMEDIR + d[0], exist_ok=True)
                    f = open(GAMEDIR + path[:-4] + '.rpgmvp', 'wb')
                    f.write(rpgmvp)
                    print(GAMEDIR + path[:-4] + '.rpgmvp')
                    f.close()
    if 't' in sel:
        path = 'www\\languages\\IT.json'
        f = open(path, 'r', encoding='utf-8')
        cte = json2cte(f.read())
        f.close()

        f = open(GAMEDIR + path[:-5] + '.cte', 'w')
        f.write(cte)
        f.close()
