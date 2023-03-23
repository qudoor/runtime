from ansible.module_utils._text import to_text
from collections.abc import MutableMapping
from ansible.utils.vars import combine_vars
from ansible.errors import AnsibleOptionsError


def load_extra_vars(loader, extra_vars_opt):
    extra_vars = {}
    extra_vars_opt = to_text(extra_vars_opt, errors='surrogate_or_strict')
    if extra_vars_opt is None or not extra_vars_opt:
        extra_vars = {}

    data = loader.load_from_file(extra_vars_opt)

    if isinstance(data, MutableMapping):
        extra_vars = combine_vars(extra_vars, data)
    else:
        raise AnsibleOptionsError(
            "Invalid extra vars data supplied. '%s' could not be made into a dictionary" % extra_vars_opt)

    return extra_vars
