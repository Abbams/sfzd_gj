import os
import subprocess
from PyQt5.QtCore import QThread, pyqtSignal

class DataTester(QThread):
    """数据测试线程 - 使用编译好的C++程序运行所有输入文件"""
    progress_signal = pyqtSignal(int)
    message_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, exe_path, input_files, output_dir):
        super().__init__()
        self.exe_path = exe_path
        self.input_files = input_files
        self.output_dir = output_dir

    def run(self):
        total = len(self.input_files)
        for i, in_file in enumerate(self.input_files):
            try:
                with open(in_file, 'r', encoding='utf-8') as f:
                    input_data = f.read()

                process = subprocess.Popen(
                    [self.exe_path],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='utf-8'
                )

                stdout, stderr = process.communicate(input=input_data, timeout=30)

                if stderr:
                    self.error_signal.emit(f"运行 {os.path.basename(in_file)} 时出错:\n{stderr}")
                else:
                    out_file = os.path.join(self.output_dir, os.path.basename(in_file).replace('.in', '.out'))
                    with open(out_file, 'w', encoding='utf-8') as f:
                        f.write(stdout)

                    self.message_signal.emit(f"已生成 {os.path.basename(out_file)}")

            except subprocess.TimeoutExpired:
                process.kill()
                self.error_signal.emit(f"运行 {os.path.basename(in_file)} 时超时")
            except Exception as e:
                self.error_signal.emit(f"运行 {os.path.basename(in_file)} 时出错: {str(e)}")

            self.progress_signal.emit(int((i + 1) / total * 100))

        self.finished_signal.emit()