import math

def calculate_backplate_force(
    rpm: float, 
    p_out_gauge_pa: float, 
    p_in_gauge_pa: float, 
    rho: float,
    d_impeller_mm: float, 
    d_shaft_mm: float,
    has_seal2: bool = False, 
    d_seal2_mm: float = 0.0,
    has_balance_holes: bool = False, 
    d_hole_mm: float = 0.0,
    a_hole_cm2: float = 0.0,
    alpha: float = 0.3,
    p_hole_target_pa: float = 101325.0,
    p_ambient_pa: float = 101325.0,
    k_factor: float = 0.15
) -> float:
    """
    计算高速半开式离心风机背板所承受的气动轴向力 (N)。
    方向定义：指向入口为正（电机 -> 叶轮方向）。
    由于 CSV 内记录的轴向力通常为绝对气压合成（甚至在无流量时也承载全大气压推力），
    本函数统一将所有表压转为绝对压力 (P_abs) 再进行面积积分。
    """
    R_out = (d_impeller_mm / 2.0) / 1000.0
    R_in = (d_shaft_mm / 2.0) / 1000.0
    
    # 转绝对压力
    P_out_abs = p_out_gauge_pa + p_ambient_pa
    P_in_abs = p_in_gauge_pa + p_ambient_pa
    
    omega = rpm * (2.0 * math.pi / 60.0)
    omega_fluid = k_factor * omega
    
    # 确定第二道密封的位置 (R_s2)
    R_s2 = (d_seal2_mm / 2.0) / 1000.0 if (has_seal2 and d_seal2_mm > 0) else R_in
    if R_s2 > R_out: R_s2 = R_out
    if R_s2 < R_in:  R_s2 = R_in
    
    # --- 区域1: R_s2 到 R_out (外环主流区，背压直接受出口控制) ---
    # P(r) = P_out_abs - 0.5 * rho * (omega_fluid)^2 * (R_out^2 - r^2)
    term_1_const = P_out_abs - 0.5 * rho * (omega_fluid**2) * (R_out**2)
    F1 = math.pi * (R_out**2 - R_s2**2) * term_1_const \
         + 0.25 * math.pi * rho * (omega_fluid**2) * (R_out**4 - R_s2**4)
         
    # 区域1边界（即密封外侧）的流体压力
    P_at_Rs2 = P_out_abs - 0.5 * rho * (omega_fluid**2) * (R_out**2 - R_s2**2)
    
    # --- 区域2: R_in 到 R_s2 (带有平衡孔衰减的内腔区) ---
    F2 = 0.0
    if R_s2 > R_in:
        # 默认无孔时的自然衰减抛物线尽头：
        P_root_theoretical = P_at_Rs2 - 0.5 * rho * (omega_fluid**2) * (R_s2**2 - R_in**2)
        P_root_actual = P_root_theoretical
        
        # 若有平衡孔，按孔所在圆周处的理论压力进行阻力折减
        if has_balance_holes and a_hole_cm2 > 0 and d_hole_mm > 0:
            R_hole = (d_hole_mm / 2.0) / 1000.0
            # 限制孔位置在腔体内
            if R_hole > R_s2: R_hole = R_s2
            if R_hole < R_in: R_hole = R_in
            
            # 计算该圆周处的理论未泄压压力
            P_hole_theoretical = P_at_Rs2 - 0.5 * rho * (omega_fluid**2) * (R_s2**2 - R_hole**2)
            
            # 使用泄压系数逼进目标压力 (入口或大气)
            relief_ratio = min(1.0, alpha * (a_hole_cm2 / 10.0))
            P_hole_actual = P_hole_theoretical - relief_ratio * (P_hole_theoretical - p_hole_target_pa)
            
            # 锚定此处的实际压力后，再向下推演到根部的压力
            P_root_actual = P_hole_actual - 0.5 * rho * (omega_fluid**2) * (R_hole**2 - R_in**2)
            
        # 根据重置的根部压力 P_root_actual 重新积分此区间
        term_2_const = P_root_actual - 0.5 * rho * (omega_fluid**2) * (R_in**2)
        F2 = math.pi * (R_s2**2 - R_in**2) * term_2_const \
             + 0.25 * math.pi * rho * (omega_fluid**2) * (R_s2**4 - R_in**4)
             
    # --- 最终背板推力 (绝对压力积分) ---
    # 因为叶轮前盖板(Blade+Hub)的受力是 CFX 基于绝对压力给出的积分值，
    # 我们这里也必须维持纯粹的绝对气压积分，不再额外减除背面的大气压(除非有暴露界面)。
    total_backplate_force = F1 + F2
    return total_backplate_force

def calculate_total_axial_force(force_blade_and_hub_n: float, force_backplate_n: float) -> float:
    """
    总轴向合力: 
    force_backplate_n 推向入口（正）
    force_blade_and_hub_n 已经被 data_parser 反转为了负值（即推向电机）
    直接相加即为净合力。
    """
    return force_backplate_n + force_blade_and_hub_n
