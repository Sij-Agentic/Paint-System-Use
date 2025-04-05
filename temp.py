import tkinter as tk
import threading
import pyautogui
import time

class DrawingApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AI Canvas")
        self.root.geometry("800x600+200+100")
        self.canvas = tk.Canvas(self.root, width=800, height=600, bg="white")
        self.canvas.pack()

        self.start_x = None
        self.start_y = None
        self.rect = None
        self.entry = None

        self.canvas.bind("<ButtonPress-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.drawing)
        self.canvas.bind("<ButtonRelease-1>", self.finish_draw)

    def start_draw(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline="black", width=2)

    def drawing(self, event):
        self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

    def finish_draw(self, event):
        # Prevent adding multiple Entry boxes
        if self.entry:
            return

        # Get final rectangle bounds
        x1, y1, x2, y2 = self.canvas.coords(self.rect)
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2

        # Create Entry at center
        self.entry = tk.Entry(self.root, font=("Arial", 16), justify="center")
        self.canvas.create_window((center_x, center_y), window=self.entry)
        self.entry.focus_set()

    def run(self):
        self.root.mainloop()

def launch_drawing_app():
    app = DrawingApp()
    threading.Thread(target=simulate_mouse_draw_and_type).start()
    app.run()

def simulate_mouse_draw_and_type():
    # Wait for the canvas to load
    time.sleep(2)

    canvas_origin = (200, 100)
    draw_start = (canvas_origin[0] + 100, canvas_origin[1] + 100)
    draw_end = (canvas_origin[0] + 500, canvas_origin[1] + 300)
    entry_click = (canvas_origin[0] + 200, canvas_origin[1] + 150)

    # Simulate rectangle drawing
    pyautogui.moveTo(draw_start)
    pyautogui.mouseDown()
    pyautogui.moveTo(draw_end, duration=1)
    pyautogui.mouseUp()
    time.sleep(1)

    # Simulate typing
    pyautogui.moveTo(entry_click)
    pyautogui.click()
    time.sleep(0.5)
    pyautogui.write("7.599e+33", interval=0.1)
    print("✅ Finished drawing and typing")

if __name__ == "__main__":
    launch_drawing_app()
