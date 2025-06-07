#!/usr/bin/env python3
import os
import argparse
import logging
import sys
import platform
import subprocess
from pathlib import Path

# Attempt to import pyautogui for screen/window capture. If unavailable, set to None for graceful error handling later.
try:
    import pyautogui
    pyautogui.FAILSAFE = False  # Disable failsafe to prevent unwanted interruptions during automation.
except ImportError:
    pyautogui = None

from PIL import Image

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(lineno)d] %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WindowCapture:
    """
    macOS only: Provides window and fullscreen capture using pyautogui and AppleScript.
    This class centralizes all capture-related logic for maintainability and platform-specific handling.
    """
    @staticmethod
    def check_dependencies():
        # Check for required dependencies and platform. This ensures the tool fails fast with clear errors if misconfigured.
        missing = []
        if pyautogui is None:
            missing.append("pyautogui")
        try:
            import PIL
        except ImportError:
            missing.append("Pillow")
        if platform.system() != "Darwin":
            missing.append("macOS only")
        if missing:
            logger.error(f"Missing or unsupported: {', '.join(missing)}")
            logger.error("Install with: pip install pyautogui pillow")
            return False
        return True

    @staticmethod
    def list_windows():
        """
        Print all available windows (app name, title, position, size).
        Uses AppleScript to enumerate windows, as Python cannot natively access this info on macOS.
        """
        script = '''
        tell application "System Events"
            set windowList to {}
            repeat with proc in (every process whose background only is false)
                try
                    set procName to name of proc
                    repeat with win in (every window of proc)
                        try
                            set winName to name of win
                            set winPos to position of win
                            set winSize to size of win
                            set x to item 1 of winPos
                            set y to item 2 of winPos
                            set w to item 1 of winSize
                            set h to item 2 of winSize
                            if w > 10 and h > 10 then
                                if winName is "" then set winName to "<" & procName & ">"
                                set end of windowList to procName & "|" & winName & "|" & x & "|" & y & "|" & w & "|" & h
                            end if
                        end try
                    end repeat
                end try
            end repeat
            return windowList
        end tell
        '''
        result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, timeout=15)
        if result.returncode != 0:
            logger.error(f"AppleScript failed: {result.stderr}")
            return
        windows_data = result.stdout.strip()
        if not windows_data or windows_data == "{}":
            logger.error("No windows found")
            return
        content = windows_data[1:-1] if windows_data.startswith('{') and windows_data.endswith('}') else windows_data
        items = [i.strip().strip('"') for i in content.split(',') if i.strip()]
        print("\nAvailable Windows:")
        for i, item in enumerate(items, 1):
            parts = item.split('|')
            if len(parts) == 6:
                proc_name, win_name, x, y, w, h = parts
                print(f"{i:2d}. [{proc_name}] {win_name}  ({x},{y}) {w}x{h}")

    @staticmethod
    def get_window_info(app_name=None, window_title=None):
        """
        Return window info only if app_name or title is an exact match (case-insensitive).
        Uses AppleScript for window enumeration, as this is not possible natively in Python on macOS.
        """
        if not WindowCapture.check_dependencies():
            return None
        script = '''
        tell application "System Events"
            set windowList to {}
            repeat with proc in (every process whose background only is false)
                try
                    set procName to name of proc
                    repeat with win in (every window of proc)
                        try
                            set winName to name of win
                            set winPos to position of win
                            set winSize to size of win
                            set x to item 1 of winPos
                            set y to item 2 of winPos
                            set w to item 1 of winSize
                            set h to item 2 of winSize
                            if w > 10 and h > 10 then
                                if winName is "" then set winName to "<" & procName & ">"
                                set end of windowList to procName & "|" & winName & "|" & x & "|" & y & "|" & w & "|" & h
                            end if
                        end try
                    end repeat
                end try
            end repeat
            return windowList
        end tell
        '''
        result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, timeout=15)
        if result.returncode != 0:
            logger.error(f"AppleScript failed: {result.stderr}")
            return None
        windows_data = result.stdout.strip()
        if not windows_data or windows_data == "{}":
            logger.error("No windows found")
            return None
        windows = []
        content = windows_data[1:-1] if windows_data.startswith('{') and windows_data.endswith('}') else windows_data
        items = [i.strip().strip('"') for i in content.split(',') if i.strip()]
        for item in items:
            parts = item.split('|')
            if len(parts) == 6:
                try:
                    proc_name, win_name, x, y, w, h = parts
                    x, y, w, h = int(float(x)), int(float(y)), int(float(w)), int(float(h))
                    windows.append((proc_name, win_name, x, y, w, h))
                except Exception:
                    continue
        # Only exact match (case-insensitive) to avoid ambiguity and ensure user intent.
        for proc_name, win_name, x, y, w, h in windows:
            try:
                # Convert all coordinates to integers
                x, y, w, h = int(round(float(x))), int(round(float(y))), int(round(float(w))), int(round(float(h)))
                if app_name and proc_name.lower() == app_name.lower():
                    return (proc_name, win_name, x, y, w, h)
                if window_title and win_name.lower() == window_title.lower():
                    return (proc_name, win_name, x, y, w, h)
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid window coordinates for {proc_name} - {win_name}: x={x}, y={y}, w={w}, h={h}. Error: {e}")
                continue
                
        logger.error("No exact matching window found with valid coordinates")
        return None

    @staticmethod
    def capture_window(x, y, width, height, output_path, left_third_only=False):
        """
        Capture a window region using pyautogui and save to the specified path.
        
        Args:
            x (int): X coordinate of the top-left corner
            y (int): Y coordinate of the top-left corner
            width (int): Width of the capture region
            height (int): Height of the capture region
            output_path (str): Path to save the screenshot
            
        Returns:
            bool: True if capture was successful, False otherwise
        """
        try:
            if not pyautogui:
                logger.error("pyautogui is required for capturing")
                return False
                
            # Ensure all parameters are integers
            x = int(x)
            y = int(y)
            width = int(width) /3 
            height = int(height)
            
            # Validate dimensions
            if width <= 0 or height <= 0:
                logger.error(f"Invalid dimensions: {width}x{height}")
                return False
                
            logger.debug(f"Capturing region: x={x}, y={y}, width={width}, height={height}")
            screenshot = pyautogui.screenshot(region=(x, y, width, height))
            screenshot.save(output_path)
            logger.info(f"Captured window saved: {output_path}")
            return True
        except ValueError as ve:
            logger.error(f"Invalid coordinate values - x:{x}, y:{y}, width:{width}, height:{height}. Error: {str(ve)}")
            return False
        except Exception as e:
            logger.error(f"Capture failed: {str(e)}", exc_info=True)
            return False

