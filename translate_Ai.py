import time
import threading
import mss
import cv2
import numpy as np
import easyocr

# =========================
# 설정
# =========================
reader = easyocr.Reader(['ko', 'en'], gpu=False)

OCR_INTERVAL = 0.5  # OCR 주기(초)

region = {
    "left": 100,
    "top": 100,
    "width": 800,
    "height": 300
}

latest_frame = None
latest_text = ""
running = True

frame_lock = threading.Lock()
text_lock = threading.Lock()
region_lock = threading.Lock()

# 마우스 조작 상태
drag_mode = None   # None / move / resize / new
drag_start_x = 0
drag_start_y = 0
start_region = None

HANDLE_SIZE = 12  # 오른쪽 아래 리사이즈 핸들 크기


# =========================
# OCR 스레드
# =========================
def ocr_worker():
    global latest_frame, latest_text, running

    while running:
        frame_copy = None

        with frame_lock:
            if latest_frame is not None:
                frame_copy = latest_frame.copy()

        if frame_copy is not None:
            try:
                results = reader.readtext(frame_copy, detail=0)
                text = "\n".join(results).strip()
                with text_lock:
                    latest_text = text
            except Exception:
                pass

        time.sleep(OCR_INTERVAL)


# =========================
# 마우스 이벤트
# =========================
def point_in_rect(x, y, rect):
    return (
        rect["left"] <= x <= rect["left"] + rect["width"] and
        rect["top"] <= y <= rect["top"] + rect["height"]
    )

def point_in_resize_handle(x, y, rect):
    rx = rect["left"] + rect["width"]
    ry = rect["top"] + rect["height"]
    return abs(x - rx) <= HANDLE_SIZE and abs(y - ry) <= HANDLE_SIZE

def mouse_callback(event, x, y, flags, param):
    global drag_mode, drag_start_x, drag_start_y, start_region, region

    with region_lock:
        current = region.copy()

    if event == cv2.EVENT_LBUTTONDOWN:
        drag_start_x, drag_start_y = x, y
        start_region = current.copy()

        if point_in_resize_handle(x, y, current):
            drag_mode = "resize"
        elif point_in_rect(x, y, current):
            drag_mode = "move"
        else:
            drag_mode = "new"
            with region_lock:
                region = {
                    "left": x,
                    "top": y,
                    "width": 1,
                    "height": 1
                }

    elif event == cv2.EVENT_MOUSEMOVE and drag_mode is not None:
        dx = x - drag_start_x
        dy = y - drag_start_y

        with region_lock:
            if drag_mode == "move":
                region["left"] = max(0, start_region["left"] + dx)
                region["top"] = max(0, start_region["top"] + dy)

            elif drag_mode == "resize":
                new_w = max(20, start_region["width"] + dx)
                new_h = max(20, start_region["height"] + dy)
                region["width"] = new_w
                region["height"] = new_h

            elif drag_mode == "new":
                x1 = min(drag_start_x, x)
                y1 = min(drag_start_y, y)
                x2 = max(drag_start_x, x)
                y2 = max(drag_start_y, y)

                region["left"] = x1
                region["top"] = y1
                region["width"] = max(20, x2 - x1)
                region["height"] = max(20, y2 - y1)

    elif event == cv2.EVENT_LBUTTONUP:
        drag_mode = None
        start_region = None


# =========================
# 메인
# =========================
def main():
    global latest_frame, latest_text, running, region

    ocr_thread = threading.Thread(target=ocr_worker, daemon=True)
    ocr_thread.start()

    cv2.namedWindow("Control")
    cv2.setMouseCallback("Control", mouse_callback)

    last_printed_text = ""

    with mss.mss() as sct:
        monitor = sct.monitors[1]  # 주 모니터

        print("실행 중")
        print("- Control 창에서 영역을 마우스로 조절")
        print("- 박스 안 드래그: 이동")
        print("- 오른쪽 아래 모서리 드래그: 크기 조절")
        print("- 빈 곳 드래그: 새 영역 지정")
        print("- ESC: 종료")

        while True:
            # 전체 화면 캡처 (Control 창용)
            full_shot = sct.grab(monitor)
            full_img = np.array(full_shot)
            full_img = cv2.cvtColor(full_img, cv2.COLOR_BGRA2BGR)

            # 현재 OCR 영역 캡처
            with region_lock:
                current_region = region.copy()

            # 화면 밖으로 나가지 않게 보정
            current_region["left"] = max(0, min(current_region["left"], monitor["width"] - 20))
            current_region["top"] = max(0, min(current_region["top"], monitor["height"] - 20))
            current_region["width"] = max(20, min(current_region["width"], monitor["width"] - current_region["left"]))
            current_region["height"] = max(20, min(current_region["height"], monitor["height"] - current_region["top"]))

            with region_lock:
                region = current_region.copy()

            # OCR용 최신 프레임 업데이트
            crop = full_img[
                current_region["top"]:current_region["top"] + current_region["height"],
                current_region["left"]:current_region["left"] + current_region["width"]
            ]

            if crop.size > 0:
                with frame_lock:
                    latest_frame = crop.copy()

                cv2.imshow("OCR Region", crop)

            # 텍스트 출력
            with text_lock:
                current_text = latest_text

            if current_text and current_text != last_printed_text:
                print("=" * 40)
                print(current_text)
                last_printed_text = current_text

            # Control 창에 박스 표시
            display = full_img.copy()

            x1 = current_region["left"]
            y1 = current_region["top"]
            x2 = x1 + current_region["width"]
            y2 = y1 + current_region["height"]

            cv2.rectangle(display, (x1, y1), (x2, y2), (0, 255, 0), 2)

            # 오른쪽 아래 리사이즈 핸들
            cv2.rectangle(
                display,
                (x2 - HANDLE_SIZE, y2 - HANDLE_SIZE),
                (x2, y2),
                (0, 0, 255),
                -1
            )

            cv2.putText(
                display,
                f"Region: x={x1}, y={y1}, w={current_region['width']}, h={current_region['height']}",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2
            )

            cv2.imshow("Control", display)

            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                running = False
                break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()