# ask_question

**Kind**: `function`  
**File**: `mathsquiz/mathsquiz-step2.py`  
**Lines**: 8–20  
**Betweenness Centrality**: 0.0000  
**In-degree**: 0 | **Out-degree**: 0

## Source

```python
def ask_question(first_number, second_number):
    print("What is", first_number, "x", second_number)
    answer = input("Answer: ")
    if int(answer) == first_number * second_number:
        print("Correct!")
        points_awarded = 1
    else:
        print("Wrong!")
        points_awarded = 0

    print("")

    return points_awarded
```

## Outgoing Relationships

_None — this node has no outgoing edges._

## Incoming Relationships

_None — this node has no incoming edges._
