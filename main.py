import sys
import os
import json
import re
import subprocess
import tempfile
import shutil
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QMenuBar, QMenu, QAction, QPushButton, QLabel, QTextEdit,
    QListWidget, QListWidgetItem, QMessageBox, QFileDialog,
    QSplitter, QGroupBox, QLineEdit, QTabWidget,
    QComboBox, QProgressDialog, QSpinBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont


class CodeRunner(QThread):
    """代码运行线程"""
    output_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, code, input_data, language='python'):
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
            # 运行代码并捕获输出
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
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False, encoding='utf-8') as f:
            f.write(self.code)
            cpp_file = f.name

        exe_file = cpp_file + '.exe'

        try:
            # 编译
            compile_process = subprocess.run(
                ['g++', cpp_file, '-o', exe_file],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )

            if compile_process.returncode != 0:
                self.error_signal.emit(f"编译错误:\n{compile_process.stderr}")
                return

            # 运行
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
            # 清理临时文件
            if os.path.exists(cpp_file):
                os.unlink(cpp_file)
            if os.path.exists(exe_file):
                os.unlink(exe_file)

    def run_java(self):
        """运行Java代码"""
        # 提取类名
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
            # 编译
            compile_process = subprocess.run(
                ['javac', java_file],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )

            if compile_process.returncode != 0:
                self.error_signal.emit(f"编译错误:\n{compile_process.stderr}")
                return

            # 运行
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
            # 清理临时文件
            if os.path.exists(java_file):
                os.unlink(java_file)
            class_file = os.path.join(os.path.dirname(java_file), f"{class_name}.class")
            if os.path.exists(class_file):
                os.unlink(class_file)


class DataGenerator(QThread):
    """数据生成线程 - 使用外部文件"""
    progress_signal = pyqtSignal(int)
    message_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, generator_file, count=10, data_scale=1):
        super().__init__()
        self.generator_file = generator_file  # 文件路径
        self.count = count
        self.data_scale = data_scale  # 数据规模参数
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
                # 直接运行外部生成器文件
                process = subprocess.Popen(
                    [sys.executable, self.generator_file],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='utf-8'
                )

                # 传入当前编号和数据规模作为参数
                # 格式：编号 数据规模
                input_data = f"{i} {self.data_scale}"
                stdout, stderr = process.communicate(input=input_data, timeout=10)

                if stderr:
                    self.error_signal.emit(f"生成第{i}个数据时出现错误:\n{stderr}")
                else:
                    # 保存生成的输入数据
                    input_file = os.path.join(self.output_dir, f"{i}.in")
                    with open(input_file, 'w', encoding='utf-8') as f:
                        f.write(stdout)

                    self.message_signal.emit(f"已生成第{i}个输入文件")

            except subprocess.TimeoutExpired:
                process.kill()
                self.error_signal.emit(f"生成第{i}个数据时超时")
            except Exception as e:
                self.error_signal.emit(f"生成第{i}个数据时出错: {str(e)}")

            # 更新进度
            self.progress_signal.emit(int(i / self.count * 100))


class DataTester(QThread):
    """数据测试线程 - 使用编译好的C++程序运行所有输入文件"""
    progress_signal = pyqtSignal(int)
    message_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, exe_path, input_files, output_dir):
        super().__init__()
        self.exe_path = exe_path  # 编译好的exe文件路径
        self.input_files = input_files  # 输入文件列表
        self.output_dir = output_dir  # 输出目录

    def run(self):
        total = len(self.input_files)
        for i, in_file in enumerate(self.input_files):
            try:
                # 读取输入文件
                with open(in_file, 'r', encoding='utf-8') as f:
                    input_data = f.read()

                # 运行exe文件
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
                    # 保存输出文件
                    out_file = os.path.join(self.output_dir, os.path.basename(in_file).replace('.in', '.out'))
                    with open(out_file, 'w', encoding='utf-8') as f:
                        f.write(stdout)

                    self.message_signal.emit(f"已生成 {os.path.basename(out_file)}")

            except subprocess.TimeoutExpired:
                process.kill()
                self.error_signal.emit(f"运行 {os.path.basename(in_file)} 时超时")
            except Exception as e:
                self.error_signal.emit(f"运行 {os.path.basename(in_file)} 时出错: {str(e)}")

            # 更新进度
            self.progress_signal.emit(int((i + 1) / total * 100))

        self.finished_signal.emit()


class Problem:
    """题目类，包含题面和数据文件信息"""

    def __init__(self, title="新题目", problem_id="0"):
        self.id = problem_id  # 题目编号
        self.title = title  # 题目名称
        self.full_title = f"{problem_id}_{title}" if problem_id != "0" else title  # 完整标题
        self.description = ""  # 题面描述
        self.input_description = ""  # 输入说明
        self.output_description = ""  # 输出说明
        self.sample_input = ""  # 样例输入
        self.sample_output = ""  # 样例输出
        self.solution_code = ""  # 正解代码
        self.generator_path = ""  # 生成器文件路径
        self.data_files = []  # 数据文件列表
        self.problem_path = ""  # 题目保存路径
        self.language = "c++"  # 默认语言
        self.compiled_exe_path = ""  # 编译好的exe文件路径


