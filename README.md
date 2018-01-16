# django-add-default-value

> This django Migration Operation can be used to transfer a fields default value
> to the database scheme.

<a href="https://pypi.python.org/pypi/django-add-default-value/"><img src="https://img.shields.io/pypi/v/django-add-default-value.svg" alt="PyPi version" /></a>
<a href="./LICENSE"><img src="https://img.shields.io/github/license/3yourmind/django-add-default-value.svg" alt="badge of license" /></a>
<a href="https://github.com/3YOURMIND/django-add-default-value/pulls"><img src="https://img.shields.io/badge/PR-welcome-green.svg" alt="badge of pull request welcome" /></a>
<a href="https://www.3yourmind.com/career"><img src="https://img.shields.io/badge/3YOURMIND-Hiring-brightgreen.svg" alt="badge of hiring advertisement of 3yourmind" /></a>
<a href="https://github.com/3YOURMIND/django-add-default-value/stargazers"><img src="https://img.shields.io/github/stars/3YOURMIND/django-add-default-value.svg?style=social&label=Stars" alt="badge of github star" /></a>

## Dependencies

* MySQL (or compatible),
* PostgreSQL

## Usage

Install the package.

`pip install django-add-default-value`

Whenever you need a default value to be present in your database scheme,
you need to add an `AddDefaultValue` - Operation to your migration file,
before executing `python manage.py migrate`.

### Example

Given the following migration:

```python
operations = [
    migrations.AddField(
        model_name='my_model',
        name='my_field',
        field=models.CharField(default='my_default', max_length=255),
    ),
]
```

Modify that migration, in Order to add a default value:

```python
from django_add_default_value import AddDefaultValue

# ...

operations = [
    migrations.AddField(
        model_name='my_model',
        name='my_field',
        field=models.CharField(default='my_default', max_length=255),
    ),
    AddDefaultValue(
        model_name='my_model',
        name='my_field',
        value='my_default',
    ),
]
```

If you check `python manage.py sqlmigrate [app name] [migration]`,
you will see that this migration now set's a default value.

## Contributing

First, thank you very much if you want to contribute to the project. Please base your work on the `master` branch and also target this branch in your pull request.

## License

_django-add-default-value_ is released under the [Apache 2.0 License](./LICENSE).
