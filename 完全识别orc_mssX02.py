import re
import cv2
from PIL import Image
from paddleocr import PaddleOCR
import mss
import winsound
from pynput import mouse
import random
from datetime import datetime
import customtkinter as ctk
import tkinter as tk
import threading
import time
import os
import ast
import ctypes


# 随机生成文件名
def generate_random_filename(length=10):
    return ''.join(random.choice('abcdefghijklmnopqrstuvwxyz1234567890') for _ in range(length)) + '.exe'


# 定义 Windows 数据结构
class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class INPUT(ctypes.Structure):
    class _INPUT_U(ctypes.Union):
        _fields_ = [("mi", MOUSEINPUT)]

    _anonymous_ = ("_input",)
    _fields_ = [("type", ctypes.c_ulong), ("_input", _INPUT_U)]


class ScreenshotOverlay:
    def __init__(self, region):
        """初始化截图框但不立即显示"""
        self.region = region  # 可以是 (x, y, width, height) 或 {"top": y, "left": x, "width": w, "height": h}

        # 解析区域参数，支持字典和元组
        if isinstance(region, dict):
            if not all(k in region for k in ("top", "left", "width", "height")):
                raise ValueError(f"region 必须包含 top, left, width, height，但收到: {region}")
            x, y, width, height = region["left"], region["top"], region["width"], region["height"]
        elif isinstance(region, (tuple, list)) and len(region) == 4:
            x, y, width, height = region  # 如果 region 是 (x, y, width, height) 形式
        else:
            raise ValueError(f"region 格式错误，必须是包含键的字典或 (x, y, width, height) 元组，但收到: {region}")

        # 创建一个透明窗口
        self.root = tk.Tk()
        self.root.overrideredirect(True)  # 无边框
        self.root.attributes('-topmost', True)  # 置顶窗口
        self.root.attributes('-transparentcolor', 'black')  # 让黑色变透明（背景透明）
        self.root.geometry(f"{width}x{height}+{x}+{y}")  # 设置窗口位置和大小

        # 创建 Canvas 画布
        self.canvas = tk.Canvas(self.root, width=width, height=height, bg='black', highlightthickness=0)
        self.canvas.pack()

        # 画绿色边框（4 条线）
        border_width = 3  # 修改线条宽度
        self.canvas.create_line(0, 0, width, 0, fill="green", width=border_width)  # 顶部
        self.canvas.create_line(0, 0, 0, height, fill="green", width=border_width)  # 左侧
        self.canvas.create_line(width, 0, width, height, fill="green", width=border_width)  # 右侧
        self.canvas.create_line(0, height, width, height, fill="green", width=border_width)  # 底部

        # 先不显示，等 show() 时候再显示
        self.root.withdraw()

    def show(self, duration=1000):
        """显示截图框，并在 duration 毫秒后关闭"""
        self.root.deiconify()  # 显示窗口
        self.root.update()
        self.root.after(duration, self.close)  # duration 毫秒后自动关闭

    def close(self):
        """关闭截图框"""
        self.root.destroy()


