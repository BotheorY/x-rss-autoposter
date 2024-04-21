from abconsolemenu.validators.base import BaseValidator


class IntValidator(BaseValidator):

    def __init__(self):
        """
        URL Validator class
        """
        super(IntValidator, self).__init__()

    def validate(self, input_string):
        """
        Validate int

        :return: True if match / False otherwise
        """
        input_string = input_string.strip()
        if not input_string:
            return False
        return (input_string[0] == '-' and input_string[1:].isdigit()) or input_string.isdigit()
