import ctypes
import pygetwindow as gw
import pyautogui
import time

def wait_for_paint_focus(timeout=30):
    print("⏳ Waiting for Paint to be focused...")
    for i in range(timeout):
        win = gw.getActiveWindow()
        if win and "Paint" in win.title:
            print("✅ Paint is now focused!")
            return True
        time.sleep(3)
    print("❌ Timeout: Paint was never focused")
    return False


def open_paint():
    SW_SHOW = 5
    ctypes.windll.shell32.ShellExecuteW(None, "open", "mspaint.exe", None, None, SW_SHOW)
    time.sleep(3)

def focus_paint_window():
    for window in gw.getWindowsWithTitle("Paint"):
        if window.isMinimized:
            window.restore()
            time.sleep(0.5)
        window.activate()
        time.sleep(0.5)
        if window.isActive:
            print("✅ Paint window is active")
            return True
    return False

def draw_rectangle():
    if not focus_paint_window():
        if not wait_for_paint_focus():
            print("❌ Cannot proceed, Paint is not in focus.")
            return

    print("🖌 Drawing rectangle now...")

    # Get the Paint window dimensions
    window = gw.getWindowsWithTitle("Paint")[0]
    center_x = window.left + window.width // 2
    center_y = window.top + window.height // 2

    # Clear any active selections and ensure canvas is ready
    pyautogui.press("esc")
    time.sleep(2.0)
    
    # Activate the canvas by clicking in the center
    pyautogui.moveTo(center_x, center_y)
    pyautogui.click()
    time.sleep(2.0)

    # Select the rectangle tool
    pyautogui.moveTo(659, 105)
    pyautogui.click()
    time.sleep(1.0)

    # Click canvas again to ensure it's active
    pyautogui.moveTo(center_x, center_y)
    pyautogui.click()
    time.sleep(1.0)

    # Draw the rectangle relative to the center
    start_x = center_x - 100
    start_y = center_y - 100
    end_x = center_x + 100
    end_y = center_y + 100
    
    pyautogui.moveTo(start_x, start_y)
    pyautogui.mouseDown()
    pyautogui.moveTo(end_x, end_y, duration=0.5)
    pyautogui.mouseUp()
    time.sleep(0.5)

    # Final click to commit the rectangle
    pyautogui.moveTo(center_x, center_y)
    pyautogui.click()
    print("✅ Rectangle drawn and should persist.")


import sys

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python paint_worker.py [open_paint|draw_rectangle|add_text_in_paint]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "open_paint":
        open_paint()
    elif command == "draw_rectangle":
        draw_rectangle()
    elif command == "add_text_in_paint":
        if len(sys.argv) < 3:
            print("Please provide text to add.")
            sys.exit(1)
        text = sys.argv[2]
        #add_text_in_paint(text)
    else:
        print(f"Unknown command: {command}")

