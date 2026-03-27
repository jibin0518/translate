import tkinter as tk
import keyboard
import mss
import cv2
import numpy as np
import easyocr
import re

def close(event=None):
    window.destroy()

gpu_state = True

reader = easyocr.Reader(['ko', 'en'], gpu=gpu_state)

window = tk.Tk()
window.title("HELLO 오버레이")
window.attributes("-topmost", True)
window.attributes("-transparentcolor", "white")  # white는 투명
window.overrideredirect(True)
window.configure(bg="white")

window.geometry("1920x1080+0+0")

canvas = tk.Canvas(window,width=1920,height=1080,bg="white",highlightthickness=0)
canvas.pack()

box = canvas.create_rectangle(100, 100, 400, 300, outline="green", width=7, tags="box")

langage_select_frame = tk.Frame(window, bg="white")
langage_select_frame.place(x=1800, y=100, width=50, height=50)
'''
def on_click0():
    global language_state
    language_state = "한영"
def on_click1():
    global language_state
    language_state = "영어"

langage_mode_bu1 = tk.Button(langage_select_frame, text="한/영",command=on_click0)
langage_mode_bu1.pack()
langage_mode_bu2 = tk.Button(langage_select_frame, text="영어-포기",command=on_click1)
langage_mode_bu2.pack()
'''

rec_pos = [100,100,400,300]
last_rec_pos = [0,0,0,0]

last_rec_pos = rec_pos
box_in_ckick=False
rec_mouse_pont = [0,0]

mode_state = "Move"

last_text = ""

before_text = ""

print(gpu_state)

def preprocess_image(img):
    global language_state
    global gpu_state

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 확대만
    gray = cv2.resize(gray, None, fx=2.8, fy=2.8, interpolation=cv2.INTER_CUBIC)

    if(gpu_state):
        gray = cv2.convertScaleAbs(gray, alpha=1.2, beta=0)

        # 너무 강하지 않은 이진화
        _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        return th
    elif(gpu_state!=True):
        return gray

def mos_pos(event):
    global mode_state
    global rec_mouse_pont
    global rec_pos
    if(event.x<rec_pos[0]+10 and event.y<rec_pos[1]+10):#x<110 and y<110 우측 상단
        mode_state = "Size_aw"
    elif(event.x<rec_pos[0]+10 and event.y>rec_pos[3]-10):#x<110 and y>290 우측 하단
        mode_state = "Size_as"
    elif(event.x>rec_pos[2]-10 and event.y<rec_pos[1]+10):#x>390 and y<110 좌측 상단
        mode_state = "Size_dw"
    elif(event.x>rec_pos[2]-10 and event.y>rec_pos[3]-10):#x>390 and y>290 좌측 하단
        mode_state = "Size_ds"
    else: mode_state = "Move"
    rec_mouse_pont[0]=event.x
    rec_mouse_pont[1]=event.y
    #print(mode_state)

def box_move(event):
    global rec_pos
    global last_rec_pos
    global mode_state
    if(mode_state=="Move"):
        x_lenght = rec_pos[2]-rec_pos[0]
        y_lenght = rec_pos[3]-rec_pos[1]
        x1 = rec_pos[0]+event.x-x_lenght
        y1 = rec_pos[1]+event.y-y_lenght
        x2 = rec_pos[2]+event.x-x_lenght
        y2 = rec_pos[3]+event.y-y_lenght
        global rec_mouse_pont
        mos_gap = [rec_mouse_pont[0]-rec_pos[0],rec_mouse_pont[1]-rec_pos[1],
                    rec_pos[2]-rec_mouse_pont[0],rec_pos[3]-rec_mouse_pont[1]]
        x1 = event.x-mos_gap[0]
        y1 = event.y-mos_gap[1]
        x2 = event.x+mos_gap[2]
        y2 = event.y+mos_gap[3]

    elif(mode_state=="Size_aw"):#우측 상단
        x1=event.x
        y1=event.y
        x2=rec_pos[2]
        y2=rec_pos[3]
    elif(mode_state=="Size_as"):#우측 하단
        x1=event.x
        y1=rec_pos[1]
        x2=rec_pos[2]
        y2=event.y
    elif(mode_state=="Size_dw"):#좌측 상단
        x1=rec_pos[0]
        y1=event.y
        x2=event.x
        y2=rec_pos[3]
    elif(mode_state=="Size_ds"):#좌측 하단
        x1=rec_pos[0]
        y1=rec_pos[1]
        x2=event.x
        y2=event.y
    canvas.coords("box",x1,y1,x2,y2)
    last_rec_pos = [x1,y1,x2,y2]

