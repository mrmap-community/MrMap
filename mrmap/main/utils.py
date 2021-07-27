from django.contrib import messages
from django.utils.html import escape
from django.utils.safestring import mark_safe
import re
from django.conf import settings


def get_absolute_url(reverse_url) -> str:
    """Convert the given path url to an absolute url with the currently configured schema and hostname.

    :Example:

    .. code-block:: python
       from main.utils import get_absolute_url

       reverse_url = "services/123/xml"
       absolute_url = get_absolute_url(reverse_url=reverse_url)

       print(absolute_url)
       >>> https://mrmap.org/services/123/xml


    :return absolute_url: the given url path as absolute url
    :rtype: str
    """
    return f"{settings.ROOT_URL}{reverse_url}"


def camel_to_snake(name):
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


def handle_protected_error(obj_list, request, e):
    """
    Generate a user-friendly error message in response to a ProtectedError exception.
    """
    protected_objects = list(e.protected_objects)
    protected_count = len(protected_objects) if len(protected_objects) <= 50 else 'More than 50'
    err_message = f"Unable to delete <strong>{', '.join(str(obj) for obj in obj_list)}</strong>. " \
                  f"{protected_count} dependent objects were found: "

    # Append dependent objects to error message
    dependent_objects = []
    for dependent in protected_objects[:50]:
        if hasattr(dependent, 'get_absolute_url') and dependent.get_absolute_url():
            dependent_objects.append(f'<a href="{dependent.get_absolute_url()}">{escape(dependent)}</a>')
        elif hasattr(dependent, 'get_concrete_table_url') and dependent.get_concrete_table_url():
            dependent_objects.append(f'<a href="{dependent.get_concrete_table_url()}">{escape(dependent)}</a>')
        else:
            dependent_objects.append(str(dependent))
    err_message += ', '.join(dependent_objects)

    messages.error(request, mark_safe(err_message))
