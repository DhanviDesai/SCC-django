from firebase_admin import messaging, exceptions

def send_fcm_notification(token: str, title: str, body: str, data: dict = None):
    """
    Sends a single push notification to a specific device.

    Args:
        token: The FCM registration token of the target device.
        title: The title of the notification.
        body: The body text of the notification.
        data: A dictionary of custom key-value data to send with the message.
    """
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data or {},
            token=token
        )
        response = messaging.send(message)
        print('Successfully sent message: ', response)
        return True
    except exceptions.FirebaseError as e:
        print('Failed to send FCM message: ', e)
        if isinstance(e, (exceptions.UnregisteredError, exceptions.InvalidArgumentError)):
            # The token is invalid, so its better to delete it
            pass
        return False