def mos_point_finish(event):#좌클릭 땜 -> 박스 위치 업데이트
    global rec_mouse_pont
    global rec_pos
    rec_pos = last_rec_pos

def load_text(processed):
    results = reader.readtext(
        processed,
        detail=0,
        paragraph=True
        )
    return results
    
def load_short_text(img):
    results = reader.readtext(
        img,
        detail=0,
        paragraph=True
        )
    return results

EXCEPTION_WORDS = {
    "틀", "이틀", "사흘", "돼지울", "심울", "저울", "거울", "방울", "틀다", "여울", "땀방울", "눈물방울", "암울", "목거울", "물방울"
    , "솔방울", "파울", "조준틀","재봉틀","셔틀",
}

def fix_josa_errors(text):
    def replace_match(match):
        full = match.group(0)
        word = match.group(1)   # 앞 단어
        wrong = match.group(2)  # 틀 / 울 / 올

        if full in EXCEPTION_WORDS:
            return full

        if wrong == "틀" or wrong == "릎":
            return word + "를"
        elif wrong == "울" or wrong == "올" or wrong == "블":
            return word + "을"

        return match.group(0)

    return re.sub(r'([가-힣]+)(틀|울|올|블|릎)(?=\s|$|[.,!?])', replace_match, text)

def text_fix(text):
    replacements = {
        "어두위": "어두워","어무위" : "어두워","심치어": "심지어","엇조": "었죠","이특": "이득",
        "없조": "없죠","옆죠": "였죠","하조": "하죠","도료": "도로","뛰어터조" : "뛰어났죠","넷조" : "났죠",
        "뛰어낫조" : "뛰어났죠","잇없" : "있없","있있" : "있었","상처클" : "상처를",
        "만들없다는" : "만들었다는","주지논" : "주지는","잡아쥐" : "잡아줘","살려쥐" : "살려줘","오젠지" : "오겠지","만나기름" : "만나기를","원랫듯이" : "원했듯이",
        "열무시" : "열두시","친구논" : "친구는","없잡아" : "없잖아","믿어앗지만" : "믿어왔지만", "외로원지" : "외로웠지","부르다" : "부른다","뜯해" : "뜸해",
        "걸어쩄으면" : "걸어줬으면","걸어짓으면" : "걸어줬으면","꺼쨌" : "꺼냈","말햇" : "말했", "햇권" : "했던", "햇던" : "했던",
          "햇어" : "했어", "배위" : "배워", "기지개흘" : "기지개를", "엇던" : "었던","엇년" : "었던", "없없던" : "없었던", "지논" : "지는","옷고" : "왔고",
          "왕고" : "왔고","사라저" : "사라져","노썹" : "노랠","노길" : "노랠","부로면" : "부르면","몰차던" : "몰랐던","몰탓던" : "몰랐던", "못햇년" : "못했던",
          "너느" : "너는","알잡아" : "알잖아","것클" : "것을","없년" : "없던","시계름" : "시계를","햇듯이" : "했듯이",
          "꺼넷" : "꺼냇","어제논" : "어제는","위블" : "위를","위릎" : "위를","하느데" : "하는데","아년" : "아닌","잇는" : "있는",
          "내계선" : "내게선","쓰러저" : "쓰러져","엇으" : "었으","월 바라" : "뭘 바라", "저가는" : "져가는","동지선달" : "동지섣달","동지설달" : "동지설달",
        "까방고" : "까맣고","새하용게" : "새하얗게","엉꼴" : "벛꽃","벗꽃" : "벚꽃","파탕게" : "파랗게","깜빠" : "깜빡","없젯군" : "없겠군","찾들" : "찾을","들올" : "들을",
        "확출" : "확률","렌데" : "텐데","켓지" : "겠지","엇군요" : "었군요","앗어" : "았어","덜켜" : "덜컥","되없습니다" : "되었습니다","나변" : "나쁘",
        "용계" : "용케","들들" : "들을","엿지" : "였지","지취관" : "지휘관","쾌다고" : "했다고","웟년" : "웠던","논데" : "는데","햇잡아" : "했잖아","있없" : "있었",
        "잇든" : "있는","멀정한" : "멀쩡한","아니잡아" : "아니잖아","활 일" : "할 일","햇다" : "했다","생각할" : "생각할","있둘던" : "있었던","흐려저 가능" : "흐려져 가는","분이없다" : "뿐이었다",
        "울부짓는" : "울부짖는","움질" : "움찔","차럿군" : "차렸군","갖으" : "갔으","뻔화" : "뻔했","뻔쾌" : "뻔했","켓어" : "겠어","재각" : "째각","논군" : "는군","하시조" : "하시죠",
        "않앗" : "않았","엿다" : "였다","않사" : "않았","알앉다" : "알았다","있," : "있었","엿는" : "였는","저없다" : "저었다","리논" : "리는","참이없으니" : "참이었으니",
        "켓군" : "겠군","켓균" : "겠군","걸없던" : "걸었던","컷지" : "렀지","균요" : "군요","잇나" : "있나","햇는" : "했는","부혹게" : "부를게","알레로기" : "알레르기",
        "달려칼" : "달려갈","가져운" : "가벼운","중젲" : "좋겠","중깊" : "좋겠","켓습" : "겠습","않논" : "않는",
        "활 수" : "할 수",
    }
    eng_replacements={
        "We\"l" : "We\"ll",";" : ",",
    }

    for wrong, correct in replacements.items():
        text = text.replace(wrong, correct)

    text = fix_josa_errors(text)

    return text
        
    