def resize_window(app_name, win_name, width, height):
    """
    Resize a window using AppleScript.
    
    Args:
        app_name (str): Name of the application
        win_name (str): Title of the window to resize
        width (int): New width in pixels
        height (int): New height in pixels
    """
    try:
        # Ensure width and height are integers
        width = int(width)
        height = int(height)
        
        # Validate dimensions
        if width <= 0 or height <= 0:
            logger.error(f"Invalid dimensions for resize: {width}x{height}")
            return False
            
        script = f'''
        tell application "System Events"
            try
                set proc to first process whose name is "{app_name}"
                set win to first window of proc whose name is "{win_name}"
                set size of win to {{{width}, {height}}}
                return "OK"
            on error errMsg
                return "ERROR: " & errMsg
            end try
        end tell
        '''
        
        logger.debug(f"Resizing window '{win_name}' to {width}x{height}")
        result = subprocess.run(['osascript', '-e', script], 
                              capture_output=True, 
                              text=True,
                              timeout=10)  # Add timeout to prevent hanging
        
        if result.returncode != 0 or result.stderr:
            logger.error(f"Resize failed: {result.stderr}")
            return False
            
        if result.stdout and result.stdout.strip() != "OK":
            logger.error(f"Resize failed: {result.stdout.strip()}")
            return False
            
        logger.debug(f"Successfully resized window to {width}x{height}")
        return True
        
    except ValueError as ve:
        logger.error(f"Invalid dimensions: {width}x{height}. Error: {ve}")
        return False
    except subprocess.TimeoutExpired:
        logger.error("Window resize operation timed out")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during window resize: {str(e)}", exc_info=True)
        return False

