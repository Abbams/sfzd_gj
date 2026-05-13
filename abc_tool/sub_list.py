import sys
import json
import os
import time
from datetime import datetime, timedelta
from typing import List, Dict, Set

import requests
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QComboBox, QPushButton, QTableWidget,
                             QTableWidgetItem, QDialog, QMessageBox, QHeaderView,
                             QLabel, QLineEdit, QProgressBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSettings


# ---------------------------- 网络请求线程（通用） ----------------------------
class SubmissionsWorker(QThread):
    """获取用户提交记录的线程，支持时间过滤和全部记录"""
    finished = pyqtSignal(list)   # 成功时返回提交列表
    error = pyqtSignal(str)       # 出错时返回错误信息

    def __init__(self, username: str, from_second: int = 0):
        """
        :param username: AtCoder 用户名
        :param from_second: 起始时间戳（秒），0 表示获取全部
        """
        super().__init__()
        self.username = username
        self.from_second = from_second

    def run(self):
        url = "https://kenkoooo.com/atcoder/atcoder-api/v3/user/submissions"
        params = {"user": self.username, "from_second": self.from_second}
        try:
            resp = requests.get(url, params=params, timeout=30)  # 全部记录可能较慢，延长超时
            resp.raise_for_status()
            data = resp.json()
            self.finished.emit(data)
        except requests.exceptions.RequestException as e:
            self.error.emit(f"网络请求失败：{e}")
        except json.JSONDecodeError:
            self.error.emit("解析响应数据失败")
        except Exception as e:
            self.error.emit(f"未知错误：{e}")


# ---------------------------- 比赛通过情况对话框 ----------------------------
class ContestStatusDialog(QDialog):
    """显示用户在指定比赛中的每道题通过情况"""
    def __init__(self, username: str, contest_id: str, submissions: List[Dict], parent=None):
        super().__init__(parent)
        self.username = username
        self.contest_id = contest_id
        self.submissions = submissions   # 已经过滤过该比赛的所有提交
        self.setWindowTitle(f"{username} 在 {contest_id} 中的通过情况")
        self.resize(700, 500)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 添加说明标签
        info_label = QLabel(f"比赛 {self.contest_id} - 共 {len(self.submissions)} 次提交")
        layout.addWidget(info_label)

        # 分析每道题的状态
        problem_status = {}  # problem_id -> {"status": "AC"/"not AC", "last_result": str, "submission_time": int}
        for sub in self.submissions:
            pid = sub["problem_id"]
            result = sub["result"]
            epoch = sub["epoch_second"]
            # 只关心该比赛中的题目（问题ID通常包含比赛ID，但以防万一）
            if not pid.startswith(self.contest_id):
                continue
            # 如果已经 AC，则保持 AC，否则更新最新状态
            if pid not in problem_status:
                problem_status[pid] = {"status": result, "last_result": result, "submission_time": epoch}
            else:
                if result == "AC":
                    problem_status[pid]["status"] = "AC"
                # 更新最后提交结果和时间
                if epoch > problem_status[pid]["submission_time"]:
                    problem_status[pid]["last_result"] = result
                    problem_status[pid]["submission_time"] = epoch
                # 如果当前是AC但之前状态不是AC，更新状态
                if result == "AC" and problem_status[pid]["status"] != "AC":
                    problem_status[pid]["status"] = "AC"

        # 创建表格
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["题目ID", "最终通过", "最后提交结果", "最后提交时间"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        # 按题目ID排序
        sorted_problems = sorted(problem_status.keys())
        self.table.setRowCount(len(sorted_problems))

        for row, pid in enumerate(sorted_problems):
            status = problem_status[pid]
            final_pass = "✅ 通过" if status["status"] == "AC" else "❌ 未通过"
            last_result = status["last_result"]
            last_time = datetime.fromtimestamp(status["submission_time"]).strftime("%Y-%m-%d %H:%M:%S")

            self.table.setItem(row, 0, QTableWidgetItem(pid))
            self.table.setItem(row, 1, QTableWidgetItem(final_pass))
            self.table.setItem(row, 2, QTableWidgetItem(last_result))
            self.table.setItem(row, 3, QTableWidgetItem(last_time))

            # 设置颜色：通过绿色，未通过红色
            if status["status"] == "AC":
                self.table.item(row, 1).setForeground(Qt.green)
            else:
                self.table.item(row, 1).setForeground(Qt.red)

        layout.addWidget(self.table)

        # 关闭按钮
        btn_close = QPushButton("关闭")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignRight)


