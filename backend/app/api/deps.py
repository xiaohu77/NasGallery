from typing import Generator
from app.database import get_db

# 依赖注入别名
DependsDB = get_db