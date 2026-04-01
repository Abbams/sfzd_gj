import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QTabWidget, QComboBox, QPushButton, QGroupBox,
    QListWidget, QListWidgetItem, QFileDialog, QMessageBox, QSpinBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class LeftPanel(QWidget):
    """左侧题目信息面板"""

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # 题目标题和编号
        title_layout = QHBoxLayout()

        id_label = QLabel("题目编号:")
        self.id_edit = QLineEdit()
        self.id_edit.setPlaceholderText("输入题目编号")
        self.id_edit.setMaximumWidth(80)
        self.id_edit.setReadOnly(True)

        title_label = QLabel("题目标题:")
        self.title_edit = QLineEdit()
        self.title_edit.setReadOnly(True)

        title_layout.addWidget(id_label)
        title_layout.addWidget(self.id_edit)
        title_layout.addWidget(title_label)
        title_layout.addWidget(self.title_edit)
        layout.addLayout(title_layout)

        # 语言选择
        lang_layout = QHBoxLayout()
        lang_label = QLabel("编程语言:")
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["Python", "C++", "Java"])
        self.lang_combo.currentTextChanged.connect(self.onLanguageChanged)

        lang_layout.addWidget(lang_label)
        lang_layout.addWidget(self.lang_combo)
        lang_layout.addStretch()
        layout.addLayout(lang_layout)

        # 使用TabWidget组织题目信息
        tab_widget = QTabWidget()
        tab_widget.addTab(self.createDescriptionTab(), "题面")
        tab_widget.addTab(self.createInputTab(), "输入")
        tab_widget.addTab(self.createOutputTab(), "输出")
        tab_widget.addTab(self.createSampleTab(), "样例")
        tab_widget.addTab(self.createSolutionTab(), "正解代码")
        tab_widget.addTab(self.createGeneratorTab(), "数据生成器")
        tab_widget.addTab(self.createDataTab(), "测试数据")

        layout.addWidget(tab_widget)

        # 输出显示区域
        output_group = QGroupBox("运行输出")
        output_layout = QVBoxLayout(output_group)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Consolas", 9))
        self.output_text.setMaximumHeight(150)

        output_layout.addWidget(self.output_text)
        layout.addWidget(output_group)

    def createDescriptionTab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        desc_label = QLabel("题面描述:")
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("输入题面描述...")
        self.description_edit.textChanged.connect(self.onDescriptionChanged)

        layout.addWidget(desc_label)
        layout.addWidget(self.description_edit)
        return widget

    def createInputTab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        input_label = QLabel("输入说明:")
        self.input_edit = QTextEdit()
        self.input_edit.setPlaceholderText("输入说明...")
        self.input_edit.textChanged.connect(self.onInputChanged)

        layout.addWidget(input_label)
        layout.addWidget(self.input_edit)
        return widget

    def createOutputTab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        output_label = QLabel("输出说明:")
        self.output_edit = QTextEdit()
        self.output_edit.setPlaceholderText("输出说明...")
        self.output_edit.textChanged.connect(self.onOutputChanged)

        layout.addWidget(output_label)
        layout.addWidget(self.output_edit)
        return widget

    def createSampleTab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        sample_input_label = QLabel("样例输入:")
        self.sample_input_edit = QTextEdit()
        self.sample_input_edit.setPlaceholderText("样例输入...")
        self.sample_input_edit.textChanged.connect(self.onSampleInputChanged)

        sample_output_label = QLabel("样例输出:")
        self.sample_output_edit = QTextEdit()
        self.sample_output_edit.setPlaceholderText("样例输出...")
        self.sample_output_edit.textChanged.connect(self.onSampleOutputChanged)

        layout.addWidget(sample_input_label)
        layout.addWidget(self.sample_input_edit)
        layout.addWidget(sample_output_label)
        layout.addWidget(self.sample_output_edit)
        return widget

    def createSolutionTab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        solution_label = QLabel("正解代码:")
        self.solution_edit = QTextEdit()
        self.solution_edit.setPlaceholderText("输入题目的正解代码...")
        self.solution_edit.setFont(QFont("Consolas", 10))
        self.solution_edit.textChanged.connect(self.onSolutionChanged)

        solution_buttons = QHBoxLayout()
        compile_btn = QPushButton("编译正解")
        compile_btn.clicked.connect(self.parent.compileSolution)
        run_solution_btn = QPushButton("运行正解")
        run_solution_btn.clicked.connect(self.parent.runSolution)
        solution_buttons.addWidget(compile_btn)
        solution_buttons.addWidget(run_solution_btn)
        solution_buttons.addStretch()

        layout.addWidget(solution_label)
        layout.addWidget(self.solution_edit)
        layout.addLayout(solution_buttons)
        return widget

    def createGeneratorTab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        generator_label = QLabel("数据生成器文件:")

        generator_file_layout = QHBoxLayout()
        self.generator_path_edit = QLineEdit()
        self.generator_path_edit.setPlaceholderText("请选择数据生成器文件")
        self.generator_path_edit.setReadOnly(True)

        select_generator_btn = QPushButton("选择文件")
        select_generator_btn.clicked.connect(self.selectGeneratorFile)

        generator_file_layout.addWidget(self.generator_path_edit)
        generator_file_layout.addWidget(select_generator_btn)

        scale_layout = QHBoxLayout()
        scale_label = QLabel("数据规模(1-10):")
        self.data_scale_spin = QSpinBox()
        self.data_scale_spin.setMinimum(1)
        self.data_scale_spin.setMaximum(10)
        self.data_scale_spin.setValue(1)

        scale_layout.addWidget(scale_label)
        scale_layout.addWidget(self.data_scale_spin)
        scale_layout.addStretch()

        tip_label = QLabel("提示：生成器将从标准输入接收两个参数：数据编号(1,2,3...) 和 数据规模(1-10)")
        tip_label.setStyleSheet("color: gray; font-size: 8pt;")

        generator_control = QHBoxLayout()
        generator_count_label = QLabel("生成数量:")
        self.generator_count = QLineEdit()
        self.generator_count.setPlaceholderText("10")
        self.generator_count.setMaximumWidth(60)

        generate_btn = QPushButton("创建输入文件")
        generate_btn.clicked.connect(self.parent.generateData)

        generator_control.addWidget(generator_count_label)
        generator_control.addWidget(self.generator_count)
        generator_control.addWidget(generate_btn)
        generator_control.addStretch()

        layout.addWidget(generator_label)
        layout.addLayout(generator_file_layout)
        layout.addLayout(scale_layout)
        layout.addWidget(tip_label)
        layout.addLayout(generator_control)
        return widget

    def createDataTab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        data_list_label = QLabel("数据文件列表:")
        self.data_list_widget = QListWidget()
        self.data_list_widget.itemDoubleClicked.connect(self.parent.openDataFile)

        test_buttons = QHBoxLayout()

        test_selected_btn = QPushButton("测试选中(运行exe)")
        test_selected_btn.clicked.connect(self.parent.testSelectedWithExe)

        test_all_btn = QPushButton("测试所有(运行exe)")
        test_all_btn.clicked.connect(self.parent.batchTestWithExe)

        clear_output_btn = QPushButton("清除输出文件")
        clear_output_btn.clicked.connect(self.parent.clearOutputFiles)

        pack_btn = QPushButton("打包数据文件")
        pack_btn.clicked.connect(self.parent.packDataFiles)

        test_buttons.addWidget(test_selected_btn)
        test_buttons.addWidget(test_all_btn)
        test_buttons.addWidget(clear_output_btn)
        test_buttons.addWidget(pack_btn)
        test_buttons.addStretch()

        layout.addWidget(data_list_label)
        layout.addWidget(self.data_list_widget)
        layout.addLayout(test_buttons)
        return widget

    def selectGeneratorFile(self):
        if not self.parent.current_problem:
            QMessageBox.warning(self, "警告", "请先选择一个题目")
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择数据生成器文件",
            'datamaker.py',
            "Python文件 (*.py);;所有文件 (*.*)"
        )

        if file_path:
            self.generator_path_edit.setText(file_path)
            self.parent.current_problem.generator_path = file_path

    def onLanguageChanged(self, text):
        if self.parent.current_problem:
            lang_map = {"Python": "python", "C++": "cpp", "Java": "java"}
            self.parent.current_problem.language = lang_map.get(text, "cpp")

    def onDescriptionChanged(self):
        if self.parent.current_problem:
            self.parent.current_problem.description = self.description_edit.toPlainText()

    def onInputChanged(self):
        if self.parent.current_problem:
            self.parent.current_problem.input_description = self.input_edit.toPlainText()

    def onOutputChanged(self):
        if self.parent.current_problem:
            self.parent.current_problem.output_description = self.output_edit.toPlainText()

    def onSampleInputChanged(self):
        if self.parent.current_problem:
            self.parent.current_problem.sample_input = self.sample_input_edit.toPlainText()

    def onSampleOutputChanged(self):
        if self.parent.current_problem:
            self.parent.current_problem.sample_output = self.sample_output_edit.toPlainText()

    def onSolutionChanged(self):
        if self.parent.current_problem:
            self.parent.current_problem.solution_code = self.solution_edit.toPlainText()

    def updateFromProblem(self, problem):
        """从题目对象更新UI"""
        if not problem:
            return

        self.id_edit.setText(problem.id)
        self.title_edit.setText(problem.title)
        self.description_edit.setText(problem.description)
        self.input_edit.setText(problem.input_description)
        self.output_edit.setText(problem.output_description)
        self.sample_input_edit.setText(problem.sample_input)
        self.sample_output_edit.setText(problem.sample_output)

        if problem.solution_code == "":
            problem.solution_code = """#include<bits/stdc++.h>
using namespace std;
int main()
{
    return 0;
}"""
        self.solution_edit.setText(problem.solution_code)

        if problem.generator_path:
            self.generator_path_edit.setText(problem.generator_path)
        else:
            self.generator_path_edit.clear()

        lang_map = {"python": "Python", "cpp": "C++", "java": "Java"}
        self.lang_combo.setCurrentText(lang_map.get(problem.language, "C++"))

    def clearDataList(self):
        """清空数据文件列表"""
        self.data_list_widget.clear()

    def addDataFileItem(self, file_name, file_path, has_out):
        """添加数据文件项"""
        display_text = file_name
        if has_out:
            display_text += " ✓"

        item = QListWidgetItem(display_text)
        item.setData(Qt.UserRole, file_path)

        if has_out:
            item.setForeground(Qt.darkGreen)

        self.data_list_widget.addItem(item)

    def appendOutput(self, text):
        """添加输出文本"""
        self.output_text.append(text)

    def clearOutput(self):
        """清空输出"""
        self.output_text.clear()