from complexity_analyzer import analyze


def test(arr):
    total = 0

    for x in arr:
        total += x

result = analyze(test)

print(result)