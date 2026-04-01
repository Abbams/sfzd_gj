import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTextEdit,
    QTabWidget, QPushButton
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class PreviewDialog(QWidget):
    """题目预览对话框"""

    def __init__(self, problem, parent=None):
        super().__init__(parent, Qt.Window)
        self.problem = problem
        self.setWindowTitle(f"预览 - {problem.full_title}")
        self.setGeometry(150, 150, 800, 600)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        # 标题
        title_label = QLabel(f"{self.problem.id}. {self.problem.title}")
        title_font = QFont("微软雅黑", 16, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        preview_tabs = QTabWidget()
        preview_tabs.addTab(self.createDescriptionTab(), "题面")
        preview_tabs.addTab(self.createInputTab(), "输入")
        preview_tabs.addTab(self.createOutputTab(), "输出")
        preview_tabs.addTab(self.createSampleTab(), "样例")
        preview_tabs.addTab(self.createCodeTab(), "代码")

        layout.addWidget(preview_tabs)

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

    def createDescriptionTab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        text = QTextEdit()
        text.setReadOnly(True)
        text.setText(self.problem.description)
        layout.addWidget(text)
        return widget

    def createInputTab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        text = QTextEdit()
        text.setReadOnly(True)
        text.setText(self.problem.input_description)
        layout.addWidget(text)
        return widget

    def createOutputTab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        text = QTextEdit()
        text.setReadOnly(True)
        text.setText(self.problem.output_description)
        layout.addWidget(text)
        return widget

    def createSampleTab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        sample_input_label = QLabel("样例输入:")
        sample_input_text = QTextEdit()
        sample_input_text.setReadOnly(True)
        sample_input_text.setText(self.problem.sample_input)

        sample_output_label = QLabel("样例输出:")
        sample_output_text = QTextEdit()
        sample_output_text.setReadOnly(True)
        sample_output_text.setText(self.problem.sample_output)

        layout.addWidget(sample_input_label)
        layout.addWidget(sample_input_text)
        layout.addWidget(sample_output_label)
        layout.addWidget(sample_output_text)
        return widget

    def createCodeTab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        lang_map = {"python": "Python", "cpp": "C++", "java": "Java"}
        lang_display = lang_map.get(self.problem.language, "C++")

        solution_label = QLabel(f"正解代码 ({lang_display}):")
        solution_text = QTextEdit()
        solution_text.setReadOnly(True)
        solution_text.setFont(QFont("Consolas", 10))
        solution_text.setText(self.problem.solution_code)

        generator_info = QLabel(
            f"生成器文件: {os.path.basename(self.problem.generator_path) if self.problem.generator_path else '未选择'}"
        )

        exe_info = QLabel(
            f"编译状态: {'已编译' if self.problem.compiled_exe_path and os.path.exists(self.problem.compiled_exe_path) else '未编译'}"
        )

        layout.addWidget(solution_label)
        layout.addWidget(solution_text)
        layout.addWidget(generator_info)
        layout.addWidget(exe_info)
        return widget