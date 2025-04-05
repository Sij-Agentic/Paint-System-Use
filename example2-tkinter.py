from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent
import asyncio
import threading
import pyautogui
import time
import sys
import tkinter as tk
import math

# Create MCP server
mcp = FastMCP("CanvasDraw")

# Shared state
app_ready = threading.Event()
canvas_origin = (200, 100)
drawing_app = None



@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two integers and return the result."""
    return a + b

@mcp.tool()
def subtract(a: int, b: int) -> int:
    """Subtract b from a and return the result."""
    return a - b

@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two integers and return the result."""
    return a * b

@mcp.tool()
def divide(a: int, b: int) -> float:
    """Divide a by b and return the result as a float."""
    return a / b

@mcp.tool()
def power(a: int, b: int) -> int:
    """Return a raised to the power of b."""
    return a ** b

@mcp.tool()
def sqrt(a: int) -> float:
    """Return the square root of a."""
    return a ** 0.5

@mcp.tool()
def cbrt(a: int) -> float:
    """Return the cube root of a."""
    return a ** (1 / 3)

@mcp.tool()
def factorial(a: int) -> int:
    """Return the factorial of a."""
    return math.factorial(a)

@mcp.tool()
def log(a: int) -> float:
    """Return the natural logarithm of a."""
    return math.log(a)

@mcp.tool()
def remainder(a: int, b: int) -> int:
    """Return the remainder when a is divided by b."""
    return a % b

@mcp.tool()
def sin(a: int) -> float:
    """Return the sine of a (in radians)."""
    return math.sin(a)

@mcp.tool()
def cos(a: int) -> float:
    """Return the cosine of a (in radians)."""
    return math.cos(a)

@mcp.tool()
def tan(a: int) -> float:
    """Return the tangent of a (in radians)."""
    return math.tan(a)

@mcp.tool()
def add_list(l: list) -> int:
    """Return the sum of a list of integers."""
    return sum(l)

@mcp.tool()
def strings_to_chars_to_int(string: str) -> list[int]:
    """Convert each character in a string to its ASCII integer value."""
    return [ord(char) for char in string]

@mcp.tool()
def int_list_to_exponential_sum(int_list: list) -> float:
    """Return the sum of the exponentials of a list of integers."""
    return sum(math.exp(i) for i in int_list)

@mcp.tool()
def fibonacci_numbers(n: int) -> list:
    """Return the first n numbers in the Fibonacci sequence."""
    if n <= 0:
        return []
    fib = [0, 1]
    for _ in range(2, n):
        fib.append(fib[-1] + fib[-2])
    return fib[:n]

# --------------------
# Tkinter Drawing App
# --------------------

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
        if self.entry:
            return  # Only one text box
        x1, y1, x2, y2 = self.canvas.coords(self.rect)
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        self.entry = tk.Entry(self.root, font=("Arial", 16), justify="center")
        self.canvas.create_window((center_x, center_y), window=self.entry)
        self.entry.focus_set()

    def run(self):
        app_ready.set()
        self.root.mainloop()

def launch_drawing_app():
    global drawing_app
    drawing_app = DrawingApp()
    drawing_app.run()

# --------------------
# MCP Tool Definitions
# --------------------

@mcp.tool()
async def open_canvas() -> dict:
    """Open a Tkinter-based drawing canvas window."""
    try:
        if not app_ready.is_set():
            threading.Thread(target=launch_drawing_app, daemon=True).start()
            app_ready.wait()
            time.sleep(1)
            return {
                "content": [TextContent(type="text", text="✅ Canvas window opened and ready.")]
            }
        return {
            "content": [TextContent(type="text", text="✅ Canvas already open.")]
        }
    except Exception as e:
        return {
            "content": [TextContent(type="text", text=f"❌ Failed to open canvas: {e}")]
        }

@mcp.tool()
async def draw_rectangle() -> dict:
    """Draw a visible rectangle using simulated mouse drag."""
    try:
        if not app_ready.is_set():
            return {
                "content": [TextContent(type="text", text="❌ Canvas is not ready.")]
            }

        start = (canvas_origin[0] + 100, canvas_origin[1] + 100)
        end   = (canvas_origin[0] + 500, canvas_origin[1] + 300)

        pyautogui.moveTo(start)
        pyautogui.mouseDown()
        pyautogui.moveTo(end, duration=1)
        pyautogui.mouseUp()
        time.sleep(0.5)

        return {
            "content": [TextContent(type="text", text="✅ Rectangle drawing has been triggered.")]
        }
    except Exception as e:
        return {
            "content": [TextContent(type="text", text=f"❌ Failed to draw rectangle: {e}")]
        }

@mcp.tool()
async def add_text(text: str) -> dict:
    """Simulate typing text into the canvas window."""
    try:
        if not app_ready.is_set():
            return {
                "content": [TextContent(type="text", text="❌ Canvas is not ready.")]
            }

        target = (canvas_origin[0] + 300, canvas_origin[1] + 200)
        pyautogui.moveTo(target)
        pyautogui.click()
        time.sleep(0.3)
        pyautogui.write(text, interval=0.1)

        return {
            "content": [TextContent(type="text", text=f"✅ Text '{text}' added to canvas.")]
        }
    except Exception as e:
        return {
            "content": [TextContent(type="text", text=f"❌ Error adding text: {e}")]
        }

# --------------------
# Start MCP Server
# --------------------

if __name__ == "__main__":
    print("MCP Tkinter Server Starting...")
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        mcp.run()
    else:
        mcp.run(transport="stdio")
