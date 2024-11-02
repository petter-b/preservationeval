# With numpy (even cleaner):
emc_table_np = np.array(emctable).reshape(86, 101)

def emc_np(t: float, rh: float) -> float:
    """Calculate EMC using numpy 2D array."""
    t_idx = clamp(round(t), -20, 65) + 20
    rh_idx = clamp(round(rh), 0, 100)
    
    return emc_table_np[t_idx, rh_idx]

pi_table_np = np.array(pitable).reshape(89, 90)

def pi_np(t: float, rh: float) -> float:
    """Calculate PI using numpy 2D array."""
    t_idx = clamp(round(t), -23, 65) + 23
    rh_idx = clamp(round(rh), 6, 95) - 6
    
    return pi_table_np[t_idx, rh_idx]