comparing tests/test_presentation/cases/co2_emissions/diff.csv.md

~~~text
< comparing a.csv/b.csv
---
> comparing .
---
  |     | Country     | -Region | Date       | Kilotons of Co2 | -Metric Tons Per Capita |
  | --- | ----------- | ------- | ---------- | --------------- | ----------------------- |
(39 lines match)
~~~
comparing tests/test_presentation/cases/co2_emissions/diff.csv.txt

~~~text
< comparing a.csv/b.csv
---
> comparing .
---
      Country     -Region Date       Kilotons of Co2 -Metric Tons Per Capita
  --- ----------- ------- ---------- --------------- -----------------------
(39 lines match)
~~~
comparing tests/test_presentation/cases/co2_emissions/diff.excel.txt

~~~text
< comparing a.excel/b.excel/Sheet1
---
> comparing ./Sheet1
---
      Country     -Region Date       Kilotons of Co2 -Metric Tons Per Capita
  --- ----------- ------- ---------- --------------- -----------------------
(39 lines match)
~~~
comparing tests/test_presentation/cases/co2_emissions/diff.feather.txt

~~~text
< comparing a.feather/b.feather
---
> comparing .
---
      Country     -Region Date       Kilotons of Co2 -Metric Tons Per Capita
  --- ----------- ------- ---------- --------------- -----------------------
(39 lines match)
~~~
comparing tests/test_presentation/cases/co2_emissions/diff.parquet.txt

~~~text
< comparing a.parquet/b.parquet
---
> comparing .
---
      Country     -Region Date       Kilotons of Co2 -Metric Tons Per Capita
  --- ----------- ------- ---------- --------------- -----------------------
(39 lines match)
~~~
comparing tests/test_presentation/cases/readme/diff.txt

~~~text
< comparing a.txt/b.txt
---
> comparing .
---
  (27 lines match)
      from rdiff.sequence import diff
(77 lines match)
~~~
comparing tests/test_presentation/util.py

~~~text
  from io import StringIO
  
---
< from rdiff.contextual.path import diff_path
---
> from rdiff.cli.processor import process_iter
---
  from rdiff.presentation.base import TextPrinter
  
(2 lines match)
      if printer_kwargs is None:
          printer_kwargs = {}
---
<     diff = diff_path(a, b, f"{a.name}/{b.name}", **kwargs)
---
  
      buffer = StringIO()
      printer = TextPrinter(printer=buffer, **printer_kwargs)
---
>     for i in process_iter(a, b, **kwargs):
---
≈ ---    ---+++        +++printer.print_diff(---diff)---+++i)+++
---
  
      return buffer.getvalue()
~~~
NEW rdiff/cli/processor.py

