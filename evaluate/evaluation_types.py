from typing import TypedDict, List, Dict, Optional

class TaskResult(TypedDict):
    """
    表示单个任务执行的结果。

    Attributes:
        task_file (str): 任务文件名 (例如: "task1.py")。
        returncode (int): 任务执行的返回码。0 表示成功，非 0 表示失败。
        stdout (str): 任务执行的标准输出。
        stderr (str): 任务执行的标准错误输出。
        error (Optional[str]): 如果任务执行过程中发生异常，则包含异常信息的字符串。
                              如果任务正常执行（即使返回码非 0），则可能为空。
    """
    task_file: str
    returncode: int
    stdout: str
    stderr: str
    error: Optional[str]


class LabResult(TypedDict):
    """
    表示一个实验的测评结果。

    Attributes:
        lab_num (int): 实验编号 (例如: 1, 2, 3)。
        username (str): 用户名。
        tasks (Dict[str, TaskResult]): 一个字典，键是任务文件名 (例如: "task1.py")，
                                      值是 TaskResult 对象，包含该任务的详细执行结果。
        passed (bool):  指示该实验是否整体通过。True 表示所有任务都成功（返回码为 0），False 表示至少有一个任务失败或发生错误。
        error (Optional[str]): 如果在实验测评过程中发生整体错误（非任务执行错误），则包含错误信息的字符串。
                              例如，路径验证失败，或者其他未预料到的异常。
        table_update_error (Optional[str]): 如果在处理 README.md 文件时发生错误，则包含错误信息的字符串。
                                     例如，读取或更新 README.md 文件失败。
    """
    lab_num: int
    username: str
    tasks: Dict[str, TaskResult]
    passed: bool
    error: Optional[str]
    table_update_error: Optional[str]


EvaluationResults = List[LabResult]
"""
EvaluationResults (List[LabResult]):  测评脚本 `evaluate/main.py` 输出到标准输出的 JSON 数据类型。
                                    它是一个 LabResult 对象的列表，每个 LabResult 对象代表一个被测评实验的结果。
                                    列表中的每个元素对应一个通过命令行参数 `--path` 传入的测评路径。
"""