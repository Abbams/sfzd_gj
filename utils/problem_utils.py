import os
import re
import json
import shutil
import zipfile


def load_all_problems(problems_base_path):
    """从固定路径加载所有题目"""
    problems = []

    if not os.path.exists(problems_base_path):
        os.makedirs(problems_base_path, exist_ok=True)
        return problems

    pattern = re.compile(r'^(\d+)_(.+)$')

    for item in os.listdir(problems_base_path):
        item_path = os.path.join(problems_base_path, item)
        if os.path.isdir(item_path):
            match = pattern.match(item)
            if match:
                from models.problem import Problem
                problem_id = match.group(1)
                problem_title = match.group(2)

                problem = Problem(problem_title, problem_id)
                problem.problem_path = item_path

                exe_path = os.path.join(item_path, "solution.exe")
                if os.path.exists(exe_path):
                    problem.compiled_exe_path = exe_path

                load_problem_content(problem)
                problems.append(problem)

    problems.sort(key=lambda x: int(x.id))
    return problems


def load_problem_content(problem):
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

            generator_rel_path = problem_data.get("generator_path", "")
            if generator_rel_path:
                generator_full_path = os.path.join(problem.problem_path, generator_rel_path)
                if os.path.exists(generator_full_path):
                    problem.generator_path = generator_full_path
                else:
                    problem.generator_path = ""

            data_files = problem_data.get("data_files", [])
            for file_name in data_files:
                file_path = os.path.join(problem.problem_path, file_name)
                if os.path.exists(file_path):
                    problem.data_files.append(file_path)

        except Exception as e:
            print(f"加载题目 {problem.full_title} 失败: {e}")


def save_problem(problem, problems_base_path):
    """保存题目"""
    # 确保目录名与编号和标题一致
    # print(problems_base_path)
    expected_dir_name = f"{problem.id}_{problem.title}"
    current_dir_name = os.path.basename(problem.problem_path)

    if expected_dir_name != current_dir_name:
        new_path = os.path.join(problems_base_path, expected_dir_name)

        if os.path.exists(new_path):
            counter = 1
            while os.path.exists(f"{new_path}_{counter}"):
                counter += 1
            new_path = f"{new_path}_{counter}"

        try:
            os.rename(problem.problem_path, new_path)
            problem.problem_path = new_path
        except Exception as e:
            raise Exception(f"无法重命名目录:\n{str(e)}")

    return _save_problem_to_path(problem)


def _save_problem_to_path(problem):
    """保存题目到指定路径"""
    path = problem.problem_path

    # 收集数据文件列表
    data_files = []
    for file_name in os.listdir(path):
        if file_name.endswith('.in') or file_name.endswith('.out'):
            data_files.append(file_name)

    # 保存生成器文件路径
    generator_relative_path = "datamaker.py"
    if problem.generator_path and os.path.exists(problem.generator_path):
        try:
            abs_problem_path = os.path.abspath(path)
            abs_generator_path = os.path.abspath(problem.generator_path)

            if os.path.commonpath([abs_problem_path]) == os.path.commonpath(
                    [abs_generator_path, abs_problem_path]):
                generator_relative_path = os.path.relpath(abs_generator_path, abs_problem_path)
                print(generator_relative_path)
            else:
                new_path = os.path.join(path, os.path.basename(problem.generator_path))
                if os.path.exists(new_path):
                    base, ext = os.path.splitext(os.path.basename(problem.generator_path))
                    counter = 1
                    while os.path.exists(new_path):
                        new_filename = f"{base}_{counter}{ext}"
                        new_path = os.path.join(path, new_filename)
                        counter += 1

                shutil.copy2(problem.generator_path, new_path)
                generator_relative_path = os.path.basename(new_path)
                problem.generator_path = new_path

        except Exception as e:
            print(f"处理生成器文件时出错: {e}")
            new_path = os.path.join(path, os.path.basename(problem.generator_path))
            shutil.copy2(problem.generator_path, new_path)
            generator_relative_path = os.path.basename(new_path)
            problem.generator_path = new_path

    # 保存题面文件
    problem_data = {
        "id": problem.id,
        "title": problem.title,
        "description": problem.description,
        "input_description": problem.input_description,
        "output_description": problem.output_description,
        "sample_input": problem.sample_input,
        "sample_output": problem.sample_output,
        "solution_code": problem.solution_code,
        "generator_path": generator_relative_path,
        "language": problem.language,
        "data_files": data_files
    }

    json_path = os.path.join(path, "problem.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(problem_data, f, ensure_ascii=False, indent=2)

    # 保存正解代码到单独文件
    if problem.solution_code:
        ext_map = {"python": ".py", "cpp": ".cpp", "java": ".java"}
        ext = ext_map.get(problem.language, ".txt")
        solution_path = os.path.join(path, f"solution{ext}")
        with open(solution_path, "w", encoding="utf-8") as f:
            f.write(problem.solution_code)

    return path


def pack_data_files(problem, output_path):
    """将所有 .in 和 .out 文件打包成zip文件"""
    data_files = []
    for file_name in os.listdir(problem.problem_path):
        if file_name.endswith('.in') or file_name.endswith('.out'):
            file_path = os.path.join(problem.problem_path, file_name)
            data_files.append(file_path)

    if not data_files:
        raise Exception("没有找到数据文件")

    zip_filename = f"{problem.full_title}.zip"
    zip_path = os.path.join(output_path, zip_filename)

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in data_files:
            arcname = os.path.basename(file_path)
            zipf.write(file_path, arcname)

    return zip_path


def extract_number_from_filename(filename):
    """从文件名中提取数字"""
    match = re.search(r'(\d+)', os.path.basename(filename))
    return int(match.group(1)) if match else 0


def clear_output_files(problem_path):
    """清除所有输出文件"""
    count = 0
    for file_name in os.listdir(problem_path):
        if file_name.endswith('.out'):
            file_path = os.path.join(problem_path, file_name)
            os.remove(file_path)
            count += 1
    return count