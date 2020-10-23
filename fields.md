**Erklärung der Felder**<br>
kumuliert = Summe der Fälle seit erstem Covid-19-Fall

|Feldname CovEx| Feldname Original|Erklärung |
|---------|-----------------|----------|
|bestätigt kum.|ncumul_conf|Bestätigte Fälle kumuliert|
|getestet kum.|ncumul_tested|Getestete Personen kumuliert|
|hospitalisiert kum.|ncumul_hosp|hospitalisierte Personen kumuliert. Die meisten Kantone rapportieren in diesem Feld jedoch die Anzahl der neuen Hospitalisierungen|
|Intensivstation kum.|ncumul_ICU|Personen, die in eine Intensivstation eingeliefert wurden, kumuliert|
|künst. Beatm. kum.|ncumul_vent|Personen die künstliche Beatmung erforderten kumuliert|
|Genesungen kum.|ncumul_released|Spitalentlassungen und Genesungen kumuliert|
|Todesfälle kum.|ncumul_deceased|Sterbefälle kumuliert|
<br><br>
**Berechnete Felder**

|Feldname CovEx|Berechnung|
|---------|-----------------|
|neue Fälle|berechnet als \[bestätigt kum.\](Tag) - \[bestätigt kum.\](Vortag)|
|aktive Fälle|\[bestätigt kum.\] - \[Genesungen kum.\]|
|getestet kum. pro 100k Einw.|\[getestet kum.\] / \[Einwohner Kanton\] * 100 000|
|bestätigt kum. pro 100k Einw.|\[bestätigt kum.\] / \[Einwohner Kanton\] * 100 000|
|hospitalisiert kum. pro 100k Einw.|\[hospitalisiert kum.\] / \[Einwohner Kanton\] * 100 000|
|getestet kum. pro 100k Einw.|\[getestet kum.\] / \[Einwohner Kanton\] * 100 000|
|Intensivstation kum. pro 100k Einw.|\[Intensivstation kum.\] / \[Einwohner Kanton\] * 100 000|
|künst. Beatm. kum. pro 100k Einw.|\[künst. Beatm. kum.\] / \[Einwohner Kanton\] * 100 000|
|Spitalentlassungen kum. pro 100k Einw.|\[Genesungen kum.\] / \[Einwohner Kanton\] * 100 000|
|Todesfälle kum. pro 100k Einw.|\[Todesfälle kum.\] / \[Einwohner Kanton\] * 100 000|