from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta

from .models import Quote, SellerWorkflowTask, OrderItem


@receiver(post_save, sender=Quote)
def create_task_on_quote(sender, instance, created, **kwargs):
    """Automatically create a workflow task when a buyer sends a quote to a seller."""
    if not created:
        return
    try:
        title = f"Respond to quote from {instance.buyer.username}"
        notes = (instance.message or '').strip()
        due_date = (timezone.now() + timedelta(days=3)).date()
        SellerWorkflowTask.objects.create(
            seller=instance.seller,
            product=instance.product,
            title=title,
            notes=notes,
            due_date=due_date,
        )
    except Exception:
        # don't block quote creation on task creation failure
        pass


@receiver(post_save, sender=OrderItem)
def create_task_on_order_item(sender, instance, created, **kwargs):
    """Create a fulfillment task when an OrderItem is created.

    This gives sellers a task to pack/finish the item. If the parent Order has
    an estimated_delivery date we'll use that as the due date; otherwise default
    to 7 days from now.
    """
    if not created:
        return
    try:
        order = getattr(instance, 'order', None)
        due_date = None
        if order is not None and getattr(order, 'estimated_delivery', None):
            due_date = order.estimated_delivery
        else:
            due_date = (timezone.now() + timedelta(days=7)).date()

        # avoid creating duplicate tasks for the same order item
        exists = SellerWorkflowTask.objects.filter(order_item=instance).exists()
        if not exists:
            SellerWorkflowTask.objects.create(
                seller=order.seller if order is not None else instance.product.seller,
                order_item=instance,
                product=instance.product,
                title=f"Fulfill: {instance.product.name} (Order #{order.id if order is not None else 'N/A'})",
                notes=f"Quantity: {instance.quantity}",
                due_date=due_date,
            )
    except Exception:
        pass
