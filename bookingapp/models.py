from bookingapp import db
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Time, Date
from sqlalchemy.orm import relationship
from datetime import datetime

class user(db.Model):
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False)  # 'staff' hoặc 'admin'

    def __str__(self):
        return f"{self.username} ({self.role})"


class room_type(db.Model):
    room_type_id = Column(Integer, primary_key=True, autoincrement=True)
    room_type_name = Column(String(150), unique=True, nullable=False)
    capacity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    rooms = relationship('room', backref="room_type", lazy=True)

    def __str__(self):
        return self.room_type_name

class room(db.Model):
    room_id = Column(Integer, primary_key=True, autoincrement=True)
    room_name = Column(String(150), unique=True, nullable=False)
    image = Column(String(300), default="https://tse2.mm.bing.net/th/id/OIP.tVB9zEye0MO6UmZ-6vT8pwHaFP?pid=Api&P=0&h=180")
    status = Column(String(30), default="Available")
    room_type_id = Column(Integer, ForeignKey(room_type.room_type_id), nullable=False)
    bookings = relationship('booking', backref="room", lazy=True)

    def __str__(self):
        return self.room_name

class service_category(db.Model):
    category_id = Column(Integer, primary_key=True, autoincrement=True)
    category_name = Column(String(15), nullable=False)
    services = relationship('service', backref="service_category", lazy=True)

class service(db.Model):
    service_id = Column(Integer, primary_key=True, autoincrement=True)
    service_name = Column(String(50), nullable=False)
    price = Column(Float, nullable=False)
    category_id = Column(Integer, ForeignKey(service_category.category_id), nullable=False)
    service_orders = relationship('service_order', backref="service", lazy=True)

class customer(db.Model):
    customer_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_name = Column(String(100), nullable=False)
    phone = Column(String(15), unique=True, nullable=False)
    card_code = Column(String(20), unique=True)
    bookings = relationship("booking", backref="customer", lazy=True)
    membership_histories = relationship('membership_history', backref="customer", lazy=True)

class booking(db.Model):
    booking_id = Column(Integer, primary_key=True, autoincrement=True)
    booking_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    guest_count = Column(Integer, nullable=False)
    status = Column(String(20), default="Booked")  # Booked / InProgress / Completed
    customer_id = Column(Integer, ForeignKey(customer.customer_id))
    room_id  = Column(Integer, ForeignKey(room.room_id), nullable=False)
    service_orders = relationship('service_order', backref="booking", lazy=True)
    invoice = relationship('invoice', backref="booking", uselist=False)

class service_order(db.Model):
    booking_id = Column(Integer, ForeignKey(booking.booking_id), primary_key=True)
    service_id = Column(Integer, ForeignKey(service.service_id), primary_key=True)
    quantity = Column(Integer, default=1, nullable=False)

class invoice(db.Model):
    invoice_id = db.Column(Integer, primary_key=True, autoincrement=True)
    payment_date = Column(DateTime, default=datetime.now)
    room_cost = Column(Float, default=0)
    service_cost = Column(Float, default=0)
    discount = Column(Float, default=0)
    sub_total = Column(Float, default=0)
    vat = Column(Float, default=0)
    total_amount = Column(Float, default=0)
    booking_id = Column(Integer, ForeignKey(booking.booking_id), unique=True, nullable=False)

class membership_history(db.Model):
    history_id = Column(Integer, primary_key=True, autoincrement=True)
    usage_date = Column(Date, nullable=False)
    visit_count = Column(Integer, default=1)
    applied_discount = Column(Float, default=0)
    customer_id = Column(Integer, ForeignKey(customer.customer_id), nullable=False)
    booking_id = Column(Integer, ForeignKey(booking.booking_id))
