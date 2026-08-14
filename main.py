# main.py
import os
import struct
import hashlib
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.core.window import Window
from kivy.utils import platform
from cryptography.fernet import Fernet

# 尝试导入 Android 文件选择器
if platform == 'android':
    from plyer import filechooser

# --- 样式配置 (Kivy KV 语言字符串) ---
# 这里我们定义了界面布局，包括加密页、解密页和设置页
KV = '''
<MainLayout>:
    orientation: 'vertical'
    
    # 顶部标题栏
    BoxLayout:
        size_hint_y: 0.1
        canvas.before:
            Color:
                rgba: 0.3, 0.7, 0.3, 1 if app.theme == 'light' else (0.2, 0.8, 0.2, 1) if app.theme == 'eye' else (0.2, 0.6, 0.2, 1)
            Rectangle:
                pos: self.pos
                size: self.size
        Label:
            text: 'SecureFile Vault' if root.current_tab == 'enc' else 'Vault Decryptor'
            font_size: '20sp'
            bold: True
            color: 1, 1, 1, 1

    # 内容区域 (屏幕管理器)
    ScreenManager:
        id: sm
        Screen:
            name: 'enc_screen'
            BoxLayout:
                orientation: 'vertical'
                padding: '20dp'
                spacing: '20dp'
                
                Label:
                    text: '选择要加密的文件'
                    size_hint_y: None
                    height: '30dp'
                    color: 0, 0, 0, 1 if app.theme != 'dark' else 1, 1, 1, 1
                
                TextInput:
                    id: enc_path
                    hint_text: '未选择文件'
                    readonly: True
                    size_hint_y: None
                    height: '50dp'
                    background_color: 0.9, 0.9, 0.9, 1 if app.theme != 'dark' else 0.3, 0.3, 0.3, 1
                    foreground_color: 0, 0, 0, 1 if app.theme != 'dark' else 1, 1, 1, 1
                
                Button:
                    text: '浏览文件'
                    size_hint_y: None
                    height: '50dp'
                    background_color: 0.4, 0.5, 0.6, 1
                    on_press: app.select_file('enc')
                
                Button:
                    text: '开始加密'
                    size_hint_y: None
                    height: '60dp'
                    background_color: 0.3, 0.7, 0.3, 1
                    on_press: app.encrypt_process()
                
                ScrollView:
                    TextInput:
                        id: enc_log
                        text: '等待操作...'
                        readonly: True
                        size_hint_y: None
                        height: self.minimum_height
                        font_size: '12sp'
                        background_color: 1, 1, 1, 1 if app.theme != 'dark' else 0.2, 0.2, 0.2, 1
                        foreground_color: 0, 0, 0, 1 if app.theme != 'dark' else 1, 1, 1, 1

        Screen:
            name: 'dec_screen'
            BoxLayout:
                orientation: 'vertical'
                padding: '20dp'
                spacing: '20dp'
                
                Label:
                    text: '选择 .vault 文件'
                    size_hint_y: None
                    height: '30dp'
                    color: 0, 0, 0, 1 if app.theme != 'dark' else 1, 1, 1, 1
                
                TextInput:
                    id: dec_path
                    hint_text: '未选择文件'
                    readonly: True
                    size_hint_y: None
                    height: '50dp'
                    background_color: 0.9, 0.9, 0.9, 1 if app.theme != 'dark' else 0.3, 0.3, 0.3, 1
                    foreground_color: 0, 0, 0, 1 if app.theme != 'dark' else 1, 1, 1, 1
                
                Button:
                    text: '浏览文件'
                    size_hint_y: None
                    height: '50dp'
                    background_color: 0.4, 0.5, 0.6, 1
                    on_press: app.select_file('dec')
                
                Button:
                    text: '开始解密'
                    size_hint_y: None
                    height: '60dp'
                    background_color: 0.13, 0.59, 0.95, 1
                    on_press: app.decrypt_process()
                
                ScrollView:
                    TextInput:
                        id: dec_log
                        text: '等待操作...'
                        readonly: True
                        size_hint_y: None
                        height: self.minimum_height
                        font_size: '12sp'
                        background_color: 1, 1, 1, 1 if app.theme != 'dark' else 0.2, 0.2, 0.2, 1
                        foreground_color: 0, 0, 0, 1 if app.theme != 'dark' else 1, 1, 1, 1

        Screen:
            name: 'set_screen'
            BoxLayout:
                orientation: 'vertical'
                padding: '20dp'
                spacing: '20dp'
                
                Label:
                    text: '界面风格'
                    size_hint_y: None
                    height: '30dp'
                    color: 0, 0, 0, 1 if app.theme != 'dark' else 1, 1, 1, 1
                
                Spinner:
                    id: theme_spinner
                    text: '浅色模式'
                    values: ('浅色模式', '深色模式', '护眼模式')
                    size_hint_y: None
                    height: '50dp'
                    background_color: 0.9, 0.9, 0.9, 1 if app.theme != 'dark' else 0.3, 0.3, 0.3, 1
                    on_text: app.set_theme(self.text)

                Label:
                    text: '关于'
                    size_hint_y: None
                    height: '30dp'
                    color: 0, 0, 0, 1 if app.theme != 'dark' else 1, 1, 1, 1
                
                Button:
                    text: '关于本软件'
                    size_hint_y: None
                    height: '50dp'
                    background_color: 0.4, 0.5, 0.6, 1
                    on_press: app.show_about()

    # 底部导航栏
    BoxLayout:
        size_hint_y: 0.1
        canvas.before:
            Color:
                rgba: 0.95, 0.95, 0.95, 1 if app.theme != 'dark' else 0.2, 0.2, 0.2, 1
            Rectangle:
                pos: self.pos
                size: self.size
        
        Button:
            text: '加密'
            background_color: 0.9, 0.9, 0.9, 1
            on_press: root.switch_tab('enc')
        Button:
            text: '解密'
            background_color: 0.9, 0.9, 0.9, 1
            on_press: root.switch_tab('dec')
        Button:
            text: '设置'
            background_color: 0.9, 0.9, 0.9, 1
            on_press: root.switch_tab('set')
'''

