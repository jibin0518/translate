import tkinter as tk
import keyboard
import mouse

def close(event=None):
    window.destroy()

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

rec_pos = [100,100,400,300]
last_rec_pos = [0,0,0,0]
last_rec_pos = rec_pos
box_in_ckick=False
rec_mouse_pont = [0,0]

def mos_pos(event):
    global rec_mouse_pont
    rec_mouse_pont[0]=event.x
    rec_mouse_pont[1]=event.y

def box_move(event):
    global rec_pos
    global last_rec_pos
    global rec_mouse_pont
    mos_gap = [rec_mouse_pont[0]-rec_pos[0],rec_mouse_pont[1]-rec_pos[1],
               rec_pos[2]-rec_mouse_pont[0],rec_pos[3]-rec_mouse_pont[1]]
    x1 = event.x-mos_gap[0]
    y1 = event.y-mos_gap[1]
    x2 = event.x+mos_gap[2]
    y2 = event.y+mos_gap[3]
    canvas.coords("box",x1,y1,x2,y2)
    last_rec_pos = [x1,y1,x2,y2]

def box_size_change(event):
    global rec_pos
    if(event.x<rec_pos[0]+10 and event.y<rec_pos[1]+10):#x<110 and y<110
        print("우측 상단 :",event.x,event.y)
    elif(event.x<rec_pos[0]+10 and event.y>rec_pos[3]-10):#x<110 and y>290
        print("우측 하단 :",event.x,event.y)
    elif(event.x>rec_pos[2]-10 and event.y<rec_pos[1]+10):#x>390 and y<110
        print("좌측 상단 :",event.x,event.y)
    elif(event.x>rec_pos[2]-10 and event.y>rec_pos[3]-10):#x>390 and y>290
        print("좌측 하단 :",event.x,event.y)

def mos_point_finish(event):#좌클릭 땜 -> 박스 위치 업데이트
    global rec_mouse_pont
    global rec_pos
    rec_pos = last_rec_pos
    
def key_loop():
    if keyboard.is_pressed('esc'):
        print("꺼짐")
        window.destroy()
        return
    window.after(100, key_loop)

canvas.bind("<Button-1>", mos_pos)
canvas.bind("<B1-Motion>", box_move)
canvas.bind("<Motion>",box_size_change)
canvas.bind("<ButtonRelease-1>",mos_point_finish)

key_loop()
window.mainloop()