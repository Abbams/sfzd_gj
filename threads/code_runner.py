import sys
import os
import re
import subprocess
import tempfile
from PyQt5.QtCore import QThread, pyqtSignal

class CodeRunner(QThread):
    """代码运行线程"""
    output_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, code, input_data, language='cpp'):
        super().__init__()
        self.code = code
        self.input_data = input_data
        self.language = language

    def run(self):
        try:
            if self.language == 'python':
                self.run_python()
            elif self.language == 'cpp':
                self.run_cpp()
            elif self.language == 'java':
                self.run_java()
            else:
                self.error_signal.emit(f"不支持的语言: {self.language}")
        except Exception as e:
            self.error_signal.emit(str(e))
        finally:
            self.finished_signal.emit()

    def run_python(self):
        """运行Python代码"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(self.code)
            temp_file = f.name

        try:
            process = subprocess.Popen(
                [sys.executable, temp_file],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )

            stdout, stderr = process.communicate(input=self.input_data, timeout=10)

            if stderr:
                self.error_signal.emit(stderr)
            else:
                self.output_signal.emit(stdout)

        except subprocess.TimeoutExpired:
            process.kill()
            self.error_signal.emit("程序运行超时（超过10秒）")
        except Exception as e:
            self.error_signal.emit(str(e))
        finally:
            os.unlink(temp_file)

    def run_cpp(self):
        """运行C++代码"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False, encoding='utf-8') as f:
            f.write(self.code)
            cpp_file = f.name

        exe_file = cpp_file + '.exe'

        try:
            compile_process = subprocess.run(
                ['g++', cpp_file, '-o', exe_file],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )

            if compile_process.returncode != 0:
                self.error_signal.emit(f"编译错误:\n{compile_process.stderr}")
                return

            run_process = subprocess.run(
                [exe_file],
                input=self.input_data,
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=10
            )

            if run_process.stderr:
                self.error_signal.emit(run_process.stderr)
            else:
                self.output_signal.emit(run_process.stdout)

        except subprocess.TimeoutExpired:
            self.error_signal.emit("程序运行超时（超过10秒）")
        except Exception as e:
            self.error_signal.emit(str(e))
        finally:
            if os.path.exists(cpp_file):
                os.unlink(cpp_file)
            if os.path.exists(exe_file):
                os.unlink(exe_file)

    def run_java(self):
        """运行Java代码"""
        class_name = None
        for line in self.code.split('\n'):
            if 'public class' in line:
                match = re.search(r'public\s+class\s+(\w+)', line)
                if match:
                    class_name = match.group(1)
                    break

        if not class_name:
            class_name = 'Main'

        with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False, encoding='utf-8') as f:
            f.write(self.code)
            java_file = f.name

        try:
            compile_process = subprocess.run(
                ['javac', java_file],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )

            if compile_process.returncode != 0:
                self.error_signal.emit(f"编译错误:\n{compile_process.stderr}")
                return

            class_dir = os.path.dirname(java_file)
            run_process = subprocess.run(
                ['java', '-cp', class_dir, class_name],
                input=self.input_data,
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=10
            )

            if run_process.stderr:
                self.error_signal.emit(run_process.stderr)
            else:
                self.output_signal.emit(run_process.stdout)

        except subprocess.TimeoutExpired:
            self.error_signal.emit("程序运行超时（超过10秒）")
        except Exception as e:
            self.error_signal.emit(str(e))
        finally:
            if os.path.exists(java_file):
                os.unlink(java_file)
            class_file = os.path.join(os.path.dirname(java_file), f"{class_name}.class")
            if os.path.exists(class_file):
                os.unlink(class_file)