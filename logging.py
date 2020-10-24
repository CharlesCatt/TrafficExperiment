
from enum import Enum

# define level hierarchy
class Level(Enum):
    ALL = 1
    ERROR = 2
    WARNING = 3
    INFO = 4
    DEBUG = 5

class Logging(object):
    """
    logging class to handle extraneous info
    can write to file or stdout
    """

    def __init__(self, stdout_level, file_level=None, output_file=None):
        super(Logging, self).__init__()
        self.level = stdout_level
        self.file_level = file_level
        self.output_file = None
        if output_file != None:
            self.output_file = open(output_file, 'w')

    def close():
        self.output_file.close()

    def debug(self, message):
        if self.file_level >= 5:
            self.output_file.write('DEBUG:     {}\n'.format(message))
        if self.level >= 5:
            print('DEBUG:   {}'.format(message))

    def info(self, message):
        if self.file_level >= 4:
            self.output_file.write('INFO:      {}\n'.format(message))
        if self.level >= 4:
            print('INFO:    {}'.format(message))

    def warning(self, message):
        if self.file_level >= 3:
            self.output_file.write('WARNING:   {}\n'.format(message))
        if self.level >= 3:
            print('WARNING: {}'.format(message))

    def error(self, message):
        if self.file_level >= 2:
            self.output_file.write('INFO:     {}\n'.format(message))
        if self.level >= 2:
            print('ERROR:   {}'.format(message))

    def all(self, message):
        if self.file_level >= 1:
            self.output_file.write('ALL:      {}\n'.format(message))
        if self.level >= 1:
            print('ALL:     {}'.format(message))
