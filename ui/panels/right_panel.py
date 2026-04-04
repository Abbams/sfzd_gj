from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QPushButton
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class RightPanel(QWidget):
    """右侧题目选择面板"""

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # 标题
        title_label = QLabel("题目列表")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont("微软雅黑", 12, QFont.Bold)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # 路径显示
        self.path_label = QLabel()
        self.path_label.setWordWrap(True)
        self.path_label.setStyleSheet("color: blue; font-size: 9pt;")
        layout.addWidget(self.path_label)

        # 题目列表
        self.problem_list = QListWidget()
        self.problem_list.itemClicked.connect(self.parent.onProblemSelected)
        layout.addWidget(self.problem_list)

        # 题目操作按钮
        buttons_layout = QHBoxLayout()

        add_btn = QPushButton("新建题目")
        add_btn.clicked.connect(self.parent.newProblem)
        delete_btn = QPushButton("删除题目")
        delete_btn.clicked.connect(self.parent.deleteProblem)
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.parent.loadAllProblems)
        airewrite_btn = QPushButton("ai重写")
        airewrite_btn.clicked.connect(self.parent.airewrite)

        buttons_layout.addWidget(add_btn)
        buttons_layout.addWidget(delete_btn)
        buttons_layout.addWidget(refresh_btn)
        buttons_layout.addWidget(airewrite_btn)

        layout.addLayout(buttons_layout)

    def setPathText(self, text):
        """设置路径文本"""
        self.path_label.setText(text)

    def clearProblemList(self):
        """清空题目列表"""
        self.problem_list.clear()

    def addProblemItem(self, display_text):
        """添加题目项"""
        item = QListWidgetItem(display_text)
        self.problem_list.addItem(item)

    def setCurrentRow(self, row):
        """设置当前选中行"""
        self.problem_list.setCurrentRow(row)

    def getCurrentRow(self):
        """获取当前选中行"""
        return self.problem_list.currentRow()

    def getItemAt(self, row):
        """获取指定行的项"""
        return self.problem_list.item(row)

    def takeItem(self, row):
        """移除指定行的项"""
        return self.problem_list.takeItem(row)

    def updateProblemItem(self, index, text):
        """更新指定索引的题目项"""
        item = self.problem_list.item(index)
        if item:
            item.setText(text)