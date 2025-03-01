from py_markdown_table.markdown_table import markdown_table
from typing import List, Dict, TypedDict, Optional
from datetime import datetime
from evaluation_types import TaskResult

class UserAchievement:
    """表示单个用户的成就数据"""
    def __init__(self, username: str, rank: str = "1"):
        self.username = username
        self.rank = rank
        self.achievements: Dict[str, str] = {}

    def update_lab(self, lab_num: int, percentage: float) -> None:
        """更新用户某个实验的完成情况"""
        lab_key = f'lab{lab_num}'
        if percentage > 0:
            current_date = datetime.now().strftime('%Y-%m-%d')
            if percentage == 100.0:  # 完全通过时显示√
                self.achievements[lab_key] = f'{current_date} : √'
            else:
                self.achievements[lab_key] = f'{current_date} : {percentage:.1f}%'
        else:
            self.achievements[lab_key] = ''
        
    def get_completed_tasks(self) -> int:
        """计算用户完成的任务总数"""
        completed = 0
        for value in self.achievements.values():
            if value.strip():  # 如果有任何内容（非空字符串）
                completed += 1
        return completed

    def to_dict(self, headers: List[str]) -> Dict[str, str]:
        """转换为表格行数据"""
        row = {'用户排名': self.rank, '用户名': self.username}
        for header in headers:
            if header.startswith('lab'):
                row[header] = self.achievements.get(header, '')
            elif header == '完成任务总数':
                row[header] = str(self.get_completed_tasks())
        return row


class AchievementTable:
    """成就表格数据结构"""
    def __init__(self):
        self.headers: List[str] = ['用户排名', '用户名', '完成任务总数']
        self.achievements: List[UserAchievement] = []

    def ensure_lab_column(self, lab_num: int) -> None:
        """确保实验列存在"""
        lab_header = f'lab{lab_num}'
        if lab_header not in self.headers:
            # 插入到完成任务总数列之前
            total_tasks_index = self.headers.index('完成任务总数')
            self.headers.insert(total_tasks_index, lab_header)

    def get_or_create_user(self, username: str) -> UserAchievement:
        """获取或创建用户成就记录"""

        for user in self.achievements:
            if user.username == username:
                return user
        
        user = UserAchievement(username=username)
        self.achievements.append(user)
        return user

    def update_rankings(self) -> None:
        """更新用户排名"""
        # 使用稳定排序，当完成任务总数相同时，保持原有顺序（即先达到总数的排前面）
        # 先按照完成任务总数排序，然后按总分排序
        sorted_achievements = sorted(
            self.achievements,
            key=lambda x: (x.get_completed_tasks()),
            reverse=True
        )
        # 更新排名
        self.achievements = sorted_achievements
        for i, achievement in enumerate(self.achievements, 1):
            achievement.rank = str(i)


class TableParser:
    """Markdown表格解析和格式化"""
    @staticmethod
    def find_table_start(content: List[str]) -> int:
        """查找表格起始位置"""
        for i, line in enumerate(content):
            if '用户排名' in line and '用户名' in line:
                return i
        raise ValueError('未找到表格起始行')

    @staticmethod
    def parse_table(content: List[str]) -> AchievementTable:
        """解析Markdown表格内容"""
        start_idx = TableParser.find_table_start(content)
        table = AchievementTable()
        
        table_lines = [line for line in content[start_idx:] if line.strip()]
        if not table_lines:
            return table

        # 解析表头
        headers = [h.strip() for h in table_lines[0].strip('|').split('|') if h.strip()]
        table.headers = headers

        # 解析数据行
        for line in table_lines[2:]:  # 跳过分隔行
            cells = [cell.strip() for cell in line.strip('|').split('|')]
            if len(cells) < len(headers):
                continue
                
            user = UserAchievement(
                username=cells[headers.index('用户名')],
                rank=cells[headers.index('用户排名')]
            )
            
            for i, header in enumerate(headers):
                if header.startswith('lab') and i < len(cells):
                    user.achievements[header] = cells[i]
                    
            table.achievements.append(user)
        print(table.achievements)
        if len(table.achievements) > 0:
            print(table.achievements[0].achievements)
        
        return table

    @staticmethod
    def format_table(table: AchievementTable) -> Optional[str]:
        """将表格转换为Markdown格式"""
        rows = [user.to_dict(table.headers) for user in table.achievements]
        if rows:
            return markdown_table(rows).set_params(row_sep='markdown').get_markdown()
        else:
            return None

    @staticmethod
    def update_content(content: List[str], table: AchievementTable) -> List[str]:
        """更新文件内容中的表格部分"""
        start_idx = TableParser.find_table_start(content)
        table_str = TableParser.format_table(table)
        if table_str:
            table_str = table_str.strip("```")
            return content[:start_idx] + table_str.splitlines(keepends=True)
        else:
            return content

    @staticmethod
    def ensure_lab_columns(content: List[str], available_labs: List[int]) -> List[str]:
        """确保所有实验列都存在"""
        table = TableParser.parse_table(content)

        for lab_num in available_labs:
            table.ensure_lab_column(lab_num)
        return TableParser.update_content(content, table)

    @staticmethod
    def update_user_achievement(content: List[str], username: str, lab_num: int, task_results: Dict[str, TaskResult]) -> List[str]:
        """更新用户实验成就"""
        table = TableParser.parse_table(content)
        
        # 计算通过率
        passed_tasks = sum(1 for r in task_results.values() if r['returncode'] == 0)
        total_tasks = len(task_results)
        percentage = (passed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
        
        # 更新用户成就
        user = table.get_or_create_user(username)
        table.ensure_lab_column(lab_num)
        user.update_lab(lab_num, percentage)
        table.update_rankings()
        
        return TableParser.update_content(content, table)