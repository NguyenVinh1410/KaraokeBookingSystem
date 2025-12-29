from datetime import datetime, date
from sqlalchemy import func

from bookingapp import db
from bookingapp.models import room, room_type, booking, service, service_order, invoice, customer, membership_history, user


def get_user_by_username(username: str):
    return user.query.filter_by(username=username).first()


def load_room_types():
    return room_type.query.all()

def load_rooms(q=None, room_type_id=None):
    query = room.query

    if q:
        query = query.filter(room.room_name.contains(q))

    if room_type_id:
        query = query.filter(room.room_type_id.__eq__(room_type_id))

    return query.all()

def get_room_by_id(room_id):
    return room.query.get(room_id)


def get_available_rooms(booking_date, start_time, end_time, guest_count):
    sub = db.session.query(booking.room_id).filter(
        booking.booking_date == booking_date,
        booking.status != 'Completed',
        booking.start_time < end_time,
        booking.end_time > start_time
    )

    qs = room.query.join(room_type, room.room_type_id == room_type.room_type_id) \
        .filter(
            room_type.capacity >= guest_count,
            ~room.room_id.in_(sub)
        )

    return qs.all()


def create_booking(customer_name, phone, room_id, booking_date, start_time, end_time, guest_count):
    c = customer.query.filter_by(phone=phone).first()
    if not c:
        c = customer(customer_name=customer_name, phone=phone, card_code=None)
        db.session.add(c)
        db.session.flush()

    b = booking(
        customer_id=c.customer_id,
        room_id=room_id,
        booking_date=booking_date,
        start_time=start_time,
        end_time=end_time,
        guest_count=guest_count,
        status="Booked"
    )
    db.session.add(b)

    r = room.query.get(room_id)
    if r:
        r.status = "Occupied"

    db.session.commit()
    return b

def get_booking_by_id(booking_id: int):
    return booking.query.get(booking_id)


def get_services():
    return service.query.all()

def add_service_to_booking(booking_id: int, service_id: int, quantity: int = 1):
    so = service_order.query.filter_by(booking_id=booking_id, service_id=service_id).first()
    if so:
        so.quantity += quantity
    else:
        so = service_order(booking_id=booking_id, service_id=service_id, quantity=quantity)
        db.session.add(so)
    db.session.commit()
    return so

def calc_service_cost(booking_id: int):
    total = db.session.query(
        func.sum(service_order.quantity * service.price)
    ).join(service, service.service_id == service_order.service_id) \
     .filter(service_order.booking_id == booking_id).scalar()
    return total or 0


def count_month_visits(customer_id: int, on_date: date):
    return db.session.query(func.count(membership_history.history_id)) \
        .filter(
            membership_history.customer_id == customer_id,
            func.month(membership_history.usage_date) == on_date.month,
            func.year(membership_history.usage_date) == on_date.year
        ).scalar() or 0


def create_invoice_for_booking(booking_id: int, actual_hours: float):
    b = booking.query.get(booking_id)
    if not b:
        return None

    r = b.room
    c = b.customer

    rt = r.room_type
    room_cost = actual_hours * rt.price
    service_cost = calc_service_cost(booking_id)

    discount = 0.0
    today = date.today()
    if c and c.card_code:
        visits = count_month_visits(c.customer_id, today)
        if visits >= 10:
            discount = 0.05

    gross = room_cost + service_cost
    subtotal = gross * (1 - discount)
    vat = subtotal * 0.10
    total = subtotal + vat

    inv = invoice(
        booking_id=booking_id,
        room_cost=room_cost,
        service_cost=service_cost,
        discount=discount,
        sub_total=subtotal,
        vat=vat,
        total_amount=total
    )
    db.session.add(inv)

    if c:
        hist = membership_history(
            customer_id=c.customer_id,
            booking_id=booking_id,
            usage_date=today,
            visit_count=1,
            applied_discount=discount
        )
        db.session.add(hist)

    b.status = "Completed"
    r.status = "Available"

    db.session.commit()
    return inv


def revenue_by_room_type(start_date: date, end_date: date):
    q = db.session.query(
        room_type.room_type_name,
        func.sum(invoice.total_amount).label("revenue"),
        func.count(invoice.invoice_id).label("total_bookings")
    ).join(room, room.room_type_id == room_type.room_type_id) \
     .join(booking, booking.room_id == room.room_id) \
     .join(invoice, invoice.booking_id == booking.booking_id) \
     .filter(
        invoice.payment_date >= start_date,
        invoice.payment_date < end_date
     ).group_by(room_type.room_type_name)

    return q.all()
