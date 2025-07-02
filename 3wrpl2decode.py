import sys, pathlib, time, typing, os, re
from construct import Tell, Computed, RestreamData, Bit ,Const, Struct, Bytes, Construct, this, Int8ul,Int16ul,Int32ul,Int64ul
import zlib



"""
(Size..) (Type) 00 (?Time) (Function + args + Data..)

!! SIZE
First bit of SIZE should be eliminated
First bit location 

7) [xx] (type) 00
6) [xx] [xx] (type) 00
5) [xx] [xx] [xx] (type) 00

!! TYPE:
x0 - EOF
x2 - Object Generation?
x3 - Chat
x4 - Movement?
x6 - Log?

x1,x5,x8 - ??

1) Case Time exists
{4x} yy 02 00 (time) data..
{4x} yy 03 00 (time) data..

2) Case Time does NOT exists
{4x} yy 14 00 data..
{4x} yy 16 00 data..

!! TIME:
H:M:S.ms format, Little Endian order

"""
def pass1(byteData):
    data_iter = iter(byteData)

    lines = []

    # {4x} [SIZE] [TYPE] [00] [TIME] [00] [FUNCTION] + a
    time_now = 0

    """
    Find MSB(Most Significant Bit)
    
    Returns (MSB, input without MSB == size)
    """
    def MSBDigest(n):
        tmp = n
        highBit = 0
        while 1 < tmp :
            tmp = tmp >> 1
            highBit += 1
        return (highBit, n - (1 << (highBit)))

    for e in data_iter:
        ## First significant bit ignored
        skipLine = 0
        highBit, size = MSBDigest(int(e))

        if(highBit == 7): # 94 ~~
            pass #
        elif(highBit == 6): # 40 XX ~~
            size = size << 8
            size += int(next(data_iter, None))
        elif(highBit == 5): # 20 20 XX ~~
            size = size << 16
            size += int(next(data_iter, None)) << 8
            size += int(next(data_iter, None))
        else: # Highbit == 4?? case not found
            size = size << 24
            size += int(next(data_iter, None)) << 16
            size += int(next(data_iter, None)) << 8
            size += int(next(data_iter, None))

        skipLine += 1
        dtype = int(next(data_iter, None)) # [TYPE]

        skipLine += 1
        next(data_iter, None) # 00 (skip)

        ## ( [TIME_NOW], [TYPE], [DATA] )
        # Case : 0 < dtype < 15 = NEW TIMESTAMP (H:M:S.ms)
        if 0 <= dtype and dtype <= 15:
            time_now = next(data_iter, None)
            time_now += next(data_iter, None)<<8
            time_now += next(data_iter, None)<<16
            time_now += next(data_iter, None)<<24
            time_now = str(time.strftime('%H:%M:%S', time.gmtime(time_now/1000)))+'.'+str("{:03d}".format(time_now%1000))
            skipLine += 4   
        # Case : 16 < dtype < 31 = no timestamp
        else:
            pass
        #dtype = f'{dtype:x}'

        line = []
        for i in range(size - skipLine):
            nxt = next(data_iter,None)
            if nxt == None: break
            line += [nxt]
        lines += [(time_now, dtype, line)]
        #print(line)
        #return lines
        
    return lines

"""
UserId in Little Endian
"""
def getUserId(lst):
    i1, i2, i3, i4 = lst
    return str(int((i4 << 24) + (i3 << 16) + (i2 << 8) + i1))

"""
Team # Player # formatting
- Cases when Starting w/ 0
01 => Team 1 Player 2

- Cases when Starting w/ 1
23 => Team 2 Player 3

- If > Team 2 Then AI
"""
def tnpn(input, isStartOne=True):
    if (input >> 4) > 2 : return "AI" #print(hex(input)); return "AI"

    Team = (input >> 4) + (1 if isStartOne else 0)
    Player = (input & 0xF) + (1 if isStartOne else 0)
    #print('tnpn',input,Team,Player)
    return f't{int(Team)}_p{f'{int(Player):02d}'}'

