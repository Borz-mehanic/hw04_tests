import datetime

from typing import Dict


def year(request: Dict[str, int]) -> datetime:
    """Добавляет переменную с текущим годом."""
    return{
        'year': datetime.date.today().year
    }
