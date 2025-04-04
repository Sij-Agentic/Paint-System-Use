from mcp.server.fastmcp import FastMCP, Image
from mcp.server.fastmcp.prompts import base
from mcp.types import TextContent
from PIL import Image as PILImage
import math
import time
import sys
import pyautogui
from pywinauto.application import Application
import win32gui
import win32con
from win32api import GetSystemMetrics

import subprocess
from pywinauto.findwindows import ElementNotFoundError

# Disable pywinauto logs to avoid bad file descriptor error
import logging
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
logging.getLogger('pywinauto').handlers = []
logging.getLogger('pywinauto').propagate = False
logging.getLogger('pywinauto').disabled = True



paint_app = None
mcp = FastMCP("Calculator")

# --------------------
# Math Tools
# --------------------

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
# Paint Tools
# --------------------
    """Open Microsoft Paint maximized on secondary monitor"""
    """Draw a rectangle in Paint from (x1,y1) to (x2,y2)"""
    """Add text in Paint"""

import os

@mcp.tool()
async def open_paint() -> dict:
    """Open Microsoft Paint maximized on secondary monitor"""
    try:
        os.startfile("paint_worker_open_paint.bat")
        return {
            "content": [
                TextContent(
                    type="text",
                    text="✅ Paint has been opened successfully and is ready to draw."
                )
            ]
        }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"❌ Paint launch failed: {e}"
                )
            ]
        }

@mcp.tool()
async def draw_rectangle() -> dict:
    """Draw a rectangle in Paint from (x1,y1) to (x2,y2)"""
    try:
        os.startfile("paint_worker_draw_rectangle.bat")
        return {
            "content": [
                TextContent(
                    type="text",
                    text="✅ Rectangle drawing has been triggered."
                )
            ]
        }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"❌ Failed to draw rectangle: {e}"
                )
            ]
        }

@mcp.tool()
async def add_text_in_paint(text: str) -> dict:
    """Add text in Paint"""
    try:
        # First, try to handle the case of multiple windows
        import win32gui
        import win32con
        
        def enum_window_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if "Paint" in title:
                    windows.append(hwnd)
        
        paint_windows = []
        win32gui.EnumWindows(enum_window_callback, paint_windows)
        
        if len(paint_windows) > 1:
            print(f"[Debug] Found {len(paint_windows)} Paint windows, focusing on the first one")
            # Close all but the first window
            for hwnd in paint_windows[1:]:
                try:
                    win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                    time.sleep(0.5)
                except Exception as e:
                    print(f"[Debug] Error closing Paint window: {e}")
        
        # Now connect to the Paint window with a specific strategy
        try:
            # Try connecting to Paint by using a more specific approach
            paint_app = Application(backend="win32").connect(title_re=".*Paint.*", class_name='MSPaintApp')
        except Exception:
            # If that fails, try the original approach
            paint_app = Application(backend="win32").connect(class_name='MSPaintApp')
        
        paint_window = paint_app.top_window()
        paint_window.set_focus()
        paint_window.type_keys("^h")  # Home tab
        time.sleep(0.5)
        paint_window.click_input(coords=(528, 92))  # Text tool
        time.sleep(1.0)

        canvas = paint_window.child_window(class_name='MSPaintView')
        canvas.click_input(coords=(10, 10))  # To activate focus
        time.sleep(0.5)

        # Get canvas bounds and calculate center
        rect = canvas.rectangle()
        center_x = rect.width() // 2
        center_y = rect.height() // 2
        print(f"[Debug] Drawing text at canvas-relative ({center_x}, {center_y})")

        canvas.click_input(coords=(center_x, center_y))
        time.sleep(0.5)

        paint_window.type_keys(text)
        time.sleep(0.5)

        return {
            "content": [TextContent(type="text", text=f"✅ Text '{text}' added to Paint")]
        }

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        return {
            "content": [TextContent(type="text", text=f"❌ Error adding text: {e} Traceback: {tb}")]
        }


# --------------------
# Prompts & Resources
# --------------------
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Return a personalized greeting using the name."""
    return f"Hello, {name}!"

@mcp.prompt()
def review_code(code: str) -> str:
    """Prompt to review a code snippet."""
    return f"Please review this code:\n\n{code}"

@mcp.prompt()
def debug_error(error: str) -> list[base.Message]:
    """Prompt to help debug an error."""
    return [
        base.UserMessage("I'm seeing this error:"),
        base.UserMessage(error),
        base.AssistantMessage("I'll help debug that. What have you tried so far?"),
    ]

# --------------------
# Server Start
# --------------------

if __name__ == "__main__":
    print("MCP Server Starting...")
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        mcp.run()
    else:
        mcp.run(transport="stdio")
