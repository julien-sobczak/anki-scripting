- Go to wikipedia https://en.wiktionary.org/wiki/Wiktionary:Frequency_lists
 
- Save the list based on the Project Gutenberg
  Source: https://en.wiktionary.org/wiki/Wiktionary:Frequency_lists#Project_Gutenberg
  Destination: resources/40000_frequency_list_gutenberg.txt

- Save the list based on TV and movie scripts 
  Source: https://en.wiktionary.org/wiki/Wiktionary:Frequency_lists#TV_and_movie_scripts
  Destination: resources/40000_frequency_list_tv.txt
  
Note: The list is divided between multiple HTML pages. Merge the table raw HTML code inside a unique file. Resulting file should have the following format:
 
```
<table>
<tbody><tr>
<td><b>rank</b></td>
<td><b>word</b></td>
<td><b>count</b></td>
</tr>
<tr>
<td>1</td>
<td><a href="/wiki/you" title="you">you</a></td>
<td>1222421 (see also ya)</td>
</tr>
<tr>
<td>2</td>
<td><a href="/wiki/I" title="I">I</a> or <a href="/wiki/I" title="I">I</a>.</td>
<td>1052546</td>
</tr>
...
</table>
```

- Convert these files to simpler CSV files following the format:

```
1,you,1222421
2,I,1052546
...
```
