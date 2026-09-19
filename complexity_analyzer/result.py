class ComplexityResult:

    def __init__(self, time, space, explanation = ""):
        self.time = time
        self.space = space
        self.explanation = explanation

    def __repr__(self):
        return (
            f"Time Complexity: {self.time}\n"
            f"Space Complexity: {self.space}\n"
            f"Explanation: {self.explanation}"
        )