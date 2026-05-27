from django import forms


DYNAMIC_FIELD_PREFIX = "dyn__"


def get_active_definitions(domain_field_definition_model, target):
    return list(
        domain_field_definition_model.objects.filter(target=target, is_active=True).order_by("order", "id")
    )


def build_dynamic_form_field(definition):
    required = bool(definition.is_required)
    model = definition.__class__
    if definition.field_type == model.TYPE_TEXT:
        return forms.CharField(required=required, label=definition.label)
    if definition.field_type == model.TYPE_NUMBER:
        return forms.DecimalField(required=required, label=definition.label)
    if definition.field_type == model.TYPE_DATE:
        return forms.DateField(
            required=required,
            label=definition.label,
            widget=forms.DateInput(attrs={"type": "date"}),
        )
    if definition.field_type == model.TYPE_BOOLEAN:
        return forms.BooleanField(required=False, label=definition.label)
    if definition.field_type == model.TYPE_SELECT:
        choices = [(choice, choice) for choice in (definition.choices_json or [])]
        return forms.ChoiceField(required=required, label=definition.label, choices=choices)
    if definition.field_type == model.TYPE_MULTISELECT:
        choices = [(choice, choice) for choice in (definition.choices_json or [])]
        return forms.MultipleChoiceField(
            required=required,
            label=definition.label,
            choices=choices,
            widget=forms.CheckboxSelectMultiple,
        )
    return None


def build_dynamic_form_fields(form, definitions, custom_data):
    field_names = []
    for definition in definitions:
        field_name = f"{DYNAMIC_FIELD_PREFIX}{definition.key}"
        initial = (custom_data or {}).get(definition.key)
        field = build_dynamic_form_field(definition)
        if field is None:
            continue

        form.fields[field_name] = field
        if initial is not None:
            form.fields[field_name].initial = initial
        field_names.append(field_name)

    return field_names


def extract_dynamic_cleaned_data(cleaned_data, definitions):
    result = {}
    for definition in definitions:
        field_name = f"{DYNAMIC_FIELD_PREFIX}{definition.key}"
        value = cleaned_data.get(field_name)
        if value in (None, "", []):
            continue
        model = definition.__class__
        if definition.field_type == model.TYPE_NUMBER:
            result[definition.key] = float(value)
        elif definition.field_type == model.TYPE_DATE:
            result[definition.key] = value.isoformat()
        elif definition.field_type == model.TYPE_BOOLEAN:
            result[definition.key] = bool(value)
        elif definition.field_type == model.TYPE_MULTISELECT:
            result[definition.key] = list(value)
        else:
            result[definition.key] = value
    return result
