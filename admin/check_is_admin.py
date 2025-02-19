from config import ADMIN_ID

def is_user_admin(user_id: int) -> bool:
    return str(user_id) == ADMIN_ID