import copy

def fix_indent():
    with open('src/app.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    out = []
    in_block = False
    for i, line in enumerate(lines):
        if not in_block and "st.sidebar.markdown('---')" in line.replace('"', "'"):
            if "数据过滤阈值" in lines[i+1]:
                in_block = True
                out.append('    if page_mode == "性能曲线看板":\n')
                out.append('        ' + line.lstrip())
                continue
                
        if in_block:
            if 'elif page_mode == "轴向力深度分析":' in line:
                in_block = False
                out.append(line)
            else:
                if line.strip() == '':
                    out.append('\n')
                else:
                    out.append('    ' + line)
        else:
            out.append(line)
            
    with open('src/app.py', 'w', encoding='utf-8') as f:
        f.writelines(out)
        
if __name__ == '__main__':
    fix_indent()
