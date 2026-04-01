import os
import subprocess
import sys
from PyQt5.QtCore import QThread, pyqtSignal

class DataGenerator(QThread):
    """数据生成线程 - 使用外部文件"""
    progress_signal = pyqtSignal(int)
    message_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, generator_file, count=10, data_scale=1):
        super().__init__()
        self.generator_file = generator_file
        self.count = count
        self.data_scale = data_scale
        self.output_dir = ""

    def run(self):
        try:
            self.run_python_generator()
        except Exception as e:
            self.error_signal.emit(str(e))
        finally:
            self.finished_signal.emit()

    def run_python_generator(self):
        """运行Python生成器文件"""
        for i in range(1, self.count + 1):
            try:
                process = subprocess.Popen(
                    [sys.executable, self.generator_file],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='utf-8'
                )

                input_data = f"{i} {self.data_scale}"
                stdout, stderr = process.communicate(input=input_data, timeout=10)

                if stderr:
                    self.error_signal.emit(f"生成第{i}个数据时出现错误:\n{stderr}")
                else:
                    input_file = os.path.join(self.output_dir, f"{i}.in")
                    with open(input_file, 'w', encoding='utf-8') as f:
                        f.write(stdout)

                    self.message_signal.emit(f"已生成第{i}个输入文件")

            except subprocess.TimeoutExpired:
                process.kill()
                self.error_signal.emit(f"生成第{i}个数据时超时")
            except Exception as e:
                self.error_signal.emit(f"生成第{i}个数据时出错: {str(e)}")

            self.progress_signal.emit(int(i / self.count * 100))