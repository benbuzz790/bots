class ToolValidator:
    """Validates tool functions meet the framework requirements."""

    @staticmethod
    def validate_tool(func) ->tuple[bool, list[str]]:
        """Validate a single tool function meets all requirements.
        
        Parameters:
            func: The function to validate
            
        Returns:
            tuple[bool, list[str]]: (is_valid, list of error messages)
        """
        errors = []
        if not func.__doc__:
            errors.append(f'Tool {func.__name__} missing docstring')
        elif 'Use when' not in func.__doc__:
            errors.append(
                f"Tool {func.__name__} docstring missing 'Use when' guidance")
        if not hasattr(func, '__annotations__'
            ) or 'return' not in func.__annotations__:
            errors.append(
                f'Tool {func.__name__} missing return type annotation')
        elif func.__annotations__['return'] not in (str, Dict[str, Any]):
            errors.append(
                f"Tool {func.__name__} must return str, found {func.__annotations__['return']}"
        # Check return annotation exists and is str
        if not hasattr(func, '__annotations__') or 'return' not in func.__annotations__:
            errors.append(f"Tool {func.__name__} missing return type annotation")
        elif func.__annotations__['return'] != str:
            errors.append(f"Tool {func.__name__} must return str, found {func.__annotations__['return']}")
                'Returns:')[0] if 'Parameters:' in func.__doc__ else ''
            for param_name in func.__annotations__:
                if param_name != 'return' and param_name not in param_section:
                    errors.append(
                        f'Tool {func.__name__} missing documentation for parameter {param_name}'
                        )
        return len(errors) == 0, errors

    @staticmethod
    def validate_module(module) ->tuple[bool, dict[str, list[str]]]:
        """Validate all tool functions in a module.
        
        Parameters:
            module: The module containing tools to validate
            
        Returns:
            tuple[bool, dict[str, list[str]]]: (all_valid, {function_name: list of error messages})
        """
        results = {}
        all_valid = True
        for name, func in module.__dict__.items():
            if callable(func) and not name.startswith('_'):
                is_valid, errors = ToolValidator.validate_tool(func)
                if not is_valid:
                    all_valid = False
                    results[name] = errors
        return all_valid, results
