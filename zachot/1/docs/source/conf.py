import sys
import os

# Добавляем корень проекта в PYTHONPATH
sys.path.insert(0, os.path.abspath('../..'))

project = 'Python-MOOD'
copyright = '2024'
author = 'MUD Team'
release = '0.1'

extensions = [
    'sphinx.ext.autodoc',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_theme = 'alabaster'
html_static_path = ['_static']

# Игнорируем импорт cowsay при сборке документации
autodoc_mock_imports = ['cowsay']

# Указываем, какие модули документировать
autodoc_default_options = {
    'members': True,
    'undoc-members': False,
}