"""
Actual Filtering

"""
def pass2(lines):
    chk0 = re.compile(r"^02 58 AA F0 01 00 .. 00 FF .. .. .. .. .. 00 0A .. 00 00 80 3F 00 00 80 BF 00 00 80 BF 00 00 80 BF 00 00 00 00 00 00 80 BF [^FF].*24$") # UserID : Vehicle
    chk1 = re.compile(r"^02 58 56 .. .. 00") # Fire
    chk2 = re.compile(r"^02 58 57 .. .. 00") # Critical
    chk3 = re.compile(r"^02 58 58 .. .. 00") # Kill

    chk21 = re.compile(r"^25 F0 09") # Air - Vehicle : User 25 57
    chk22 = re.compile(r"^25 F0 0A") # Air - Vehicle : User 26 58
    chk23 = re.compile(r"^25 F0 0B") # Air - Vehicle : User 27 59
    chk24 = re.compile(r"^25 F2 07") # Air - Vehicle : User 25-1 77

    chk31 = re.compile(r"^25 F1 07") # Ground - Vehicle : User 25-1 79
    chk32 = re.compile(r"^25 F0 16") # Ground - Vehicle : User 25 80
    chk33 = re.compile(r"^25 F0 17") # Ground - Vehicle : User 26 81
    chk34 = re.compile(r"^25 FF 7B") # Ground - Vehicle : User 26 81
    chk35 = re.compile(r"^25 FF 75") # Ground - Vehicle : User 26 81
    chk36 = re.compile(r"^25 F3 9B") # Ground - Vehicle : User 26 81
    chk37 = re.compile(r"^25 F9 67") # Ground - Vehicle : User 26 81
    


    newlines = []
    for (tn,dt,ln) in lines:
        matches = False
        match dt:
            ## x0 : < End of file >
            #case 0x00 | 0x10: matches = True
            ## x1 / x5: ?? ~~ 0x15
            #case 0x01 | 0x11 | 0x05 | 0x15 | 0x08 | 0x18: matches = True
            ## x7 / x9: 0
            #case 0x07 | 0x17 | 0x09 | 0x19: matches = True

            ## x2: create / generate object?
            #case 0x02 | 0x12: matches = True

            ## x3: < chat >
            #case 0x03 | 0x13: matches = True

            ## x4: < Game Log? > movement? 90%+ of lines
            case 0x04 | 0x14: 
                regexStr = ' '.join(map(lambda e: f'{e:02X}',ln))

                """
                User ID <-> Team # Player #

                Works only when User loggs out? before game ends??
                """
                if(chk0.match(regexStr) and  ln[41] != 0xFF): ## 7E [TO] [From] 00 00 00 # bf-109 .. ##TO starts from 1, From starts from 0
                    tmp = ['#',tnpn(ln[49]-0x11)]
                    tmp = ['User',getUserId(ln[40:44])]
                    for i in range(int(ln[51])):
                        tmp += [str(chr(ln[51+i+1]))]
                    ln = [tmp[0],':',tmp[1],' = ', ' '.join(tmp[2:])]
                    matches = True
                    dt = "41"

                """
                Fire Check
                """
                if(chk1.match(regexStr)): ## 7E [TO] [From] 00 00 00 # bf-109 .. ##TO starts from 1, From starts from 0
                    ln = ['FIRE',tnpn(ln[8]),'->',tnpn(ln[7],False)]
                    matches = True
                    dt = "4"
                """
                Crit Check
                """
                if(chk2.match(regexStr)): ## 3E [TO] 01 [From] 00 00 00 # bf-109 ..##TO starts from 1, From starts from 0
                    ln = ['CRIT',tnpn(ln[9]),'->',tnpn(ln[7],False)]
                    matches = True
                    dt = "4"
                """
                Kill Check

                0xFF -> User : Self Kill
                0xFF -> 00 : ??
                0xXX -> 00 : YY > 20 = AI Kill
                """
                if(chk3.match(regexStr)): ## FE ? [from] 00 00 00 #bf-109 [TO] 01 ..##TO starts from 1, From starts from 0
                    ln = ['KILL',tnpn(ln[8]),'->',tnpn(ln[12+ln[12]+1],False)]
                    matches = True
                    dt = "4"
            ## x6: < Game Log? > Generation?
            case 0x06 | 0x16: 
                regexStr = ' '.join(map(lambda e: f'{e:02X}',ln))
                vehPt = 0
                ## Air: F0 09
                if(chk21.match(regexStr)): # User# Byte #21, #Vehicle = #53 + ..[#53]
                    tmp = [tnpn(ln[25])]
                    vehPt=57
                    matches = True
                ## Air: F0 0A
                if(chk22.match(regexStr)):
                    tmp = [tnpn(ln[26])]
                    vehPt=58
                    matches = True
                ## Air: F0 0B
                if(chk23.match(regexStr)):
                    tmp = [tnpn(ln[27])]
                    vehPt=59
                    matches = True
                ## Air: F2 07
                if(chk24.match(regexStr)):
                    tmp = [tnpn(ln[25] -1)]
                    vehPt = 77
                    matches = True
                ## Ground: F1 07
                if(chk31.match(regexStr)):
                    tmp = [tnpn(ln[25] -1)]
                    vehPt = 79
                    matches = True
                ## Ground: F0 16
                if(chk32.match(regexStr)):
                    tmp = [tnpn(ln[25])]
                    vehPt = 80
                    matches = True
                ## Ground: F0 17
                if(chk33.match(regexStr) or chk34.match(regexStr) or chk35.match(regexStr) or chk36.match(regexStr) or chk37.match(regexStr)):
                    tmp = [tnpn(ln[26])]
                    vehPt = 81
                    matches = True

                if matches:
                    for i in range(int(ln[vehPt])):
                        tmp += [str(chr(ln[vehPt+i+1]))]
                    ln = [tmp[0],':',''.join(tmp[1:])]
                    matches = True
                    dt = "6"
        if matches:
            newlines += [(tn,dt,ln)]
    return newlines


