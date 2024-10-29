import logging
import inspect
from .const import PITABLE, EMCTABLE


# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(funcName)s - %(message)s')
logger = logging.getLogger(__name__)


# Custom Exceptions
class PreservationError(Exception):
    """Base exception for preservation calculation errors."""
    pass

class HumidityError(PreservationError):
    """Exception for humidity range violations."""
    pass


# Types
Number = Union[int, float]
Temperature = Number
RelativeHumidity = Number
PreservationIndex = float
MoldRisk = float
MoistureContent = float


class EnvironmentalRating(Enum):
    GOOD = "GOOD"
    OK = "OK"
    RISK = "RISK"


def to_celsius(x: emperature, scale: str='f') -> Temperature:
    """Convert temperature to specified scale.

    
    Args:
        x (float / int): Temperature value
        scale (str): Target scale ('f' for Fahrenheit, 'c' for Celsius, 'k' for Kelvin)
    
    Returns:
        Temperature: Converted temperature value

    Raises:
        ValueError: If scale is none of 'f', 'c' or 'k'
    """
    if scale == 'f':
        return float((x * 1.8) + 32.0)
    elif scale == 'c':
        return float(x)
    elif scale == 'k':
        return float(x + 273.15)
    else:
        raise ValueError(f"Unsupported scale '{scale}'")


def validate_rh(rh: RelativeHumidity) -> None:
    """
    Validate relative humidity is between 0 [%] and 100 [%] incluive

    Args:
        rh (int / float)

    Raises:
        HumidityError: If 'rh' is < 0 or 'rh' > 100.
    """
    if not (0 <= rh <= 100):
        raise HumidityError(
            f"Relative humidity must be between {min}% and {max}%, got {rh}%"
        )


def clamp(x: Number, min: Number, max: Number) -> Number:
    """Clamp a value between min and max values.
    
    Args:
        x: Value to clamp
        min: Minimum allowed value
        max: Maximum allowed value
    
    Returns:
        Clamped value between min and max
    """
    # Get the name of the variable from the caller's frame
    frame = inspect.currentframe().f_back
    callargs = frame.f_locals
    # Find the argument name that matches our value
    name = next(k for k, v in callargs.items() if v is x)
        
    caller = frame.f_code.co_name
    
    if x < min:
        logger.info(
            f"{caller}: Clamping {name} from {x} to minimum {min}"
        )
        return min
    elif value > max:
        logger.info(
            f"{caller}: Clamping {name} from {x} to maximum {max}"
        )
        return max
    return x


def temp(rh: RelativeHumidity, td: Temperature) -> Temperature:
    """Calculate temperature given relative humidity and dew point.
    
    Args:
        rh (float / int): Relative humidity (%)
        td (float / int): Dew point temperature
    
    Returns:
        float: Calculated temperature
    """
    validate_rh(rh)
    t_a: float = pow(rh/100, 1/8)
    return (td - (112*t_a) + 112) / ((0.9 * t_a) + 0.1)


def rh(t: Temperature, td: Temperature) -> RelativeHumidity:
    """Calculate relative humidity given temperature and dew point.
    
    Args:
        t (float / int): Temperature
        td (float / int): Dew point temperature
    
    Returns:
        RelativeHumidity: Calculated relative humidity (%)
    """
    return 100 * (pow((112-(0.1*t) + td) / (112 + (0.9 * t)), 8))


def dp(t: Temperature, rh: RelativeHumidity) -> Temperature:
    """Calculate dew point given temperature and relative humidity.
    
    Args:
        t (float / int): Temperature
        rh (float / int): Relative humidity (%)
    
    Returns:
        Temperature: Calculated dew point temperature
    """
    validate_rh(rh)
    t_a: float = pow(rh/100, 1/8)
    return ((112 + (0.9 * t)) * t_a + (0.1 * t)) - 112


