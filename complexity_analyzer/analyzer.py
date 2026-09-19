import ast
import inspect

from .result import ComplexityResult


class ComplexityAnalyzer(ast.NodeVisitor):

    def __init__(self):
        self.loop_depth = 0
        self.max_loop_depth = 0
        self.for_loops = 0
        self.while_loops = 0
        self.logarithmic_loops = 0
        self.dynamic_structures = set()

    def visit_For(self, node):
        self.for_loops += 1
        self.loop_depth += 1

        self.max_loop_depth = max(self.max_loop_depth, self.loop_depth)

        self.generic_visit(node)
        self.loop_depth -= 1

    def visit_While(self, node):
        self.while_loops += 1

        if self.is_logarithm_update(node):
            self.logarithmic_loops += 1
    
        self.loop_depth += 1

        self.max_loop_depth = max(
            self.max_loop_depth, self.loop_depth
        )
        self.generic_visit(node)
        self.loop_depth -= 1

    def visit_Assign(self, node):
        if isinstance(node.value, (ast.List, ast.Dict, ast.Set)):

            for target in node.targets:

                if isinstance(target, ast.Name):
                    self.dynamic_structures.add(target.id)

        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute):

            if node.func.attr in (
                "append",
                "extend",
                "add",
                "update"
            ):

                if isinstance(node.func.value, ast.Name):
                    self.dynamic_structures.add(
                        node.func.value.id
                    )

        self.generic_visit(node)

    def is_logarithm_update(self, node):
        condition_variable = self.get_condition_variable(node)

        updated_variable, operation = self.get_updated_variable(node)

        if condition_variable is None:
            return False

        if updated_variable is None:
            return False

        if condition_variable != updated_variable:
            return False

        return isinstance(
            operation,
            (ast.Mult, ast.Div, ast.FloorDiv)
        )

    def get_condition_variable(self, node):
        condition = node.test

        if isinstance(condition, ast.Compare):
            left = condition.left

            if isinstance(left, ast.Name):
                return left.id

        return None

    def get_updated_variable(self, node):
        for statement in node.body:

            if isinstance(statement, ast.AugAssign):

                if isinstance(statement.target, ast.Name):
                    return statement.target.id, statement.op

        return None, None

def calculate_time_complexity(analyzer):
    if analyzer.logarithmic_loops > 0:
        return "O(log n)"

    depth = analyzer.max_loop_depth
    if depth == 0:
        return "O(1)"
    if depth == 1:
        return "O(n)"
    return f"O(n^{depth})"

def calculate_space_complexity(analyzer):
    if analyzer.dynamic_structures:
        return "O(n)"

    return "O(1)"
    
def analyze(function):
    source = inspect.getsource(function)
    tree = ast.parse(source)

    analyzer = ComplexityAnalyzer()
    analyzer.visit(tree)

    time_complexity = calculate_time_complexity(analyzer)
    space_complexity = calculate_space_complexity(analyzer)
    
    return ComplexityResult(
    time=time_complexity,
    space=space_complexity,
    explanation=(
        f"For loops: {analyzer.for_loops}, "
        f"While loops: {analyzer.while_loops}, "
        f"Logarithmic loops: {analyzer.logarithmic_loops}, "
        f"Dynamic structures: {analyzer.dynamic_structures}"
    )
)