"""
Credited yay5379/wt_client_replay_parser
* Modified some un-necessary parts
"""
Header = Struct(
    'magic' / Const(bytes.fromhex('e5ac0010')),
    'version' / Int32ul,  # 2.9.0.38 ~ 101111
    'level' / Bytes(128),  # levels/avg_stalingrad_factory.bin
    'level_settings' / Bytes(260),  # gamedata/missions/cta/tanks/stalingrad_factory/stalingrad_factory_dom.blk
    'battle_type' / Bytes(128),  # stalingrad_factory_Dom
    'environment' / Bytes(128),  # day
    'visibility' / Bytes(32),  # good
    'rez_offset' / Int32ul,  # not used for server replays
    
    ## 2B0 ~ 2D7
    'difficulty' / Bytes(5),
    'unk_3' / Bytes(3),
    'srv_id' / Int8ul,
    'unk_31' / Bytes(31),

    # 2D8 ~ 2E3
    'session_type' / Int32ul,  # меня интересует только RANDOM_BATTLE для танков
    'session_id' / Int64ul,
    
    #2E4
    'server_replay_order_number' / Int16ul,  # the number from the title of the server replay ex: 0001.wrpl. always 0 for client replays
    'unk_int16' / Int16ul,
    'weather_seed' / Int32ul,

    #2ED
    'm_set_size' / Int64ul,
    'unk_19' / Bytes(19),
    'local_player_country' / Int8ul,
    'unk_4' / Bytes(4),
    'loc_name' / Bytes(128),  # missions/_Dom;stalingrad_factory/name

    #38C ~ #4C7
    'start_time' / Int32ul,
    'time_limit' / Int32ul,
    'score_limit' / Int64ul,
    'unk_8' / Bytes(8),
    'local_player_id' / Int8ul,  # always 0 for server replays
    'unk_2' / Bytes(2),
    'unk_Int8ul' / Int8ul,
    'unk_4' / Bytes(4),
    'dynamicResult' / Int32ul,
    'unk_20' / Bytes(20),
    'gm' / Int32ul,
    'battle_class' / Bytes(128),  # air_ground_Dom
    'battle_kill_streak' / Bytes(128),  # killStreaksAircraftOrHelicopter_1
)

