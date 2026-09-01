async def create_notification(
    db,
    user_id,
    notification_type,
    message
):
    notification = Notification(
        user_id=user_id,
        type=notification_type,
        message=message,
        read_status=False
    )

    db.add(notification)
    await db.commit()
    await db.refresh(notification)

    return notification