class Auto_OCR(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.listener1 = None
        self.click_num_old = 0
        self.click_num_new = 0
        self.right_button_pressed = True
        self.max_val_poper_list = []
        self.notrun = 0
        self.is_on00 = True
        self.is_on22 = True
        self.spot11 = None
        self.lastname00 = None
        self.name00 = 'zero'
        self.spot00 = None
        self.xy00 = None
        self.xyt00 = None
        self.clicking00 = None
        # 定义鼠标事件标志
        self.INPUT_MOUSE = 0
        self.MOUSEEVENTF_MOVE = 0x0001
        self.MOUSEEVENTF_ABSOLUTE = 0x8000  # 绝对移动（通常不需要）
        self.MOUSEEVENTF_LEFTDOWN = 0x0002  # 鼠标左键按下
        self.MOUSEEVENTF_LEFTUP = 0x0004  # 鼠标左键松开
        # 调用 SendInput 函数
        self.SendInput = ctypes.windll.user32.SendInput

        # 如果文件夹不存在，则创建文件夹路径
        if not os.path.exists(r'C:\Duck Gun helper\configFile\ini'):
            os.makedirs(r'C:\Duck Gun helper\configFile\ini')
            print(r"文件夹路径 C:\Duck Gun helper\configFile\ini 已创建")
        else:
            print(r"文件夹路径 C:\Duck Gun helper\configFile\ini 已存在")

        # 误差累计变量，用于鼠标移动补偿（浮点数累计）
        self.residual_x = 0.0
        self.residual_y = 0.0

        # 检查鼠标按键是否按下
        self.VK_LBUTTON = 0x01  # 左键
        self.VK_RBUTTON = 0x02  # 右键
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        # 随机生成窗口标题
        random_title = generate_random_filename(8)  # 随机生成一个长度为 8 的文件名作为标题
        self.title('tmp' + random_title)  # 设置随机标题名
        # 创建 TabView 控件
        self.tab_view = ctk.CTkTabview(self, width=320, height=500)
        self.tab_view.pack(fill="both", expand=True, padx=20, pady=20)
        # 添加选项卡
        self.tab_view.add("自动识别")
        self.tab_view.add("识别设置")
        self.tab_view.add("工具")
        self.tab_view.add("鼠标宏")
        self.tab_view.add("配置")
        self.tab_view.grid_propagate(True)
        # 自动识别页
        self.button = ctk.CTkButton(self.tab_view.tab("自动识别"), text="自动识别", command=self.main)
        self.button.pack(padx=20, pady=10)
        self.is_on = True
        self.is_on_muisc = False
        self.display_label = ctk.CTkLabel(self.tab_view.tab("自动识别"), text="版本:orc_mss.X.02", font=("Arial", 14))
        self.display_label.pack(pady=10)
        self.button_muisc = ctk.CTkButton(self.tab_view.tab("自动识别"), text="声音提示", command=self.muisc_onffo)
        self.button_muisc.pack(padx=20, pady=10)
        self.display_label2 = ctk.CTkLabel(self.tab_view.tab("自动识别"), text="", font=("Arial", 14))
        self.display_label2.pack(pady=10)
        self.text_display_label3 = ctk.CTkTextbox(self.tab_view.tab("自动识别"), height=110, width=260, wrap="word")
        self.text_display_label3.pack(side="bottom", fill="x", padx=10, pady=10)
        # 自动识别设置页
        # **进攻标志开关**
        self.toggle_preview_true = True
        self.preview_var = ctk.BooleanVar(value=True)  # 默认值为 True
        self.preview_checkbox = ctk.CTkCheckBox(
            self.tab_view.tab("识别设置"),
            text="进攻防守标志是否使用开关",
            variable=self.preview_var,
            command=self.toggle_preview
        )
        self.preview_checkbox.pack(pady=5)
        # **截图位置预览**
        self.toggle_preview_true22 = False
        self.overlay22 = None
        self.preview_var22 = ctk.BooleanVar(value=False)  # 默认值为 True
        self.preview_checkbox22 = ctk.CTkCheckBox(
            self.tab_view.tab("识别设置"),
            text="截图预览开关(关闭需关闭识别;压枪需关闭)",
            variable=self.preview_var22,
            command=self.toggle_preview22
        )
        self.preview_checkbox22.pack(pady=5)
        # 添加局内识别速度滑块
        self.slider_label = ctk.CTkLabel(self.tab_view.tab("识别设置"), text="局内切枪识别速度(默认0.5秒):")
        self.slider_label.pack(pady=10)

        self.slider = ctk.CTkSlider(self.tab_view.tab("识别设置"),
                                    from_=0.1,
                                    to=0.5,
                                    number_of_steps=40,  # 每次滑动多少步
                                    command=self.update_slider_value)
        self.slider.pack(pady=10)
        self.slider.set(0.5)
        # 显示滑块当前值
        self.slider_value_label = ctk.CTkLabel(self.tab_view.tab("识别设置"), text="当前值: 0.5")
        self.slider_value_label.pack(pady=10)
        self.slider_time_value = 0.5
        # 添加干员锁定滑块
        self.slider_label2 = ctk.CTkLabel(self.tab_view.tab("识别设置"), text="干员锁定配置识别次数(默认3次):")
        self.slider_label2.pack(pady=10)

        self.slider2 = ctk.CTkSlider(self.tab_view.tab("识别设置"),
                                     from_=1,
                                     to=3,
                                     number_of_steps=40,  # 每次滑动多少步
                                     command=self.update_slider_value2)
        self.slider2.pack(pady=10)
        self.slider2.set(3)
        # 显示滑块当前值
        self.slider_value_label2 = ctk.CTkLabel(self.tab_view.tab("识别设置"), text="当前值: 3")
        self.slider_value_label2.pack(pady=10)
        self.slider_time_name_value = 3
        # 工具页

        # 创建文本框并居中显示
        submit_button = ctk.CTkButton(self.tab_view.tab("工具"), text="名称识别工具", command=self.mssg_name)
        submit_button.pack(padx=10, pady=10)
        self.button000 = ctk.CTkButton(self.tab_view.tab("工具"), text="截图定位工具", command=self.main000)
        self.button000.pack(padx=10, pady=10)

        self.display_label000 = ctk.CTkLabel(self.tab_view.tab("工具"), text="按住右键框选,Alt+Tap切换应用跳出框选",
                                             font=("Arial", 14))
        self.display_label000.pack(padx=10, pady=10)
        self.is_on000 = True

        # 初始化画布相关变量
        self.start_position = None
        self.drawing = False
        self.listener = None

        # 创建画布窗口
        self.overlay = tk.Toplevel(self)
        self.overlay.attributes("-fullscreen", True)
        self.overlay.attributes("-alpha", 0.3)
        self.overlay.configure(background='black')
        self.overlay.withdraw()  # 初始隐藏

        self.canvas = tk.Canvas(self.overlay, bg="black", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.text1 = str
        self.text_display = ctk.CTkTextbox(self.tab_view.tab("工具"), height=280, width=260, wrap="word")
        self.text_display.pack(side="bottom", fill="x", padx=10, pady=10)

        # 鼠标宏页
        self.button00 = ctk.CTkButton(self.tab_view.tab("鼠标宏"), text="AUTO配置", command=self.main00)
        self.button00.pack(padx=20, pady=10)
        self.display_label00 = ctk.CTkLabel(self.tab_view.tab("鼠标宏"), text="和自动识别配合使用", font=("Arial", 14))
        self.display_label00.pack(pady=10)
        self.button22 = ctk.CTkButton(self.tab_view.tab("鼠标宏"), text="压枪", command=self.main22)
        self.button22.pack(padx=20, pady=10)
        self.display_label22 = ctk.CTkLabel(self.tab_view.tab("鼠标宏"), text="压枪开关",
                                            font=("Arial", 14))
        self.display_label22.pack(pady=10)
        self.text_display00 = ctk.CTkTextbox(self.tab_view.tab("鼠标宏"), height=230, width=260, wrap="word")
        self.text_display00.pack(side="bottom", fill="x", padx=10, pady=10)
        self.print_to_text00(
            "使用条款&免责声明：\n1.使用此软件不得用于非法目的。\n2.此软件仅供学习交流。\n3.使用软件造成的一切后果由使用人全权承担。")
        # 配置页
        self.file_dropdown00 = ctk.CTkComboBox(self.tab_view.tab("配置"), values=[], width=200)
        self.file_dropdown00.pack(padx=20, pady=10)
        self.refresh_button00 = ctk.CTkButton(self.tab_view.tab("配置"), text="刷新", command=self.refresh_files)
        self.refresh_button00.pack(padx=5, pady=10)
        self.refresh_files()
        self.refresh_button22 = ctk.CTkButton(self.tab_view.tab("配置"), text="确定", command=self.on_file_select)
        self.refresh_button22.pack(padx=5, pady=10)

        # 灵敏度
        # x力度倍率部分
        self.slider_label_xb = ctk.CTkLabel(self.tab_view.tab("配置"), text="x力度倍率:         当前值: 1.0")
        self.slider_label_xb.pack(pady=10)

        self.slider_xb = ctk.CTkSlider(self.tab_view.tab("配置"),
                                       from_=0.01,
                                       to=5.00,
                                       number_of_steps=500,
                                       command=self.update_slider_value_xb,
                                       width=260)
        self.slider_xb.pack(pady=10, fill="x", padx=20)
        self.slider_xb.set(1.0)
        self.slider_xb_value = 1.00

        # x倍率调整按钮
        frame_xb_adjust = ctk.CTkFrame(self.tab_view.tab("配置"))
        frame_xb_adjust.pack(pady=5)

        self.btn_xb_decrease = ctk.CTkButton(frame_xb_adjust, text="-", width=30, command=self.decrease_slider_xb)
        self.btn_xb_decrease.pack(side="left", padx=5)

        self.btn_xb_increase = ctk.CTkButton(frame_xb_adjust, text="+", width=30, command=self.increase_slider_xb)
        self.btn_xb_increase.pack(side="left", padx=5)

        self.btn_xyb_read = ctk.CTkButton(frame_xb_adjust, text="读取", width=30, command=self.xyb_read)
        self.btn_xyb_read.pack(side="left", padx=5)

        # y力度倍率部分
        self.slider_label_yb = ctk.CTkLabel(self.tab_view.tab("配置"), text="y力度倍率:         当前值: 1.0")
        self.slider_label_yb.pack(pady=10)

        self.slider_yb = ctk.CTkSlider(self.tab_view.tab("配置"),
                                       from_=0.01,
                                       to=5.00,
                                       number_of_steps=500,
                                       command=self.update_slider_value_yb,
                                       width=260)
        self.slider_yb.pack(pady=10, fill="x", padx=20)
        self.slider_yb.set(1.0)
        self.slider_yb_value = 1.00

        # y倍率调整按钮
        frame_yb_adjust = ctk.CTkFrame(self.tab_view.tab("配置"))
        frame_yb_adjust.pack(pady=5)

        self.btn_yb_decrease = ctk.CTkButton(frame_yb_adjust, text="-", width=30, command=self.decrease_slider_yb)
        self.btn_yb_decrease.pack(side="left", padx=5)

        self.btn_yb_increase = ctk.CTkButton(frame_yb_adjust, text="+", width=30, command=self.increase_slider_yb)
        self.btn_yb_increase.pack(side="left", padx=5)

        self.btn_xyb_save = ctk.CTkButton(frame_yb_adjust, text="保存", width=30, command=self.xyb_save)
        self.btn_xyb_save.pack(side="left", padx=5)

        self.print_to_text(
            "使用条款&免责声明：\n1.使用此软件不得用于非法目的。\n2.此软件仅供学习交流。\n3.使用软件造成的一切后果由使用人全权承担。")

        self.desktop_path = r'C:\Duck Gun helper\configFile\mode'
        self.desktop_path_name = r'C:\Duck Gun helper\configFile\mode\fff'
        self.desktop_path_ini = r'C:\Duck Gun helper\configFile\mode\fff\orc_mss_ini.txt'
        self.desktop_path_name_mss_ini = r'C:\Duck Gun helper\configFile\mode\fff\name_mss_ini.txt'
        self.desktop_path_name_dun_one_ini = r'C:\Duck Gun helper\configFile\mode\fff\dun_one_name.txt'
        self.img_path_name = self.desktop_path + r"\screenshot2.png"
        self.img_path_zhu = self.desktop_path + r"\screenshot4.png"
        self.img_path_fu = self.desktop_path + r"\screenshot5.png"
        self.img_path_zhunei = self.desktop_path + r"\screenshot6.png"
        self.img_path_funei = self.desktop_path + r"\screenshot7.png"
        self.img_path_7XZ = self.desktop_path + r"\screenshot8.png"
        self.img_path_guanz = self.desktop_path + r"\screenshot10.png"
        self.img_path_guanz_true = self.desktop_path + r"\fff\5.png"
        self.img_path_7XZ_true = self.desktop_path + r"\fff\z.png"
        self.img_path_poper = self.desktop_path + r"\screenshot11.png"
        self.img_path_poper_true = self.desktop_path + r"\fff\pop"
        self.template_files = [f for f in os.listdir(self.img_path_poper_true) if
                               f.endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
        self.spot = ''
        # 初始化OCR引擎
        self.ocrrr = PaddleOCR(use_angle_cls=True, lang="ch")
        self.ocr_en = PaddleOCR(use_angle_cls=True, lang="en")
        self.name = ''
        self.name_zhu = ''
        self.name_fu = ''
        self.name_with = ''
        self.name_zero = 'zero'
        self.c = 0
        self.xy = []
        self.num = 0
        self.name_sss = []
        self.name_dun_one = []
        self.name_zhu_color = False
        self.name_fu_color = False
        self.reft_num = 0
        self.mui = 0
        self.text_names_s = ''
        with open(self.desktop_path_ini, 'r', encoding='utf-8') as file:
            # 迭代文件对象
            for line in file:
                # 处理每行内容（这里仅仅是打印）
                print(line.strip().split('图')[1])
                dict_str = line.strip().split('图')[1]
                data_dict = ast.literal_eval(dict_str)
                self.xy.append(data_dict)
        with open(self.desktop_path_name_mss_ini, 'r', encoding='utf-8') as file:
            # 迭代文件对象
            for line in file:
                x_name = line.replace(" ", "").strip().split('/')
                for i in x_name:
                    # print(i)
                    self.name_sss.append(i)
        with open(self.desktop_path_name_dun_one_ini, 'r', encoding='utf-8') as file:
            # 迭代文件对象
            for line in file:
                x_name = line.replace(" ", "").strip().split('/')
                for i in x_name:
                    # print(i)
                    self.name_dun_one.append(i)
        self.xyb_read()

    def update_slider_value_xb(self, value):
        self.slider_xb_value = round(float(value), 2)
        self.slider_label_xb.configure(text=f"x力度倍率:         当前值: {self.slider_xb_value}")

    def update_slider_value_yb(self, value):
        self.slider_yb_value = round(float(value), 2)
        self.slider_label_yb.configure(text=f"y力度倍率:         当前值: {self.slider_yb_value}")

    def decrease_slider_xb(self):
        new_value = max(self.slider_xb_value - 0.01, 0.01)
        self.slider_xb_value = round(new_value, 2)
        self.slider_xb.set(self.slider_xb_value)
        self.slider_label_xb.configure(text=f"x力度倍率:         当前值: {self.slider_xb_value}")

    def increase_slider_xb(self):
        new_value = min(self.slider_xb_value + 0.01, 5.00)
        self.slider_xb_value = round(new_value, 2)
        self.slider_xb.set(self.slider_xb_value)
        self.slider_label_xb.configure(text=f"x力度倍率:         当前值: {self.slider_xb_value}")

    def decrease_slider_yb(self):
        new_value = max(self.slider_yb_value - 0.01, 0.01)
        self.slider_yb_value = round(new_value, 2)
        self.slider_yb.set(self.slider_yb_value)
        self.slider_label_yb.configure(text=f"y力度倍率:         当前值: {self.slider_yb_value}")

    def increase_slider_yb(self):
        new_value = min(self.slider_yb_value + 0.01, 5.00)
        self.slider_yb_value = round(new_value, 2)
        self.slider_yb.set(self.slider_yb_value)
        self.slider_label_yb.configure(text=f"y力度倍率:         当前值: {self.slider_yb_value}")

    def xyb_read(self):
        xyb_list = []
        try:
            with open(r"C:\Duck Gun helper\configFile\ini\xyb_save.ini", 'r', encoding='utf-8') as file:
                for line in file:
                    xyb_list.append(line.strip())
            print(xyb_list)
        except Exception as e:
            print('读取失败：', e)
        try:
            # 转换为浮点数
            self.slider_xb_value = round(float(xyb_list[0]), 2)
            self.slider_yb_value = round(float(xyb_list[1]), 2)
        except Exception as e:
            print("数据格式错误：", e)
            return
        self.slider_xb.set(self.slider_xb_value)
        self.slider_label_xb.configure(text=f"x力度倍率:         当前值: {self.slider_xb_value}")
        self.slider_yb.set(self.slider_yb_value)
        self.slider_label_yb.configure(text=f"y力度倍率:         当前值: {self.slider_yb_value}")

    def xyb_save(self):
        try:
            with open(r"C:\Duck Gun helper\configFile\ini\xyb_save.ini", "w", encoding='utf-8') as f:
                f.write(f'{self.slider_xb_value}\n{self.slider_yb_value}')
        except Exception as e:
            print('保存失败：', e)

    def update_slider_value(self, value):
        # 更新滑块当前值
        self.slider_time_value = round(float(value), 1)
        self.slider_value_label.configure(text=f"当前值: {self.slider_time_value}")

    def update_slider_value2(self, value):
        # 更新滑块当前值
        self.slider_time_name_value = int(value)
        self.slider_value_label2.configure(text=f"当前值: {self.slider_time_name_value}")

    def toggle_preview(self):
        self.toggle_preview_true = not self.toggle_preview_true

    def toggle_preview22(self):
        self.toggle_preview_true22 = not self.toggle_preview_true22

    def draw_rectangle(self, start, end):
        # 清除之前的矩形
        self.canvas.delete("rect")
        self.canvas.create_rectangle(start[0], start[1], end[0], end[1], outline="red", tag="rect")

    def on_click(self, x, y, button, pressed):
        if button == mouse.Button.right:  # 检测鼠标右键
            if pressed:
                # 按下鼠标右键时记录初始位置
                self.start_position = (x, y)
                # self.print_to_text(f"Mouse pressed at: {self.start_position}")
                self.text1 = '{' + "'top'" + ':' + f"{self.start_position[1]}," + "'left'" + ':' + f"{self.start_position[0]},"
                self.drawing = True
            else:
                # 松开鼠标右键时记录当前位置
                end_position = (x, y)
                # self.print_to_text(f"Mouse released at: {end_position}")
                if self.start_position:
                    relative_position = (end_position[0] - self.start_position[0],
                                         end_position[1] - self.start_position[1])
                    # self.print_to_text(f"Relative position: {relative_position}")
                    text2 = "'width'" + ':' + f"{relative_position[0]}," + "'height'" + ':' + f"{relative_position[1]}" + '}'
                    self.print_to_text(self.text1 + text2)
                self.drawing = False

    def on_move(self, x, y):
        if self.drawing and self.start_position:
            # 实时更新矩形框
            end_position = (x, y)
            self.draw_rectangle(self.start_position, end_position)

    def print_to_label000(self, content):
        self.display_label000.configure(text=content)

    def start_listener(self):
        self.listener = mouse.Listener(on_click=self.on_click, on_move=self.on_move)
        self.listener.start()

    def stop_listener(self):
        if self.listener:
            self.listener.stop()
            self.listener = None

    def main000(self):
        if self.is_on000:
            self.overlay.deiconify()  # 显示画布窗口
            t = threading.Thread(target=self.start_listener)
            t.daemon = True
            t.start()
            self.button000.configure(text="截图定位工具-on", fg_color="green")
            self.print_to_label000("截图定位工具已启动😍")
        else:
            try:
                self.overlay.withdraw()  # 隐藏画布窗口
                self.stop_listener()  # 停止鼠标监听
                self.button000.configure(text="截图定位工具-off", fg_color="red")
                self.print_to_label000("截图定位工具已关闭😒")
            except:
                self.print_to_label000("截图画布框异常关闭,需要重启app")
        self.is_on000 = not self.is_on000

    def refresh_files(self):
        """刷新文件列表"""
        files = [f for f in os.listdir(r'C:\Duck Gun helper\configFile\ini') if f.endswith('.ini')]
        self.file_dropdown00.configure(values=files)
        if files:
            self.file_dropdown00.set(files[0])  # 默认选中第一个文件

    def on_file_select(self, event=None):
        """当用户选择文件时，自动调用read2函数"""
        selected_file = self.file_dropdown00.get()
        if selected_file:
            self.name00 = selected_file.replace('.ini', '')  # 去掉扩展名
            self.read2()

    def print_to_text00(self, content):
        self.text_display00.insert(tk.END, content + "\n")
        self.text_display00.see(tk.END)  # 自动滚动到最新内容

    def print_to_label00(self, content):
        self.display_label00.configure(text=content)

    def print_to_label22(self, content):
        self.display_label22.configure(text=content)

    def is_left_mouse_button_pressed00(self):
        return ctypes.windll.user32.GetAsyncKeyState(self.VK_LBUTTON) & 0x8000 != 0

    def is_right_mouse_button_pressed00(self):
        return ctypes.windll.user32.GetAsyncKeyState(self.VK_RBUTTON) & 0x8000 != 0

    def create_mouse_event(self, dx, dy, flags):
        event = INPUT()
        event.type = self.INPUT_MOUSE  # 输入类型是鼠标事件
        # 初始化 mi 字段
        event._input.mi = MOUSEINPUT(dx=dx, dy=dy, mouseData=0, dwFlags=flags, time=0, dwExtraInfo=None)
        return event

    def move_mouse(self, dx, dy):
        """
        经过补偿算法的鼠标移动：
        利用误差累计的方法先计算浮点位移，再累加残差，最后转换为整数进行实际移动。
        """
        # print('xb:', self.slider_xb_value, 'yb:', self.slider_yb_value)
        # 计算基于倍率后的浮点位移，并累计上一次未补偿的残差
        total_dx = dx * self.slider_xb_value + self.residual_x
        total_dy = dy * self.slider_yb_value + self.residual_y

        # 取整数位进行实际移动
        int_dx = int(total_dx)
        int_dy = int(total_dy)

        # 更新残差，保留小数部分
        self.residual_x = total_dx - int_dx
        self.residual_y = total_dy - int_dy

        # 构造鼠标输入事件
        input_event = INPUT(type=self.INPUT_MOUSE)
        input_event._input.mi = MOUSEINPUT(dx=int_dx, dy=int_dy, mouseData=0, dwFlags=self.MOUSEEVENTF_MOVE, time=0,
                                           dwExtraInfo=None)
        self.SendInput(1, ctypes.byref(input_event), ctypes.sizeof(INPUT))
        # 可以打印调试信息：
        # print(f"move: dx={int_dx}, dy={int_dy}, residual_x={self.residual_x:.2f}, residual_y={self.residual_y:.2f}")

    def click_num(self, x, y, button, pressed):
        if button.name == 'left' and not pressed:
            # print("鼠标左键松开，且右键仍然按住！")
            # 在这里可以执行你需要的操作
            self.click_num_new += 1
        time.sleep(0.01)

    def click_num_listener(self):
        if self.listener1 is None:  # 防止多次创建监听器
            self.listener1 = mouse.Listener(on_click=self.click_num)
            self.listener1.start()

    def click_left_button(self):
        while self.spot11 == 0:
            if self.clicking00 == 1:
                if self.is_left_mouse_button_pressed00() and self.is_right_mouse_button_pressed00():
                    if self.right_button_pressed:
                        click_num_thread = threading.Thread(target=self.click_num_listener)
                        click_num_thread.daemon = True
                        click_num_thread.start()
                        self.right_button_pressed = False
                    time.sleep(0.01)  # 随机间隔
                    event = self.create_mouse_event(0, 0, self.MOUSEEVENTF_LEFTUP)  # 左键松开事件
                    ctypes.windll.user32.SendInput(1, ctypes.byref(event), ctypes.sizeof(event))
                    self.click_num_old += 1
                    time.sleep(random.uniform(0.01, 0.02))  # 随机间隔
                    event = self.create_mouse_event(0, 0, self.MOUSEEVENTF_LEFTDOWN)  # 左键按下事件
                    ctypes.windll.user32.SendInput(1, ctypes.byref(event), ctypes.sizeof(event))
                    time.sleep(random.uniform(0.06, 0.14))  # 随机间隔
                    # print('click_left_button')
                else:
                    time.sleep(0.01)
                if self.click_num_old != self.click_num_new:
                    print('new:', self.click_num_new, 'old:', self.click_num_old)
                    event = self.create_mouse_event(0, 0, self.MOUSEEVENTF_LEFTUP)  # 左键松开事件
                    ctypes.windll.user32.SendInput(1, ctypes.byref(event), ctypes.sizeof(event))
                    self.right_button_pressed = True
                    self.click_num_old = 0
                    self.click_num_new = 0
                    if self.listener1:
                        self.listener1.stop()
                        self.listener1 = None
            else:
                time.sleep(0.01)

    def read1(self):
        while self.spot00 == 0:
            time.sleep(0.1)
            if self.name00 != self.lastname00:
                self.lastname00 = self.name00
                self.read2()

    def read2(self):
        self.xy00 = []
        try:
            with open(rf'C:\Duck Gun helper\configFile\ini\{self.name00}.ini', 'r', encoding='utf-8') as file:
                for line in file:
                    print(line.strip())
                    self.xy00.append(ast.literal_eval(line.strip()))
            # print(self.xy00)
            self.xyt00 = self.xy00[1:]  # 移除首个元素（假设首元素是点击标志位）
            self.clicking00 = self.xy00[0]  # 假设第一个元素为点击标志位
            # print(self.xyt00)
            # 获取当前时间
            current_time = datetime.now()
            # 格式化时间为 [HH:MM:SS] 的格式
            formatted_time = current_time.strftime("[%H:%M:%S]")
            self.print_to_text00(f'{formatted_time}当前使用配置：{self.name00}')
        except FileNotFoundError:
            with open(r'C:\Duck Gun helper\configFile\ini\zero.ini', 'w') as f:
                f.write('0\n[0,0,10000]')
            with open(r'C:\Duck Gun helper\configFile\ini\zero.ini', 'r', encoding='utf-8') as file:
                for line in file:
                    print(line.strip())
                    self.xy00.append(ast.literal_eval(line.strip()))
            # print(self.xy00)
            self.xyt00 = self.xy00[1:]  # 移除首个元素（假设首元素是点击标志位）
            self.clicking00 = self.xy00[0]  # 假设第一个元素为点击标志位
            # print(self.xyt00)
            # 获取当前时间
            current_time = datetime.now()
            # 格式化时间为 [HH:MM:SS] 的格式
            formatted_time = current_time.strftime("[%H:%M:%S]")
            self.print_to_text00(f'{formatted_time}{self.name00}配置不存在,已自动生成并更换zero配置')
        # except:
        #     self.print_to_text00(f'{formatted_time}{self.name00}配置文件格式错误')

    def run(self):
        while self.spot11 == 0:
            c = self.is_left_mouse_button_pressed00()
            d = self.is_right_mouse_button_pressed00()
            time.sleep(0.01)
            if c and d:
                self.notrun = 0
            else:
                self.notrun += 1
            if self.notrun < 8:
                try:
                    for i in self.xyt00:
                        time_s = time.time()
                        while ((i[2] / 1000) + time_s) > time.time():  # 时间间隔控制
                            c = self.is_left_mouse_button_pressed00()
                            d = self.is_right_mouse_button_pressed00()
                            if c and d:
                                self.notrun = 0
                            else:
                                self.notrun += 1
                            if self.notrun < 8:
                                self.move_mouse(i[0], i[1])
                                time.sleep(0.01)
                            else:
                                # print('break')
                                break
                except:
                    self.print_to_label22('没有选择配置文件或者配置内容错误')

    def main00(self):
        if self.is_on00:
            self.spot00 = 0
            t_get = threading.Thread(target=self.read1)
            t_get.daemon = True
            t_get.start()
            self.button00.configure(text="AUTO配置-on", fg_color="green")
            self.print_to_label00('自动切换配置已启动😍😍')
        else:
            self.spot00 = 1
            self.button00.configure(text="AUTO配置-off", fg_color="red")
            self.print_to_label00('自动切换配置已关闭😒😒')
        self.is_on00 = not self.is_on00  # 切换状态

    def main22(self):
        if self.is_on22:
            self.spot11 = 0
            t_get2 = threading.Thread(target=self.run)
            t_get2.daemon = True
            t_get2.start()
            click_thread = threading.Thread(target=self.click_left_button)
            click_thread.daemon = True
            click_thread.start()
            self.button22.configure(text="压枪-on", fg_color="green")
            self.print_to_label22('压枪功能已启动😍😍')
        else:
            self.spot11 = 1
            self.button22.configure(text="压枪-off", fg_color="red")
            self.print_to_label22('压枪功能已关闭😒😒')
        self.is_on22 = not self.is_on22  # 切换状态

    def mssg_name(self):
        self.jietu_name()
        result_name = self.ocr(self.img_path_name)
        self.text_names(result_name)

        self.jietu_zhu()
        result_zhu = self.ocren(self.img_path_zhu)
        self.text_zhus(result_zhu)

        self.jietu_fu()
        result_fu = self.ocren(self.img_path_fu)
        self.text_fus(result_fu)

    def muisc(self):
        frequency = 1600
        duration = 150
        if self.is_on_muisc:
            for i in range(1):
                winsound.Beep(frequency, duration)

    def muisc_onffo(self):
        self.is_on_muisc = not self.is_on_muisc
        if self.is_on_muisc:
            self.button_muisc.configure(text="声音提示", fg_color="green")
            self.print_to_label2('声音提示已启动😍😍')
        else:
            self.button_muisc.configure(text="声音提示", fg_color="red")
            self.print_to_label2('声音提示已关闭😒😒')

    def is_left_mouse_button_pressed(self):
        left = ctypes.windll.user32.GetAsyncKeyState(0x01) != 0
        return left

    def is_reft_mouse_button_pressed(self):
        reft = ctypes.windll.user32.GetAsyncKeyState(0x02) != 0
        return reft

    def jietu_guanz(self):
        with mss.mss() as sct:
            region = self.xy[0]
            screenshot = sct.grab(region)
            mss.tools.to_png(screenshot.rgb, screenshot.size, output=self.img_path_guanz)
        # 创建截图框并显示
        if self.toggle_preview_true22:
            self.overlay22 = ScreenshotOverlay(region)
            self.overlay22.show(1000)  # 显示 1 秒后自动关闭

    def jietu_7XZ(self):
        with mss.mss() as sct:
            region = self.xy[1]
            screenshot = sct.grab(region)
            mss.tools.to_png(screenshot.rgb, screenshot.size, output=self.img_path_7XZ)
        # 创建截图框并显示
        if self.toggle_preview_true22:
            self.overlay22 = ScreenshotOverlay(region)
            self.overlay22.show(1000)  # 显示 1 秒后自动关闭

    def jietu_name(self):
        with mss.mss() as sct:
            region = self.xy[2]
            screenshot = sct.grab(region)
            mss.tools.to_png(screenshot.rgb, screenshot.size, output=self.img_path_name)
        # 创建截图框并显示
        if self.toggle_preview_true22:
            self.overlay22 = ScreenshotOverlay(region)
            self.overlay22.show(1000)  # 显示 1 秒后自动关闭

    def jietu_zhu(self):
        with mss.mss() as sct:
            region = self.xy[3]
            screenshot = sct.grab(region)
            mss.tools.to_png(screenshot.rgb, screenshot.size, output=self.img_path_zhu)
        # 创建截图框并显示
        if self.toggle_preview_true22:
            self.overlay22 = ScreenshotOverlay(region)
            self.overlay22.show(1000)  # 显示 1 秒后自动关闭

    def jietu_fu(self):
        with mss.mss() as sct:
            region = self.xy[4]
            screenshot = sct.grab(region)
            mss.tools.to_png(screenshot.rgb, screenshot.size, output=self.img_path_fu)
        # 创建截图框并显示
        if self.toggle_preview_true22:
            self.overlay22 = ScreenshotOverlay(region)
            self.overlay22.show(1000)  # 显示 1 秒后自动关闭

    def jietu_zhunei(self):
        with mss.mss() as sct:
            region = self.xy[5]
            screenshot = sct.grab(region)
            mss.tools.to_png(screenshot.rgb, screenshot.size, output=self.img_path_zhunei)
        # 创建截图框并显示
        if self.toggle_preview_true22:
            self.overlay22 = ScreenshotOverlay(region)
            self.overlay22.show(1000)  # 显示 1 秒后自动关闭

    def jietu_funei(self):
        with mss.mss() as sct:
            region = self.xy[6]
            screenshot = sct.grab(region)
            mss.tools.to_png(screenshot.rgb, screenshot.size, output=self.img_path_funei)
        # 创建截图框并显示
        if self.toggle_preview_true22:
            self.overlay22 = ScreenshotOverlay(region)
            self.overlay22.show(1000)  # 显示 1 秒后自动关闭

    def jietu_poper(self):
        with mss.mss() as sct:
            region = self.xy[7]
            screenshot = sct.grab(region)
            mss.tools.to_png(screenshot.rgb, screenshot.size, output=self.img_path_poper)
        # 创建截图框并显示
        if self.toggle_preview_true22:
            self.overlay22 = ScreenshotOverlay(region)
            self.overlay22.show(1000)  # 显示 1 秒后自动关闭

    def ocr(self, path):
        # 识别结果
        result = self.ocrrr.ocr(path, cls=True)
        # print(type(result))
        return result

    def ocren(self, path):
        # 识别结果
        result = self.ocr_en.ocr(path, cls=True)
        # print(type(result))
        return result

    def contains_chinese(self, s):
        return bool(re.search(r'[\u4e00-\u9fa5]', s))

    def text_name(self, result):
        # 输出识别结果
        try:
            r = result[0][0][1][0].replace(" ", "")
            t = re.sub(r'[\\/:*?"<>|]', '', r)
            # print(result)
            # print(t)
            if t not in self.name_sss:
                print(t, '干员不存在')
                return
            elif self.contains_chinese(t):
                return
            elif self.name != t:
                self.name = t
                self.muisc()
                print(self.name)
                self.mui = 0
                self.c = 0
                self.num = 0
            else:
                print('和上次识别内容相同 return')
                self.num = 0
                return
        except:
            if self.num < 1:
                self.num += 1
                result_name = self.ocren(self.img_path_name)
                self.text_name(result_name)
            else:
                print('识别错误')
                self.num = 0

    def text_zhu(self, result):  # 主武器名字
        # 输出识别结果
        try:
            r = result[0][0][1][0].replace(" ", "")
            t = re.sub(r'[\\/:*?"<>|]', '', r)
            # print('主武器', result)
            # print(t)
            a = self.name + t
            if self.name_zhu != a:
                self.name_zhu = self.name + t
                print(self.name_zhu)
                self.name_with = self.name_zhu
                self.fff(self.name_with)
                self.num = 0
            else:
                print('主武器内容相同 return')
                self.c += 1
                self.num = 0
                return
        except:
            if self.num < 1:
                self.num += 1
                result_zhu = self.ocr(self.img_path_zhu)
                self.text_zhu(result_zhu)
            else:
                print('识别错误')
                self.num = 0

    def text_fu(self, result):  # 副武器名字
        # 输出识别结果
        try:
            r = result[0][0][1][0].replace(" ", "")
            t = re.sub(r'[\\/:*?"<>|]', '', r)
            # print('副武器', result)
            # print(t)
            a = self.name + t
            if self.name_fu != a:
                self.name_fu = self.name + t
                print(self.name_fu)
                self.num = 0
            else:
                print('副武器内容相同 return')
                self.c += 1
                self.num = 0
                return
        except:
            if self.num < 1:
                self.num += 1
                result_fu = self.ocr(self.img_path_fu)
                self.text_fu(result_fu)
            else:
                print('识别错误')
                self.num = 0

    def text_names(self, result):
        # 输出识别结果
        try:
            r = result[0][0][1][0].replace(" ", "")
            t = re.sub(r'[\\/:*?"<>|]', '', r)
            # print(result)
            # print(t)
            self.text_names_s = t
            self.print_to_text(f'干员名：{t}')
            if self.contains_chinese(t):
                self.print_to_text('干员名不得有中文😒😒')
        except:
            if self.num < 1:
                self.num += 1
                result_name = self.ocren(self.img_path_name)
                self.text_names(result_name)
            else:
                self.num = 0
                self.print_to_text('识别错误😒😒')

    def text_zhus(self, result):  # 主武器名字
        # 输出识别结果
        try:
            r = result[0][0][1][0].replace(" ", "")
            t = re.sub(r'[\\/:*?"<>|]', '', r)
            # print('主武器', result)
            # print(t)
            a = self.text_names_s + t
            self.print_to_text(f'主武器名：{a}')
        except:
            if self.num < 1:
                self.num += 1
                result_zhu = self.ocr(self.img_path_zhu)
                self.text_zhus(result_zhu)
            else:
                self.num = 0
                self.print_to_text('识别错误😒😒')

    def text_fus(self, result):  # 副武器名字
        # 输出识别结果
        try:
            r = result[0][0][1][0].replace(" ", "")
            t = re.sub(r'[\\/:*?"<>|]', '', r)
            # print('副武器', result)
            # print(t)
            a = self.text_names_s + t
            self.print_to_text(f'副武器名：{a}')
        except:
            if self.num < 1:
                self.num += 1
                result_fu = self.ocr(self.img_path_fu)
                self.text_fus(result_fu)
            else:
                self.num = 0
                self.print_to_text('识别错误😒😒')

    def colorr_zhu_and_fu(self, path_zhu, path_fu):
        img = Image.open(path_zhu)
        color = img.getpixel((1, 1))
        # print(color)
        a, b, c = color
        # print('主武器颜色', a)
        if a >= 120:
            self.name_zhu_color = True
        elif (self.name_fu_color and self.name_zhu_color) or (not self.name_zhu_color and not self.name_fu_color):
            # print('执行zero配置')
            if self.name in self.name_dun_one or self.name_zhu in self.name_dun_one:
                self.name_with = self.name_fu
                self.fff(self.name_with)
            else:
                self.name_with = self.name_zero
                self.fff(self.name_zero)
        if a < 120:
            self.name_zhu_color = False
        elif (self.name_fu_color and self.name_zhu_color) or (not self.name_zhu_color and not self.name_fu_color):
            # print('执行zero配置')
            if self.name in self.name_dun_one or self.name_zhu in self.name_dun_one:
                self.name_with = self.name_fu
                self.fff(self.name_with)
            else:
                self.name_with = self.name_zero
                self.fff(self.name_zero)

        imgimg = Image.open(path_fu)
        colorcolor = imgimg.getpixel((1, 1))
        # print(color)
        aa, bb, cc = colorcolor
        # print('副武器颜色', a)
        if aa >= 120:
            self.name_fu_color = True
        elif (self.name_fu_color and self.name_zhu_color) or (not self.name_zhu_color and not self.name_fu_color):
            # print('执行zero配置')
            if self.name in self.name_dun_one or self.name_zhu in self.name_dun_one:
                self.name_with = self.name_fu
                self.fff(self.name_with)
            else:
                self.name_with = self.name_zero
                self.fff(self.name_zero)
        if aa < 120:
            self.name_fu_color = False
        elif (self.name_fu_color and self.name_zhu_color) or (not self.name_zhu_color and not self.name_fu_color):
            # print('执行zero配置')
            if self.name in self.name_dun_one or self.name_zhu in self.name_dun_one:
                self.name_with = self.name_fu
                self.fff(self.name_with)
            else:
                self.name_with = self.name_zero
                self.fff(self.name_zero)

        if (not self.name_zhu_color and self.name_fu_color) or (self.name_zhu_color and not self.name_fu_color):
            if a < 120 and self.name_fu != self.name_with:
                self.name_zhu_color = False
                self.name_with = self.name_fu
                self.fff(self.name_with)
            elif a >= 120 and self.name_with != self.name_zhu:
                self.name_fu_color = False
                self.name_with = self.name_zhu
                self.fff(self.name_with)

        if (not self.name_zhu_color and self.name_fu_color) or (self.name_zhu_color and not self.name_fu_color):
            if aa < 120 and self.name_with != self.name_zhu:
                self.name_fu_color = False
                self.name_with = self.name_zhu
                self.fff(self.name_with)
            elif aa >= 120 and self.name_fu != self.name_with:
                self.name_zhu_color = False
                self.name_with = self.name_fu
                self.fff(self.name_with)

    def fff(self, txt):
        self.name00 = str(txt)

    def text_7XZ(self, result):
        try:
            t = result[0][0][1][0]
            print(result)
            print(t)
            return t
        except:
            return '77777'

    def text_guanz(self, result):
        try:
            print(result)
            t = result[0][0][1][0]
            print(t)
            return t
        except:
            return 'sssss'

    def aaaaa(self):
        while True:
            if self.spot == 1:
                return
            reft = self.is_reft_mouse_button_pressed()
            if reft:
                self.reft_num += 1
            else:
                self.reft_num = 0
                self.jietu_zhunei()
                self.jietu_funei()
                self.colorr_zhu_and_fu(self.img_path_zhunei, self.img_path_funei)
                time.sleep(self.slider_time_value)
            if reft and 0 < self.reft_num < 2 / self.slider_time_value:
                self.reft_num += 1
                self.jietu_zhunei()
                self.jietu_funei()
                self.colorr_zhu_and_fu(self.img_path_zhunei, self.img_path_funei)
                time.sleep(self.slider_time_value)
            elif self.reft_num >= 2 / self.slider_time_value:
                print('------------------局内配置锁定1秒--------------------')
                time.sleep(1)
            else:
                self.reft_num = 0
                self.jietu_zhunei()
                self.jietu_funei()
                self.colorr_zhu_and_fu(self.img_path_zhunei, self.img_path_funei)
                time.sleep(self.slider_time_value)

    def cv(self, path1, path2):
        # 读取目标图像和模板图像
        try:
            image = cv2.imread(path1)  # 目标图像
            template = cv2.imread(path2)  # 模板图像

            # 将图像转换为灰度图像（模板匹配在灰度图像上效果更好）
            image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

            # 使用模板匹配函数进行匹配
            result = cv2.matchTemplate(image_gray, template_gray, cv2.TM_CCOEFF_NORMED)

            # 获取匹配位置（找到相似度最高的位置）
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            # 输出相似度值
            print(f'相似度值: {max_val}')
            return max_val
        except Exception as e:
            print(e)
            self.print_to_label('cv识别出错,需自行截图替换标志图😒😒')
            self.print_to_label2('如替换后无法解决联系作者😒😒')

    def zhuxianc(self):
        while True:
            if self.spot == 1:
                return
            self.jietu_guanz()
            max_val_guan = self.cv(self.img_path_guanz, self.img_path_guanz_true)
            self.jietu_7XZ()
            max_val_7XZ = self.cv(self.img_path_7XZ, self.img_path_7XZ_true)
            if max_val_guan > 0.8 or max_val_7XZ > 0.8:
                self.print_to_text_display_label3("⚠️局内休眠5秒")
                time.sleep(5)
            else:
                if self.toggle_preview_true:
                    self.jietu_poper()
                    self.max_val_poper_list = []
                    for path in self.template_files:
                        # 拼接文件夹路径和模板文件路径
                        template_path = os.path.join(self.img_path_poper_true, path)
                        # print(template_path)

                        # 调用 cv 方法计算匹配度
                        max_val = self.cv(self.img_path_poper, template_path)

                        # 将每次计算的匹配度添加到列表
                        self.max_val_poper_list.append(max_val)

                    # 检查是否有任何一个模板的匹配度大于 0.8
                    if any(max_val > 0.8 for max_val in self.max_val_poper_list):
                        self.jietu_name()
                        result_name = self.ocr(self.img_path_name)
                        self.text_name(result_name)
                        if self.c >= self.slider_time_name_value:
                            if self.mui == 0 and self.name != '':
                                self.muisc()
                                self.muisc()
                                self.muisc()
                                self.mui += 1
                                self.print_to_label(f'当前配置\n{self.name}\n{self.name_zhu}\n{self.name_fu}')
                            self.print_to_text_display_label3('⚠️锁定中')
                            self.print_to_text_display_label3("⚠️干员页识别间隔1秒")
                            time.sleep(1)
                        else:
                            if self.slider_time_name_value == 1:
                                self.c += 1
                                self.jietu_zhu()
                                result_zhu = self.ocren(self.img_path_zhu)
                                self.text_zhu(result_zhu)
                                self.jietu_fu()
                                result_fu = self.ocren(self.img_path_fu)
                                self.text_fu(result_fu)
                            else:
                                self.jietu_zhu()
                                result_zhu = self.ocren(self.img_path_zhu)
                                self.text_zhu(result_zhu)
                                self.jietu_fu()
                                result_fu = self.ocren(self.img_path_fu)
                                self.text_fu(result_fu)
                                self.print_to_text_display_label3("⚠️干员页识别间隔1秒")
                                time.sleep(1)
                    else:
                        self.print_to_text_display_label3("⚠️非干员页休眠2秒")
                        time.sleep(2)
                else:
                    self.jietu_name()
                    result_name = self.ocr(self.img_path_name)
                    self.text_name(result_name)
                    if self.c >= self.slider_time_name_value:
                        if self.mui == 0 and self.name != '':
                            self.muisc()
                            self.muisc()
                            self.muisc()
                            self.mui += 1
                            self.print_to_label(f'当前配置\n{self.name}\n{self.name_zhu}\n{self.name_fu}')
                        self.print_to_text_display_label3('⚠️锁定中')
                        self.print_to_text_display_label3("⚠️干员页识别间隔1秒")
                        time.sleep(1)
                    else:
                        if self.slider_time_name_value == 1:
                            self.c += 1
                            self.jietu_zhu()
                            result_zhu = self.ocren(self.img_path_zhu)
                            self.text_zhu(result_zhu)
                            self.jietu_fu()
                            result_fu = self.ocren(self.img_path_fu)
                            self.text_fu(result_fu)
                        else:
                            self.jietu_zhu()
                            result_zhu = self.ocren(self.img_path_zhu)
                            self.text_zhu(result_zhu)
                            self.jietu_fu()
                            result_fu = self.ocren(self.img_path_fu)
                            self.text_fu(result_fu)
                            self.print_to_text_display_label3("⚠️干员页识别间隔1秒")
                            time.sleep(1)

    def print_to_label(self, content):
        self.display_label.configure(text=content)

    def print_to_label2(self, content):
        self.display_label2.configure(text=content)

    def print_to_text_display_label3(self, content):
        self.text_display_label3.delete("1.0", "end-5l")
        self.text_display_label3.insert(tk.END, content + "\n")
        self.text_display_label3.see(tk.END)  # 自动滚动到最新内容

    def print_to_text(self, content):
        self.text_display.insert(tk.END, content + "\n")
        self.text_display.see(tk.END)  # 自动滚动到最新内容

    def main(self):
        if self.is_on:
            self.spot = 0
            t_get2 = threading.Thread(target=self.aaaaa)
            t_get2.daemon = True
            t_get2.start()
            t_get3 = threading.Thread(target=self.zhuxianc)
            t_get3.daemon = True
            t_get3.start()
            self.button.configure(text="自动识别-on", fg_color="green")
            self.print_to_label('自动识别已启动😍😍')
        else:
            self.spot = 1
            self.button.configure(text="自动识别-off", fg_color="red")
            self.print_to_label('自动识别已关闭😒😒')
            self.name = ''
            self.name_zhu = ''
            self.name_fu = ''
            self.name_with = ''
            self.mui = 0
            self.c = 0
        self.is_on = not self.is_on  # 切换状态

    def main_end(self):
        self.spot = 1
        self.spot11 = 1
        self.spot00 = 1
        if self.listener1:
            self.listener1.stop()
            self.listener1 = None


if __name__ == '__main__':
    x = Auto_OCR()
    x.mainloop()
    x.main_end()
