from complexity_analyzer import analyze, analyze_code


def test(arr):
    for x in arr:
        temp = [0] * len(arr)
    return 0


# 1. Original sample function test
result = analyze(test)
print("Original test result:")
print(result)
assert result.time == "O(n)", f"Expected O(n), got {result.time}"
assert result.space == "O(n^2)", f"Expected O(n^2), got {result.space}"

# 2. Single loop with constant range(10) -> O(1)
res_const = analyze_code("for i in range(10):\n    print(i)")
print("\nConstant range(10):", res_const.time, res_const.space)
assert res_const.time == "O(1)", f"Expected O(1), got {res_const.time}"
assert res_const.space == "O(1)", f"Expected O(1), got {res_const.space}"

# 3. Nested loops with constant ranges -> O(1)
res_nested_const = analyze_code("for i in range(10):\n    for j in range(5):\n        print(i, j)")
print("Nested constant range(10), range(5):", res_nested_const.time, res_nested_const.space)
assert res_nested_const.time == "O(1)", f"Expected O(1), got {res_nested_const.time}"
assert res_nested_const.space == "O(1)", f"Expected O(1), got {res_nested_const.space}"

# 4. Outer input loop, inner constant loop -> O(n)
res_outer_input = analyze_code("for i in range(n):\n    for j in range(10):\n        print(i, j)")
print("Outer range(n), inner range(10):", res_outer_input.time, res_outer_input.space)
assert res_outer_input.time == "O(n)", f"Expected O(n), got {res_outer_input.time}"

# 5. Outer constant loop, inner input loop -> O(n)
res_inner_input = analyze_code("for i in range(10):\n    for j in range(n):\n        print(i, j)")
print("Outer range(10), inner range(n):", res_inner_input.time, res_inner_input.space)
assert res_inner_input.time == "O(n)", f"Expected O(n), got {res_inner_input.time}"

# 6. Nested input loops -> O(n^2)
res_nested_input = analyze_code("for i in range(n):\n    for j in range(n):\n        print(i, j)")
print("Nested input range(n), range(n):", res_nested_input.time, res_nested_input.space)
assert res_nested_input.time == "O(n^2)", f"Expected O(n^2), got {res_nested_input.time}"

# 7. Inner loop bounded by outer constant loop variable -> O(1)
res_dep_on_const = analyze_code("for i in range(10):\n    for j in range(i):\n        print(i, j)")
print("Inner range(i) where i in range(10):", res_dep_on_const.time, res_dep_on_const.space)
assert res_dep_on_const.time == "O(1)", f"Expected O(1), got {res_dep_on_const.time}"

# 8. Inner loop bounded by outer input loop variable -> O(n^2)
res_dep_on_input = analyze_code("for i in range(n):\n    for j in range(i):\n        print(i, j)")
print("Inner range(i) where i in range(n):", res_dep_on_input.time, res_dep_on_input.space)
assert res_dep_on_input.time == "O(n^2)", f"Expected O(n^2), got {res_dep_on_input.time}"

# 9. Constant while loop -> O(1)
res_while_const = analyze_code("i = 0\nwhile i < 10:\n    print(i)\n    i += 1")
print("Constant while loop i < 10:", res_while_const.time, res_while_const.space)
assert res_while_const.time == "O(1)", f"Expected O(1), got {res_while_const.time}"

# 10. Depth 3 loops with 2 input and 1 constant -> O(n^2)
res_depth3 = analyze_code("for i in range(n):\n    for j in range(n):\n        for k in range(10):\n            print(i, j, k)")
print("Depth 3 (n, n, 10):", res_depth3.time, res_depth3.space)
assert res_depth3.time == "O(n^2)", f"Expected O(n^2), got {res_depth3.time}"

print("\nAll unit tests passed successfully!")