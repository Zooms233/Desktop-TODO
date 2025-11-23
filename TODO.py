import customtkinter as ctk
import tkinter as tk
import json
import os

# 设置全局主题
ctk.set_appearance_mode("Dark")  # 模式：System, Dark, Light
ctk.set_default_color_theme("dark-blue")  # 主题：blue, dark-blue, green


class StickyNotesApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- 窗口基础设置 ---
        self.title("Desktop TODO")

        # 加载窗口位置和大小
        self.load_window_position()

        # 去除原生标题栏
        self.overrideredirect(True)

        # 设置窗口透明度 (0.0 - 1.0)
        self.attributes("-alpha", 0.92)

        # 默认置顶
        self.attributes("-topmost", True)
        self.is_topmost = True

        # 初始化数据
        self.tasks = []
        self.load_tasks()

        # --- 布局容器 ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)  # 让任务列表区域自动填充

        # 1. 自定义标题栏
        self.create_title_bar()

        # 2. 输入区域
        self.create_input_area()

        # 3. 任务列表区域
        self.create_task_list()

        # 4. 底部调整大小的手柄 (Grip)
        self.create_resize_grip()

        # 加载现有任务
        self.render_tasks()

        # 绑定快捷键
        self.bind("<Escape>", lambda e: self.quit())

        # 窗口拖拽变量
        self.x_pos = 0
        self.y_pos = 0

        # 绑定窗口大小和位置变化事件
        self.bind("<Configure>", self.on_window_configure)

    def load_window_position(self):
        """加载窗口位置和大小"""
        try:
            if os.path.exists("position.json"):
                with open("position.json", "r", encoding="utf-8") as f:
                    pos_data = json.load(f)
                width = pos_data.get("width", 300)
                height = pos_data.get("height", 450)
                x = pos_data.get("x", (self.winfo_screenwidth() - 300) // 2)
                y = pos_data.get("y", (self.winfo_screenheight() - 450) // 2)
                self.geometry(f"{width}x{height}+{x}+{y}")
            else:
                # 默认位置为窗口正中央
                screen_width = self.winfo_screenwidth()
                screen_height = self.winfo_screenheight()
                x = (screen_width - 300) // 2
                y = (screen_height - 450) // 2
                self.geometry(f"300x450+{x}+{y}")
                # 创建默认的position.json文件
                self.save_window_position()
        except:
            # 出错时使用默认设置
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()
            x = (screen_width - 300) // 2
            y = (screen_height - 450) // 2
            self.geometry(f"300x450+{x}+{y}")
            self.save_window_position()

    def save_window_position(self):
        """保存窗口位置和大小到position.json"""
        try:
            geometry = self.geometry()
            # geometry 可能为空或 None（例如窗口尚未映射），在这种情况下使用 winfo_* 的值作为回退
            if not geometry:
                # 使用合理的最小值作为默认回退
                try:
                    width = max(250, self.winfo_width())
                    height = max(300, self.winfo_height())
                    x = self.winfo_x()
                    y = self.winfo_y()
                except Exception:
                    width, height, x, y = 300, 450, 0, 0
            else:
                # 解析geometry字符串，格式如 "300x450+100+50"
                parts = geometry.split('+')
                size_part = parts[0]
                width, height = map(int, size_part.split('x'))
                x = int(parts[1]) if len(parts) > 1 else self.winfo_x()
                y = int(parts[2]) if len(parts) > 2 else self.winfo_y()

            pos_data = {
                "width": width,
                "height": height,
                "x": x,
                "y": y
            }

            with open("position.json", "w", encoding="utf-8") as f:
                json.dump(pos_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存窗口位置时出错: {e}")

    def on_window_configure(self, event=None):
        """当窗口大小或位置改变时调用"""
        # 防止在初始化时保存位置
        if hasattr(self, 'title_frame'):
            self.after(100, self.save_window_position)  # 延迟保存以避免频繁写入

    def create_title_bar(self):
        """创建自定义标题栏"""
        self.title_frame = ctk.CTkFrame(
            self, height=40, corner_radius=0, fg_color="#202020"
        )
        self.title_frame.grid(row=0, column=0, sticky="ew")
        self.title_frame.grid_columnconfigure(1, weight=1)  # 让中间空白撑开

        # 拖拽事件绑定
        self.title_frame.bind("<Button-1>", self.start_drag)
        self.title_frame.bind("<B1-Motion>", self.drag_window)

        # 标题文字
        self.title_label = ctk.CTkLabel(
            self.title_frame,
            text="📌 My Todo",
            font=("Roboto Medium", 14),
            text_color="#e0e0e0",
        )
        self.title_label.grid(row=0, column=0, padx=10, pady=8)
        # 也可以让文字支持拖拽
        self.title_label.bind("<Button-1>", self.start_drag)
        self.title_label.bind("<B1-Motion>", self.drag_window)

        # 置顶按钮
        self.topmost_btn = ctk.CTkButton(
            self.title_frame,
            text="📌",
            width=30,
            height=30,
            fg_color="transparent",
            hover_color="#333333",
            font=("Arial", 12),
            command=self.toggle_topmost,
        )
        self.topmost_btn.grid(row=0, column=2, padx=2)

        # 关闭按钮
        self.close_btn = ctk.CTkButton(
            self.title_frame,
            text="✕",
            width=30,
            height=30,
            fg_color="transparent",
            hover_color="#c42b1c",
            font=("Arial", 12),
            command=self.quit,
        )
        self.close_btn.grid(row=0, column=3, padx=(2, 5))

    def create_input_area(self):
        """创建输入框和添加按钮"""
        self.input_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.input_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(10, 5))

        self.task_entry = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="Add a new task...",
            height=35,
            border_width=0,
            fg_color="#2b2b2b",
            corner_radius=8,
        )
        self.task_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.task_entry.bind("<Return>", self.add_task)

        self.add_btn = ctk.CTkButton(
            self.input_frame,
            text="+",
            width=35,
            height=35,
            corner_radius=8,
            font=("Arial", 18),
            command=self.add_task,
        )
        self.add_btn.pack(side="right")

    def create_task_list(self):
        """创建可滚动的任务列表"""
        self.scroll_frame = ctk.CTkScrollableFrame(
            self, fg_color="transparent", corner_radius=0
        )
        self.scroll_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
        # 修改滚动条样式使其更隐蔽
        self.scroll_frame._scrollbar.configure(width=8, fg_color="transparent")

    def create_resize_grip(self):
        """右下角调整大小的手柄"""
        self.grip = ctk.CTkLabel(self, text="◢", font=("Arial", 12), text_color="#444")
        self.grip.place(relx=1.0, rely=1.0, anchor="se", x=0, y=0)

        # --- 修复了这里 ---
        # 使用 configure 而不是 set_cursor
        # size_nw_se 是 Windows/Tkinter 标准的斜向调整大小光标
        self.grip.configure(cursor="size_nw_se")

        self.grip.bind("<Button-1>", self.start_resize)
        self.grip.bind("<B1-Motion>", self.resize_window)

    # --- 逻辑功能区 ---

    def start_drag(self, event):
        self.x_pos = event.x
        self.y_pos = event.y

    def drag_window(self, event):
        x = self.winfo_x() + event.x - self.x_pos
        y = self.winfo_y() + event.y - self.y_pos
        self.geometry(f"+{x}+{y}")
        # 拖拽时也保存位置
        self.after(100, self.save_window_position)

    def start_resize(self, event):
        self.resize_start_x = event.x_root
        self.resize_start_y = event.y_root
        self.start_width = self.winfo_width()
        self.start_height = self.winfo_height()

    def resize_window(self, event):
        delta_x = event.x_root - self.resize_start_x
        delta_y = event.y_root - self.resize_start_y
        new_w = max(250, self.start_width + delta_x)
        new_h = max(300, self.start_height + delta_y)
        self.geometry(f"{new_w}x{new_h}")
        # 调整大小时也保存位置
        self.after(100, self.save_window_position)

    def toggle_topmost(self):
        self.is_topmost = not self.is_topmost
        self.attributes("-topmost", self.is_topmost)
        self.topmost_btn.configure(
            text="📌" if self.is_topmost else "⚓",
            fg_color="#3b3b3b" if not self.is_topmost else "transparent",
        )

    def add_task(self, event=None):
        text = self.task_entry.get().strip()
        if text:
            self.tasks.append({"text": text, "completed": False})
            self.task_entry.delete(0, "end")
            self.render_tasks()
            self.save_tasks()

    def delete_task(self, index):
        del self.tasks[index]
        self.render_tasks()
        self.save_tasks()

    def toggle_status(self, index, value):
        self.tasks[index]["completed"] = bool(value)
        self.render_tasks()  # 重新渲染以更新文字样式
        self.save_tasks()

    def render_tasks(self):
        """渲染任务列表"""
        # 清空现有组件
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        for i, task in enumerate(self.tasks):
            self.create_task_item(i, task)

    def create_task_item(self, index, task_data):
        """创建一个单独的任务条目组件"""
        # 任务容器背景
        item_frame = ctk.CTkFrame(
            self.scroll_frame, fg_color="#2b2b2b", corner_radius=6
        )
        item_frame.pack(fill="x", pady=2, padx=2)

        # 复选框
        is_done = task_data["completed"]

        checkbox = ctk.CTkCheckBox(
            item_frame,
            text="",
            width=24,
            height=24,
            corner_radius=12,  # 圆形复选框
            border_width=2,
            checkbox_width=24,
            checkbox_height=24,
            command=lambda v=None: self.toggle_status(index, checkbox.get()),
        )
        if is_done:
            checkbox.select()
        checkbox.pack(side="left", padx=(8, 5), pady=8)

        # 任务文本
        text_color = "#666666" if is_done else "#e0e0e0"
        # 自定义字体不支持直接 strikethrough，这里用颜色区分
        font_style = ("Roboto", 12)

        label = ctk.CTkLabel(
            item_frame,
            text=task_data["text"],
            text_color=text_color,
            font=font_style,
            anchor="w",
            wraplength=180,
        )
        label.pack(side="left", fill="x", expand=True, padx=5)

        # 删除按钮
        del_btn = ctk.CTkButton(
            item_frame,
            text="✕",
            width=24,
            height=24,
            fg_color="transparent",
            hover_color="#c42b1c",
            text_color="#666",
            font=("Arial", 10),
            command=lambda: self.delete_task(index),
        )
        del_btn.pack(side="right", padx=5)

    def load_tasks(self):
        try:
            if os.path.exists("tasks.json"):
                with open("tasks.json", "r", encoding="utf-8") as f:
                    self.tasks = json.load(f)
        except:
            self.tasks = []

    def save_tasks(self):
        try:
            with open("tasks.json", "w", encoding="utf-8") as f:
                json.dump(self.tasks, f, ensure_ascii=False, indent=2)
        except:
            pass


if __name__ == "__main__":
    app = StickyNotesApp()
    app.mainloop()
