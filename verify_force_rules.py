import sys
import pandas as pd
from src.force_calculator import calculate_backplate_force, calculate_total_axial_force

def test_calculus():
    # 模拟极端工况测试
    rpm = 24000.0
    p_out_gauge = 150000.0 # 150kPa 表压
    p_in_gauge = 0.0
    rho = 1.204
    d_imp = 500.0
    d_shaft = 100.0
    d_seal2 = 300.0
    
    # CASE 1: 无密封无孔 (基准测试)
    f_bp_1 = calculate_backplate_force(
        rpm, p_out_gauge, p_in_gauge, rho, d_imp, d_shaft, 
        has_seal2=False, has_balance_holes=False
    )
    
    # CASE 2: 有主密封但无孔 (隔离后，由于无孔，内侧压力衰减至抛物线底端，受力会略变)
    f_bp_2 = calculate_backplate_force(
        rpm, p_out_gauge, p_in_gauge, rho, d_imp, d_shaft, 
        has_seal2=True, d_seal2_mm=d_seal2, has_balance_holes=False
    )
    
    # CASE 3: 有主密封且开大平衡孔 (内侧腔室压力骤降至入口大气基准附近)
    f_bp_3 = calculate_backplate_force(
        rpm, p_out_gauge, p_in_gauge, rho, d_imp, d_shaft, 
        has_seal2=True, d_seal2_mm=d_seal2, has_balance_holes=True, d_hole_mm=200.0, a_hole_cm2=20.0, alpha=0.5
    )
    
    print(f"CASE 1 (No Seal/Hole): {f_bp_1:.2f} N")
    print(f"CASE 2 (With Seal): {f_bp_2:.2f} N")
    print(f"CASE 3 (With Seal + Big Hole): {f_bp_3:.2f} N")
    
    if round(f_bp_1, 2) == round(f_bp_2, 2) and f_bp_2 > f_bp_3:
        print("✅ 物理逻辑符合预期：不加孔时无水头流失，加孔后背板推力显著断崖下跌。")
        sys.exit(0)
    else:
        print("🚨 警告：物理学衰减逻辑异常！")
        sys.exit(1)

if __name__ == '__main__':
    test_calculus()