def activate_app_window(app_name=None, window_name=None):
    """
    Activate a window by application name and/or window title.
    
    Args:
        app_name (str, optional): Name of the application
        window_name (str, optional): Title of the window to activate
    """
    try:
        if not app_name and not window_name:
            logger.error("Either app_name or window_name must be provided")
            return False
            
        if app_name and window_name:
            # Activate specific window by title within the app
            script = f'''
            tell application "System Events"
                try
                    set appProc to first application process whose name is "{app_name}"
                    set targetWindow to first window of appProc whose name is "{window_name}"
                    set frontmost of appProc to true
                    perform action "AXRaise" of targetWindow
                    return true
                on error errMsg
                    return "ERROR: " & errMsg
                end try
            end tell
            '''
        elif app_name:
            # Just activate the app
            script = f'tell application "{app_name}" to activate'
        else:
            # Find window by title across all apps
            script = f'''
            tell application "System Events"
                try
                    set appProc to first application process whose (exists window whose name is "{window_name}")
                    set targetWindow to first window of appProc whose name is "{window_name}"
                    set frontmost of appProc to true
                    perform action "AXRaise" of targetWindow
                    return true
                on error errMsg
                    return "ERROR: " & errMsg
                end try
            end tell
            '''
            
        result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, timeout=5)
        
        if result.returncode != 0 or (result.stdout and 'ERROR:' in result.stdout):
            error_msg = result.stderr or result.stdout or 'Unknown error'
            logger.warning(f"Failed to activate window - app: {app_name}, name: {window_name}, error: {error_msg}")
            return False
            
        logger.debug(f"Activated window - app: {app_name}, name: {window_name}")
        return True
        
    except Exception as e:
        logger.warning(f"Error in activate_app - app: {app_name}, title: {window_title}, error: {str(e)}")
        return False

