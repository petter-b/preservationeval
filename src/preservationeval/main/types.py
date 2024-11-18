"""Type definitions for preservation calculations.

This module defines domain-specific types used throughout
the package for preservation environment calculations.

Types:
    Temperature: Type for temperature values in Celsius
    RelativeHumidity: Type for RH values in percent
    PreservationIndex: Type for PI values in years
    MoldRisk: Type for mold risk factor values
    MoistureContent: Type for EMC values in percent
"""

from typing import Annotated

# Domain-specific types with documentation
Temperature = Annotated[float, "Temperature in Celsius"]
RelativeHumidity = Annotated[float, "Relative Humidity in %"]
PreservationIndex = Annotated[int, "PI value in years"]
MoldRisk = Annotated[float, "Mold risk factor"]
MoistureContent = Annotated[float, "EMC value in %"]
