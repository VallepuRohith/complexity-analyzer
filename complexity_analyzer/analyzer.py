import ast
import inspect

from .result import ComplexityResult


class ComplexityAnalyzer(ast.NodeVisitor):

    def __init__(self, input_variables):
        self.input_variables = set(input_variables)

        self.variables = {}

        self.loop_depth = 0
        self.max_loop_depth = 0

        self.for_loops = 0
        self.while_loops = 0
        self.logarithmic_loops = 0

        # self.dynamic_structures = set()
        # self.constant_structures = set()
        self.allocations = []


    def record_allocation(
        self,
        variable,
        complexity,
        reason,
        retained=True
    ):
        self.allocations.append({
            "variable": variable,
            "complexity": complexity,
            "reason": reason,
            "loop_depth": self.loop_depth,
            "retained": retained
        })


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

        for target in node.targets:

            if not isinstance(target, ast.Name):
                continue

            variable = target.id

            if isinstance(node.value, (ast.List, ast.Dict, ast.Set)):

                if self.depends_on_input(node.value):

                    complexity = "O(n)"
                    reason = "Collection size depends on input"

                else:

                    complexity = "O(1)"
                    reason = "Constant-size collection"

                self.variables[variable] = complexity

                self.record_allocation(
                    variable,
                    complexity,
                    reason
                    retained = False
                )

            elif isinstance(node.value, ast.BinOp):

                if isinstance(node.value.op, ast.Mult):

                    if self.depends_on_input(node.value):

                        complexity = "O(n)"
                        reason = "Collection size depends on input"

                    else:

                        complexity = "O(1)"
                        reason = "Constant-size multiplication"

                    self.variables[variable] = complexity

                    self.record_allocation(
                        variable,
                        complexity,
                        reason
                    )

        self.generic_visit(node)


    def visit_Call(self, node):

        if isinstance(node.func, ast.Attribute):

            method = node.func.attr

            if method in (
                "append",
                "extend",
                "add",
                "update"
            ):

                if isinstance(node.func.value, ast.Name):

                    collection = node.func.value.id

                    if node.args:

                        value = node.args[0]

                        if isinstance(value, ast.Name):

                            variable = value.id

                            if variable in self.variables:

                                self.allocations.append({
                                    "variable": variable,
                                    "complexity":
                                        self.variables[variable],
                                    "reason":
                                        f"Retained by {collection}.{method}()",
                                    "loop_depth":
                                        self.loop_depth,
                                    "retained": True
                                })

        self.generic_visit(node)


    def visit_FunctionDef(self, node):

        for argument in node.args.args:
            self.input_variables.add(argument.arg)

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
    

    def depends_on_input(self, node):
        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                if child.id in self.input_variables:
                    return True

        return False


def is_retained_by_collection(self, variable, node):
    parent = getattr(node, "parent", None)

    if parent is None:
        return False

    if isinstance(parent, ast.Call):

        if isinstance(parent.func, ast.Attribute):

            if parent.func.attr in (
                "append",
                "extend",
                "add"
            ):
                return True

    return False
    
    
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

    for allocation in analyzer.allocations:

        if allocation["retained"]:

            if allocation["complexity"] == "O(n)":
                return "O(n^2)"

    for allocation in analyzer.allocations:

        if allocation["complexity"] == "O(n)":
            return "O(n)"

    return "O(1)"
    
def analyze(function):
    source = inspect.getsource(function)

    tree = ast.parse(source)

    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            child.parent = parent

    signature = inspect.signature(function)

    input_variables = signature.parameters.keys()

    analyzer = ComplexityAnalyzer(input_variables)

    analyzer.visit(tree)

    print("Inputs:", analyzer.input_variables)
    print("Allocations:")

    for allocation in analyzer.allocations:
        print(allocation)

    time_complexity = calculate_time_complexity(analyzer)

    space_complexity = calculate_space_complexity(analyzer)

    return ComplexityResult(
        time=time_complexity,
        space=space_complexity,
        explanation="Analysis completed."
    )