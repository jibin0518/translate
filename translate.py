import tkinter as tk
import keyboard

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

box_in_ckick=False

def box_move(event):
    global rec_pos
    global last_rec_pos
    x_lenght = rec_pos[2]-rec_pos[0]
    y_lenght = rec_pos[3]-rec_pos[1]
    x1 = rec_pos[0]+event.x-x_lenght
    y1 = rec_pos[1]+event.y-y_lenght
    x2 = rec_pos[2]+event.x-x_lenght
    y2 = rec_pos[3]+event.y-y_lenght
    canvas.coords("box",x1,y1,x2,y2)
    print(x1,y1,x2,y2)


def key_loop():
    if keyboard.is_pressed('esc'):
        print("꺼짐")
        window.destroy()
        return
    window.after(100, key_loop)

canvas.bind("<B1-Motion>", box_move)

key_loop()
window.mainloop()