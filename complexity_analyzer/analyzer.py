import ast
import inspect
import re

from .result import ComplexityResult


class ComplexityAnalyzer(ast.NodeVisitor):

    def __init__(self, input_variables=None):
        self.input_variables = set(input_variables or [])
        self.input_dependent_vars = set(self.input_variables)
        self.constant_vars = set()
        self.variables = {}

        self.loop_depth = 0
        self.max_loop_depth = 0

        self.input_loop_depth = 0
        self.max_input_loop_depth = 0

        self.for_loops = 0
        self.while_loops = 0
        self.constant_loops = 0
        self.logarithmic_loops = 0

        self.allocations = []
        self.current_function = None
        self.recursive_calls = 0
        self.recursive_branching = 0
        self.logarithmic_recursion = False

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

    def depends_on_input(self, node):
        if node is None:
            return False

        if isinstance(node, ast.Constant):
            return False

        if isinstance(node, ast.Name):
            if node.id in self.input_variables or node.id in self.input_dependent_vars:
                return True
            return False

        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                fname = node.func.id
                if fname in ("range", "len", "enumerate", "reversed", "zip"):
                    return any(self.depends_on_input(arg) for arg in node.args)

        if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            return any(self.depends_on_input(elt) for elt in node.elts)

        if isinstance(node, ast.BinOp):
            return self.depends_on_input(node.left) or self.depends_on_input(node.right)

        if isinstance(node, ast.UnaryOp):
            return self.depends_on_input(node.operand)

        if isinstance(node, ast.Compare):
            return self.depends_on_input(node.left) or any(self.depends_on_input(c) for c in node.comparators)

        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                if child.id in self.input_variables or child.id in self.input_dependent_vars:
                    return True
        return False

    def is_loop_iter_dependent_on_input(self, iter_node):
        # Literal collections have fixed length (constant number of iterations)
        if isinstance(iter_node, (ast.List, ast.Tuple, ast.Set)):
            return False

        if isinstance(iter_node, ast.Constant):
            return False

        if isinstance(iter_node, ast.Call) and isinstance(iter_node.func, ast.Name):
            if iter_node.func.id == "range":
                return any(self.depends_on_input(arg) for arg in iter_node.args)
            if iter_node.func.id in ("enumerate", "reversed") and iter_node.args:
                return self.is_loop_iter_dependent_on_input(iter_node.args[0])

        if isinstance(iter_node, ast.Name):
            return iter_node.id in self.input_variables or iter_node.id in self.input_dependent_vars

        return self.depends_on_input(iter_node)

    def visit_FunctionDef(self, node):
        prev_func = self.current_function
        self.current_function = node.name

        for argument in node.args.args:
            self.input_variables.add(argument.arg)
            self.input_dependent_vars.add(argument.arg)

        # Count recursive calls within this function
        func_calls = 0
        is_log_rec = False
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                target_name = None
                if isinstance(child.func, ast.Name):
                    target_name = child.func.id
                elif isinstance(child.func, ast.Attribute) and child.func.attr == node.name:
                    target_name = node.name
                
                if target_name == node.name:
                    func_calls += 1
                    # Check for logarithmic step in recursion (e.g., n // 2)
                    for arg in child.args:
                        if isinstance(arg, ast.BinOp) and isinstance(arg.op, (ast.Div, ast.FloorDiv)):
                            is_log_rec = True

        if func_calls > 0:
            self.recursive_calls = max(self.recursive_calls, func_calls)
            self.recursive_branching = max(self.recursive_branching, func_calls)
            if is_log_rec:
                self.logarithmic_recursion = True

        self.generic_visit(node)
        self.current_function = prev_func

    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)

    def visit_For(self, node):
        self.for_loops += 1
        self.loop_depth += 1
        self.max_loop_depth = max(self.max_loop_depth, self.loop_depth)

        is_input_loop = self.is_loop_iter_dependent_on_input(node.iter)

        for name_node in ast.walk(node.target):
            if isinstance(name_node, ast.Name) and isinstance(name_node.ctx, ast.Store):
                if is_input_loop:
                    self.input_dependent_vars.add(name_node.id)
                    self.constant_vars.discard(name_node.id)
                else:
                    self.constant_vars.add(name_node.id)
                    self.input_dependent_vars.discard(name_node.id)

        if is_input_loop:
            self.input_loop_depth += 1
            self.max_input_loop_depth = max(self.max_input_loop_depth, self.input_loop_depth)
        else:
            self.constant_loops += 1

        self.generic_visit(node)

        if is_input_loop:
            self.input_loop_depth -= 1
        self.loop_depth -= 1

    def visit_While(self, node):
        self.while_loops += 1
        self.loop_depth += 1
        self.max_loop_depth = max(self.max_loop_depth, self.loop_depth)

        is_input_loop = self.depends_on_input(node.test)
        is_log = False

        if is_input_loop:
            is_log = self.is_logarithm_update(node)
            if is_log:
                self.logarithmic_loops += 1
            else:
                self.input_loop_depth += 1
                self.max_input_loop_depth = max(self.max_input_loop_depth, self.input_loop_depth)
        else:
            self.constant_loops += 1

        self.generic_visit(node)

        if is_input_loop and not is_log:
            self.input_loop_depth -= 1
        self.loop_depth -= 1

    def visit_Assign(self, node):
        is_dep = self.depends_on_input(node.value)
        for target in node.targets:
            for name_node in ast.walk(target):
                if isinstance(name_node, ast.Name) and isinstance(name_node.ctx, ast.Store):
                    var_name = name_node.id
                    if is_dep:
                        self.input_dependent_vars.add(var_name)
                        self.constant_vars.discard(var_name)
                    else:
                        self.constant_vars.add(var_name)
                        self.input_dependent_vars.discard(var_name)

            if isinstance(target, ast.Name):
                variable = target.id

                # List/Dict/Set literal or comprehension
                if isinstance(node.value, (ast.List, ast.Dict, ast.Set, ast.ListComp, ast.DictComp, ast.SetComp)):
                    if is_dep:
                        complexity = "O(n)"
                        reason = "Collection size depends on input"
                    else:
                        complexity = "O(1)"
                        reason = "Constant-size collection"

                    self.variables[variable] = complexity
                    self.record_allocation(
                        variable,
                        complexity,
                        reason,
                        retained=(self.input_loop_depth > 0)
                    )

                elif isinstance(node.value, ast.BinOp) and isinstance(node.value.op, ast.Mult):
                    if is_dep:
                        complexity = "O(n)"
                        reason = "Collection size depends on input"
                    else:
                        complexity = "O(1)"
                        reason = "Constant-size multiplication"

                    self.variables[variable] = complexity
                    self.record_allocation(
                        variable,
                        complexity,
                        reason,
                        retained=(self.input_loop_depth > 0)
                    )

                elif isinstance(node.value, ast.Call):
                    # Collection constructors e.g. list(range(n)), set(...)
                    is_col = False
                    if isinstance(node.value.func, ast.Name) and node.value.func.id in ("list", "dict", "set", "bytearray"):
                        is_col = True

                    if is_col and is_dep:
                        complexity = "O(n)"
                        reason = "Allocated collection depends on input"
                        self.variables[variable] = complexity
                        self.record_allocation(
                            variable,
                            complexity,
                            reason,
                            retained=(self.input_loop_depth > 0)
                        )

        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute):
            method = node.func.attr
            if method in ("append", "extend", "add", "update"):
                if isinstance(node.func.value, ast.Name):
                    collection = node.func.value.id
                    if node.args:
                        value = node.args[0]
                        if isinstance(value, ast.Name):
                            variable = value.id
                            if variable in self.variables:
                                self.allocations.append({
                                    "variable": variable,
                                    "complexity": self.variables[variable],
                                    "reason": f"Retained by {collection}.{method}()",
                                    "loop_depth": self.loop_depth,
                                    "retained": (self.input_loop_depth > 0)
                                })
                        elif self.depends_on_input(value):
                            self.allocations.append({
                                "variable": collection,
                                "complexity": "O(n)",
                                "reason": f"Input-dependent element appended to {collection}",
                                "loop_depth": self.loop_depth,
                                "retained": (self.input_loop_depth > 0)
                            })

        self.generic_visit(node)

    def is_logarithm_update(self, node):
        # 1. Check for binary search / halving assignment
        for child in ast.walk(node):
            if isinstance(child, ast.Assign) and isinstance(child.value, ast.BinOp):
                if isinstance(child.value.op, (ast.Div, ast.FloorDiv, ast.RShift)):
                    return True

        # 2. Check for augassign: n //= 2, n /= 2, n *= 2, n >>= 1
        condition_variable = self.get_condition_variable(node)
        for statement in ast.walk(node):
            if isinstance(statement, ast.AugAssign):
                if isinstance(statement.op, (ast.Mult, ast.Div, ast.FloorDiv, ast.RShift, ast.LShift)):
                    if condition_variable is None or (isinstance(statement.target, ast.Name) and statement.target.id == condition_variable):
                        return True
            elif isinstance(statement, ast.Assign):
                if isinstance(statement.value, ast.BinOp) and isinstance(statement.value.op, (ast.Mult, ast.Div, ast.FloorDiv, ast.RShift, ast.LShift)):
                    if condition_variable is None or any(isinstance(t, ast.Name) and t.id == condition_variable for t in statement.targets):
                        return True

        return False

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

    def get_details(self):
        return {
            "input_variables": list(self.input_variables),
            "max_loop_depth": self.max_loop_depth,
            "max_input_loop_depth": self.max_input_loop_depth,
            "for_loops": self.for_loops,
            "while_loops": self.while_loops,
            "constant_loops": self.constant_loops,
            "logarithmic_loops": self.logarithmic_loops,
            "recursive_calls": self.recursive_calls,
            "recursive_branching": self.recursive_branching,
            "allocations": self.allocations,
            "variables": self.variables
        }


