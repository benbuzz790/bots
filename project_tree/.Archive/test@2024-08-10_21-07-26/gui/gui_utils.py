import tkinter as tk
from tkinter import font
import unittest
from typing import Dict, Any, Callable, Tuple
import time

# Color and theme constants
COLORS: Dict[str, str] = {
    "primary": "#3498db",
    "secondary": "#2ecc71",
    "accent": "#e74c3c",
    "background": "#ecf0f1",
    "text": "#2c3e50"
}

THEME: Dict[str, Any] = {
    "font": ("Helvetica", 12),
    "button_bg": COLORS["primary"],
    "button_fg": COLORS["background"],
    "label_fg": COLORS["text"],
    "entry_bg": COLORS["background"],
    "entry_fg": COLORS["text"]
}

def center_window(window: tk.Tk, width: int, height: int) -> None:
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")
    window.update_idletasks()

def create_styled_button(master: tk.Widget, text: str, command: Callable, **kwargs) -> tk.Button:
    button = tk.Button(master, text=text, command=command,
                       bg=THEME["button_bg"], fg=THEME["button_fg"],
                       font=THEME["font"], **kwargs)
    return button

class CustomWidget(tk.Frame):
    def __init__(self, master: tk.Widget, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(bg=COLORS["background"])

def get_scaled_font(base_size: int, scale_factor: float = 1.0) -> tk.font.Font:
    return tk.font.Font(family=THEME["font"][0], size=int(base_size * scale_factor))

def validate_input(input_value: Any, input_type: type) -> bool:
    try:
        input_type(input_value)
        return True
    except ValueError:
        return False

def show_error_message(message: str, parent: tk.Widget) -> None:
    error_label = tk.Label(parent, text=message, fg=COLORS["accent"], bg=COLORS["background"])
    error_label.pack(pady=5)
    parent.after(3000, error_label.destroy)

def simulate_click(widget: tk.Widget) -> None:
    widget.event_generate('<Button-1>')
    widget.event_generate('<ButtonRelease-1>')
    widget.update()

def set_timeout(widget: tk.Widget, timeout: float, callback: Callable) -> None:
    widget.after(int(timeout * 1000), callback)

def log_gui_event(event: str, details: Dict[str, Any]) -> None:
    print(f"GUI Event: {event}")
    for key, value in details.items():
        print(f"  {key}: {value}")

def create_responsive_grid(master: tk.Widget, rows: int, columns: int) -> tk.Frame:
    frame = tk.Frame(master)
    for i in range(rows):
        frame.grid_rowconfigure(i, weight=1)
    for j in range(columns):
        frame.grid_columnconfigure(j, weight=1)
    return frame

def convert_game_state_to_gui(game_state: Dict[str, Any]) -> Dict[str, Any]:
    gui_state = {
        "board": game_state["board"],
        "current_player": game_state["current_player"],
        "winner": game_state.get("winner", None),
        "is_game_over": game_state["is_game_over"]
    }
    return gui_state

def convert_gui_state_to_game(gui_state: Dict[str, Any]) -> Dict[str, Any]:
    game_state = {
        "board": gui_state["board"],
        "current_player": gui_state["current_player"],
        "is_game_over": gui_state["is_game_over"]
    }
    if gui_state["winner"]:
        game_state["winner"] = gui_state["winner"]
    return game_state

def create_tooltip(widget: tk.Widget, text: str) -> None:
    def enter(event):
        x = y = 0
        x, y, _, _ = widget.bbox("insert")
        x += widget.winfo_rootx() + 25
        y += widget.winfo_rooty() + 25

        # creates a toplevel window
        tw = tk.Toplevel(widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=text, justify='left',
                         background="#ffffff", relief='solid', borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

        def leave(event):
            tw.destroy()

        tw.bind('<Leave>', leave)
        widget.bind('<Leave>', leave)

    widget.bind('<Enter>', enter)

def get_widget_state(widget: tk.Widget) -> Dict[str, Any]:
    state = {}
    for key in widget.configure():
        state[key] = widget.cget(key)
    return state

def set_widget_state(widget: tk.Widget, state: Dict[str, Any]) -> None:
    for key, value in state.items():
        try:
            widget.configure({key: value})
        except tk.TclError:
            pass  # Ignore if the option is not configurable

def create_color_scheme(primary: str, secondary: str, accent: str) -> Dict[str, str]:
    return {
        "primary": primary,
        "secondary": secondary,
        "accent": accent,
        "background": "#ffffff",
        "text": "#000000"
    }

def apply_theme(widget: tk.Widget, theme: Dict[str, Any]) -> None:
    for key, value in theme.items():
        try:
            widget.configure({key: value})
        except tk.TclError:
            pass  # Ignore if the option is not configurable
    for child in widget.winfo_children():
        apply_theme(child, theme)

class TestGUIUtils(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the root window during tests

    def tearDown(self):
        self.root.destroy()

    def test_center_window(self):
        window = tk.Toplevel(self.root)
        center_window(window, 200, 200)
        self.assertEqual(window.winfo_width(), 200)
        self.assertEqual(window.winfo_height(), 200)

    def test_create_styled_button(self):
        button = create_styled_button(self.root, "Test", lambda: None)
        self.assertEqual(button.cget("text"), "Test")
        self.assertEqual(button.cget("bg"), THEME["button_bg"])

    def test_custom_widget(self):
        widget = CustomWidget(self.root)
        self.assertEqual(widget.cget("bg"), COLORS["background"])

    def test_get_scaled_font(self):
        font = get_scaled_font(12, 1.5)
        self.assertEqual(font.cget("size"), 18)

    def test_validate_input(self):
        self.assertTrue(validate_input("123", int))
        self.assertFalse(validate_input("abc", int))

    def test_show_error_message(self):
        show_error_message("Test Error", self.root)
        error_labels = [w for w in self.root.winfo_children() if isinstance(w, tk.Label)]
        self.assertEqual(len(error_labels), 1)
        self.assertEqual(error_labels[0].cget("text"), "Test Error")

    def test_simulate_click(self):
        clicked = [False]
        def on_click(event=None):
            clicked[0] = True
        button = tk.Button(self.root, text="Test")
        button.bind('<Button-1>', on_click)
        button.pack()
        self.root.update()
        simulate_click(button)
        self.root.update()
        self.root.after(100, self.root.quit)  # Give some time for the click to be processed
        self.root.mainloop()
        self.assertTrue(clicked[0])

    def test_set_timeout(self):
        called = [False]
        set_timeout(self.root, 0.1, lambda: called.__setitem__(0, True))
        self.root.after(200, self.root.quit)
        self.root.mainloop()
        self.assertTrue(called[0])

    def test_create_responsive_grid(self):
        frame = create_responsive_grid(self.root, 2, 3)
        self.assertEqual(frame.grid_size(), (3, 2))

    def test_convert_game_state_to_gui(self):
        game_state = {"board": [[0, 1], [1, 0]], "current_player": 1, "is_game_over": False}
        gui_state = convert_game_state_to_gui(game_state)
        self.assertEqual(gui_state["board"], game_state["board"])
        self.assertEqual(gui_state["current_player"], game_state["current_player"])
        self.assertIsNone(gui_state["winner"])

    def test_convert_gui_state_to_game(self):
        gui_state = {"board": [[0, 1], [1, 0]], "current_player": 1, "is_game_over": True, "winner": 2}
        game_state = convert_gui_state_to_game(gui_state)
        self.assertEqual(game_state["board"], gui_state["board"])
        self.assertEqual(game_state["winner"], gui_state["winner"])

    def test_create_tooltip(self):
        button = tk.Button(self.root, text="Test")
        button.pack()
        create_tooltip(button, "Tooltip text")
        self.root.update()
        
        def check_tooltip():
            button.event_generate('<Enter>')
            self.root.update()
            tooltips = [w for w in self.root.winfo_children() if isinstance(w, tk.Toplevel)]
            self.assertEqual(len(tooltips), 1)
            button.event_generate('<Leave>')
            self.root.update()
            tooltips = [w for w in self.root.winfo_children() if isinstance(w, tk.Toplevel)]
            self.assertEqual(len(tooltips), 0)
            self.root.quit()

        self.root.after(100, check_tooltip)
        self.root.mainloop()

    def test_get_widget_state(self):
        button = tk.Button(self.root, text="Test")
        state = get_widget_state(button)
        self.assertEqual(state["text"], "Test")

    def test_set_widget_state(self):
        button = tk.Button(self.root)
        set_widget_state(button, {"text": "New Text"})
        self.assertEqual(button.cget("text"), "New Text")

    def test_create_color_scheme(self):
        scheme = create_color_scheme("#ff0000", "#00ff00", "#0000ff")
        self.assertEqual(scheme["primary"], "#ff0000")
        self.assertEqual(scheme["secondary"], "#00ff00")
        self.assertEqual(scheme["accent"], "#0000ff")

    def test_apply_theme(self):
        frame = tk.Frame(self.root)
        label = tk.Label(frame, text="Test")
        apply_theme(frame, {"bg": "#ff0000", "fg": "#ffffff"})
        self.assertEqual(frame.cget("bg"), "#ff0000")
        self.assertEqual(label.cget("fg"), "#ffffff")

if __name__ == "__main__":
    unittest.main()