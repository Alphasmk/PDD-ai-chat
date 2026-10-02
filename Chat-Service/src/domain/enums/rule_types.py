from enum import StrEnum

class RuleType(StrEnum):
    TRAFFIC_LIGHT = "traffic_light"
    RULE = "rule"
    SIGN = "sign"
    MARKING = "marking"
    IDENTIFICATION_SIGN = "identification_sign"