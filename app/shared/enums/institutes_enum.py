"""
Módulo de Catálogo de Institutos - Proyecto MACTI

Este Enum centraliza la identificación de todas las entidades y sedes
que forman parte del ecosistema MACTI. Actúa como el discriminador principal
para la selección dinámica de bases de datos, instancias de Moodle
y reinos (Realms) de Keycloak.
"""

from enum import Enum


class InstitutesEnum(Enum):
    """
    Enumeración de los institutos soportados por la plataforma.

    Cada valor corresponde a un identificador único utilizado en las
    configuraciones de servicios externos y en la persistencia de datos.
    """

    PRINCIPAL = "principal"
    CUANTICO = "cuantico"
    CIENCIAS = "ciencias"
    INGENIERIA = "ingenieria"
    ENCIT = "encit"
    IER = "ier"
    ENES_M = "enes_m"
    HPC = "hpc"
    IGF = "igf"
    ENES_JUR = "enes_jur"
