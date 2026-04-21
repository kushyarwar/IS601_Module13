from enum import Enum


class OperationType(str, Enum):
    Add = "Add"
    Sub = "Sub"
    Multiply = "Multiply"
    Divide = "Divide"


class AddOperation:
    def compute(self, a: float, b: float) -> float:
        return a + b


class SubOperation:
    def compute(self, a: float, b: float) -> float:
        return a - b


class MultiplyOperation:
    def compute(self, a: float, b: float) -> float:
        return a * b


class DivideOperation:
    def compute(self, a: float, b: float) -> float:
        if b == 0:
            raise ValueError("Division by zero is not allowed")
        return a / b


class CalculationFactory:
    _registry = {
        OperationType.Add: AddOperation,
        OperationType.Sub: SubOperation,
        OperationType.Multiply: MultiplyOperation,
        OperationType.Divide: DivideOperation,
    }

    @classmethod
    def get_operation(cls, op_type: OperationType):
        operation_class = cls._registry.get(op_type)
        if operation_class is None:
            raise ValueError(f"Unknown operation type: {op_type}")
        return operation_class()

    @classmethod
    def compute(cls, op_type: OperationType, a: float, b: float) -> float:
        return cls.get_operation(op_type).compute(a, b)
