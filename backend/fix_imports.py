#!/usr/bin/env python3
"""
修正所有 routers 中的相對導入問題
"""

import os
import re

def fix_imports_in_file(filepath):
    """恢復相對導入"""
    print(f"修正檔案: {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 恢復相對導入
    patterns = [
        (r'import database, models, schemas, security', r'from .. import database, models, schemas, security'),
        (r'import (.+)', r'from .. import \1'),
    ]
    
    original_content = content
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✅ 已修正 {filepath}")
        return True
    else:
        print(f"  ⏭️  {filepath} 無需修正")
        return False

def fix_all_router_imports():
    """修正所有 router 檔案中的導入"""
    routers_dir = "routers"
    fixed_count = 0
    
    if not os.path.exists(routers_dir):
        print(f"錯誤: {routers_dir} 目錄不存在")
        return
    
    for filename in os.listdir(routers_dir):
        if filename.endswith('.py') and not filename.startswith('test_'):
            filepath = os.path.join(routers_dir, filename)
            if fix_imports_in_file(filepath):
                fixed_count += 1
    
    print(f"\n總共修正了 {fixed_count} 個檔案")

if __name__ == "__main__":
    fix_all_router_imports()