def is_retained_by_collection(self, variable, node):
    parent = getattr(node, "parent", None)
    if parent is None:
        return False

    if isinstance(parent, ast.Call):
        if isinstance(parent.func, ast.Attribute):
            if parent.func.attr in ("append", "extend", "add"):
                return True

    return False


def calculate_time_complexity(analyzer):
    if getattr(analyzer, "recursive_branching", 0) >= 2:
        return "O(2^n)"
    elif getattr(analyzer, "recursive_calls", 0) >= 1:
        if getattr(analyzer, "logarithmic_recursion", False):
            return "O(log n)"
        return "O(n)"

    input_depth = getattr(analyzer, "max_input_loop_depth", 0)
    log_loops = getattr(analyzer, "logarithmic_loops", 0)

    if log_loops > 0:
        if input_depth == 0:
            if log_loops == 1:
                return "O(log n)"
            return f"O(log^{log_loops} n)"
        elif input_depth == 1:
            if log_loops == 1:
                return "O(n log n)"
            return f"O(n log^{log_loops} n)"
        else:
            if log_loops == 1:
                return f"O(n^{input_depth} log n)"
            return f"O(n^{input_depth} log^{log_loops} n)"

    if input_depth == 0:
        return "O(1)"
    if input_depth == 1:
        return "O(n)"
    return f"O(n^{input_depth})"


