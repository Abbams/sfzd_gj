import os

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