# django-add-default-value
This django Migration Operation can be used to transfer a fields default value
to the database scheme.

## Requirements

* MySQL (or compatible),
* PostgreSQL

## Usage

Install the package.
`pip install django-add-default-value`

Whenever you need a default value to be present in your Database scheme,
you need to add an `AddDefaultValue`-Operation to your migration file,
before executing `python manage.py migrate`.

### Example

Given the following migration:

```python
    operations = [
        migrations.AddField(
            model_name='my_model    ',
            name='my_field',
            field=models.CharField(default='my_default', max_length=255),
        ),
    ]
```

Modify that migration, in Order to add a default value:

```python

from django_add_default_value import AddDefaultValue

// ...

    operations = [
        migrations.AddField(
            model_name='my_model',
            name='my_field',
            field=models.CharField(default='my_default', max_length=255),
        ),
        AddDefaultValue(
            model_name='my_model',
            name='tax_field',
            value='my_default'
        )
    ]
```

If you check `python manage.py sqlmigrate [app name] [migration]`,
you will see that this migration now set's a default value.

