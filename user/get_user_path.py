import os

root_path = "downloads/"

async def get_user_path(chat_id):
    if not os.path.exists(root_path):
        os.makedirs(root_path)
    
    user_folder = os.path.join(root_path, str(chat_id))
    os.makedirs(user_folder, exist_ok=True)
    
    return user_folder