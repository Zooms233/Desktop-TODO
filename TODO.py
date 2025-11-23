import customtkinter as ctk
import tkinter as tk
import json
import os
import ctypes

# --- 1. 强制开启高DPI感知 ---
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except:
        pass

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")


class StickyNotesApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Desktop TODO")
        self.overrideredirect(True)
        self.attributes("-alpha", 0.92)
        self.attributes("-topmost", True)

        # 状态变量
        self.tasks = []
        self.current_scaling = 1.0
        self.is_topmost = True

        # 初始化布局
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.create_title_bar()
        self.create_input_area()
        self.create_task_list()
        self.create_resize_grip()

        self.load_tasks()
        self.load_window_position()  # 启动时加载位置

        # 绑定退出事件
        self.bind("<Escape>", lambda e: self.close_app())

        # 初始化拖拽变量
        self.x_pos = 0
        self.y_pos = 0

    def close_app(self):
        """关闭程序前保存位置"""
        self.save_window_position()
        self.quit()

    # --- 核心工具：获取缩放比例 ---
    def update_scaling_factor(self):
        try:
            hwnd = self.winfo_id()
            dpi = ctypes.windll.user32.GetDpiForWindow(hwnd)
            self.current_scaling = dpi / 96.0
        except:
            self.current_scaling = ctk.ScalingTracker.get_widget_scaling(self)

        if self.current_scaling == 0:
            self.current_scaling = 1.0

    # --- 窗口调整逻辑 ---
    def start_resize(self, event):
        self.update_scaling_factor()

    def resize_window(self, event):
        mouse_x_root = event.x_root
        mouse_y_root = event.y_root
        win_x_root = self.winfo_rootx()
        win_y_root = self.winfo_rooty()

        target_width_phys = mouse_x_root - win_x_root
        target_height_phys = mouse_y_root - win_y_root

        new_w_logical = int(target_width_phys / self.current_scaling)
        new_h_logical = int(target_height_phys / self.current_scaling)

        new_w_logical = max(250, new_w_logical)
        new_h_logical = max(300, new_h_logical)

        self.geometry(f"{new_w_logical}x{new_h_logical}")

    # --- 窗口拖拽逻辑 ---
    def start_drag(self, event):
        self.x_pos = event.x
        self.y_pos = event.y

    def drag_window(self, event):
        x = self.winfo_x() + event.x - self.x_pos
        y = self.winfo_y() + event.y - self.y_pos
        self.geometry(f"+{x}+{y}")

    # --- UI 组件 ---
    def create_resize_grip(self):
        self.grip = ctk.CTkLabel(self, text="◢", font=("Arial", 12), text_color="#444")
        self.grip.place(relx=1.0, rely=1.0, anchor="se", x=0, y=0)
        self.grip.configure(cursor="size_nw_se")
        self.grip.bind("<Button-1>", self.start_resize)
        self.grip.bind("<B1-Motion>", self.resize_window)

    def load_window_position(self):
        try:
            if os.path.exists("position.json"):
                with open("position.json", "r") as f:
                    d = json.load(f)
                # geometry 接收的是逻辑大小，position.json 里保存的现在也是逻辑大小了
                self.geometry(
                    f"{d.get('width',300)}x{d.get('height',450)}+{d.get('x',0)}+{d.get('y',0)}"
                )
            else:
                self.geometry("300x450")
        except:
            self.geometry("300x450")

    # --- [关键修复] 保存逻辑 ---
    def save_window_position(self):
        try:
            # 1. 必须先更新缩放比例，确保 current_scaling 是最新的
            self.update_scaling_factor()

            # 2. 获取当前的物理尺寸
            phys_width = self.winfo_width()
            phys_height = self.winfo_height()

            # 3. 转换为逻辑尺寸 (物理 / 缩放比例)
            # geometry() 函数期望的是逻辑尺寸，所以我们需要保存逻辑尺寸
            logical_width = int(phys_width / self.current_scaling)
            logical_height = int(phys_height / self.current_scaling)

            # 4. 位置坐标 (x, y)
            # 在 Windows High DPI Awareness 模式下，geometry("+x+y") 通常直接使用屏幕物理坐标
            # 所以 x 和 y 不需要除以缩放比例 (除非你发现位置也发生巨大漂移)
            x = self.winfo_x()
            y = self.winfo_y()

            d = {
                "width": logical_width,
                "height": logical_height,
                "x": x,
                "y": y,
            }
            with open("position.json", "w") as f:
                json.dump(d, f, indent=2)
        except Exception as e:
            print(f"Error saving position: {e}")

    # --- UI 组件构建 ---
    def create_title_bar(self):
        self.title_frame = ctk.CTkFrame(
            self, height=40, fg_color="#202020", corner_radius=0
        )
        self.title_frame.grid(row=0, column=0, sticky="ew")
        self.title_frame.bind("<Button-1>", self.start_drag)
        self.title_frame.bind("<B1-Motion>", self.drag_window)

        ctk.CTkLabel(self.title_frame, text="📌 My Todo", text_color="#e0e0e0").pack(
            side="left", padx=10
        )

        # 关闭按钮调用 close_app
        ctk.CTkButton(
            self.title_frame,
            text="✕",
            width=30,
            fg_color="transparent",
            hover_color="#c42b1c",
            command=self.close_app,
        ).pack(side="right", padx=5)

        self.top_btn = ctk.CTkButton(
            self.title_frame,
            text="📌",
            width=30,
            fg_color="transparent",
            command=self.toggle_topmost,
        )
        self.top_btn.pack(side="right")

    def create_input_area(self):
        f = ctk.CTkFrame(self, fg_color="transparent")
        f.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        self.task_entry = ctk.CTkEntry(
            f,
            placeholder_text="New Task...",
            height=35,
            border_width=0,
            fg_color="#2b2b2b",
        )
        self.task_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.task_entry.bind("<Return>", self.add_task)
        ctk.CTkButton(f, text="+", width=35, height=35, command=self.add_task).pack(
            side="right"
        )

    def create_task_list(self):
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)

    # --- 业务逻辑 ---
    def toggle_topmost(self):
        self.is_topmost = not self.is_topmost
        self.attributes("-topmost", self.is_topmost)
        self.top_btn.configure(fg_color="transparent" if self.is_topmost else "#333")

    def add_task(self, e=None):
        if t := self.task_entry.get().strip():
            self.tasks.append({"text": t, "completed": False})
            self.task_entry.delete(0, "end")
            self.render_tasks()
            self.save_tasks()

    def render_tasks(self):
        for w in self.scroll_frame.winfo_children():
            w.destroy()
        for i, t in enumerate(self.tasks):
            f = ctk.CTkFrame(self.scroll_frame, fg_color="#2b2b2b")
            f.pack(fill="x", pady=2)
            cb = ctk.CTkCheckBox(
                f, text="", width=24, command=lambda v=i: self.toggle(v)
            )
            if t["completed"]:
                cb.select()
            cb.pack(side="left", padx=5, pady=5)
            ctk.CTkLabel(
                f, text=t["text"], text_color="#666" if t["completed"] else "#e0e0e0"
            ).pack(side="left")
            ctk.CTkButton(
                f,
                text="✕",
                width=20,
                fg_color="transparent",
                hover_color="red",
                command=lambda v=i: self.del_task(v),
            ).pack(side="right")

    def toggle(self, i):
        self.tasks[i]["completed"] = not self.tasks[i]["completed"]
        self.render_tasks()
        self.save_tasks()

    def del_task(self, i):
        del self.tasks[i]
        self.render_tasks()
        self.save_tasks()

    def load_tasks(self):
        if os.path.exists("tasks.json"):
            with open("tasks.json", "r") as f:
                self.tasks = json.load(f)

    def save_tasks(self):
        with open("tasks.json", "w") as f:
            json.dump(self.tasks, f)


if __name__ == "__main__":
    app = StickyNotesApp()
    app.mainloop()