class ProblemMaker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.problems = []  # 题目列表
        self.current_problem = None
        self.current_problem_index = -1
        self.problems_base_path = r".\AlgorithmProblems"  # 固定题目路径
        self.initUI()
        self.loadAllProblems()  # 启动时加载所有题目

    def initUI(self):
        """初始化用户界面"""
        self.setWindowTitle("算法题目制作软件")
        self.setGeometry(100, 100, 1300, 900)

        # 设置字体
        font = QFont("微软雅黑", 9)
        self.setFont(font)

        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 创建菜单栏
        self.createMenuBar()

        # 创建主内容区域（水平分割）
        content_splitter = QSplitter(Qt.Horizontal)

        # 左侧题目信息栏
        left_widget = self.createLeftPanel()
        content_splitter.addWidget(left_widget)

        # 右侧题目选择栏
        right_widget = self.createRightPanel()
        content_splitter.addWidget(right_widget)

        # 设置分割比例
        content_splitter.setSizes([1000, 500])

        main_layout.addWidget(content_splitter)

        # 底部按钮栏
        bottom_widget = self.createBottomPanel()
        main_layout.addWidget(bottom_widget)

        # 显示题目路径
        self.path_label.setText(f"题目路径: {self.problems_base_path}")

    def packDataFiles(self):
        """
        将所有 .in 和 .out 文件打包成zip文件
        zip文件名与题目名称相同，保存在题目目录的同级目录
        """
        if not self.current_problem:
            QMessageBox.warning(self, "警告", "请先选择一个题目")
            return

        # 获取所有 .in 和 .out 文件
        data_files = []
        for file_name in os.listdir(self.current_problem.problem_path):
            if file_name.endswith('.in') or file_name.endswith('.out'):
                file_path = os.path.join(self.current_problem.problem_path, file_name)
                data_files.append(file_path)

        if not data_files:
            QMessageBox.warning(self, "警告", "没有找到数据文件")
            return

        # 创建zip文件名（与题目名称相同）
        zip_filename = f"{self.current_problem.full_title}.zip"
        zip_path = os.path.join(self.problems_base_path, zip_filename)

        # 如果zip文件已存在，询问是否覆盖
        if os.path.exists(zip_path):
            reply = QMessageBox.question(
                self, "文件已存在",
                f"文件 {zip_filename} 已存在，是否覆盖？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        try:
            import zipfile

            # 创建zip文件
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in data_files:
                    # 获取相对路径（只保留文件名）
                    arcname = os.path.basename(file_path)
                    zipf.write(file_path, arcname)

            self.output_text.append("=" * 50)
            self.output_text.append(f"打包成功！")
            self.output_text.append(f"文件保存为: {zip_path}")
            self.output_text.append(f"共打包 {len(data_files)} 个文件")

            self.status_label.setText(f"打包成功: {zip_filename}")

            # 询问是否打开所在文件夹
            reply = QMessageBox.question(
                self, "打包完成",
                f"文件已成功打包到:\n{zip_path}\n\n是否打开所在文件夹？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                # 打开文件夹并选中文件
                if sys.platform == 'win32':
                    os.startfile(os.path.dirname(zip_path))
                else:
                    import subprocess
                    subprocess.Popen(['open' if sys.platform == 'darwin' else 'xdg-open',
                                      os.path.dirname(zip_path)])

        except Exception as e:
            QMessageBox.critical(self, "打包失败", f"打包过程中发生错误:\n{str(e)}")
            self.output_text.append(f"【错误】打包失败: {str(e)}")

    def createMenuBar(self):
        """创建菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")

        # 刷新题目列表
        refresh_action = QAction("刷新题目列表(&R)", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.loadAllProblems)
        file_menu.addAction(refresh_action)

        file_menu.addSeparator()

        # 设置题目路径
        set_path_action = QAction("设置题目路径(&P)", self)
        set_path_action.triggered.connect(self.setProblemsPath)
        file_menu.addAction(set_path_action)

        file_menu.addSeparator()

        # 退出
        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 运行菜单
        run_menu = menubar.addMenu("运行(&R)")

        # 编译正解
        compile_action = QAction("编译正解(&C)", self)
        compile_action.setShortcut("F8")
        compile_action.triggered.connect(self.compileSolution)
        run_menu.addAction(compile_action)

        run_menu.addSeparator()

        # 运行正解
        run_solution_action = QAction("运行正解(&S)", self)
        run_solution_action.setShortcut("F9")
        run_solution_action.triggered.connect(self.runSolution)
        run_menu.addAction(run_solution_action)

        # 批量生成数据
        batch_generate_action = QAction("批量生成数据(&G)", self)
        batch_generate_action.setShortcut("F10")
        batch_generate_action.triggered.connect(self.generateData)
        run_menu.addAction(batch_generate_action)

        # 批量测试
        batch_test_action = QAction("批量测试(&T)", self)
        batch_test_action.setShortcut("F11")
        batch_test_action.triggered.connect(self.batchTestWithExe)
        run_menu.addAction(batch_test_action)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")

        about_action = QAction("关于(&A)", self)
        about_action.triggered.connect(self.about)
        help_menu.addAction(about_action)

    def createLeftPanel(self):
        """创建左侧题目信息面板"""
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(10, 10, 10, 10)

        # 题目标题和编号
        title_layout = QHBoxLayout()

        id_label = QLabel("题目编号:")
        self.id_edit = QLineEdit()
        self.id_edit.setPlaceholderText("输入题目编号")
        self.id_edit.setMaximumWidth(80)
        self.id_edit.setReadOnly(True)  # 设置为只读
        # self.id_edit.textChanged.connect(self.onTitleChanged)  # 注释掉这行

        title_label = QLabel("题目标题:")
        self.title_edit = QLineEdit()
        self.title_edit.setReadOnly(True)  # 设置为只读
        # self.title_edit.textChanged.connect(self.onTitleChanged)  # 注释掉这行

        title_layout.addWidget(id_label)
        title_layout.addWidget(self.id_edit)
        title_layout.addWidget(title_label)
        title_layout.addWidget(self.title_edit)
        left_layout.addLayout(title_layout)

        # 语言选择
        lang_layout = QHBoxLayout()
        lang_label = QLabel("编程语言:")
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["Python", "C++", "Java"])
        self.lang_combo.currentTextChanged.connect(self.onLanguageChanged)

        lang_layout.addWidget(lang_label)
        lang_layout.addWidget(self.lang_combo)
        lang_layout.addStretch()
        left_layout.addLayout(lang_layout)

        # 使用TabWidget组织题目信息
        tab_widget = QTabWidget()

        # 题面选项卡
        description_widget = QWidget()
        description_layout = QVBoxLayout(description_widget)

        desc_label = QLabel("题面描述:")
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("输入题面描述...")
        self.description_edit.textChanged.connect(self.onDescriptionChanged)
        description_layout.addWidget(desc_label)
        description_layout.addWidget(self.description_edit)

        tab_widget.addTab(description_widget, "题面")

        # 输入说明选项卡
        input_widget = QWidget()
        input_layout = QVBoxLayout(input_widget)

        input_label = QLabel("输入说明:")
        self.input_edit = QTextEdit()
        self.input_edit.setPlaceholderText("输入说明...")
        self.input_edit.textChanged.connect(self.onInputChanged)
        input_layout.addWidget(input_label)
        input_layout.addWidget(self.input_edit)

        tab_widget.addTab(input_widget, "输入")

        # 输出说明选项卡
        output_widget = QWidget()
        output_layout = QVBoxLayout(output_widget)

        output_label = QLabel("输出说明:")
        self.output_edit = QTextEdit()
        self.output_edit.setPlaceholderText("输出说明...")
        self.output_edit.textChanged.connect(self.onOutputChanged)
        output_layout.addWidget(output_label)
        output_layout.addWidget(self.output_edit)

        tab_widget.addTab(output_widget, "输出")

        # 样例信息选项卡
        sample_widget = QWidget()
        sample_layout = QVBoxLayout(sample_widget)

        # 样例输入
        sample_input_label = QLabel("样例输入:")
        self.sample_input_edit = QTextEdit()
        self.sample_input_edit.setPlaceholderText("样例输入...")
        self.sample_input_edit.textChanged.connect(self.onSampleInputChanged)
        sample_layout.addWidget(sample_input_label)
        sample_layout.addWidget(self.sample_input_edit)

        # 样例输出
        sample_output_label = QLabel("样例输出:")
        self.sample_output_edit = QTextEdit()
        self.sample_output_edit.setPlaceholderText("样例输出...")
        self.sample_output_edit.textChanged.connect(self.onSampleOutputChanged)
        sample_layout.addWidget(sample_output_label)
        sample_layout.addWidget(self.sample_output_edit)

        tab_widget.addTab(sample_widget, "样例")

        # 正解代码选项卡
        solution_widget = QWidget()
        solution_layout = QVBoxLayout(solution_widget)

        solution_label = QLabel("正解代码:")
        self.solution_edit = QTextEdit()
        self.solution_edit.setPlaceholderText("输入题目的正解代码...")

        self.solution_edit.setFont(QFont("Consolas", 10))
        self.solution_edit.textChanged.connect(self.onSolutionChanged)

        # 代码运行按钮
        solution_buttons = QHBoxLayout()
        compile_btn = QPushButton("编译正解")
        compile_btn.clicked.connect(self.compileSolution)
        run_solution_btn = QPushButton("运行正解")
        run_solution_btn.clicked.connect(self.runSolution)
        solution_buttons.addWidget(compile_btn)
        solution_buttons.addWidget(run_solution_btn)
        solution_buttons.addStretch()

        solution_layout.addWidget(solution_label)
        solution_layout.addWidget(self.solution_edit)
        solution_layout.addLayout(solution_buttons)

        tab_widget.addTab(solution_widget, "正解代码")

        # 数据生成器选项卡
        generator_widget = QWidget()
        generator_layout = QVBoxLayout(generator_widget)

        generator_label = QLabel("数据生成器文件:")

        # 文件路径显示和选择
        generator_file_layout = QHBoxLayout()
        self.generator_path_edit = QLineEdit()
        self.generator_path_edit.setPlaceholderText("请选择数据生成器文件")
        self.generator_path_edit.setReadOnly(True)

        select_generator_btn = QPushButton("选择文件")
        select_generator_btn.clicked.connect(self.selectGeneratorFile)

        generator_file_layout.addWidget(self.generator_path_edit)
        generator_file_layout.addWidget(select_generator_btn)

        # 数据规模设置
        scale_layout = QHBoxLayout()
        scale_label = QLabel("数据规模(1-10):")
        self.data_scale_spin = QSpinBox()
        self.data_scale_spin.setMinimum(1)
        self.data_scale_spin.setMaximum(10)
        self.data_scale_spin.setValue(1)
        self.data_scale_spin.setToolTip("设置数据规模，生成器可以根据此参数生成不同规模的数据")

        scale_layout.addWidget(scale_label)
        scale_layout.addWidget(self.data_scale_spin)
        scale_layout.addStretch()

        # 提示信息
        tip_label = QLabel("提示：生成器将从标准输入接收两个参数：数据编号(1,2,3...) 和 数据规模(1-10)")
        tip_label.setStyleSheet("color: gray; font-size: 8pt;")

        # 生成器控制
        generator_control = QHBoxLayout()
        generator_count_label = QLabel("生成数量:")
        self.generator_count = QLineEdit()
        self.generator_count.setPlaceholderText("10")
        self.generator_count.setMaximumWidth(60)

        generate_btn = QPushButton("创建输入文件")
        generate_btn.clicked.connect(self.generateData)

        generator_control.addWidget(generator_count_label)
        generator_control.addWidget(self.generator_count)
        generator_control.addWidget(generate_btn)
        generator_control.addStretch()

        generator_layout.addWidget(generator_label)
        generator_layout.addLayout(generator_file_layout)
        generator_layout.addLayout(scale_layout)
        generator_layout.addWidget(tip_label)
        generator_layout.addLayout(generator_control)

        tab_widget.addTab(generator_widget, "数据生成器")

        # 数据文件选项卡
        data_widget = QWidget()
        data_layout = QVBoxLayout(data_widget)

        # 数据文件列表
        data_list_label = QLabel("数据文件列表:")
        self.data_list_widget = QListWidget()
        self.data_list_widget.itemDoubleClicked.connect(self.openDataFile)

        # 测试按钮
        test_buttons = QHBoxLayout()

        test_selected_btn = QPushButton("测试选中(运行exe)")
        test_selected_btn.clicked.connect(self.testSelectedWithExe)

        test_all_btn = QPushButton("测试所有(运行exe)")
        test_all_btn.clicked.connect(self.batchTestWithExe)

        clear_output_btn = QPushButton("清除输出文件")
        clear_output_btn.clicked.connect(self.clearOutputFiles)
        # 添加打包按钮
        pack_btn = QPushButton("打包数据文件")
        pack_btn.clicked.connect(self.packDataFiles)

        test_buttons.addWidget(test_selected_btn)
        test_buttons.addWidget(test_all_btn)
        test_buttons.addWidget(clear_output_btn)
        test_buttons.addWidget(pack_btn)
        test_buttons.addStretch()

        data_layout.addWidget(data_list_label)
        data_layout.addWidget(self.data_list_widget)
        data_layout.addLayout(test_buttons)

        tab_widget.addTab(data_widget, "测试数据")

        left_layout.addWidget(tab_widget)

        # 输出显示区域
        output_group = QGroupBox("运行输出")
        output_layout = QVBoxLayout(output_group)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Consolas", 9))
        self.output_text.setMaximumHeight(150)

        output_layout.addWidget(self.output_text)
        left_layout.addWidget(output_group)

        return left_widget

    def createRightPanel(self):
        """创建右侧题目选择面板"""
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(10, 10, 10, 10)

        # 标题
        title_label = QLabel("题目列表")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont("微软雅黑", 12, QFont.Bold)
        title_label.setFont(title_font)
        right_layout.addWidget(title_label)

        # 路径显示
        self.path_label = QLabel()
        self.path_label.setWordWrap(True)
        self.path_label.setStyleSheet("color: blue; font-size: 9pt;")
        right_layout.addWidget(self.path_label)

        # 题目列表
        self.problem_list = QListWidget()
        self.problem_list.itemClicked.connect(self.onProblemSelected)
        right_layout.addWidget(self.problem_list)

        # 题目操作按钮
        buttons_layout = QHBoxLayout()

        add_btn = QPushButton("新建题目")
        add_btn.clicked.connect(self.newProblem)
        delete_btn = QPushButton("删除题目")
        delete_btn.clicked.connect(self.deleteProblem)
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.loadAllProblems)

        buttons_layout.addWidget(add_btn)
        buttons_layout.addWidget(delete_btn)
        buttons_layout.addWidget(refresh_btn)

        right_layout.addLayout(buttons_layout)

        return right_widget

    def createBottomPanel(self):
        """创建底部按钮面板"""
        bottom_widget = QWidget()
        bottom_layout = QHBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(10, 5, 10, 5)

        # 左侧状态信息
        self.status_label = QLabel("就绪")
        bottom_layout.addWidget(self.status_label)

        bottom_layout.addStretch()

        # 右侧按钮
        save_btn = QPushButton("保存题目")
        save_btn.clicked.connect(self.saveProblem)
        preview_btn = QPushButton("预览")
        preview_btn.clicked.connect(self.previewProblem)

        bottom_layout.addWidget(save_btn)
        bottom_layout.addWidget(preview_btn)

        return bottom_widget

    def setProblemsPath(self):
        """设置题目路径"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "选择题目根目录", self.problems_base_path,
            QFileDialog.ShowDirsOnly
        )

        if dir_path:
            self.problems_base_path = dir_path
            self.path_label.setText(f"题目路径: {self.problems_base_path}")
            self.loadAllProblems()

    def selectGeneratorFile(self):
        """选择生成器文件"""
        if not self.current_problem:
            QMessageBox.warning(self, "警告", "请先选择一个题目")
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择数据生成器文件",
            self.current_problem.problem_path,
            "Python文件 (*.py);;所有文件 (*.*)"
        )

        if file_path:
            self.generator_path_edit.setText(file_path)
            self.current_problem.generator_path = file_path

    def compileSolution(self):
        """编译正解代码"""
        if not self.current_problem:
            QMessageBox.warning(self, "警告", "请先选择一个题目")
            return

        if not self.current_problem.solution_code:
            QMessageBox.warning(self, "警告", "没有正解代码")
            return

        if self.current_problem.language != 'cpp':
            QMessageBox.warning(self, "警告", "只有C++代码可以编译成exe文件")
            return

        self.output_text.append("=" * 50)
        self.output_text.append("开始编译C++代码...")

        # 创建临时cpp文件
        cpp_file = os.path.join(self.current_problem.problem_path, "solution.cpp")
        exe_file = os.path.join(self.current_problem.problem_path, "solution.exe")

        try:
            # 保存代码到文件
            with open(cpp_file, 'w', encoding='utf-8') as f:
                f.write(self.current_problem.solution_code)

            # 编译
            compile_process = subprocess.run(
                ['g++', cpp_file, '-o', exe_file],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )

            if compile_process.returncode != 0:
                self.output_text.append(f"编译错误:\n{compile_process.stderr}")
                QMessageBox.warning(self, "编译失败", f"编译错误:\n{compile_process.stderr}")
                return

            self.current_problem.compiled_exe_path = exe_file
            self.output_text.append(f"编译成功！生成文件: solution.exe")
            self.status_label.setText("编译成功")

        except Exception as e:
            self.output_text.append(f"编译过程出错: {str(e)}")
            QMessageBox.critical(self, "编译错误", f"编译过程出错:\n{str(e)}")

    def loadAllProblems(self):
        """从固定路径加载所有题目"""
        self.problems.clear()
        self.problem_list.clear()

        if not os.path.exists(self.problems_base_path):
            os.makedirs(self.problems_base_path, exist_ok=True)
            self.status_label.setText(f"创建题目目录: {self.problems_base_path}")

        # 遍历目录，查找符合格式的题目目录
        pattern = re.compile(r'^(\d+)_(.+)$')

        for item in os.listdir(self.problems_base_path):
            item_path = os.path.join(self.problems_base_path, item)
            if os.path.isdir(item_path):
                # 检查目录名是否符合格式
                match = pattern.match(item)
                if match:
                    problem_id = match.group(1)
                    problem_title = match.group(2)

                    # 创建题目对象
                    problem = Problem(problem_title, problem_id)
                    problem.problem_path = item_path

                    # 检查是否有编译好的exe文件
                    exe_path = os.path.join(item_path, "solution.exe")
                    if os.path.exists(exe_path):
                        problem.compiled_exe_path = exe_path

                    # 加载题目内容
                    self.loadProblemContent(problem)

                    self.problems.append(problem)

        # 按编号排序
        self.problems.sort(key=lambda x: int(x.id))

        # 添加到列表
        for problem in self.problems:
            display_text = f"{problem.id}. {problem.title}"
            item_widget = QListWidgetItem(display_text)
            self.problem_list.addItem(item_widget)

        if self.problems:
            # 加载第一个题目
            self.loadProblem(0)
            self.problem_list.setCurrentRow(0)
            self.status_label.setText(f"已加载 {len(self.problems)} 个题目")
        else:
            self.status_label.setText("没有找到题目，请新建题目")

    def loadProblemContent(self, problem):
        """加载题目的具体内容"""
        json_path = os.path.join(problem.problem_path, "problem.json")

        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    problem_data = json.load(f)

                problem.description = problem_data.get("description", "")
                problem.input_description = problem_data.get("input_description", "")
                problem.output_description = problem_data.get("output_description", "")
                problem.sample_input = problem_data.get("sample_input", "")
                problem.sample_output = problem_data.get("sample_output", "")
                problem.solution_code = problem_data.get("solution_code", "")
                problem.language = problem_data.get("language", "cpp")

                # 加载生成器路径
                generator_rel_path = problem_data.get("generator_path", "")
                if generator_rel_path:
                    generator_full_path = os.path.join(problem.problem_path, generator_rel_path)
                    if os.path.exists(generator_full_path):
                        problem.generator_path = generator_full_path
                    else:
                        problem.generator_path = ""

                # 加载数据文件
                data_files = problem_data.get("data_files", [])
                for file_name in data_files:
                    file_path = os.path.join(problem.problem_path, file_name)
                    if os.path.exists(file_path):
                        problem.data_files.append(file_path)

            except Exception as e:
                print(f"加载题目 {problem.full_title} 失败: {e}")

    def loadProblem(self, index):
        """加载指定索引的题目"""
        if 0 <= index < len(self.problems):
            self.current_problem_index = index
            self.current_problem = self.problems[index]

            # 更新UI
            self.id_edit.setText(self.current_problem.id)
            self.title_edit.setText(self.current_problem.title)
            self.description_edit.setText(self.current_problem.description)
            self.input_edit.setText(self.current_problem.input_description)
            self.output_edit.setText(self.current_problem.output_description)
            self.sample_input_edit.setText(self.current_problem.sample_input)
            self.sample_output_edit.setText(self.current_problem.sample_output)
            if self.current_problem.solution_code=="":
                self.current_problem.solution_code="""#include<bits/stdc++.h>
using namespace std;
int main()
{
	return 0;
}"""
            self.solution_edit.setText(self.current_problem.solution_code)


            # 设置生成器路径
            if self.current_problem.generator_path:
                self.generator_path_edit.setText(self.current_problem.generator_path)
            else:
                self.generator_path_edit.clear()

            # 设置语言
            lang_map = {"python": "Python", "cpp": "C++", "java": "Java"}
            self.lang_combo.setCurrentText(lang_map.get(self.current_problem.language, "C++"))

            # 更新数据文件列表
            self.updateDataFileList()

            self.status_label.setText(f"已加载题目: {self.current_problem.full_title}")

    def updateDataFileList(self):
        """更新数据文件列表"""
        self.data_list_widget.clear()

        if not self.current_problem:
            return

        # 获取所有 .in 文件
        in_files = []
        for file_name in os.listdir(self.current_problem.problem_path):
            if file_name.endswith('.in'):
                file_path = os.path.join(self.current_problem.problem_path, file_name)
                in_files.append(file_path)

        # 按数字排序
        def extract_number(filename):
            match = re.search(r'(\d+)', os.path.basename(filename))
            return int(match.group(1)) if match else 0

        in_files.sort(key=extract_number)

        for file_path in in_files:
            file_name = os.path.basename(file_path)

            # 检查是否有对应的 .out 文件
            out_file = file_path.replace('.in', '.out')
            has_out = os.path.exists(out_file)

            # 显示状态图标
            display_text = file_name
            if has_out:
                display_text += " ✓"

            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, file_path)

            # 设置颜色
            if has_out:
                item.setForeground(Qt.darkGreen)

            self.data_list_widget.addItem(item)

    def onProblemSelected(self, item):
        """题目选择事件"""
        index = self.problem_list.row(item)
        self.loadProblem(index)
        self.title_edit.setText(self.problems[index].title)

    def onTitleChanged(self, text=None):
        """标题变更事件"""
        if self.current_problem:
            new_id = self.id_edit.text().strip()
            new_title = self.title_edit.text().strip()

            if new_id:
                self.current_problem.id = new_id
            if new_title:
                self.current_problem.title = new_title

            self.current_problem.full_title = f"{self.current_problem.id}_{self.current_problem.title}"

            # 更新列表项
            if self.current_problem_index >= 0:
                item = self.problem_list.item(self.current_problem_index)
                if item:
                    display_text = f"{self.current_problem.id}. {self.current_problem.title}"
                    item.setText(display_text)

    def onLanguageChanged(self, text):
        """语言变更事件"""
        if self.current_problem:
            lang_map = {"Python": "python", "C++": "cpp", "Java": "java"}
            self.current_problem.language = lang_map.get(text, "cpp")

    def onDescriptionChanged(self):
        """题面变更事件"""
        if self.current_problem:
            self.current_problem.description = self.description_edit.toPlainText()

    def onInputChanged(self):
        """输入说明变更事件"""
        if self.current_problem:
            self.current_problem.input_description = self.input_edit.toPlainText()

    def onOutputChanged(self):
        """输出说明变更事件"""
        if self.current_problem:
            self.current_problem.output_description = self.output_edit.toPlainText()

    def onSampleInputChanged(self):
        """样例输入变更事件"""
        if self.current_problem:
            self.current_problem.sample_input = self.sample_input_edit.toPlainText()

    def onSampleOutputChanged(self):
        """样例输出变更事件"""
        if self.current_problem:
            self.current_problem.sample_output = self.sample_output_edit.toPlainText()

    def onSolutionChanged(self):
        """正解代码变更事件"""
        if self.current_problem:
            self.current_problem.solution_code = self.solution_edit.toPlainText()

    def newProblem(self):
        """新建题目"""
        # 弹出对话框让用户输入题目名称
        from PyQt5.QtWidgets import QInputDialog

        # 生成新的编号
        max_id = 0
        for problem in self.problems:
            try:
                pid = int(problem.id)
                max_id = max(max_id, pid)
            except:
                pass

        new_id = str(max_id + 1)

        # 弹出输入对话框让用户输入题目名称
        new_title, ok = QInputDialog.getText(
            self, "新建题目",
            "请输入题目名称（创建后将不可修改）:",
            QLineEdit.Normal,
            "新题目"
        )

        if not ok or not new_title.strip():
            # 用户取消或输入为空，不创建题目
            return

        new_title = new_title.strip()

        # 创建题目目录
        dir_name = f"{new_id}_{new_title}"
        problem_path = os.path.join(self.problems_base_path, dir_name)

        # 如果目录已存在，添加后缀
        counter = 1
        while os.path.exists(problem_path):
            dir_name = f"{new_id}_{new_title}_{counter}"
            problem_path = os.path.join(self.problems_base_path, dir_name)
            counter += 1

        os.makedirs(problem_path, exist_ok=True)

        # 创建题目对象
        problem = Problem(new_title, new_id)
        problem.problem_path = problem_path

        self.problems.append(problem)

        # 添加到列表
        display_text = f"{problem.id}. {problem.title}"
        item = QListWidgetItem(display_text)
        self.problem_list.addItem(item)

        # 选中新题目
        self.problem_list.setCurrentItem(item)
        self.loadProblem(len(self.problems) - 1)

        self.status_label.setText(f"已创建新题目: {problem.full_title}")
    def deleteProblem(self):
        """删除当前题目"""
        if self.current_problem_index >= 0:
            reply = QMessageBox.question(
                self, "确认删除",
                f"确定要删除题目 '{self.current_problem.full_title}' 吗？\n"
                f"这将永久删除目录:\n{self.current_problem.problem_path}",
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                try:
                    # 删除目录
                    shutil.rmtree(self.current_problem.problem_path)

                    # 从列表中移除
                    self.problem_list.takeItem(self.current_problem_index)
                    # 从数据中移除
                    self.problems.pop(self.current_problem_index)

                    if len(self.problems) > 0:
                        # 如果有其他题目，加载第一个
                        self.loadProblem(0)
                        self.problem_list.setCurrentRow(0)
                    else:
                        # 没有题目了，清空UI
                        self.current_problem = None
                        self.current_problem_index = -1
                        self.id_edit.clear()
                        self.title_edit.clear()
                        self.description_edit.clear()
                        self.input_edit.clear()
                        self.output_edit.clear()
                        self.sample_input_edit.clear()
                        self.sample_output_edit.clear()
                        self.solution_edit.clear()
                        self.generator_path_edit.clear()
                        self.data_list_widget.clear()
                        self.output_text.clear()
                        self.status_label.setText("没有题目")

                    self.status_label.setText("题目已删除")

                except Exception as e:
                    QMessageBox.critical(self, "删除失败", f"删除题目时发生错误:\n{str(e)}")

    def saveProblem(self):
        """保存当前题目"""
        if not self.current_problem:
            QMessageBox.warning(self, "警告", "没有要保存的题目")
            return

        # 确保目录名与编号和标题一致
        expected_dir_name = f"{self.current_problem.id}_{self.current_problem.title}"
        current_dir_name = os.path.basename(self.current_problem.problem_path)

        if expected_dir_name != current_dir_name:
            # 重命名目录
            new_path = os.path.join(self.problems_base_path, expected_dir_name)

            # 如果新路径已存在，添加后缀
            if os.path.exists(new_path):
                counter = 1
                while os.path.exists(f"{new_path}_{counter}"):
                    counter += 1
                new_path = f"{new_path}_{counter}"

            try:
                os.rename(self.current_problem.problem_path, new_path)
                self.current_problem.problem_path = new_path
            except Exception as e:
                QMessageBox.warning(self, "重命名失败", f"无法重命名目录:\n{str(e)}")

        self._saveProblemToPath(self.current_problem.problem_path)

    def _saveProblemToPath(self, path):
        """保存题目到指定路径"""
        try:
            # 收集数据文件列表
            data_files = []
            for file_name in os.listdir(path):
                if file_name.endswith('.in') or file_name.endswith('.out'):
                    data_files.append(file_name)

            # 保存生成器文件路径（相对路径）
            generator_relative_path = "datamaker.py"
            if self.current_problem.generator_path and os.path.exists(self.current_problem.generator_path):
                try:
                    # 确保两个路径都是绝对路径
                    abs_problem_path = os.path.abspath(path)
                    abs_generator_path = os.path.abspath(self.current_problem.generator_path)

                    # 判断生成器文件是否在当前题目目录内
                    if os.path.commonpath([abs_problem_path]) == os.path.commonpath(
                            [abs_generator_path, abs_problem_path]):
                        # 生成器文件在目录内，保存相对路径
                        generator_relative_path = os.path.relpath(abs_generator_path, abs_problem_path)
                    else:
                        # 如果不在目录内，复制一份到题目目录
                        new_path = os.path.join(path, os.path.basename(self.current_problem.generator_path))
                        # 如果目标文件已存在，先询问是否覆盖
                        if os.path.exists(new_path):
                            # 可以选择添加时间戳或数字后缀
                            base, ext = os.path.splitext(os.path.basename(self.current_problem.generator_path))
                            counter = 1
                            while os.path.exists(new_path):
                                new_filename = f"{base}_{counter}{ext}"
                                new_path = os.path.join(path, new_filename)
                                counter += 1

                        shutil.copy2(self.current_problem.generator_path, new_path)
                        generator_relative_path = os.path.basename(new_path)
                        self.current_problem.generator_path = new_path  # 更新路径

                except ValueError as e:
                    # 处理路径比较错误
                    print(f"路径比较错误: {e}")
                    # 如果路径比较失败，直接复制文件
                    new_path = os.path.join(path, os.path.basename(self.current_problem.generator_path))
                    shutil.copy2(self.current_problem.generator_path, new_path)
                    generator_relative_path = os.path.basename(new_path)
                    self.current_problem.generator_path = new_path

            # 保存题面文件
            problem_data = {
                "id": self.current_problem.id,
                "title": self.current_problem.title,
                "description": self.current_problem.description,
                "input_description": self.current_problem.input_description,
                "output_description": self.current_problem.output_description,
                "sample_input": self.current_problem.sample_input,
                "sample_output": self.current_problem.sample_output,
                "solution_code": self.current_problem.solution_code,
                "generator_path": generator_relative_path,
                "language": self.current_problem.language,
                "data_files": data_files
            }

            # 保存为JSON文件
            json_path = os.path.join(path, "problem.json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(problem_data, f, ensure_ascii=False, indent=2)

            # 保存正解代码到单独文件
            if self.current_problem.solution_code:
                ext_map = {"python": ".py", "cpp": ".cpp", "java": ".java"}
                ext = ext_map.get(self.current_problem.language, ".txt")
                solution_path = os.path.join(path, f"solution{ext}")
                with open(solution_path, "w", encoding="utf-8") as f:
                    f.write(self.current_problem.solution_code)

            self.status_label.setText(f"题目已保存到: {path}")
            QMessageBox.information(self, "保存成功", f"题目已成功保存到:\n{path}")

        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"保存题目时发生错误:\n{str(e)}")

    def runSolution(self):
        """运行正解代码"""
        if not self.current_problem:
            QMessageBox.warning(self, "警告", "请先选择一个题目")
            return

        if not self.current_problem.solution_code:
            QMessageBox.warning(self, "警告", "没有正解代码")
            return

        # 获取样例输入
        sample_input = self.sample_input_edit.toPlainText()
        if not sample_input:
            QMessageBox.warning(self, "警告", "没有样例输入")
            return

        self.output_text.append("=" * 50)
        self.output_text.append("开始运行正解代码...")

        # 创建运行线程
        self.runner = CodeRunner(
            self.current_problem.solution_code,
            sample_input,
            self.current_problem.language
        )
        self.runner.output_signal.connect(self.onSolutionOutput)
        self.runner.error_signal.connect(self.onSolutionError)
        self.runner.finished_signal.connect(lambda: self.output_text.append("运行完成\n"))
        self.runner.start()

    def onSolutionOutput(self, text):
        """处理正解输出"""
        self.output_text.append("【输出】")
        self.output_text.append(text)

    def onSolutionError(self, text):
        """处理正解错误"""
        self.output_text.append("【错误】")
        self.output_text.append(text)

    def generateData(self):
        """生成数据文件"""
        if not self.current_problem:
            QMessageBox.warning(self, "警告", "请先选择一个题目")
            return

        if not self.current_problem.generator_path or not os.path.exists(self.current_problem.generator_path):
            QMessageBox.warning(self, "警告", "请先选择数据生成器文件")
            return

        # 获取生成数量
        count_text = self.generator_count.text().strip()
        try:
            count = int(count_text) if count_text else 10
            if count <= 0 or count > 100:
                QMessageBox.warning(self, "警告", "生成数量应为1-100之间的整数")
                return
        except ValueError:
            QMessageBox.warning(self, "警告", "请输入有效的整数")
            return

        # 获取数据规模
        data_scale = self.data_scale_spin.value()

        # 确认是否覆盖
        existing_files = []
        for i in range(1, count + 1):
            in_file = os.path.join(self.current_problem.problem_path, f"{i}.in")
            if os.path.exists(in_file):
                existing_files.append(f"{i}.in")

        if existing_files:
            reply = QMessageBox.question(
                self, "文件已存在",
                f"以下文件已存在:\n{', '.join(existing_files[:5])}\n"
                f"是否覆盖？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        self.output_text.append("=" * 50)
        self.output_text.append(f"开始使用外部生成器生成 {count} 个输入文件...")
        self.output_text.append(f"生成器文件: {self.current_problem.generator_path}")
        self.output_text.append(f"数据规模: {data_scale}")

        # 创建进度对话框
        self.progress = QProgressDialog("正在生成数据...", "取消", 0, 100, self)
        self.progress.setWindowModality(Qt.WindowModal)

        # 创建生成器线程
        self.generator = DataGenerator(
            self.current_problem.generator_path,
            count,
            data_scale
        )
        self.generator.output_dir = self.current_problem.problem_path
        self.generator.progress_signal.connect(self.progress.setValue)
        self.generator.message_signal.connect(self.onGeneratorMessage)
        self.generator.error_signal.connect(self.onGeneratorError)
        self.generator.finished_signal.connect(self.onGeneratorFinished)
        self.generator.start()

    def onGeneratorMessage(self, message):
        """处理生成器消息"""
        self.output_text.append(message)

    def onGeneratorError(self, message):
        """处理生成器错误"""
        self.output_text.append(f"【错误】{message}")
        QMessageBox.warning(self, "生成错误", message)

    def onGeneratorFinished(self):
        """生成器完成"""
        self.progress.close()
        self.output_text.append("数据生成完成")
        self.updateDataFileList()
        self.status_label.setText("数据生成完成")

    def testSelectedWithExe(self):
        """使用编译好的exe测试选中的数据文件"""
        if not self.current_problem:
            QMessageBox.warning(self, "警告", "请先选择一个题目")
            return

        if not self.current_problem.compiled_exe_path or not os.path.exists(self.current_problem.compiled_exe_path):
            QMessageBox.warning(self, "警告", "请先编译正解代码")
            return

        selected_items = self.data_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请先选择要测试的数据文件")
            return

        # 收集选中的输入文件
        input_files = []
        for item in selected_items:
            in_file_path = item.data(Qt.UserRole)
            input_files.append(in_file_path)

        self.output_text.append("=" * 50)
        self.output_text.append(f"开始使用exe测试 {len(input_files)} 个文件...")

        # 创建进度对话框
        self.progress = QProgressDialog("正在测试...", "取消", 0, 100, self)
        self.progress.setWindowModality(Qt.WindowModal)

        # 创建测试线程
        self.tester = DataTester(
            self.current_problem.compiled_exe_path,
            input_files,
            self.current_problem.problem_path
        )
        self.tester.progress_signal.connect(self.progress.setValue)
        self.tester.message_signal.connect(self.onTesterMessage)
        self.tester.error_signal.connect(self.onTesterError)
        self.tester.finished_signal.connect(self.onTesterFinished)
        self.tester.start()

    def batchTestWithExe(self):
        """使用编译好的exe批量测试所有数据文件"""
        if not self.current_problem:
            QMessageBox.warning(self, "警告", "请先选择一个题目")
            return

        if not self.current_problem.compiled_exe_path or not os.path.exists(self.current_problem.compiled_exe_path):
            QMessageBox.warning(self, "警告", "请先编译正解代码")
            return

        # 获取所有 .in 文件
        in_files = []
        for file_name in os.listdir(self.current_problem.problem_path):
            if file_name.endswith('.in'):
                in_files.append(os.path.join(self.current_problem.problem_path, file_name))

        if not in_files:
            QMessageBox.warning(self, "警告", "没有找到输入文件")
            return

        # 按数字排序
        def extract_number(filename):
            match = re.search(r'(\d+)', os.path.basename(filename))
            return int(match.group(1)) if match else 0

        in_files.sort(key=extract_number)

        self.output_text.append("=" * 50)
        self.output_text.append(f"开始使用exe批量测试 {len(in_files)} 个文件...")

        # 创建进度对话框
        self.progress = QProgressDialog("正在批量测试...", "取消", 0, 100, self)
        self.progress.setWindowModality(Qt.WindowModal)

        # 创建测试线程
        self.tester = DataTester(
            self.current_problem.compiled_exe_path,
            in_files,
            self.current_problem.problem_path
        )
        self.tester.progress_signal.connect(self.progress.setValue)
        self.tester.message_signal.connect(self.onTesterMessage)
        self.tester.error_signal.connect(self.onTesterError)
        self.tester.finished_signal.connect(self.onTesterFinished)
        self.tester.start()

    def onTesterMessage(self, message):
        """处理测试器消息"""
        self.output_text.append(message)

    def onTesterError(self, message):
        """处理测试器错误"""
        self.output_text.append(f"【错误】{message}")
        QMessageBox.warning(self, "测试错误", message)

    def onTesterFinished(self):
        """测试器完成"""
        self.progress.close()
        self.output_text.append("测试完成")
        self.updateDataFileList()
        self.status_label.setText("测试完成")

    def clearOutputFiles(self):
        """清除所有输出文件"""
        if not self.current_problem:
            return

        reply = QMessageBox.question(
            self, "确认清除",
            "确定要删除所有 .out 文件吗？",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            count = 0
            for file_name in os.listdir(self.current_problem.problem_path):
                if file_name.endswith('.out'):
                    file_path = os.path.join(self.current_problem.problem_path, file_name)
                    os.remove(file_path)
                    count += 1

            self.updateDataFileList()
            self.status_label.setText(f"已清除 {count} 个输出文件")

    def openDataFile(self, item):
        """打开数据文件"""
        file_path = item.data(Qt.UserRole)
        if file_path and os.path.exists(file_path):
            os.startfile(file_path)

    def previewProblem(self):
        """预览题目"""
        if not self.current_problem:
            QMessageBox.warning(self, "警告", "没有要预览的题目")
            return

        # 创建预览对话框
        preview_dialog = QWidget(self, Qt.Window)
        preview_dialog.setWindowTitle(f"预览 - {self.current_problem.full_title}")
        preview_dialog.setGeometry(150, 150, 800, 600)

        layout = QVBoxLayout(preview_dialog)

        # 标题
        title_label = QLabel(f"{self.current_problem.id}. {self.current_problem.title}")
        title_font = QFont("微软雅黑", 16, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # 使用TabWidget显示预览内容
        preview_tabs = QTabWidget()

        # 题面预览
        desc_widget = QWidget()
        desc_layout = QVBoxLayout(desc_widget)
        desc_text = QTextEdit()
        desc_text.setReadOnly(True)
        desc_text.setText(self.current_problem.description)
        desc_layout.addWidget(desc_text)
        preview_tabs.addTab(desc_widget, "题面")

        # 输入预览
        input_widget = QWidget()
        input_layout = QVBoxLayout(input_widget)
        input_text = QTextEdit()
        input_text.setReadOnly(True)
        input_text.setText(self.current_problem.input_description)
        input_layout.addWidget(input_text)
        preview_tabs.addTab(input_widget, "输入")

        # 输出预览
        output_widget = QWidget()
        output_layout = QVBoxLayout(output_widget)
        output_text = QTextEdit()
        output_text.setReadOnly(True)
        output_text.setText(self.current_problem.output_description)
        output_layout.addWidget(output_text)
        preview_tabs.addTab(output_widget, "输出")

        # 样例预览
        sample_widget = QWidget()
        sample_layout = QVBoxLayout(sample_widget)

        sample_input_label = QLabel("样例输入:")
        sample_input_text = QTextEdit()
        sample_input_text.setReadOnly(True)
        sample_input_text.setText(self.current_problem.sample_input)

        sample_output_label = QLabel("样例输出:")
        sample_output_text = QTextEdit()
        sample_output_text.setReadOnly(True)
        sample_output_text.setText(self.current_problem.sample_output)

        sample_layout.addWidget(sample_input_label)
        sample_layout.addWidget(sample_input_text)
        sample_layout.addWidget(sample_output_label)
        sample_layout.addWidget(sample_output_text)

        preview_tabs.addTab(sample_widget, "样例")

        # 代码预览
        code_widget = QWidget()
        code_layout = QVBoxLayout(code_widget)

        solution_label = QLabel(f"正解代码 ({self.lang_combo.currentText()}):")
        solution_text = QTextEdit()
        solution_text.setReadOnly(True)
        solution_text.setFont(QFont("Consolas", 10))
        solution_text.setText(self.current_problem.solution_code)

        generator_info = QLabel(
            f"生成器文件: {os.path.basename(self.current_problem.generator_path) if self.current_problem.generator_path else '未选择'}")

        exe_info = QLabel(
            f"编译状态: {'已编译' if self.current_problem.compiled_exe_path and os.path.exists(self.current_problem.compiled_exe_path) else '未编译'}")

        code_layout.addWidget(solution_label)
        code_layout.addWidget(solution_text)
        code_layout.addWidget(generator_info)
        code_layout.addWidget(exe_info)

        preview_tabs.addTab(code_widget, "代码")

        layout.addWidget(preview_tabs)

        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(preview_dialog.close)
        layout.addWidget(close_btn)

        preview_dialog.show()

    def about(self):
        """关于对话框"""
        QMessageBox.about(
            self, "关于",
            "算法题目制作软件\n\n"
            "版本：4.0\n\n"
            "功能：\n"
            "- 从固定路径加载题目（格式：数字_题目名）\n"
            "- 创建和管理算法题目\n"
            "- 编辑题面、输入、输出和样例信息\n"
            "- 支持正解代码（Python/C++/Java）\n"
            "- 支持外部数据生成器文件\n"
            "- 创建输入文件（通过生成器，可设置数据规模）\n"
            "- 编译C++代码为exe文件\n"
            "- 通过exe文件批量生成输出文件\n"
            "- 批量测试功能\n\n"
            f"当前题目路径：{self.problems_base_path}\n\n"
            "使用PyQt5开发"
        )


def main():
    app = QApplication(sys.argv)

    window = ProblemMaker()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()