# ---------------------------- 比赛查询对话框（输入比赛ID） ----------------------------
class ContestQueryDialog(QDialog):
    """弹窗让用户输入比赛ID"""
    def __init__(self, username: str, parent=None):
        super().__init__(parent)
        self.username = username
        self.setWindowTitle(f"查看 {username} 的比赛通过情况")
        self.setFixedSize(400, 150)
        self.init_ui()
        self.contest_id = None

    def init_ui(self):
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(f"用户：{self.username}"))
        layout.addWidget(QLabel("请输入比赛 ID（例如 abc300, arc150, typical90 等）："))

        self.contest_edit = QLineEdit()
        layout.addWidget(self.contest_edit)

        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("查询")
        self.cancel_btn = QPushButton("取消")
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        self.ok_btn.clicked.connect(self.on_ok)
        self.cancel_btn.clicked.connect(self.reject)

    def on_ok(self):
        contest = self.contest_edit.text().strip()
        if not contest:
            QMessageBox.warning(self, "警告", "比赛 ID 不能为空")
            return
        self.contest_id = contest
        self.accept()


# ---------------------------- 主窗口（原有功能 + 新增按钮） ----------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AtCoder 提交记录查询")
        self.setFixedSize(550, 200)
        self.settings = QSettings("AtCoderViewer", "History")
        self.init_ui()
        self.load_history()
        self.current_username = ""

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 输入区域
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("用户名："))
        self.user_combo = QComboBox()
        self.user_combo.setEditable(True)
        self.user_combo.setInsertPolicy(QComboBox.NoInsert)
        self.user_combo.setMinimumWidth(250)
        input_layout.addWidget(self.user_combo)
        layout.addLayout(input_layout)

        # 按钮区域
        btn_layout = QHBoxLayout()
        self.search_week_btn = QPushButton("查询最近一周提交")
        self.search_week_btn.clicked.connect(self.on_search_week)
        self.search_contest_btn = QPushButton("查看比赛通过情况")
        self.search_contest_btn.clicked.connect(self.on_query_contest)
        btn_layout.addWidget(self.search_week_btn)
        btn_layout.addWidget(self.search_contest_btn)
        layout.addLayout(btn_layout)

        # 进度条（用于获取全部提交时显示）
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # 状态栏
        self.statusBar().showMessage("就绪")

    def load_history(self):
        """加载之前保存的用户名历史记录"""
        history = self.settings.value("usernames", [])
        if isinstance(history, str):
            history = [history]
        seen = set()
        for name in history:
            if name and name not in seen:
                self.user_combo.addItem(name)
                seen.add(name)
        if self.user_combo.count() == 0:
            self.user_combo.addItem("")
        self.user_combo.setCurrentIndex(0)

    def save_history(self, username):
        """保存用户名到历史记录"""
        if not username:
            return
        history = self.settings.value("usernames", [])
        if not isinstance(history, list):
            history = [history] if history else []
        if username in history:
            history.remove(username)
        history.insert(0, username)
        history = history[:20]
        self.settings.setValue("usernames", history)

        # 更新下拉框
        self.user_combo.clear()
        for name in history:
            self.user_combo.addItem(name)
        self.user_combo.setCurrentText(username)

    def get_current_username(self):
        return self.user_combo.currentText().strip()

    # ---------- 功能1：最近一周提交 ----------
    def on_search_week(self):
        username = self.get_current_username()
        if not username:
            QMessageBox.warning(self, "警告", "请输入用户名")
            return

        week_ago = datetime.now() - timedelta(days=7)
        from_second = int(week_ago.timestamp())

        self.set_buttons_enabled(False)
        self.statusBar().showMessage(f"正在获取 {username} 最近一周提交...")

        self.worker = SubmissionsWorker(username, from_second)
        self.worker.finished.connect(lambda subs: self.on_week_finished(username, subs))
        self.worker.error.connect(self.on_fetch_error)
        self.worker.start()

    def on_week_finished(self, username, submissions):
        self.set_buttons_enabled(True)
        self.save_history(username)
        if not submissions:
            QMessageBox.information(self, "提示", f"用户 {username} 最近一周没有提交记录")
            self.statusBar().showMessage("未找到提交记录")
            return
        self.statusBar().showMessage(f"获取成功，共 {len(submissions)} 条记录")
        dialog = SubmissionsDialog(submissions, self)
        dialog.exec_()

    # ---------- 功能2：比赛通过情况 ----------
    def on_query_contest(self):
        username = self.get_current_username()
        if not username:
            QMessageBox.warning(self, "警告", "请先输入用户名")
            return

        # 弹出比赛ID输入对话框
        contest_dialog = ContestQueryDialog(username, self)
        if contest_dialog.exec_() != QDialog.Accepted:
            return
        contest_id = contest_dialog.contest_id

        # 确认后开始获取该用户的所有提交
        self.set_buttons_enabled(False)
        self.statusBar().showMessage(f"正在获取 {username} 的全部提交记录（可能较慢）...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 不确定进度，显示忙碌

        self.worker_all = SubmissionsWorker(username, from_second=0)  # 0 表示全部
        self.worker_all.finished.connect(lambda subs: self.on_all_submissions_finished(username, contest_id, subs))
        self.worker_all.error.connect(self.on_fetch_error)
        self.worker_all.start()

    def on_all_submissions_finished(self, username, contest_id, all_submissions):
        self.progress_bar.setVisible(False)
        self.set_buttons_enabled(True)
        self.save_history(username)   # 保存用户名

        # 过滤出指定比赛的提交
        contest_submissions = [sub for sub in all_submissions if sub.get("contest_id") == contest_id]
        if not contest_submissions:
            QMessageBox.information(self, "提示", f"用户 {username} 在比赛 {contest_id} 中没有提交记录")
            self.statusBar().showMessage("未找到该比赛的提交")
            return

        self.statusBar().showMessage(f"找到 {len(contest_submissions)} 条提交记录")
        # 弹出通过情况对话框
        dialog = ContestStatusDialog(username, contest_id, contest_submissions, self)
        dialog.exec_()

    # ---------- 辅助方法 ----------
    def set_buttons_enabled(self, enabled):
        self.search_week_btn.setEnabled(enabled)
        self.search_contest_btn.setEnabled(enabled)

    def on_fetch_error(self, error_msg):
        self.progress_bar.setVisible(False)
        self.set_buttons_enabled(True)
        self.statusBar().showMessage("获取失败")
        QMessageBox.critical(self, "错误", f"获取提交记录失败：\n{error_msg}")


# ---------------------------- 最近一周提交的展示对话框（原样保留） ----------------------------
class SubmissionsDialog(QDialog):
    def __init__(self, submissions: List[Dict], parent=None):
        super().__init__(parent)
        self.submissions = submissions
        self.setWindowTitle("最近一周提交记录")
        self.resize(900, 500)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["提交时间", "比赛ID", "题目ID", "结果"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)

        sorted_subs = sorted(self.submissions, key=lambda x: x.get("epoch_second", 0))
        self.table.setRowCount(len(sorted_subs))

        for row, sub in enumerate(sorted_subs):
            dt = datetime.fromtimestamp(sub["epoch_second"])
            time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            contest_id = sub.get("contest_id", "")
            problem_id = sub.get("problem_id", "")
            result = sub.get("result", "")

            self.table.setItem(row, 0, QTableWidgetItem(time_str))
            self.table.setItem(row, 1, QTableWidgetItem(contest_id))
            self.table.setItem(row, 2, QTableWidgetItem(problem_id))
            self.table.setItem(row, 3, QTableWidgetItem(result))

            if result == "AC":
                self.table.item(row, 3).setForeground(Qt.green)
            elif result in ("WA", "TLE", "RE", "CE"):
                self.table.item(row, 3).setForeground(Qt.red)
            else:
                self.table.item(row, 3).setForeground(Qt.gray)

        layout.addWidget(self.table)
        btn_close = QPushButton("关闭")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignRight)


# ---------------------------- 程序入口 ----------------------------
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("AtCoderSubmissionsViewer")
    app.setOrganizationName("AtCoderViewer")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()