def pi(t: Temperature, rh: RelativeHumidity) -> PreservationIndex:
    """
    Calculate Preservation Index (PI) value. PI represents the overall rate of chemical decay in organic materials based on a constant T and RH. A higher number indicates a slower the rate of chemical decay.
    
    Args:
        t: Temperature in Celsius
        rh: Relative Humidity percentage
    
    Returns:
        PI value [years].
        Use rate_natural_aging() to convert PI to Environmental Rating.
    """
    validate_rh(rh)
    clamped_rh = clamp(rh, 6, 95) # Make sure that 6 <= rh <= 95 
    clamped_t = clamp(t, -23, 65) # Make sure that -23 <= rh <= 65
    idx: int = ((round(clamped_t) + 23) * 90) + round(clamped_rh) - 6
    if idx >= len(PITABLE):
        logger.info(f"pi(): PITABLE[{idx}] does not exist, returning 0")
        return 0.0
    return float(PITABLE[idx])


def mold(t: Temperature, rh: RelativeHumidity) -> MoldRisk:
    """Calculate Mold Risk Factor.
    
    Args:
        t: Temperature in Celsius (2 to 45°C for risk calculation)
        rh: Relative Humidity percentage (≥65% for risk calculation)
    
    Returns:
        0 if no risk (t < 2°C or t > 45°C or rh < 65%),
        otherwise returns risk value from lookup table where
        higher values indicate greater mold risk
    """
    validate_rh(rh)
    if t > 45 or t < 2 or rh < 65:
        return 0.0
    idx: int = 8010 + (round(t) - 2) * 36 + round(rh) - 65
    if idx >= len(PITABLE):
        logger.info(f"mold(): PITABLE[{idx}] does not exist, returning 0")
        return 0.0
    return float(PITABLE[idx])


def emc(t: Temperature, rh: RelativeHumidity) -> MoistureContent:
    """Calculate Equilibrium Moisture Content (EMC).
    
    Args:
        t: Temperature in Celsius (-20 to 65°C)
        rh: Relative Humidity percentage (0 to 100%)
    
    Returns:
        EMC value from lookup table as percentage, where:
        - 5% ≤ EMC ≤ 12.5%: OK for mechanical damage
        - EMC < 7.0%: Good for metal corrosion
        - 7.0% ≤ EMC < 10.5%: OK for metal corrosion
        - EMC ≥ 10.5%: Risk for metal corrosion
    """
    validate_rh(rh)
    clamped_t = clamp(t, -20, 65)
    idx: int = round(clamped_t + 20) * 101 + round(rh)
    if idx >= len(EMCTABLE):
        logger.info(f"emc(): EMCTABLE[{idx}] does not exist, returning 0")
        return 0.0
    return float(EMCTABLE[idx])


def rate_natural_aging(pi: PreservationIndex) -> EnvironmentalRating:
    """
    Evaluates Natural Aging risk as a function of PI:
        ≥75: Good
        45-75: OK
        <45: Risk
    """
    if pi >= 75:
        return EnvironmentalRating.GOOD
    elif pi < 45:
        return EnvironmentalRating.RISK
    else:
        return EnvironmentalRating.OK


def rate_mechanical_damage(emc: MoistureContent) -> EnvironmentalRating:
    """
    Evaluates risk of Mechanical Damage as a function of %EMC:
        5-12.5: OK
        <5 or >12.5: Risk
    """
    if 5 <= emc <= 12.5:
        return EnvironmentalRating.OK     
    else:
        return EnvironmentalRating.RISK


def rate_mold_growth(mrf: MoldRisk) -> EnvironmentalRating:
    """
    Evaluates risk  of Mold Growth as a fucntion of Mold Risk Factor:
        0: No Risk
        >0: Risk (value represents days to mold)
    """
    if mrf == 0:
        return EnvironmentalRating.GOOD
    else:
        return EnvironmentalRating.RISK


def rate_metal_corrosion(emc: MoistureContent) -> EnvironmentalRating:
    """
    Evaluates risk of Metal Corrosion as a function of %EMC:
        <7.0: Good
        7.1-10.5: OK
        ≥10.5: Risk
    """
    if emc < 7.0:
        return EnvironmentalRating.GOOD
    elif emc < 10.5:
        return EnvironmentalRating.OK
    else:
        return EnvironmentalRating.RISK
    