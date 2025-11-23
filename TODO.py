import customtkinter as ctk
import tkinter as tk
import json
import os
import ctypes

# --- 1. 强制开启高DPI感知 (High DPI Awareness) ---
# 这一步非常重要，它让 Python 获取真实的物理像素坐标
try:
    # awareness = 1 (System DPI Aware), 2 (Per Monitor DPI Aware)
    # 尝试设置为 2，这是最现代的设置
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
        self._save_timer = None
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
        self.load_window_position()  # 加载位置

        self.bind("<Escape>", lambda e: self.quit())
        self.bind("<Configure>", self.on_window_configure)

        # 初始化拖拽变量
        self.x_pos = 0
        self.y_pos = 0

    # --- 核心工具：获取缩放比例 ---
    def update_scaling_factor(self):
        """更新当前的缩放比例"""
        try:
            hwnd = self.winfo_id()
            dpi = ctypes.windll.user32.GetDpiForWindow(hwnd)
            self.current_scaling = dpi / 96.0
        except:
            # 回退方案
            self.current_scaling = ctk.ScalingTracker.get_widget_scaling(self)

        # 确保不会除以0
        if self.current_scaling == 0:
            self.current_scaling = 1.0

    # --- 窗口调整逻辑 (带 Debug) ---
    def start_resize(self, event):
        # 在开始调整时，更新一次缩放比例
        self.update_scaling_factor()

    def resize_window(self, event):
        """
        使用绝对坐标计算法 + Debug 日志
        """
        # 1. 获取鼠标当前的屏幕绝对坐标 (物理像素)
        mouse_x_root = event.x_root
        mouse_y_root = event.y_root

        # 2. 获取窗口左上角的屏幕绝对坐标 (物理像素)
        # winfo_rootx/y 通常返回物理坐标，如果已设置 DPI Aware
        win_x_root = self.winfo_rootx()
        win_y_root = self.winfo_rooty()

        # 3. 计算期望的物理尺寸 (物理宽度 = 鼠标位置 - 窗口左边缘)
        target_width_phys = mouse_x_root - win_x_root
        target_height_phys = mouse_y_root - win_y_root

        # 4. 转换为逻辑尺寸 (逻辑宽度 = 物理宽度 / 缩放比例)
        # CustomTkinter 的 geometry() 需要逻辑尺寸
        new_w_logical = int(target_width_phys / self.current_scaling)
        new_h_logical = int(target_height_phys / self.current_scaling)

        # 限制最小尺寸
        new_w_logical = max(250, new_w_logical)
        new_h_logical = max(300, new_h_logical)

        # 5. 应用尺寸
        self.geometry(f"{new_w_logical}x{new_h_logical}")

        # --- DEBUG 日志区域 ---
        # 计算当前窗口理论上的物理右边缘
        current_logic_w = self.winfo_width()
        current_phys_w = current_logic_w * self.current_scaling
        calc_edge_x = win_x_root + current_phys_w

        # 误差 = 鼠标位置 - 窗口右边缘
        diff_x = mouse_x_root - calc_edge_x

        # --------------------

    # --- 窗口拖拽逻辑 ---
    def start_drag(self, event):
        self.x_pos = event.x
        self.y_pos = event.y

    def drag_window(self, event):
        x = self.winfo_x() + event.x - self.x_pos
        y = self.winfo_y() + event.y - self.y_pos
        self.geometry(f"+{x}+{y}")

    # --- 其他基础功能 ---
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
                self.geometry(
                    f"{d.get('width',300)}x{d.get('height',450)}+{d.get('x',0)}+{d.get('y',0)}"
                )
            else:
                self.geometry("300x450")
        except:
            self.geometry("300x450")

    def save_window_position(self):
        try:
            d = {
                "width": self.winfo_width(),
                "height": self.winfo_height(),
                "x": self.winfo_x(),
                "y": self.winfo_y(),
            }
            with open("position.json", "w") as f:
                json.dump(d, f, indent=2)
        except:
            pass

    def debounce_save_position(self):
        if self._save_timer:
            self.after_cancel(self._save_timer)
        self._save_timer = self.after(500, self.save_window_position)

    def on_window_configure(self, event=None):
        if event and event.widget == self:
            self.debounce_save_position()

    # --- UI 组件 ---
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
        ctk.CTkButton(
            self.title_frame,
            text="✕",
            width=30,
            fg_color="transparent",
            hover_color="#c42b1c",
            command=self.quit,
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
