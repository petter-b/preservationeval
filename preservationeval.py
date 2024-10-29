from .const import pitable, emctable

def to_deg(x, scale='f'):
    """Convert temperature to specified scale.
    
    Args:
        x (float): Temperature value
        scale (str): Target scale ('f' for Fahrenheit, 'c' for Celsius, 'k' for Kelvin)
    
    Returns:
        float: Converted temperature value
    """
    if scale == 'f':
        return (x * 1.8) + 32.0
    elif scale == 'c':
        return x
    elif scale == 'k':
        return x + 273.15
    return 0

def calculate_temperature(rh, td):
    """Calculate temperature given relative humidity and dew point.
    
    Args:
        rh (float): Relative humidity (%)
        td (float): Dew point temperature
    
    Returns:
        float: Calculated temperature
    """
    t_a = pow(rh/100, 1/8)
    return (td - (112*t_a) + 112) / ((0.9 * t_a) + 0.1)

def calculate_rh(t, td):
    """Calculate relative humidity given temperature and dew point.
    
    Args:
        t (float): Temperature
        td (float): Dew point temperature
    
    Returns:
        float: Calculated relative humidity (%)
    """
    return 100 * (pow((112-(0.1*t) + td) / (112 + (0.9 * t)), 8))

def calculate_dew_point(t, rh):
    """Calculate dew point given temperature and relative humidity.
    
    Args:
        t (float): Temperature
        rh (float): Relative humidity (%)
    
    Returns:
        float: Calculated dew point temperature
    """
    t_a = pow(rh/100, 1/8)
    return ((112 + (0.9 * t)) * t_a + (0.1 * t)) - 112

def evaluate_preservation(t, rh):
    """Evaluate preservation conditions based on temperature and relative humidity.
    
    Evaluates four preservation metrics:
    1. Natural aging (TWPI)
    2. Mechanical damage risk
    3. Mold risk
    4. Metal corrosion risk
    
    Args:
        t (float): Temperature (°C)
        rh (float): Relative humidity (%)
    
    Returns:
        dict: Dictionary containing preservation evaluation results
        
    Ratings interpretation:
    TWPI (Time-Weighted Preservation Index):
        ≥75: Good
        45-75: OK
        <45: Risk
        
    Mechanical Damage (% EMC):
        5-12.5: OK
        <5 or >12.5: Risk
        
    Mold Risk:
        0: No Risk
        >0: Risk (value represents days to mold)
        
    Metal Corrosion (% EMC):
        <7.0: Good
        7.1-10.5: OK
        ≥10.5: Risk
    """
    # Bound input values
    t = max(-20, min(65, round(t)))
    rh = max(0, min(100, round(rh)))
    
    # Calculate EMC (Equilibrium Moisture Content)
    emc_idx = (t + 20) * 101 + round(rh)
    emc = emctable[emc_idx] if emc_idx < len(emctable) else 0
    
    # Calculate PI (Preservation Index)
    pi_idx = ((max(-23, min(65, round(t))) + 23) * 90 + 
             (max(6, min(95, round(rh)))) - 6)
    pi = pitable[pi_idx] if pi_idx < len(pitable) else 0
    
    # Calculate Mold Risk
    mold_risk = 0
    if 2 <= t <= 45 and rh >= 65:
        mold_idx = 8010 + (round(t) - 2) * 36 + round(rh) - 65
        mold_risk = pitable[mold_idx] if mold_idx < len(pitable) else 0
    
    return {
        'twpi': {
            'value': pi,
            'rating': 'GOOD' if pi >= 75 else 'OK' if pi >= 45 else 'RISK'
        },
        'mechanical_damage': {
            'value': emc,
            'rating': 'OK' if 5 <= emc <= 12.5 else 'RISK'
        },
        'mold_risk': {
            'value': mold_risk,
            'rating': 'GOOD' if mold_risk == 0 else 'RISK'
        },
        'metal_corrosion': {
            'value': emc,
            'rating': 'GOOD' if emc < 7.0 else 'OK' if emc < 10.5 else 'RISK'
        }
    }
