import csv
import os

def check_csv_status():
    csv_path = 'D:\\怖客\\scripts\\space_merged_with_summary.csv'
    
    if not os.path.exists(csv_path):
        print('CSV文件不存在')
        return
    
    try:
        encodings = ['utf-8', 'gbk', 'gb2312', 'ansi']
        rows = None
        
        for encoding in encodings:
            try:
                with open(csv_path, 'r', encoding=encoding) as f:
                    reader = csv.reader(f)
                    rows = list(reader)
                print(f'成功使用编码 {encoding} 读取CSV文件')
                break
            except Exception as e:
                continue
        
        if rows is None:
            print('无法读取CSV文件')
            return
        
        total_rows = len(rows) - 1  # 减去表头
        processed_rows = 0
        unprocessed_rows = 0
        
        for row in rows[1:]:  # 跳过表头
            if len(row) > 1 and row[1].strip():
                processed_rows += 1
            else:
                unprocessed_rows += 1
        
        print(f'总行数: {total_rows}')
        print(f'已处理行数: {processed_rows}')
        print(f'未处理行数: {unprocessed_rows}')
        print(f'处理进度: {processed_rows/total_rows*100:.2f}%')
        
        # 找到第一个未处理的行
        first_unprocessed = None
        for i, row in enumerate(rows[1:], 1):  # 从1开始计数
            if len(row) <= 1 or not row[1].strip():
                first_unprocessed = i
                break
        
        if first_unprocessed:
            print(f'第一个未处理的行: {first_unprocessed}')
        else:
            print('所有行都已处理')
            
    except Exception as e:
        print(f'错误: {str(e)}')

if __name__ == '__main__':
    check_csv_status()
