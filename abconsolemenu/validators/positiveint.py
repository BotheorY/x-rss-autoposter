from abconsolemenu.validators.base import BaseValidator


class PositiveIntValidator(BaseValidator):

    def __init__(self):
        """
        URL Validator class
        """
        super(PositiveIntValidator, self).__init__()

    def validate(self, input_string):
        """
        Validate int

        :return: True if match / False otherwise
        """
        input_string = input_string.strip()
        if not input_string:
            return False
        return input_string.isdigit()
