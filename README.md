# django-add-default-value

> Django Migration Operation that can be used to transfer a field’s default value
to the database scheme.

<a href="https://pypi.python.org/pypi/django-add-default-value/"><img src="https://img.shields.io/pypi/v/django-add-default-value.svg" alt="PyPi version" /></a>
<a href="./LICENSE"><img src="https://img.shields.io/github/license/3yourmind/django-add-default-value.svg" alt="badge of license" /></a>
<a href="https://github.com/3YOURMIND/django-add-default-value/pulls"><img src="https://img.shields.io/badge/PR-welcome-green.svg" alt="badge of pull request welcome" /></a>
<a href="https://www.3yourmind.com/career"><img src="https://img.shields.io/badge/3YOURMIND-Hiring-brightgreen.svg" alt="badge of hiring advertisement of 3yourmind" /></a>
<a href="https://github.com/3YOURMIND/django-add-default-value/stargazers"><img src="https://img.shields.io/github/stars/3YOURMIND/django-add-default-value.svg?style=social&label=Stars" alt="badge of github star" /></a>

## Dependencies

* [MySQL][mysql] (or compatible)
* [PostgreSQL][postgresql]

## Installation

<pre>
<a href="https://.com">pip</a> install <a href="https://pypi.org/project/django-add-default-value/">django-add-default-value</a>
</pre>

You can then use `AddDefaultValue` in your migration file to transfer the default
values to your database. Afterwards, it’s just the usual `./manage.py migrate`.

## Usage

```python
AddDefaultValue(
    model_name='my_model',
    name='my_field',
    value='my_default'
)
```

### Example

Given the following migration:

```python
operations = [
    migrations.AddField(
        field=models.CharField(default='my_default', max_length=255),
        model_name='my_model',
        name='my_field',
    ),
]
```

Modify the migration to add a default value:

```diff
+from django_add_default_value import AddDefaultValue
+
 operations = [
     migrations.AddField(
         field=models.CharField(default='my_default', max_length=255),
         model_name='my_model',
         name='my_field',
     ),
+    AddDefaultValue(
+        model_name='my_model',
+        name='my_field',
+        value='my_default'
+    )
 ]
```

If you check `python manage.py sqlmigrate [app name] [migration]`,
you will see that the default value now gets set.

## Contributing

First of all, thank you very much for contributing to this project. Please base
your work on the `master` branch and target `master` in your pull request.

## License

`django-add-default-value` is released under the [Apache 2.0 License](./LICENSE).

[mysql]: https://www.mysql.com
[postgresql]: https://www.postgresql.org