def calculate_space_complexity(analyzer):
    for allocation in analyzer.allocations:
        if allocation.get("retained", False):
            if allocation.get("complexity") == "O(n)":
                return "O(n^2)"

    for allocation in analyzer.allocations:
        if allocation.get("complexity") == "O(n)":
            return "O(n)"

    if getattr(analyzer, "recursive_calls", 0) > 0:
        if getattr(analyzer, "logarithmic_recursion", False):
            return "O(log n)"
        return "O(n)"

    return "O(1)"


def generate_explanation(analyzer, time_comp, space_comp):
    t_exps = []
    if getattr(analyzer, "recursive_branching", 0) >= 2:
        t_exps.append(f"Multiple recursive branches detected (branching factor {analyzer.recursive_branching}), creating an exponential call tree -> {time_comp}.")
    elif getattr(analyzer, "recursive_calls", 0) >= 1:
        if getattr(analyzer, "logarithmic_recursion", False):
            t_exps.append(f"Divide-and-conquer recursive call reducing subproblem size logarithmically -> {time_comp}.")
        else:
            t_exps.append(f"Single recursive call reducing problem size linearly -> {time_comp}.")
    elif analyzer.max_loop_depth == 0:
        t_exps.append(f"No loops or recursion detected; statements execute sequentially in constant time -> {time_comp}.")
    elif analyzer.max_input_loop_depth == 0 and analyzer.logarithmic_loops == 0:
        if analyzer.max_loop_depth == 1:
            t_exps.append(f"Loop iterates a fixed/constant number of times (independent of input size) -> {time_comp}.")
        else:
            t_exps.append(f"{analyzer.max_loop_depth} levels of nested loops iterate a fixed/constant number of times (independent of input size) -> {time_comp}.")
    elif analyzer.logarithmic_loops > 0:
        if analyzer.max_input_loop_depth == 0:
            t_exps.append(f"Loop iterates with logarithmic step updates (halving or doubling variable) -> {time_comp}.")
        else:
            t_exps.append(f"Combines {analyzer.max_input_loop_depth} linear loop(s) with {analyzer.logarithmic_loops} logarithmic loop(s) -> {time_comp}.")
    elif analyzer.max_input_loop_depth == 1:
        if analyzer.max_loop_depth == 1:
            t_exps.append(f"Single loop iterating across the input elements -> {time_comp}.")
        else:
            t_exps.append(f"{analyzer.max_loop_depth} nested loop levels ({analyzer.max_input_loop_depth} input-dependent, {analyzer.max_loop_depth - analyzer.max_input_loop_depth} constant-bound) -> {time_comp}.")
    else:
        if analyzer.max_input_loop_depth == analyzer.max_loop_depth:
            t_exps.append(f"{analyzer.max_loop_depth} levels of nested loops iterating across input size n -> {time_comp}.")
        else:
            t_exps.append(f"{analyzer.max_loop_depth} nested loop levels ({analyzer.max_input_loop_depth} input-dependent, {analyzer.max_loop_depth - analyzer.max_input_loop_depth} constant-bound) -> {time_comp}.")

    s_exps = []
    retained_n = [a for a in analyzer.allocations if a.get("retained") and a.get("complexity") == "O(n)"]
    normal_n = [a for a in analyzer.allocations if a.get("complexity") == "O(n)"]

    if retained_n:
        names = ", ".join(f"'{a['variable']}'" for a in retained_n)
        s_exps.append(f"Collection(s) {names} of size O(n) allocated inside input-dependent loop and retained in memory -> {space_comp}.")
    elif normal_n:
        names = ", ".join(f"'{a['variable']}'" for a in normal_n)
        s_exps.append(f"Dynamic memory allocated for {names} proportional to input size -> {space_comp}.")
    elif getattr(analyzer, "recursive_calls", 0) > 0:
        s_exps.append(f"Stack frames allocated on the call stack scale with recursion depth -> {space_comp}.")
    else:
        s_exps.append(f"Only constant auxiliary primitive variables used, no dynamically scaling allocations -> {space_comp}.")

    return f"Time: {' '.join(t_exps)} Space: {' '.join(s_exps)}"


