comparing a.txt vs b.txt

~~~text
(27 lines match)
    from rdiff.sequence import diff
  
---
<   print(diff(['apples', 'bananas', 'carrots', 'dill'], ['apples', 'carrots', 'dill', 'eggplant']).to_string())
---
>   print(diff(
>       ['apples', 'bananas', 'carrots', 'dill'],
>       ['apples', 'carrots', 'dill', 'eggplant']
>   ).to_string())
---
    ```
  
    ```text
---
<   Diff(0.7500):
---
>   a≈b (ratio=0.7500)
---
≈   ··a[+++0:1+++]=b[+++0:1+++]: ['apples'] = ['apples']
≈   ··a[+++1:2+++]≠b[+++1:1+++]: ['bananas'] ≠ []
≈   ··a[+++2:4+++]=b[+++1:3+++]: ['carrots', 'dill'] = ['carrots', 'dill']
≈   ··a[+++4:4+++]≠b[+++3:4+++]: [] ≠ ['eggplant']
---
    ```
  
(2 lines match)
    from rdiff.sequence import diff_nested
  
---
<   print(diff_nested([0, 1, ["alice", "bob"]], [0, 1, ["alice2", "bob2"]]).to_string())
---
>   print(diff_nested(
>       [0, 1, ["alice", "bob", "charlie", "dan"]],
>       [0, 1, ["alice2", "bob2", "karen", "dan"]]
>   ).to_string())
---
    ```
  
    ```text
---
<   Diff(1.0000):
---
>   a≈b (ratio=1.0000)
>   ··a[0:2]=b[0:2]: [0, 1] = [0, 1]
>   ··a[2:3]≈b[2:3]: [['alice', 'bob', 'charlie', 'dan']] ≈ [['alice2', 'bob2', 'karen', 'dan']]
>   ····a[2]≈b[2] (ratio=0.7500)
---
≈   ··+++····+++a[+++2][0:2+++]≈b[+++2+++]---: ---[0---,---+++:2]:+++ ---1, ---['alice', 'bob']---]--- ≈--- [0, 1,--- ['alice2', 'bob2'---]---]
---
<   ····a=b: 0
<   ····a=b: 1
<   ····Diff(1.0000):
<   ······a[]≈b[]: ['alice', 'bob'] ≈ ['alice2', 'bob2']
<   ········Diff(0.9091):
---
>   ········a[2][0]≈b[2][0] (ratio=0.9091)
---
≈   ··········a[+++2][0][0:5+++]=b[+++2][0][0:5+++]: 'alice' = 'alice'
≈   ··········a[+++2][0][5:5+++]≠b[+++2][0][5:6+++]: '' ≠ '2'
---
<   ········Diff(0.8571):
---
>   ········a[2][1]≈b[2][1] (ratio=0.8571)
---
≈   ··········a[+++2][1][0:3+++]=b[+++2][1][0:3+++]: 'bob' = 'bob'
≈   ··········a[+++2][1][3:3+++]≠b[+++2][1][3:4+++]: '' ≠ '2'
---
>   ······a[2][2:3]≠b[2][2:3]: ['charlie'] ≠ ['karen']
>   ······a[2][3:4]=b[2][3:4]: ['dan'] = ['dan']
---
    ```
  
(18 lines match)
  
  - [ ] text diffs
---
≈ - [--- ---+++x+++] table diffs
---
  
  CLI
(13 lines match)
~~~