from kivy.uix.screenmanager import Screen, ScreenManager

class MainLayout(BoxLayout):
    current_tab = 'enc'
    
    def switch_tab(self, tab):
        self.current_tab = tab
        sm = self.ids.sm
        if tab == 'enc':
            sm.current = 'enc_screen'
        elif tab == 'dec':
            sm.current = 'dec_screen'
        elif tab == 'set':
            sm.current = 'set_screen'

class SecureVaultApp(App):
    theme = 'light'  # light, dark, eye

    def build(self):
        self.title = 'SecureFile Vault'
        return MainLayout()

    def select_file(self, mode):
        if platform == 'android':
            filechooser.open_file(on_selection=lambda x: self._file_selected(x, mode))
        else:
            # 桌面测试时的简单模拟
            from tkinter import Tk, filedialog
            root = Tk()
            root.withdraw()
            file_path = filedialog.askopenfilename()
            root.destroy()
            self._file_selected([file_path], mode)

    def _file_selected(self, selection, mode):
        if selection:
            path = selection[0]
            if mode == 'enc':
                self.root.ids.enc_path.text = path
                self.log('enc', f"已选择: {os.path.basename(path)}")
            else:
                self.root.ids.dec_path.text = path
                self.log('dec', f"已选择: {os.path.basename(path)}")

    def log(self, mode, message):
        if mode == 'enc':
            self.root.ids.enc_log.text += f"\n{message}"
        else:
            self.root.ids.dec_log.text += f"\n{message}"

    def encrypt_process(self):
        input_file = self.root.ids.enc_path.text
        if not input_file or not os.path.exists(input_file):
            self.show_popup("错误", "请先选择有效的文件！")
            return

        try:
            # 1. 加密
            self.log('enc', "[1/3] 正在生成密钥并加密数据...")
            key = Fernet.generate_key()
            cipher_suite = Fernet(key)
            with open(input_file, "rb") as f:
                file_data = f.read()
            encrypted_data = cipher_suite.encrypt(file_data)

            # 2. 哈希
            self.log('enc', "[2/3] 正在计算文件指纹 (SHA-256)...")
            original_hash = self.generate_hash(input_file)
            if not original_hash:
                raise Exception("无法读取文件")

            # 3. 打包
            self.log('enc', "[3/3] 正在打包生成 .vault 文件...")
            filename_bytes = os.path.basename(input_file).encode('utf-8')
            hash_bytes = original_hash.encode('utf-8')
            key_bytes = key
            
            output_file = input_file + ".vault"
            with open(output_file, "wb") as f:
                f.write(b"VLTV")
                f.write(struct.pack('<IIII', len(filename_bytes), len(key_bytes), len(hash_bytes), len(encrypted_data)))
                f.write(filename_bytes)
                f.write(key_bytes)
                f.write(hash_bytes)
                f.write(encrypted_data)
            
            self.log('enc', f"✅ 成功！文件已保存为: {os.path.basename(output_file)}")
            self.show_popup("完成", "文件加密成功！")
            
        except Exception as e:
            self.log('enc', f"❌ 错误: {str(e)}")
            self.show_popup("错误", f"加密失败: {str(e)}")

    def decrypt_process(self):
        vault_file = self.root.ids.dec_path.text
        if not vault_file or not os.path.exists(vault_file):
            self.show_popup("错误", "请先选择有效的 .vault 文件！")
            return

        try:
            # 1. 解析
            self.log('dec', "[1/4] 正在解析文件结构...")
            with open(vault_file, "rb") as f:
                magic = f.read(4)
                if magic != b"VLTV":
                    raise Exception("无效的文件格式")
                
                fname_len, key_len, hash_len, enc_len = struct.unpack('<IIII', f.read(16))
                filename_bytes = f.read(fname_len)
                key_bytes = f.read(key_len)
                stored_hash_bytes = f.read(hash_len)
                encrypted_data = f.read(enc_len)
                
                original_filename = filename_bytes.decode('utf-8')
                stored_hash = stored_hash_bytes.decode('utf-8')

            # 2. 解密
            self.log('dec', f"[2/4] 正在解密数据 (目标文件: {original_filename})...")
            cipher_suite = Fernet(key_bytes)
            decrypted_data = cipher_suite.decrypt(encrypted_data)

            # 3. 写入
            self.log('dec', "[3/4] 正在写入磁盘...")
            output_file = original_filename
            
            # Android 存储权限处理通常比较复杂，这里假设写入应用私有目录或用户授权的目录
            # 为简化代码，这里直接写入，实际 Android 开发需要处理 Storage Access Framework
            with open(output_file, "wb") as f:
                f.write(decrypted_data)

            # 4. 校验
            self.log('dec', "[4/4] 正在校验完整性...")
            current_hash = self.generate_hash(output_file)
            
            if current_hash == stored_hash:
                self.log('dec', "✅ 校验成功！文件完整且未被篡改。")
                self.show_popup("完成", f"解密成功！\n文件已还原为: {output_file}")
            else:
                self.log('dec', "❌ 校验失败！文件可能已损坏。")
                raise Exception("哈希值不匹配")

        except Exception as e:
            self.log('dec', f"❌ 错误: {str(e)}")
            self.show_popup("错误", f"解密失败: {str(e)}")

    def generate_hash(self, filepath):
        sha256_hash = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception:
            return None

    def set_theme(self, theme_name):
        if '浅色' in theme_name:
            self.theme = 'light'
        elif '深色' in theme_name:
            self.theme = 'dark'
        elif '护眼' in theme_name:
            self.theme = 'eye'
        
        # 强制刷新界面颜色
        # 注意：KV语言中的条件判断会自动根据 app.theme 变量更新
        # 但某些背景色可能需要手动触发重绘，这里简化处理
        pass

    def show_popup(self, title, content):
        popup = Popup(title=title, content=Label(text=content), size_hint=(0.8, 0.4))
        popup.open()

    def show_about(self):
        content = (
            "文件加密工具 v1.0\n\n"
            "基于 Kivy 和 Cryptography 开发。\n"
            "功能特点：\n"
            "- 文件加密与打包\n"
            "- SHA-256 完整性校验\n"
            "- 跨平台移动端支持\n\n"
            "By WakeStar"
        )
        self.show_popup("关于", content)

if __name__ == '__main__':
    SecureVaultApp().run()