def do_ocr():
    global before_text
    global last_text
    global rec_pos
    trash_list = ["[","]","\"","/","=","@","{","}",";",":","-","@"]

    x1, y1, x2, y2 = rec_pos
    width = x2 - x1
    height = y2 - y1

    if width < 10 or height < 10:
        window.after(600, do_ocr)
        return

    try:
        with mss.mss() as sct:
            region = {
                "left": int(x1),
                "top": int(y1),
                "width": int(width),
                "height": int(height)
            }

            screenshot = sct.grab(region)
            img = np.array(screenshot)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

            processed = preprocess_image(img)
            
            if(gpu_state):
                results = load_text(processed)
                results2 = load_short_text(img)
            elif(gpu_state!=True):
                results2 = load_short_text(img)

            # OCR
            text = "\n".join(results).strip()
            text2 = "\n".join(results2).strip()
            for i in trash_list:
                if i in text:
                    text = text2
                    break
            if(len(text)-len(last_text)<4 and len(text)-len(last_text) != 0):
                for i in trash_list:
                    if i in text2:
                        text = text2
                        break
                        
            text = text_fix(text)
            
            if text and text != last_text:
                print("=" * 40)
                print(text)
                last_text = text

    except Exception as e:
        print("OCR 오류:", e)

    window.after(400, do_ocr)
    
def key_loop():
    if keyboard.is_pressed('esc'):
        print("꺼짐")
        window.destroy()
        return
    window.after(100, key_loop)

canvas.bind("<Button-1>", mos_pos)
canvas.bind("<B1-Motion>", box_move)
canvas.bind("<ButtonRelease-1>",mos_point_finish)

key_loop()
do_ocr()
window.mainloop()