def send_key_applescript(app_name=None, window_name=None, key=None):
    """
    Send a keystroke to a specific application or window.
    
    Args:
        app_name (str, optional): Name of the application
        window_name (str, optional): Title of the target window
        key (str): The key to send (e.g., 'right', 'left', 'space')
    """
    if not key:
        logger.error("No key specified to send")
        return False
        
    try:
        # First, activate the window if app_name or window_name is provided
        if app_name or window_name:
            if not activate_app_window(app_name, window_name):
                logger.warning(f"Failed to activate window before sending key - app: {app_name}, name: {window_name}")
                return False
        
        # Send the key using System Events
        key_map = {
            'right': 'key code 124',  # Right arrow
            'left': 'key code 123',   # Left arrow
            'up': 'key code 126',     # Up arrow
            'down': 'key code 125',   # Down arrow
            'space': 'key code 49',   # Space
            'return': 'key code 36',  # Return/Enter
            'escape': 'key code 53',  # Escape
            'tab': 'key code 48',     # Tab
        }
        
        # Get the key code or use keystroke as fallback
        key_command = key_map.get(key.lower(), f'keystroke "{key}"')
        
        script = f'''
        tell application "System Events"
            {key_command}
        end tell
        '''
        
        result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, timeout=5)
        
        if result.returncode != 0:
            error_msg = result.stderr or result.stdout or 'Unknown error'
            logger.warning(f"Failed to send key '{key}' - app: {app_name}, name: {window_name}, error: {error_msg}")
            return False
            
        logger.debug(f"Sent key '{key}' to app: {app_name}, window: {window_name}")
        return True
        
    except Exception as e:
        logger.warning(f"Error sending key '{key}' - app: {app_name}, name: {window_name}, error: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='macOS Window Capture Tool (PNG, batch, margin, resize)')
    parser.add_argument('--output', '-O', default='output', help='출력 디렉토리 (default: output)')
    parser.add_argument('--app', '-A', default='Windows App', help='캡처할 앱 이름 (정확히 일치, 대소문자 무시)')
    parser.add_argument('--window-name', '-N', default='Mini PC', help='캡처할 윈도우 타이틀 (정확히 일치, 대소문자 무시)')
    parser.add_argument('--width', '-W', default=2880, type=int, help='캡처할 윈도우 너비 (pixels)')
    parser.add_argument('--height', '-H', default=1800, type=int, help='캡처할 윈도우 높이 (pixels)')
    parser.add_argument('--book-title', '-T', default='book', help='파일명 접두어')
    parser.add_argument('--start', '-S', default=1, type=int, help='시작 페이지 번호 (default: 1)')
    parser.add_argument('--end', '-E', default=5, type=int, help='캡처할 페이지 수 (default: 1)')
    parser.add_argument('--next', default='right', help='다음 페이지로 이동하기 위한 키 입력 (예: right)')
    parser.add_argument('--delay', '-D', default=0.1, type=float,  help='각 캡처 사이의 지연 시간 (초) (default: 0.5)')
    parser.add_argument('--top-margin', '-TM', default = 50, type=int, help='캡처 영역 상단 마진 (pixels)')
    parser.add_argument('--bottom-margin', '-BM', default =50, type=int, help='캡처 영역 하단 마진 (pixels)')
    parser.add_argument('--left-margin', '-LM', default = 0, type=int, help='캡처 영역 왼쪽 마진 (pixels)')
    parser.add_argument('--right-margin', '-RM', default = 0, type=int, help='캡처 영역 오른쪽 마진 (pixels)')
    parser.add_argument('--log', '-L', default='INFO', help='로그 레벨 (default: INFO)')

    args = parser.parse_args()
    logger.setLevel(args.log)

    if not WindowCapture.check_dependencies():
        sys.exit(1)

    output_dir = Path(args.output) / args.book_title
    output_dir.mkdir(parents=True, exist_ok=True)

    info = WindowCapture.get_window_info(args.app, args.window_name)
    if not info:
        sys.exit(1)
    proc_name, win_name, x, y, w, h = info
    
    x += args.left_margin
    y += args.top_margin
    w -= args.left_margin + args.right_margin
    h -= args.top_margin + args.bottom_margin

    import time
    
    pad  = len(str(args.end))
    for i in range(args.end - args.start + 1):
        current_page_num = i + args.start
        output_path_page = output_dir / f'{args.book_title}_{current_page_num:0{pad}d}.png'

        # 1. Focus the specific window by both app name and window title
        if not activate_app_window(app_name=proc_name, window_name=win_name):
            logger.error(f"Failed to focus window - app: {proc_name}, title: {win_name}")
            sys.exit(1)
            
        # 2. Wait for 0.1 seconds after focusing
        time.sleep(0.1)
        
        # 3. Capture the window
        logger.info(f"Capturing page {current_page_num}...")
        WindowCapture.capture_window(x,y,w,h,str(output_path_page))

        # 4. Go to next page if not the last page
        if i < (args.end - args.start) and args.next:
            try:
                # 5. Send next page key to the specific window
                logger.debug(f"Sending next page key: {args.next}")
                if not send_key_applescript(app_name=proc_name, window_name=win_name, key=args.next):
                    logger.warning(f"Failed to send next page key: {args.next}")
                
                # 6. Additional delay if specified
                if args.delay > 0: time.sleep(args.delay)

            except Exception as e:
                logger.warning(f"Next page action failed: {e}", exc_info=True)

if __name__ == '__main__':
    main()