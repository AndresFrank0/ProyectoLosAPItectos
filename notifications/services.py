# src/notifications/services.py
from datetime import datetime

def notify_reservation_created(reservation_time: datetime, restaurant_name: str):
    """Simulates sending a notification for a created reservation."""
    print(f"Notification: Reservation confirmed for {reservation_time.strftime('%Y-%m-%d %H:%M')} in {restaurant_name}.")

def notify_reservation_cancelled(reservation_id: int):
    """Simulates sending a notification for a cancelled reservation."""
    print(f"Notification: Reservation cancelled (ID: {reservation_id}).")

def notify_preorder_registered(num_dishes: int):
    """Simulates sending a notification for a pre-order."""
    print(f"Notification: Pre-order with {num_dishes} dishes registered.")