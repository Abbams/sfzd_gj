import os
import sys
import shutil
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QMenuBar, QMenu, QAction, QSplitter, QMessageBox,
    QFileDialog, QInputDialog, QProgressDialog, QLabel,
    QPushButton, QLineEdit
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from ai.quest import ai_rewrite
from models.problem import Problem
from threads.code_runner import CodeRunner
from threads.data_generator import DataGenerator
from threads.data_tester import DataTester
from utils import problem_utils
from ui.panels.left_panel import LeftPanel
from ui.panels.right_panel import RightPanel


class ProblemMaker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.problems = []
        self.current_problem = None
        self.current_problem_index = -1
        self.problems_base_path = r".\AlgorithmProblems"
        self.initUI()
        self.loadAllProblems()

    def initUI(self):
        """初始化用户界面"""
        self.setWindowTitle("算法题目制作软件")
        self.setGeometry(100, 100, 1300, 900)

        font = QFont("微软雅黑", 9)
        self.setFont(font)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.createMenuBar()

        content_splitter = QSplitter(Qt.Horizontal)

        self.left_panel = LeftPanel(self)
        content_splitter.addWidget(self.left_panel)

        self.right_panel = RightPanel(self)
        content_splitter.addWidget(self.right_panel)

        content_splitter.setSizes([1000, 500])
        main_layout.addWidget(content_splitter)

        bottom_widget = self.createBottomPanel()
        main_layout.addWidget(bottom_widget)

        self.right_panel.setPathText(f"题目路径: {self.problems_base_path}")

    def createMenuBar(self):
        """创建菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")

        refresh_action = QAction("刷新题目列表(&R)", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.loadAllProblems)
        file_menu.addAction(refresh_action)

        file_menu.addSeparator()

        set_path_action = QAction("设置题目路径(&P)", self)
        set_path_action.triggered.connect(self.setProblemsPath)
        file_menu.addAction(set_path_action)

        file_menu.addSeparator()

        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 运行菜单
        run_menu = menubar.addMenu("运行(&R)")

        compile_action = QAction("编译正解(&C)", self)
        compile_action.setShortcut("F8")
        compile_action.triggered.connect(self.compileSolution)
        run_menu.addAction(compile_action)

        run_menu.addSeparator()

        run_solution_action = QAction("运行正解(&S)", self)
        run_solution_action.setShortcut("F9")
        run_solution_action.triggered.connect(self.runSolution)
        run_menu.addAction(run_solution_action)

        batch_generate_action = QAction("批量生成数据(&G)", self)
        batch_generate_action.setShortcut("F10")
        batch_generate_action.triggered.connect(self.generateData)
        run_menu.addAction(batch_generate_action)

        batch_test_action = QAction("批量测试(&T)", self)
        batch_test_action.setShortcut("F11")
        batch_test_action.triggered.connect(self.batchTestWithExe)
        run_menu.addAction(batch_test_action)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")

        about_action = QAction("关于(&A)", self)
        about_action.triggered.connect(self.about)
        help_menu.addAction(about_action)

    def createBottomPanel(self):
        """创建底部按钮面板"""
        bottom_widget = QWidget()
        bottom_layout = QHBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(10, 5, 10, 5)

        self.status_label = QLabel("就绪")
        bottom_layout.addWidget(self.status_label)

        bottom_layout.addStretch()

        save_btn = QPushButton("保存题目")
        save_btn.clicked.connect(self.saveProblem)
        preview_btn = QPushButton("预览")
        preview_btn.clicked.connect(self.previewProblem)

        bottom_layout.addWidget(save_btn)
        bottom_layout.addWidget(preview_btn)

        return bottom_widget

    def loadAllProblems(self):
        """从固定路径加载所有题目"""
        self.problems = problem_utils.load_all_problems(self.problems_base_path)

        self.right_panel.clearProblemList()

        for problem in self.problems:
            display_text = f"{problem.id}. {problem.title}"
            self.right_panel.addProblemItem(display_text)

        if self.problems:
            self.loadProblem(0)
            self.right_panel.setCurrentRow(0)
            self.status_label.setText(f"已加载 {len(self.problems)} 个题目")
        else:
            self.status_label.setText("没有找到题目，请新建题目")

    def loadProblem(self, index):
        """加载指定索引的题目"""
        if 0 <= index < len(self.problems):
            self.current_problem_index = index
            self.current_problem = self.problems[index]

            self.left_panel.updateFromProblem(self.current_problem)
            self.updateDataFileList()
            self.status_label.setText(f"已加载题目: {self.current_problem.full_title}")

    def onProblemSelected(self, item):
        """题目选择事件"""
        index = self.right_panel.problem_list.row(item)
        self.loadProblem(index)

    def updateDataFileList(self):
        """更新数据文件列表"""
        self.left_panel.clearDataList()

        if not self.current_problem:
            return

        in_files = []
        for file_name in os.listdir(self.current_problem.problem_path):
            if file_name.endswith('.in'):
                file_path = os.path.join(self.current_problem.problem_path, file_name)
                in_files.append(file_path)

        in_files.sort(key=problem_utils.extract_number_from_filename)

        for file_path in in_files:
            file_name = os.path.basename(file_path)
            out_file = file_path.replace('.in', '.out')
            has_out = os.path.exists(out_file)

            self.left_panel.addDataFileItem(file_name, file_path, has_out)

    def newProblem(self):
        """新建题目"""
        from PyQt5.QtWidgets import QInputDialog

        max_id = 0
        for problem in self.problems:
            try:
                pid = int(problem.id)
                max_id = max(max_id, pid)
            except:
                pass

        new_id = str(max_id + 1)

        new_title, ok = QInputDialog.getText(
            self, "新建题目",
            "请输入题目名称（创建后将不可修改）:",
            QLineEdit.Normal,
            "新题目"
        )

        if not ok or not new_title.strip():
            return

        new_title = new_title.strip()

        dir_name = f"{new_id}_{new_title}"
        problem_path = os.path.join(self.problems_base_path, dir_name)

        counter = 1
        while os.path.exists(problem_path):
            dir_name = f"{new_id}_{new_title}_{counter}"
            problem_path = os.path.join(self.problems_base_path, dir_name)
            counter += 1

        os.makedirs(problem_path, exist_ok=True)

        problem = Problem(new_title, new_id)
        problem.problem_path = problem_path

        self.problems.append(problem)

        display_text = f"{problem.id}. {problem.title}"
        self.right_panel.addProblemItem(display_text)

        self.right_panel.setCurrentRow(len(self.problems) - 1)
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
                    shutil.rmtree(self.current_problem.problem_path)

                    self.right_panel.takeItem(self.current_problem_index)
                    self.problems.pop(self.current_problem_index)

                    if len(self.problems) > 0:
                        self.loadProblem(0)
                        self.right_panel.setCurrentRow(0)
                    else:
                        self.current_problem = None
                        self.current_problem_index = -1
                        self.left_panel.updateFromProblem(None)
                        self.left_panel.clearDataList()
                        self.left_panel.clearOutput()
                        self.status_label.setText("没有题目")

                    self.status_label.setText("题目已删除")

                except Exception as e:
                    QMessageBox.critical(self, "删除失败", f"删除题目时发生错误:\n{str(e)}")

    def saveProblem(self):
        """保存当前题目"""
        if not self.current_problem:
            QMessageBox.warning(self, "警告", "没有要保存的题目")
            return

        try:
            path = problem_utils.save_problem(self.current_problem, self.problems_base_path)
            self.status_label.setText(f"题目已保存到: {path}")
            QMessageBox.information(self, "保存成功", f"题目已成功保存到:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"保存题目时发生错误:\n{str(e)}")

    def compileSolution(self):
        """编译正解代码"""
        if not self.current_problem:
            QMessageBox.warning(self, "警告", "请先选择一个题目")
            return

        if not self.current_problem.solution_code:
            QMessageBox.warning(self, "警告", "没有正解代码")
            return

        self.left_panel.appendOutput("=" * 50)
        self.left_panel.appendOutput("开始编译C++代码...")

        cpp_file = os.path.join(self.current_problem.problem_path, "solution.cpp")
        exe_file = os.path.join(self.current_problem.problem_path, "solution.exe")

        try:
            with open(cpp_file, 'w', encoding='utf-8') as f:
                f.write(self.current_problem.solution_code)

            import subprocess
            compile_process = subprocess.run(
                ['g++', cpp_file, '-o', exe_file],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )

            if compile_process.returncode != 0:
                self.left_panel.appendOutput(f"编译错误:\n{compile_process.stderr}")
                QMessageBox.warning(self, "编译失败", f"编译错误:\n{compile_process.stderr}")
                return

            self.current_problem.compiled_exe_path = exe_file
            self.left_panel.appendOutput(f"编译成功！生成文件: solution.exe")
            self.status_label.setText("编译成功")

        except Exception as e:
            self.left_panel.appendOutput(f"编译过程出错: {str(e)}")
            QMessageBox.critical(self, "编译错误", f"编译过程出错:\n{str(e)}")

    def runSolution(self):
        """运行正解代码"""
        if not self.current_problem:
            QMessageBox.warning(self, "警告", "请先选择一个题目")
            return

        if not self.current_problem.solution_code:
            QMessageBox.warning(self, "警告", "没有正解代码")
            return

        sample_input = self.left_panel.sample_input_edit.toPlainText()
        if not sample_input:
            QMessageBox.warning(self, "警告", "没有样例输入")
            return

        self.left_panel.appendOutput("=" * 50)
        self.left_panel.appendOutput("开始运行正解代码...")

        self.runner = CodeRunner(
            self.current_problem.solution_code,
            sample_input,
            self.current_problem.language
        )
        self.runner.output_signal.connect(self.onSolutionOutput)
        self.runner.error_signal.connect(self.onSolutionError)
        self.runner.finished_signal.connect(lambda: self.left_panel.appendOutput("运行完成\n"))
        self.runner.start()

    def onSolutionOutput(self, text):
        self.left_panel.appendOutput("【输出】")
        self.left_panel.appendOutput(text)

    def onSolutionError(self, text):
        self.left_panel.appendOutput("【错误】")
        self.left_panel.appendOutput(text)

    def generateData(self):
        """生成数据文件"""
        if not self.current_problem:
            QMessageBox.warning(self, "警告", "请先选择一个题目")
            return

        if not self.current_problem.generator_path or not os.path.exists(self.current_problem.generator_path):
            QMessageBox.warning(self, "警告", "请先选择数据生成器文件")
            return

        count_text = self.left_panel.generator_count.text().strip()
        try:
            count = int(count_text) if count_text else 10
            if count <= 0 or count > 100:
                QMessageBox.warning(self, "警告", "生成数量应为1-100之间的整数")
                return
        except ValueError:
            QMessageBox.warning(self, "警告", "请输入有效的整数")
            return

        data_scale = self.left_panel.data_scale_spin.value()

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

        self.left_panel.appendOutput("=" * 50)
        self.left_panel.appendOutput(f"开始使用外部生成器生成 {count} 个输入文件...")
        self.left_panel.appendOutput(f"生成器文件: {self.current_problem.generator_path}")
        self.left_panel.appendOutput(f"数据规模: {data_scale}")

        self.progress = QProgressDialog("正在生成数据...", "取消", 0, 100, self)
        self.progress.setWindowModality(Qt.WindowModal)

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
        self.left_panel.appendOutput(message)

    def onGeneratorError(self, message):
        self.left_panel.appendOutput(f"【错误】{message}")
        QMessageBox.warning(self, "生成错误", message)

    def onGeneratorFinished(self):
        self.progress.close()
        self.left_panel.appendOutput("数据生成完成")
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

        selected_items = self.left_panel.data_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请先选择要测试的数据文件")
            return

        input_files = [item.data(Qt.UserRole) for item in selected_items]

        self.left_panel.appendOutput("=" * 50)
        self.left_panel.appendOutput(f"开始使用exe测试 {len(input_files)} 个文件...")

        self.progress = QProgressDialog("正在测试...", "取消", 0, 100, self)
        self.progress.setWindowModality(Qt.WindowModal)

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

        in_files = []
        for file_name in os.listdir(self.current_problem.problem_path):
            if file_name.endswith('.in'):
                in_files.append(os.path.join(self.current_problem.problem_path, file_name))

        if not in_files:
            QMessageBox.warning(self, "警告", "没有找到输入文件")
            return

        in_files.sort(key=problem_utils.extract_number_from_filename)

        self.left_panel.appendOutput("=" * 50)
        self.left_panel.appendOutput(f"开始使用exe批量测试 {len(in_files)} 个文件...")

        self.progress = QProgressDialog("正在批量测试...", "取消", 0, 100, self)
        self.progress.setWindowModality(Qt.WindowModal)

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
        self.left_panel.appendOutput(message)

    def onTesterError(self, message):
        self.left_panel.appendOutput(f"【错误】{message}")
        QMessageBox.warning(self, "测试错误", message)

    def onTesterFinished(self):
        self.progress.close()
        self.left_panel.appendOutput("测试完成")
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
            count = problem_utils.clear_output_files(self.current_problem.problem_path)
            self.updateDataFileList()
            self.status_label.setText(f"已清除 {count} 个输出文件")

    def openDataFile(self, item):
        """打开数据文件"""
        file_path = item.data(Qt.UserRole)
        if file_path and os.path.exists(file_path):
            os.startfile(file_path)

    def packDataFiles(self):
        """打包数据文件"""
        if not self.current_problem:
            QMessageBox.warning(self, "警告", "请先选择一个题目")
            return

        try:
            zip_path = problem_utils.pack_data_files(self.current_problem, self.current_problem.problem_path)

            self.left_panel.appendOutput("=" * 50)
            self.left_panel.appendOutput(f"打包成功！")
            self.left_panel.appendOutput(f"文件保存为: {zip_path}")
            self.left_panel.appendOutput(f"共打包 {len(self.current_problem.data_files)} 个文件")

            self.status_label.setText(f"打包成功: {os.path.basename(zip_path)}")

            reply = QMessageBox.question(
                self, "打包完成",
                f"文件已成功打包到:\n{zip_path}\n\n是否打开所在文件夹？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                if sys.platform == 'win32':
                    os.startfile(os.path.dirname(zip_path))
                else:
                    import subprocess
                    subprocess.Popen(['open' if sys.platform == 'darwin' else 'xdg-open',
                                      os.path.dirname(zip_path)])

        except Exception as e:
            QMessageBox.critical(self, "打包失败", f"打包过程中发生错误:\n{str(e)}")
            self.left_panel.appendOutput(f"【错误】打包失败: {str(e)}")

    def setProblemsPath(self):
        """设置题目路径"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "选择题目根目录", self.problems_base_path,
            QFileDialog.ShowDirsOnly
        )

        if dir_path:
            self.problems_base_path = dir_path
            self.right_panel.setPathText(f"题目路径: {self.problems_base_path}")
            self.loadAllProblems()

    def previewProblem(self):
        """预览题目"""
        if not self.current_problem:
            QMessageBox.warning(self, "警告", "没有要预览的题目")
            return

        from ui.preview_dialog import PreviewDialog
        dialog = PreviewDialog(self.current_problem, self)
        dialog.show()
    def airewrite(self):
        ai_rewrite(self.current_problem)
        self.saveProblem()
        self.loadAllProblems()

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