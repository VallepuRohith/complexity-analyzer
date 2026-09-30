class ComplexityResult:

    def __init__(self, time, space, explanation = "", details = None):
        self.time = time
        self.space = space
        self.explanation = explanation
        self.details = details or {}

    def __repr__(self):
        return (
            f"Time Complexity: {self.time}\n"
            f"Space Complexity: {self.space}\n"
            f"Explanation: {self.explanation}"
        )

    def to_dict(self):
        return {
            "time": self.time,
            "space": self.space,
            "explanation": self.explanation,
            "details": self.details
        }