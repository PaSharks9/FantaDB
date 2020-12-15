"""
This script runs the FantaDB application using a development server.
"""

from os import environ
from FantaDB import fantaApp

if __name__ == '__main__':
    HOST = environ.get('SERVER_HOST', 'localhost')
    print('HOST', str(HOST))
    try:
        PORT = int(environ.get('SERVER_PORT', '5555'))
    except ValueError:
        PORT = 5555
    fantaApp.run(HOST, PORT)
