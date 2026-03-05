import math

def calculate_backplate_force(
    rpm: float, 
    p_out_pa: float, 
    p_in_pa: float, 
    rho: float,
    d_impeller_mm: float, 
    d_shaft_mm: float,
    has_seal: bool = False, 
    d_seal_mm: float = 0.0,
    has_impeller_holes: bool = False, 
    n_impeller_holes: int = 0, 
    d_impeller_holes_mm: float = 0.0,
    has_backplate_holes: bool = False, 
    n_backplate_holes: int = 0, 
    d_backplate_holes_mm: float = 0.0,
    p_ambient_pa: float = 101325.0,
    k_factor: float = 0.5
) -> float:
    """
    计算高速离心风机背板所承受的气动轴向力 (N)。
    方向定义：指向入口为正（电机 -> 叶轮方向）。
    
    采用解析积分求解：
    P(r) = P_out - 0.5 * rho * (k*omega)^2 * (R_out^2 - r^2)
    F = integral( P(r) * 2 * pi * r ) dr
    
    平衡孔影响：
    粗略模型下，如果有平衡孔，对应密封腔内的基准压力会被强制拉低。
    如果有叶轮平衡孔，内腔压力近似于 P_in。
    如果有背板平衡孔，内腔压力近似于 P_ambient。
    如果都没有，压力按标准旋转流体分布。
    """
    R_out = (d_impeller_mm / 2.0) / 1000.0
    R_shaft = (d_shaft_mm / 2.0) / 1000.0
    
    if has_seal and d_seal_mm > 0:
        R_inner = (d_seal_mm / 2.0) / 1000.0
    else:
        R_inner = R_shaft
        
    omega = rpm * (2.0 * math.pi / 60.0)
    omega_fluid = k_factor * omega
    
    # 解析积分公式:
    # F = \pi * (R_out^2 - r_inner^2) * (P_out - 0.5 * rho * omega_fluid^2 * R_out^2)
    #     + 0.25 * \pi * rho * omega_fluid^2 * (R_out^4 - r_inner^4)
    term1_pressure_const = p_out_pa - 0.5 * rho * (omega_fluid**2) * (R_out**2)
    force_main_area = math.pi * (R_out**2 - R_inner**2) * term1_pressure_const \
                      + 0.25 * math.pi * rho * (omega_fluid**2) * (R_out**4 - R_inner**4)
                      
    force_inner_cavity = 0.0
    if has_seal and R_inner > R_shaft:
        # 有密封时，密封环内侧到轴之间的面积，承受内腔压力
        cavity_area = math.pi * (R_inner**2 - R_shaft**2)
        if has_impeller_holes:
            p_cavity = p_in_pa
        elif has_backplate_holes:
            p_cavity = p_ambient_pa
        else:
            # 无平衡孔且有密封时，内腔压力近似为流体到达密封处的边界压力减去微小泄漏损失，这里取密封边界处的压力
            p_cavity = p_out_pa - 0.5 * rho * (omega_fluid**2) * (R_out**2 - R_inner**2)
            
        force_inner_cavity = p_cavity * cavity_area
        
    total_backplate_force = force_main_area + force_inner_cavity
    return total_backplate_force

def calculate_total_axial_force(force_blade_and_hub_n: float, force_backplate_n: float) -> float:
    """
    F_total = F_backplate - F_blade_hub
    正值表示合力推向入口。
    """
    return force_backplate_n - force_blade_and_hub_n