"""
Credited yay5379/wt_client_replay_parser
* Modified for not using bin.Fat
"""
def FatBlockStream(sz: typing.Union[int, callable, None] = None) -> Construct:
    return Bytes(sz) if sz == 0 else RestreamData(Bytes(sz), Bit)

"""
Credited yay5379/wt_client_replay_parser
* Modified fileSize & headless_file
"""
WRPLServFile = "wrpl" / Struct(
    'header' / Header,
    Bytes(2), # 4C8 ~ 4C9
    'm_set' / FatBlockStream(this.header.m_set_size),
    'current_position' / Tell,
    'fileSize' / Computed(lambda ctx: len(ctx._io.getvalue())),
    'headless_file' / Bytes(this.fileSize-this.current_position)
)

if __name__ == '__main__':
    pathname = sys.argv[1]
    dirfiles = [os.path.join(pathname, f) for f in os.listdir(pathname)]
    files_match = ".*.wrpl$"
    files = sorted([os.path.abspath(f) for f in dirfiles if re.search(files_match, f)])

    print("Load ..")
    rest = b""
    for file in files:
        data = pathlib.Path(file).read_bytes()
        parsed = WRPLServFile.parse(data)

        zdo = zlib.decompressobj()
        data_wrplu = zdo.decompress(parsed.headless_file)
        rest += data_wrplu

    asciiCheck = re.compile(r"[\w\s[$&+,:;=?@#|<>.^*()%!-\]]")
    ## -------------------------
    ## Pass 1: Decode Data
    print("Pass 1 ..")
    lines = pass1(rest)
    
    """
    !!Uncomment if Raw hex strings required
    """
    f=open(f'{pathname}.raw.txt','w')
    for (tn,dt,ln) in lines: f.write(f"{tn} / {str(hex(dt))} /  {' '.join(map(lambda e: f'{e:02X}',ln))}\n" )
    f.close()

    ## Pass 2 : filter wanted only
    print("Pass 2 ..")
    lines = pass2(lines)

    print("Write ..")
    f=open(f'{pathname}.txt','w')

    """
    Block 1 : UserID <-> Team # Player #
    """
    tmp = lines
    tmp = list(filter(lambda x : x[1] == '41', tmp))
    tmp.sort(key=lambda tup: tup[2][0])
    for (tn,dt,ln) in tmp:
        f.write(f'{tn} / {' '.join(ln)}\n' )
    f.write(f'============\n' )
    """
    Block 2 : Team # Player # <-> Vehicle
    """
    tmp = lines
    tmp = list(filter(lambda x : x[1] == '6', tmp))
    tmp.sort(key=lambda tup: tup[2][0])
    for (tn,dt,ln) in tmp:
        f.write(f'{tn} / {' '.join(ln)}\n' )

    f.write(f'----------------------------------------\n' )
    """
    Block 3 : Everything
    """
    for (tn,dt,ln) in lines:
        f.write(f'{tn} / {' '.join(ln)}\n' )
    #           {str(hex(dt))}
    #        {' '.join(map(lambda e: e if type(e) is str else f'{e:02X}',ln))}\n\t \
    #        {' '.join(map(lambda e: str(chr(e)) if asciiCheck.match(chr(e)) else f'{e:02X}',ln))}\n' )
    f.close()
    print(f'Lines : {len(lines)}')

