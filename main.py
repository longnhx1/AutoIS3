import cv2
import numpy as np
import subprocess
import time
import random

# --- CẤU HÌNH ---
ADB_DEVICE = "127.0.0.1:7555" 

# --- CÁC HÀM HỖ TRỢ ---
def adb_screencap():
    cmd = f"adb -s {ADB_DEVICE} exec-out screencap -p"
    pipe = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    image_bytes = pipe.stdout.read()
    if not image_bytes: return None
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    return cv2.imdecode(image_array, cv2.IMREAD_COLOR)

def adb_tap(x, y):
    x = x + random.randint(-3, 3)
    y = y + random.randint(-3, 3)
    cmd = f"adb -s {ADB_DEVICE} shell input tap {x} {y}"
    subprocess.call(cmd, shell=True)

def adb_swipe(x1, y1, x2, y2, duration=300):
    cmd = f"adb -s {ADB_DEVICE} shell input swipe {x1} {y1} {x2} {y2} {duration}"
    subprocess.call(cmd, shell=True)
    time.sleep(0.5)

def find_and_click(template_name, screen_img, threshold=0.8):
    if screen_img is None: return False
    path = f"images/{template_name}"
    template = cv2.imread(path, cv2.IMREAD_COLOR)
    if template is None: return False 

    result = cv2.matchTemplate(screen_img, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    if max_val >= threshold:
        h, w = template.shape[:2]
        center_x = max_loc[0] + w // 2
        center_y = max_loc[1] + h // 2
        print(f"[FOUND] {template_name} ({int(max_val*100)}%)")
        adb_tap(center_x, center_y)
        return True
    return False

def get_best_match(template_name, screen_img, threshold=0.8):
    path = f"images/{template_name}"
    template = cv2.imread(path, cv2.IMREAD_COLOR)
    if template is None: return None

    result = cv2.matchTemplate(screen_img, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    if max_val >= threshold:
        h, w = template.shape[:2]
        center_x = max_loc[0] + w // 2
        center_y = max_loc[1] + h // 2
        return {"name": template_name, "x": center_x, "y": center_y, "score": max_val}
    return None

# --- HÀM DI CHUYỂN MAP (ĐÃ TINH GIẢN TỐI ĐA) ---
def smart_map_move(screen):
    """
    Chỉ tìm những node QUAN TRỌNG NHẤT mà bạn chắc chắn có ảnh.
    Các node lạ (Wish, Mystery, Key...) sẽ để cho Blind Click lo.
    """
    # Rút gọn danh sách, chỉ giữ lại những file ảnh cơ bản
    # Các file này bắt buộc phải có trong thư mục images
    node_types = [
        "node_emergency.png", 
        "node_boss.png", 
        "node_combat.png", 
        "node_shop.png",
        "node_encounter.png" 
    ]
    
    found_nodes = []
    
    for node_name in node_types:
        match = get_best_match(node_name, screen, threshold=0.75)
        if match:
            # Chỉ lấy node nằm ở phía bên phải (Tương lai)
            # Tọa độ > 500 để tránh click nhầm vào node hiện tại đang đứng
            if match["x"] > 500: 
                found_nodes.append(match)

    if not found_nodes:
        return False

    # Sắp xếp từ trái sang phải -> Chọn cái gần nhất
    found_nodes.sort(key=lambda k: k['x'])
    best_node = found_nodes[0]
    
    print(f"   -> Chọn node (Nhận diện): {best_node['name']}")
    adb_tap(best_node['x'], best_node['y'])
    time.sleep(3) 
    return True

# --- CÁC HÀM CŨ ---
def select_best_operator():
    print("   -> Chọn tướng...")
    screen = adb_screencap()
    if find_and_click("icon_temporary.png", screen, 0.75): pass
    else:
        adb_swipe(1000, 400, 200, 400, 200)
        adb_swipe(1000, 400, 200, 400, 200)
        time.sleep(1)
        screen_end = adb_screencap()
        if find_and_click("icon_temporary.png", screen_end, 0.75): pass
        elif find_and_click("icon_hope_0.png", screen_end, 0.85): pass
        elif find_and_click("icon_hope_2.png", screen_end, 0.85): pass
        else: adb_tap(850, 350)
    time.sleep(0.5)
    for _ in range(3):
        if find_and_click("btn_confirm_recruit.png", adb_screencap()): break
        if _ == 2: adb_tap(1150, 680)
        time.sleep(0.5)
    time.sleep(4)
    adb_tap(640, 360)
    time.sleep(1.5)

def handle_skip_loot():
    print("--- SKIP LOOT ---")
    screen = adb_screencap()
    if find_and_click("btn_skip_loot.png", screen):
        print("   -> Skip!")
    else:
        adb_swipe(1000, 500, 200, 500, 250)
        adb_swipe(1000, 500, 200, 500, 250)
        time.sleep(1)
        if not find_and_click("btn_skip_loot.png", adb_screencap()):
            adb_tap(1100, 600)
    time.sleep(1.5)
    if not find_and_click("btn_confirm_leave.png", adb_screencap()):
        if not find_and_click("btn_check_confirm.png", adb_screencap()):
             adb_tap(800, 500)
    time.sleep(3)

def start_new_run():
    print("--- START RUN ---")
    
    # Check chọn độ khó (Surging Waves)
    screen = adb_screencap()
    if find_and_click("btn_difficulty_entry.png", screen):
        time.sleep(1.5)
        loop_scroll = 0
        while True:
            screen_diff = adb_screencap()
            if find_and_click("icon_scroll_arrow.png", screen_diff, 0.8): 
                adb_swipe(900, 200, 900, 600, duration=400) 
                time.sleep(1)
                loop_scroll += 1
                if loop_scroll > 10: break
            else: break
        
        if not find_and_click("btn_select_difficulty.png", adb_screencap()):
             adb_tap(1150, 350) 
        time.sleep(2) 

    steps = [
        {"img": "btn_explore.png", "action": "Explore"},
        {"img": "icon_mind_over_matter.png", "action": "Squad"},
        {"img": "btn_check_confirm.png", "action": "Confirm"}, 
        {"img": "card_recruit_set.png", "action": "Set"},
        {"img": "btn_check_confirm.png", "action": "Confirm"}
    ]
    for step in steps:
        for _ in range(10): 
            if find_and_click(step["img"], adb_screencap()): 
                time.sleep(1.5)
                break
            time.sleep(0.5)
    print("--- Tuyển quân ---")
    for v_name in ["voucher_vanguard.png", "voucher_sniper.png", "voucher_specialist.png"]:
        for _ in range(5):
            if find_and_click(v_name, adb_screencap()):
                time.sleep(1.5)
                select_best_operator()
                break
            time.sleep(1)
    print("--- Vào Map ---")
    for _ in range(10):
        screen = adb_screencap()
        if find_and_click("btn_enter_map.png", screen):
            time.sleep(5)
            return
        if find_and_click("node_combat.png", screen): return
        time.sleep(1)

# --- MAIN LOOP (CẬP NHẬT BLIND CLICK THÔNG MINH) ---
def main():
    print(f"Connecting to {ADB_DEVICE}...")
    subprocess.call(f"adb connect {ADB_DEVICE}", shell=True)
    print("--- BOT STARTED (Blind Click Fallback) ---")
    
    while True:
        screen = adb_screencap()
        if screen is None: 
            time.sleep(2)
            continue
        
        action_taken = False 

        # 1. MENU & COMBAT
        if find_and_click("btn_explore.png", screen):
            start_new_run()
            continue

        if find_and_click("btn_battle_explore.png", screen): 
            print("   -> VÀO TRẬN (Combat)!")
            time.sleep(10)
            continue
        
        if find_and_click("btn_ready.png", screen, threshold=0.7) or find_and_click("btn_ready_event.png", screen, threshold=0.7):
            print("   -> Ready...")
            time.sleep(2)
            adb_tap(640, 360) 
            continue

        # 2. SHOP EXIT
        if find_and_click("btn_shop_exit.png", screen):
            print("   -> Exit Shop...")
            time.sleep(1.5)
            continue
        if find_and_click("btn_shop_confirm_exit.png", screen):
            print("   -> Confirm Exit Shop!")
            time.sleep(3)
            continue

        # 3. MAP MOVE (Dùng list rút gọn)
        if smart_map_move(screen):
            action_taken = True
            continue

        # 4. INSTANT WIN
        if find_and_click("btn_settings.png", screen):
            time.sleep(1)
            if find_and_click("btn_retreat_menu.png", adb_screencap()):
                time.sleep(1)
                if find_and_click("btn_confirm_quit.png", adb_screencap()):
                    print("   -> WIN (Retreat)!")
                    time.sleep(6)
            continue

        # 5. KẾT THÚC
        if find_and_click("label_signal_lost.png", screen):
            print("   -> Signal Lost (Skip)")
            time.sleep(1)
            adb_tap(640, 600)
            time.sleep(2)
            continue

        if find_and_click("label_cleared.png", screen):
            print("   -> CLEARED! Skip Loot...")
            adb_tap(640, 600)
            time.sleep(3)
            handle_skip_loot()
            continue

        if find_and_click("btn_check_confirm.png", screen):
             print("   -> Confirm/Next...")
             adb_tap(640, 600)
             continue
        
        if find_and_click("btn_confirm_event.png", screen):
             print("   -> Confirm Event...")
             adb_tap(640, 600)
             continue

        # ========================================================
        # [QUAN TRỌNG] BLIND CLICK - FALLBACK
        # Nếu không nhận diện được gì, ta sẽ click vào vùng "tiềm năng"
        # ========================================================
        if not action_taken:
            print("   -> [Blind Click] Thử click vùng node/event...")
            
            # Tọa độ này (950, 450) có 2 tác dụng:
            # 1. Nếu đang ở Map: Nó sẽ trúng vào Node tiếp theo (thường nằm bên phải).
            # 2. Nếu đang ở Event: Nó sẽ trúng vào Option 1.
            adb_tap(950, 450)
            
            time.sleep(2) 

        time.sleep(1)

if __name__ == "__main__":
    main()