def _sanitize_code_comments(code: str) -> str:
    """Pre-processes code to handle C-style comments like // paste your code."""
    lines = code.splitlines()
    sanitized = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("//"):
            sanitized.append("#" + stripped[2:])
        else:
            # If line has ; // (C-style comment after statement)
            if "; //" in line or ";//" in line:
                idx = line.find("//")
                sanitized.append(line[:idx] + "# " + line[idx+2:])
            else:
                sanitized.append(line)
    return "\n".join(sanitized)


def _heuristic_analyze_generic_code(code: str) -> ComplexityResult:
    """Fallback complexity analyzer for C++/Java/JavaScript or non-standard syntax."""
    lines = code.splitlines()
    loop_stack = []
    max_depth = 0
    max_input_depth = 0
    log_loops = 0
    constant_loops = 0
    recursions = 0
    for_count = 0
    while_count = 0
    has_dynamic_alloc = False
    retained_in_loop = False

    # Check for recursive function calls
    func_match = re.search(r'(?:def|function|void|int|double|float|auto|public|private)\s+([a-zA-Z_]\w*)\s*\(', code)
    if func_match:
        func_name = func_match.group(1)
        calls = len(re.findall(r'\b' + re.escape(func_name) + r'\s*\(', code)) - 1
        if calls > 0:
            recursions = calls

    for line in lines:
        cleaned = re.sub(r'//.*$|/\*.*?\*/', '', line).strip()
        if not cleaned:
            continue

        is_for = bool(re.search(r'\bfor\s*\(', cleaned) or re.search(r'\bfor\s+\w+\s+in\b', cleaned))
        is_while = bool(re.search(r'\bwhile\s*\(', cleaned) or re.search(r'\bwhile\s+', cleaned))

        if is_for or is_while:
            if is_for:
                for_count += 1
            else:
                while_count += 1

            # Check if this loop is constant-bounded
            # e.g. for (int i = 0; i < 10; i++), for (i in range(10)), while (i < 10)
            is_constant = bool(
                re.search(r'\bfor\s*\([^;]*;\s*[\w\.\->]+\s*(?:<|<=|>|>=|!=|==)\s*\d+\s*;', cleaned) or
                re.search(r'\bfor\s*\([^)]*[:\bof\b]\s*[\{\[]', cleaned) or
                re.search(r'\bfor\s+\w+\s+in\s+range\s*\(\s*\d+\s*(?:,\s*\d+\s*)*\)', cleaned) or
                re.search(r'\bwhile\s*\(\s*[\w\.\->]+\s*(?:<|<=|>|>=|!=|==)\s*\d+\s*\)', cleaned)
            )

            is_log = bool(re.search(r'(/=|\*=|>>=|<<=|/ 2|\* 2)', cleaned))

            if is_constant:
                constant_loops += 1
                loop_stack.append("constant")
            elif is_log:
                log_loops += 1
                loop_stack.append("log")
            else:
                loop_stack.append("linear")

            max_depth = max(max_depth, len(loop_stack))
            current_input_depth = sum(1 for k in loop_stack if k == "linear")
            max_input_depth = max(max_input_depth, current_input_depth)

        if re.search(r'\b(new\s+\w+|malloc|vector|ArrayList|List<|Set<|Map<|append|push_back)', cleaned):
            has_dynamic_alloc = True
            if any(k in ("linear", "log") for k in loop_stack):
                retained_in_loop = True

        if '}' in cleaned:
            num_close = cleaned.count('}')
            for _ in range(num_close):
                if loop_stack:
                    loop_stack.pop()

    # Calculate Time
    if recursions >= 2:
        time_c = "O(2^n)"
    elif recursions == 1:
        time_c = "O(n)"
    elif log_loops > 0:
        if max_input_depth == 0:
            time_c = "O(log n)"
        elif max_input_depth == 1:
            time_c = "O(n log n)"
        else:
            time_c = f"O(n^{max_input_depth} log n)"
    elif max_input_depth == 0:
        time_c = "O(1)"
    elif max_input_depth == 1:
        time_c = "O(n)"
    else:
        time_c = f"O(n^{max_input_depth})"

    # Calculate Space
    if retained_in_loop:
        space_c = "O(n^2)"
    elif has_dynamic_alloc or recursions > 0:
        space_c = "O(n)"
    else:
        space_c = "O(1)"

    if max_depth == 0:
        explanation = f"Generic Code Analysis: No loops detected -> {time_c}."
    elif max_input_depth == 0 and log_loops == 0:
        if max_depth == 1:
            explanation = f"Generic Code Analysis: Loop iterates a constant number of times -> {time_c}."
        else:
            explanation = f"Generic Code Analysis: {max_depth} nested loop level(s) iterate a constant number of times -> {time_c}."
    else:
        explanation = f"Generic Code Analysis: Identified {max_depth} loop level(s) ({max_input_depth} input-dependent, {constant_loops} constant), {for_count} for-loop(s), {while_count} while-loop(s), {log_loops} logarithmic loop(s)."
    if has_dynamic_alloc:
        explanation += " Detected dynamic memory allocation."
    if recursions > 0:
        explanation += f" Detected {recursions} recursive branch(es)."

    details = {
        "input_variables": ["n"] if max_input_depth > 0 else [],
        "max_loop_depth": max_depth,
        "max_input_loop_depth": max_input_depth,
        "for_loops": for_count,
        "while_loops": while_count,
        "constant_loops": constant_loops,
        "logarithmic_loops": log_loops,
        "recursive_calls": recursions,
        "allocations": [{"variable": "heap", "complexity": "O(n)", "reason": "Dynamic structure", "loop_depth": max_depth, "retained": retained_in_loop}] if has_dynamic_alloc else [],
        "variables": {}
    }

    return ComplexityResult(
        time=time_c,
        space=space_c,
        explanation=explanation,
        details=details
    )


