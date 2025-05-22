from datetime import datetime
import pytz

class ResponseStore:
    def __init__(self):
        self.responses = {}
        self.message_ids = {}

    def update_response(self, user_id, reaction):
        self.responses[user_id] = {
            'reaction': reaction,
            'last_updated': datetime.now(pytz.timezone('Asia/Tokyo')),
            'month': datetime.now().month
        }

    def get_unresponded_users(self):
        return [user_id for user_id, data in self.responses.items() 
                if data['reaction'] is None]

storage = ResponseStore()