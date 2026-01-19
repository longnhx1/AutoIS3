import cv2
import numpy as np
import subprocess
import time
import random
import os

# --- CẤU HÌNH ---
ADB_DEVICE = "127.0.0.1:16384" # Thiết bị thực
SCREEN_WIDTH = 1920  # Độ rộng màn hình
SCREEN_HEIGHT = 1080  # Độ cao màn hình
SCREEN_DPI = 240  # DPI thiết bị
THRESHOLD_DEFAULT = 0.8  # Ngưỡng mặc định để so sánh ảnh
STATUS_INTERVAL = 60  # Hiển thị status mỗi N giây (có thể tùy chỉnh)

# --- CÁC HÀM CƠ BẢN ---
def connect_adb():
    print(f"Connecting to {ADB_DEVICE}...")
    subprocess.call(f"adb connect {ADB_DEVICE}", shell=True)

def adb_screencap():
    """Chụp màn hình để kiểm tra hình ảnh"""
    cmd = f"adb -s {ADB_DEVICE} exec-out screencap -p"
    try:
        pipe = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
        image_bytes = pipe.stdout.read()
        if not image_bytes: return None
        image_array = np.frombuffer(image_bytes, dtype=np.uint8)
        return cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    except:
        return None

def adb_tap(x, y):
    """Click theo tọa độ cứng"""
    # Random nhẹ 1-2 pixel để tránh bị game phát hiện bot
    x = x + random.randint(-2, 2)
    y = y + random.randint(-2, 2)
    cmd = f"adb -s {ADB_DEVICE} shell input tap {x} {y}"
    subprocess.call(cmd, shell=True)

def check_image_exists(template_name, screen_img, threshold=THRESHOLD_DEFAULT):
    """Kiểm tra xem ảnh có xuất hiện không, trả về (found, match_value)"""
    if screen_img is None: return False, 0.0
    
    path = f"images/{template_name}"
    if not os.path.exists(path):
        return False, 0.0

    template = cv2.imread(path, cv2.IMREAD_COLOR)
    if template is None: return False, 0.0

    result = cv2.matchTemplate(screen_img, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(result)

    if max_val >= threshold:
        return True, max_val
    return False, max_val

# --- LOGIC THOÁT TRẬN (TỌA ĐỘ CỨNG) ---
def execute_instant_win_routine():
    print("   -> ⚡ Kích hoạt thoát trận nhanh (Hardcode Click)...")
    
    # 1. Click Settings (Tọa độ cứng của bạn)
    adb_tap(119, 75)
    time.sleep(0.3) # Chờ menu trượt ra
    
    # 2. Click Retreat (Tọa độ cứng)
    adb_tap(1129,492)
    time.sleep(0.2) # Chờ bảng confirm hiện ra
    
    # 3. Click Confirm Quit (Tọa độ cứng)
    adb_tap(1252,736)
    
    print("   -> Đã bấm xác nhận. Chờ màn hình kết quả...")
    time.sleep(0.3) # Chờ animation thua (Mission Failed)

    # 4. Click bỏ qua màn hình kết quả
    adb_tap(1129, 492) # Click giữa màn hình
    adb_tap(1252, 736) # Click thêm phát nữa
    
    print("   -> Hoàn tất. Đợi về Map...")
    time.sleep(3) # Chờ load về map

# --- VÒNG LẶP CHÍNH ---
def main():
    connect_adb()
    print("--- TOOL AUTO WIN ---")
    
    last_status_time = time.time()
    
    while True:
        try:
            # 1. Chụp màn hình
            screen = adb_screencap()
            
            # 2. Kiểm tra: Có nút Settings trên màn hình không?
            found, match_val = check_image_exists("btn_settings.png", screen, threshold=THRESHOLD_DEFAULT)
            
            # Hiển thị status mỗi STATUS_INTERVAL giây
            current_time = time.time()
            if current_time - last_status_time >= STATUS_INTERVAL:
                print(f"[Status] Threshold tìm: {match_val:.3f} | Threshold mặc định: {THRESHOLD_DEFAULT}")
                last_status_time = current_time
            
            if found:
                print("🎯 ĐANG TRONG TRẬN!")
                
                # Chờ 5-10 giây trước khi thực hiện thao tác
                delay = random.randint(5, 10)
                print(f"   -> Chờ {delay}s trước khi thực hiện...")
                time.sleep(delay)
                
                # 3. Thực hiện chuỗi click tọa độ cứng
                execute_instant_win_routine()
                last_status_time = time.time()
            else:
                time.sleep(1.5)

        except KeyboardInterrupt:
            print("\nĐã dừng tool.")
            break
        except Exception as e:
            print(f"\nLỗi: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()
