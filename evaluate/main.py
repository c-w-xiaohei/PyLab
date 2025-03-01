import argparse
import os
import re
import subprocess
import json
import sys  
from datetime import datetime
import traceback  # 导入 traceback 模块

from .evaluation_types import LabResult, EvaluationResults
from table_utils import TableParser

CURRENT_DIR = os.path.normpath(os.path.dirname(os.path.abspath(__file__)))



def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='Python Lab 测评脚本')
    parser.add_argument('--path', nargs='+', required=True,
                       help='测评路径，格式为[username]/lab[number]')
    return parser.parse_args()

def validate_path(path):
    """验证路径格式"""
    pattern = r'^([a-zA-Z0-9_-]+)/lab(\d+)$'
    match = re.match(pattern, path)
    if not match:
        raise ValueError(f'测评路径格式错误: {path}')
    return match.group(1), int(match.group(2))

def get_available_labs():
    """获取所有可用的实验编号"""
    code_dir = os.path.join(CURRENT_DIR, 'code')
    lab_dirs = [d for d in os.listdir(code_dir) if d.startswith('lab') and os.path.isdir(os.path.join(code_dir, d))]
    lab_num_list = sorted([int(re.search(r'lab(\d+)', d).group(1)) for d in lab_dirs])
    return lab_num_list




def main():
    try:
        args = parse_args()
        results: EvaluationResults = []
        overall_status = True

        readme_path = os.path.join(CURRENT_DIR, 'README.md')
        try:
            with open(readme_path, 'r', encoding='utf-8') as f:
                readme_content = f.readlines()
        except FileNotFoundError:
            readme_content = ['| 用户排名 | 用户名 | lab1 | 完成任务总数 |\n', '| --- | --- | --- | --- |\n']

        # 确保所有实验列都存在
        readme_content = TableParser.ensure_lab_columns(readme_content, get_available_labs())

        for path in args.path:
            username, lab_num = validate_path(path)
            print(f'开始测评: 用户 {username}, 实验 {lab_num}', file=sys.stderr)
            submit_path = os.path.join(CURRENT_DIR, 'submit', os.path.normpath(path))
            if not os.path.isdir(submit_path):
                raise ValueError(f'找不到测评路径: {submit_path}')

            lab_results: LabResult = {
                'lab_num': lab_num,
                'username': username,
                'tasks': {},  # 修改成字典
                'passed': True  # 初始状态为 True
            }

            try:
                # 1. 构建测评脚本的完整路径
                test_script_dir = os.path.join(CURRENT_DIR, 'code', f'lab{lab_num}')
                task_files = [f for f in os.listdir(test_script_dir) if f.startswith('task') and f.endswith('.py')]
                task_files.sort(key=lambda x: int(re.search(r'task(\d+)\.py', x).group(1)))  # 按照任务编号排序

                # 2. 在path下按序执行测评脚本
                for task_file in task_files:
                    task_path = os.path.join(test_script_dir, task_file)
                    print(f'  执行测评程序: {task_path} ing...', file=sys.stderr)  # 保留，用于调试

                    task_result = {
                        'task_file': task_file,
                        'returncode': -1,
                        'stdout': '',
                        'stderr': '',
                        'error': None  # 改为 None 作为初始值
                    }

                    # 3. 使用 subprocess 模块执行测评程序
                    try:
                        print(f'  在 `{submit_path}` 下执行测评程序 `{task_file}` :', file=sys.stderr)  # 保留，用于调试
                        
                        # 创建修改后的环境变量
                        env = os.environ.copy()
                        
                        # 设置或附加PYTHONPATH环境变量
                        if 'PYTHONPATH' in env:
                            env['PYTHONPATH'] = f"{submit_path}{os.pathsep}{env['PYTHONPATH']}"
                        else:
                            env['PYTHONPATH'] = submit_path
                            
                        # 直接运行测评脚本
                        result = subprocess.run(['python', os.path.join(test_script_dir, task_file)], 
                                               cwd=submit_path,
                                               env=env,
                                               capture_output=True, 
                                               text=True, 
                                               timeout=60)
                        task_result.update({  # 使用 update 方法更新结果
                            'returncode': result.returncode,
                            'stdout': result.stdout,
                            'stderr': result.stderr
                        })

                        if result.returncode != 0:
                            lab_results['passed'] = False
                            overall_status = False
                    except subprocess.TimeoutExpired:
                        print(f'  测评程序 {task_file} 超时', file=sys.stderr)  # 保留，用于调试
                        task_result['error'] = 'Timeout'
                        lab_results['passed'] = False
                        overall_status = False
                    except subprocess.CalledProcessError as e:
                        print(f'  测评程序 {task_file} 发生错误:', file=sys.stderr)  # 保留，用于调试
                        print(f'    Return Code: {e.returncode}', file=sys.stderr)  # 保留，用于调试
                        print(f'    Stdout: {e.stdout}', file=sys.stderr)  # 保留，用于调试
                        print(f'    Stderr: {e.stderr}', file=sys.stderr)  # 保留，用于调试
                        task_result['returncode'] = e.returncode
                        task_result['stdout'] = e.stdout
                        task_result['stderr'] = e.stderr
                        lab_results['passed'] = False
                        overall_status = False
                        task_result['error'] = f'CalledProcessError: {str(e)}'  # 详细错误信息
                    except Exception as e:
                        print(f'  测评程序 {task_file} 发生未知错误: {str(e)}', file=sys.stderr)  # 保留，用于调试
                        task_result['error'] = f'未知错误: {str(e)}'  # 详细错误信息
                        lab_results['passed'] = False
                        overall_status = False
                        print(traceback.format_exc(), file=sys.stderr)  # 打印 traceback

                    task_name = re.search(r'task(\d+)\.py', task_file).group(0)
                    lab_results['tasks'][task_name] = task_result

                # 4. 结果处理与表格更新
                try:
                    # 更新用户成就
                    readme_content = TableParser.update_user_achievement(
                        readme_content, username, lab_num, lab_results['tasks']
                    )
                except Exception as e:
                    print(f'  结果处理与表格更新失败: {str(e)}', file=sys.stderr)
                    lab_results['passed'] = False
                    overall_status = False
                    lab_results['table_update_error'] = f'结果处理错误: {str(e)}'
                    print(traceback.format_exc(), file=sys.stderr)

            except Exception as e:
                print(f'  测评 {path} 失败: {str(e)}', file=sys.stderr)
                lab_results['passed'] = False
                overall_status = False
                lab_results['error'] = f'测评失败: {str(e)}'  # 详细错误信息
                print(traceback.format_exc(), file=sys.stderr)  # 打印 traceback

            results.append(lab_results)  # 将每个 lab 的结果添加到总结果中

        # 5. 输出 JSON 结果到标准输出
        print(json.dumps(results, indent=2, ensure_ascii=False))

        # 6. 保存表格（无论实验是否通过都保存）
        try:
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.writelines(readme_content)
            print(f'成功更新 README.md', file=sys.stderr)
        except Exception as e:
            print(f'保存 README.md 失败: {str(e)}', file=sys.stderr)
            sys.exit(1)
            
        # 根据整体状态返回退出码
        if overall_status:
            sys.exit(0)
        else:
            sys.exit(1)

    except Exception as e:
        
        error_info = {
            'error': f'顶层异常: {str(e)}',
        }
        # 错误详情输出到stderr用于调试
        print(f'发生顶层异常: {str(e)}', file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        
        # JSON格式的错误信息输出到stdout
        print(json.dumps(error_info, indent=2, ensure_ascii=False))
        
        sys.exit(1)

if __name__ == '__main__':
    main()