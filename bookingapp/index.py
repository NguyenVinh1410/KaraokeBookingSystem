from flask import render_template, request, redirect, session, url_for
from datetime import datetime, date
from bookingapp import app, db
import dao
from bookingapp.models import room_type, service_category, service, room, user


def init_data():
    with app.app_context():
        db.create_all()

        if room_type.query.count() == 0:
            r1 = room_type(room_type_name="Phòng đôi", capacity=2, price=100000)
            r2 = room_type(room_type_name="Phòng basic", capacity=4, price=200000)
            r3 = room_type(room_type_name="Phòng vip", capacity=8, price=300000)
            r4 = room_type(room_type_name="Phòng supper vip", capacity=15, price=500000)
            db.session.add_all([r1, r2, r3, r4])
            db.session.commit()

        if room.query.count() == 0:
            rts = room_type.query.all()
            demo_rooms = [
                room(room_name="Đôi 01", room_type_id=rts[0].room_type_id),
                room(room_name="Đôi 02", room_type_id=rts[0].room_type_id),
                room(room_name="Basic 01", room_type_id=rts[1].room_type_id),
                room(room_name="VIP 01", room_type_id=rts[2].room_type_id),
                room(room_name="SVIP 01", room_type_id=rts[3].room_type_id),
            ]
            db.session.add_all(demo_rooms)
            db.session.commit()

        if service_category.query.count() == 0:
            food = service_category(category_name="Food")
            drink = service_category(category_name="Drink")
            db.session.add_all([food, drink])
            db.session.flush()

            services = [
                service(service_name="Khô bò", price=100000, category_id=food.category_id),
                service(service_name="Đậu phộng", price=50000, category_id=food.category_id),
                service(service_name="Bim bim", price=20000, category_id=food.category_id),
                service(service_name="Tiger", price=29000, category_id=drink.category_id),
                service(service_name="Pepsi", price=20000, category_id=drink.category_id),
                service(service_name="Aqua", price=15000, category_id=drink.category_id),
            ]
            db.session.add_all(services)
            db.session.commit()

        if user.query.count() == 0:
            u1 = user(username="staff", password="123", role="staff")
            u2 = user(username="admin", password="123", role="admin")
            db.session.add_all([u1, u2])
            db.session.commit()

init_data()

@app.route('/')
def index():
    q = request.args.get("q")
    room_type_id = request.args.get("room_id")
    rooms = dao.load_rooms(q=q, room_type_id=room_type_id)
    return render_template("index.html", rooms=rooms)


@app.route("/rooms/<int:room_id>", methods=['get', 'post'])
def details(room_id):
    r = dao.get_room_by_id(room_id)
    msg = None

    if request.method == 'POST':
        customer_name = request.form.get('customer_name')
        phone = request.form.get('phone')
        booking_date_str = request.form.get('booking_date')
        start_time_str = request.form.get('start_time')
        end_time_str = request.form.get('end_time')
        guest_count = int(request.form.get('guest_count', 1))

        booking_date = datetime.strptime(booking_date_str, '%Y-%m-%d').date()
        start_time = datetime.strptime(start_time_str, '%H:%M').time()
        end_time = datetime.strptime(end_time_str, '%H:%M').time()

        if guest_count > 15 or guest_count > r.room_type.capacity:
            msg = "Số người vượt quá sức chứa phòng!"
        else:
            available = dao.get_available_rooms(booking_date, start_time, end_time, guest_count)
            if r not in available:
                msg = "Phòng không trống trong khung giờ này!"
            else:
                b = dao.create_booking(customer_name, phone, r.room_id, booking_date, start_time, end_time, guest_count)
                msg = f"Đặt phòng thành công! Booking ID: {b.booking_id}"

    return render_template("room_details.html", r=r, msg=msg)

@app.route("/booking/<int:booking_id>/services", methods=['get', 'post'])
def booking_services(booking_id):
    if 'user_role' not in session:
        return redirect(url_for('login_my_staff'))

    b = dao.get_booking_by_id(booking_id)
    if not b:
        return "Booking không tồn tại", 404

    services = dao.get_services()
    msg = None

    if request.method == 'POST':
        service_id = int(request.form.get('service_id'))
        quantity = int(request.form.get('quantity', 1))
        dao.add_service_to_booking(booking_id, service_id, quantity)
        msg = "Thêm dịch vụ thành công!"

    return render_template("booking_services.html", booking=b, services=services, msg=msg)


@app.route("/booking/<int:booking_id>/checkout", methods=['get', 'post'])
def checkout(booking_id):
    if 'user_role' not in session:
        return redirect(url_for('login_my_staff'))

    b = dao.get_booking_by_id(booking_id)
    if not b:
        return "Booking không tồn tại", 404

    inv = None
    msg = None

    if request.method == 'POST':
        actual_hours = float(request.form.get('actual_hours', 1))
        inv = dao.create_invoice_for_booking(booking_id, actual_hours)
        msg = "Thanh toán thành công!"

    return render_template("checkout.html", booking=b, invoice=inv, msg=msg)


@app.route("/report")
def report():
    role = session.get('user_role')
    if role != 'admin':
        return "Bạn không có quyền xem báo cáo (chỉ admin).", 403

    today = date.today()
    start_str = request.args.get("start")
    end_str = request.args.get("end")

    if start_str and end_str:
        start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
    else:
        start_date = today
        end_date = today

    data = dao.revenue_by_room_type(start_date, end_date)
    return render_template("report.html", data=data, start_date=start_date, end_date=end_date)


@app.context_processor
def common_attribute():
    return {
        "rs": dao.load_room_types(),
        "current_role": session.get('user_role'),
        "current_user": session.get('username')
    }


@app.route("/login", methods=['get', 'post'])
def login_my_staff():
    err_msg = None
    if request.method.__eq__('POST'):
        username = request.form.get("staffname")
        password = request.form.get("password")

        u = dao.get_user_by_username(username)
        if u and u.password == password:
            session['user_id'] = u.user_id
            session['username'] = u.username
            session['user_role'] = u.role
            return redirect('/')
        else:
            err_msg = "Tài khoản hoặc mật khẩu không đúng!"
    return render_template("login.html", err_msg=err_msg)


@app.route("/logout")
def logout():
    session.clear()
    return redirect('/')


if __name__ == "__main__":
    app.run(debug=True)