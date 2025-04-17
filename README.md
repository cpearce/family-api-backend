Family API backed.

To activate virtualenv:

```
source env/bin/activate
```

To create a new virtualenv:

```
python3 -m venv env
```

To update pip dependencies:

```
sed -i '' 's/[~=]=/>=/' requirements.txt
pip install -U -r requirements.txt
pip freeze | sed 's/==/~=/' > requirements.txt
```

To import a new GEDCOM file:

```
./manage.py importgedcom file.ged
```

To export as JSON:

```
./manage.py dump-data 2025-04-18.json
```