def analyze_code(source_code: str) -> ComplexityResult:
    if not source_code or not source_code.strip():
        return ComplexityResult(
            time="O(1)",
            space="O(1)",
            explanation="No code provided.",
            details={"max_loop_depth": 0, "max_input_loop_depth": 0, "for_loops": 0, "while_loops": 0, "constant_loops": 0, "allocations": []}
        )

    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        # Try sanitizing C-style // comments
        sanitized = _sanitize_code_comments(source_code)
        try:
            tree = ast.parse(sanitized)
        except SyntaxError:
            # Fallback to generic analysis for C++/Java/JavaScript or non-Python code
            return _heuristic_analyze_generic_code(source_code)

    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            child.parent = parent

    # Extract input variables from function or free variables
    input_vars = set()
    has_func = False
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            has_func = True
            for arg in node.args.args:
                input_vars.add(arg.arg)

    if not has_func:
        # Standalone code snippet: infer inputs from loaded but unassigned variables
        assigned = set()
        loaded = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                if isinstance(node.ctx, ast.Store):
                    assigned.add(node.id)
                elif isinstance(node.ctx, ast.Load):
                    loaded.add(node.id)
        builtins = {'range', 'len', 'print', 'int', 'float', 'str', 'list', 'dict', 'set', 'min', 'max', 'sum', 'enumerate', 'zip'}
        candidate_inputs = (loaded - assigned) - builtins
        input_vars = candidate_inputs

    analyzer = ComplexityAnalyzer(input_vars)
    analyzer.visit(tree)

    time_complexity = calculate_time_complexity(analyzer)
    space_complexity = calculate_space_complexity(analyzer)
    explanation = generate_explanation(analyzer, time_complexity, space_complexity)

    return ComplexityResult(
        time=time_complexity,
        space=space_complexity,
        explanation=explanation,
        details=analyzer.get_details()
    )


def _analyze_function(function):
    source = inspect.getsource(function)
    tree = ast.parse(source)

    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            child.parent = parent

    signature = inspect.signature(function)
    input_variables = signature.parameters.keys()

    analyzer = ComplexityAnalyzer(input_variables)
    analyzer.visit(tree)

    time_complexity = calculate_time_complexity(analyzer)
    space_complexity = calculate_space_complexity(analyzer)
    explanation = generate_explanation(analyzer, time_complexity, space_complexity)

    return ComplexityResult(
        time=time_complexity,
        space=space_complexity,
        explanation=explanation,
        details=analyzer.get_details()
    )


def analyze(target):
    if callable(target):
        return _analyze_function(target)
    elif isinstance(target, str):
        return analyze_code(target)
    else:
        raise TypeError(f"Expected function or code string, got {type(target).__name__}")