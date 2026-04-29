Техническая документация
========================

Серверный модуль
----------------

.. automodule:: mood.server.server
   :members:
   :undoc-members:
   :show-inheritance:

Игровой движок
--------------

.. automodule:: mood.common.game
   :members:
   :undoc-members:
   :show-inheritance:

Константы игрового мира
=======================

.. py:data:: FIELD_SIZE
   :type: int
   :value: 10
   
   Размер игрового поля (10x10 клеток).

.. py:data:: DEFAULT_PORT
   :type: int
   :value: 1337
   
   Порт по умолчанию для подключения к серверу.

.. py:data:: DEFAULT_HOST
   :type: str
   :value: "127.0.0.1"
   
   Адрес хоста по умолчанию (localhost).

.. py:data:: WEAPONS
   :type: dict
   :value: {'sword': 10, 'spear': 15, 'axe': 20}
   
   Словарь доступного оружия и его урона:
   
   * **sword** (меч) — урон 10
   * **spear** (копьё) — урон 15
   * **axe** (топор) — урон 20

.. py:data:: JGSBAT_COW
   :type: str
   
   ASCII-арт монстра jgsbat (летучая мышь) для cowsay.
