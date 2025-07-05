#!/usr/bin/env python3
"""
修正所有 router 檔案中的導入問題
"""

import os
import re

def fix_router_imports(filepath):
    """修正單個 router 檔案中的導入"""
    print(f"修正檔案: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修正常見的導入錯誤
    fixes = [
        # 修正 fastapi 導入
        (r'from fastapi from \.\. import (.+)', r'from fastapi import \1'),
        # 修正 sqlalchemy 導入
        (r'from sqlalchemy\.orm from \.\. import (.+)', r'from sqlalchemy.orm import \1'),
        # 修正重複的 from .. 
        (r'from \.\. from \.\. import (.+)', r'from .. import \1'),
        # 修正其他可能的錯誤格式
        (r'from (.+) from \.\. import (.+)', r'from \1 import \2'),
    ]
    
    original_content = content
    for pattern, replacement in fixes:
        content = re.sub(pattern, replacement, content)
    
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✅ 已修正 {filepath}")
        return True
    else:
        print(f"  ⏭️  {filepath} 無需修正")
        return False

def main():
    """主函數"""
    router_dir = "routers"
    
    if not os.path.exists(router_dir):
        print(f"錯誤: {router_dir} 目錄不存在")
        return
    
    fixed_count = 0
    
    # 遍歷所有 .py 檔案
    for filename in os.listdir(router_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            filepath = os.path.join(router_dir, filename)
            if fix_router_imports(filepath):
                fixed_count += 1
    
    print(f"\n總共修正了 {fixed_count} 個檔案")

if __name__ == "__main__":
    main()
