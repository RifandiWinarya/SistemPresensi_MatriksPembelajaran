from pymongo import MongoClient
import jwt
from datetime import datetime, timedelta
import hashlib
from flask import (
    Flask,
    render_template,
    jsonify,
    request,
    redirect,
    url_for,
    session
)    
from bson import ObjectId
from werkzeug.utils import secure_filename

import os
from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

MONGODB_URI = os.environ.get("MONGODB_URI")
DB_NAME =  os.environ.get("DB_NAME")

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'foto')

TOKEN_KEY = 'mytoken'
SECRET_KEY = 'SMAN5_7321'
app.secret_key = "SMAN5_7321"

@app.route("/", methods=['GET'])
def home():
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        payload = jwt.decode(
            token_receive, 
            SECRET_KEY, 
            algorithms=["HS256"]
        )
        # user_info = db.users.find_one({"username": payload.get("username")})
        # return render_template("index.html", user_info=user_info)
        nama = session.get("nama")
        nip = session.get("nip")
        profile_picture = session.get("profile_picture")

        kelas_data = db.kelas.find()
        # Menghitung jumlah total siswa dan jumlah total kelas
        jumlah_siswa = 0
        jumlah_kelas = 0
        for kelas in kelas_data:
            jumlah_siswa += len(kelas.get('siswa', []))
            jumlah_kelas += 1
        
        pelajaran_data = db.mata_pelajaran.find()  
        # Menghitung jumlah pelajaran
        jumlah_pelajaran = 0
        for pelajaran in pelajaran_data:
            if 'nama_pelajaran' in pelajaran:
                jumlah_pelajaran += 1

        jumlah_guru = db.users.count_documents({'role': 'guru'})
        return render_template("index.html",
                               nama=nama,
                               nip=nip, 
                               profile_picture=profile_picture, 
                               jumlah_siswa=jumlah_siswa, 
                               jumlah_kelas=jumlah_kelas, 
                               jumlah_pelajaran=jumlah_pelajaran,
                               jumlah_guru=jumlah_guru)
    except jwt.ExpiredSignatureError:
        msg = "Your login token has expired"
        return redirect(url_for("login", msg=msg))
        # return redirect(url_for("login"))
    except jwt.exceptions.DecodeError:
        msg = "There was a problem logging you in"
        return redirect(url_for("login", msg=msg))
        # return redirect(url_for("login"))

@app.route("/admin", methods=['GET'])
def admin():
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        payload = jwt.decode(
            token_receive, 
            SECRET_KEY, 
            algorithms=["HS256"]
        )
        pelajaran_data = db.mata_pelajaran.find()
        jumlah_pelajaran = 0
        for pelajaran in pelajaran_data:
            if 'nama_pelajaran' in pelajaran:
                jumlah_pelajaran += 1  
        kelas_data = db.kelas.find()
        # Menghitung jumlah total siswa dan jumlah total kelas
        jumlah_siswa = 0
        for kelas in kelas_data:
            jumlah_siswa += len(kelas.get('siswa', []))
        
        jumlah_user = db.users.count_documents({})
        return render_template("dashboardadmin.html",
                               jumlah_siswa=jumlah_siswa, 
                               jumlah_user=jumlah_user,
                               jumlah_pelajaran = jumlah_pelajaran)
    except jwt.ExpiredSignatureError:
        msg = "Your login token has expired"
        return redirect(url_for("login", msg=msg))
        # return redirect(url_for("login"))
    except jwt.exceptions.DecodeError:
        msg = "There was a problem logging you in"
        return redirect(url_for("login", msg=msg))
        # return redirect(url_for("login"))

@app.route("/login", methods=['GET'])
def login():
    msg = request.args.get("msg")
    return render_template("login.html", msg=msg)

@app.route("/sign_in", methods=["POST"])
def sign_in():
    # Sign in
    username_receive = request.form["username_give"]
    password_receive = request.form["password_give"]
    result = db.users.find_one(
        {
            "username": username_receive,
            "password": password_receive,
        }
    )
    if result:
        session["id"] = str(result["_id"])
        session["username"] = result["username"]
        session["nama"] = result["nama"]
        session["nip"] = result["nip"]
        session["profile_picture"] = result["profile_picture"]
        session["role"] = result["role"]
        payload = {
            "username": username_receive,
            "exp": datetime.utcnow() + timedelta(seconds=60 * 60 * 24),
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        
        if result["role"] == "guru":
            redirect_url = url_for("home")  
        elif result["role"] == "admin":
            redirect_url = url_for("admin") 
        else:
            return jsonify(
                {
                    "result": "fail",
                    "msg": "Role not recognized",
                }
            )

        return jsonify(
            {
                "result": "success",
                "token": token,
                "redirect": redirect_url,
            }
        )
    else:
        return jsonify(
            {
                "result": "fail",
                "msg": "We could not find a user with that id/password combination",
            }
        )


@app.route("/absensi", methods=['GET'])
def absensi():
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        payload = jwt.decode(
            token_receive, 
            SECRET_KEY, 
            algorithms=["HS256"]
        )
        user_info = db.users.find_one({"username": payload.get("username")})
        username = user_info['username']
        nama = session.get("nama")
        nip = session.get("nip")
        profile_picture = session.get("profile_picture")
        kelasUser = list(db.data_kelasUser.find().sort("date", 1))
        kelas = list(db.kelas.find().sort("date", 1))
        mata_pelajaran = list(db.mata_pelajaran.find().sort("date", 1))
        # Melakukan iterasi pada hasil pencarian kelas jika diperlukan
        # for kelas_info in kelas:
        #     print(kelas_info)
        return render_template("absensi.html",nama=nama,nip=nip, profile_picture=profile_picture, username=username, kelasUser=kelasUser, kelas=kelas, mata_pelajaran=mata_pelajaran)
    except jwt.ExpiredSignatureError:
        msg = "Your login token has expired"
        return redirect(url_for("login", msg=msg))
    except jwt.exceptions.DecodeError:
        msg = "There was a problem logging you in"
        return redirect(url_for("login", msg=msg))

@app.route("/absensi/<id>", methods=['GET'])
def kelas(id):
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        payload = jwt.decode(
            token_receive, 
            SECRET_KEY, 
            algorithms=["HS256"]
        )
        nama = session.get("nama")
        nip = session.get("nip")
        profile_picture = session.get("profile_picture")
        data_kelas = db.data_kelasUser.find_one({'kelas': {'$elemMatch': {'id': id}}})
        if data_kelas and 'kelas' in data_kelas:
            # Mencari data array kelas yang memiliki id yang dicari
            for kelas in data_kelas['kelas']:
                if kelas['id'] == id:
                    kelasUser = kelas
        return render_template("absensi2.html",nama=nama,nip=nip, profile_picture=profile_picture, kelasUser=kelasUser,id=id)
    except jwt.ExpiredSignatureError:
        msg = "Your login token has expired"
        return redirect(url_for("login", msg=msg))
    except jwt.exceptions.DecodeError:
        msg = "There was a problem logging you in"
        return redirect(url_for("login", msg=msg))
    
@app.route('/edit_siswa/<id>', methods=['POST'])
def edit_siswa(id):
    username = session.get('username')
    data = request.json
    idsiswa = data.get('id')
    nisn = data.get('nisn')
    nama = data.get('nama')
    new_nisn = data.get('new_nisn')
    new_nama = data.get('new_nama')
    kelas = data.get('kelas')
    kelas2 = data.get('kelas2')
    action = data.get('action')

    if action == "edit":
        db.data_kelasUser.update_one(
            {'kelas.id': id, 'kelas.data_siswa.nisn': nisn},
            {'$set': {'kelas.$[].data_siswa.$[elem].nisn': new_nisn, 'kelas.$[].data_siswa.$[elem].nama': new_nama}},
            array_filters=[{'elem.nisn': nisn}]
        )
    elif action == "delete":
        # Hapus data siswa di koleksi 'data_kelasUser'
        result = db.data_kelasUser.update_one(
            {'username': username, 'kelas.id': id},
            {'$pull': {'kelas.$.data_siswa': {'id': idsiswa}}}
        )
        
        if result.modified_count == 0:
            return jsonify({"status": "error", "message": "Gagal menghapus siswa atau siswa tidak ditemukan."})
        
        # Hitung ulang jumlah siswa setelah penghapusan
        user_data = db.data_kelasUser.find_one({'username': username})
        kelas_tertentu = next((kelas for kelas in user_data['kelas'] if kelas['id'] == id), None)
        
        if kelas_tertentu:
            jumlah_siswa = len(kelas_tertentu['data_siswa'])
        
            # Perbarui jumlah siswa di kelas
            result = db.data_kelasUser.update_one(
                {'username': username, 'kelas.id': id},
                {'$set': {'kelas.$.jumlah_siswa': jumlah_siswa}}
            )
        
            if result.modified_count == 0:
                return jsonify({"status": "error", "message": "Gagal memperbarui jumlah siswa."})
        
            return jsonify({"status": "success", "message": "Siswa berhasil dihapus dan jumlah siswa diperbarui."})
        else:
            return jsonify({"status": "error", "message": "Kelas dengan ID tersebut tidak ditemukan."})
    
    return jsonify({'status': 'success'})

@app.route('/delete_class/<class_id>', methods=['POST'])
def delete_class(class_id):
    username = session.get("username")
    # Menghapus kelas berdasarkan id
    db.data_kelasUser.update_one(
        {"username": username},
        {"$pull": {"kelas": {"id": class_id}}}
    )
    return jsonify({'status': 'success'})

@app.route("/tambah_siswa/<id>", methods=['POST'])
def tambah_siswa(id):
    username = session.get('username')
    nama_kelas = request.form.get('nama_kelas')
    nama = request.form.get('nama')
    nisn = request.form.get('nisn')

    # Validasi input
    if not nama or not nisn or not nama_kelas:
        return jsonify({"status": "error", "message": "Nama, NISN, dan Nama Kelas harus diisi"})

    # Menggunakan find_one untuk menemukan dokumen pengguna berdasarkan username
    user_data = db.data_kelasUser.find_one({'username': username})

    if user_data:
        # Menggunakan list comprehension untuk menemukan kelas yang sesuai dengan id
        kelas_tertentu = next((kelas for kelas in user_data['kelas'] if kelas['id'] == id), None)

        if kelas_tertentu:
            # Persiapkan data siswa untuk data_kelasUser
            siswa_data_kelasUser = {
                'id' : str(ObjectId()),
                'nama': nama,
                'nisn': nisn,
                'hadir': 0,
                'izin': 0,
                'sakit': 0,
                'alpha': 0
            }

            # Perbarui koleksi data_kelasUser berdasarkan ID
            result = db.data_kelasUser.update_one(
                {'username': username, 'kelas.id': id},
                {'$push': {'kelas.$.data_siswa': siswa_data_kelasUser}}
            )

            if result.modified_count == 0:
                return jsonify({"status": "error", "message": "Gagal menambahkan siswa"})

            # Menghitung ulang jumlah siswa setelah penambahan
            user_data = db.data_kelasUser.find_one({'username': username})
            kelas_tertentu = next((kelas for kelas in user_data['kelas'] if kelas['id'] == id), None)

            if kelas_tertentu:
                jumlah_siswa = len(kelas_tertentu['data_siswa'])

                # Perbarui jumlah siswa di kelas
                result = db.data_kelasUser.update_one(
                    {'username': username, 'kelas.id': id},
                    {'$set': {'kelas.$.jumlah_siswa': jumlah_siswa}}
                )

                if result.modified_count == 0:
                    return jsonify({"status": "error", "message": "Gagal memperbarui jumlah siswa"})

            return jsonify({"status": "success", "message": "Berhasil"})
        else:
            return jsonify({"status": "error", "message": "Kelas dengan ID tersebut tidak ditemukan."})
    else:
        return jsonify({"status": "error", "message": "Pengguna dengan username tersebut tidak ditemukan."})


@app.route("/tambah_kelasUser", methods=["POST"])
def tambah_kelasUser():
    username = session.get('username')
    if username:
        nama_kelas = request.form.get('nama_kelas')
        data_kelas = request.form.get('kelas')
        kelas, jumlah_siswa = data_kelas.split('|')
        # Konversi jumlah_siswa menjadi integer
        jumlah_siswa = int(jumlah_siswa)
        mata_pelajaran = request.form.get('mata_pelajaran')
        timestamp = datetime.utcnow()

        # Ambil data siswa dari koleksi kelas berdasarkan nama_kelas
        kelas_info = db.kelas.find_one({'nama_kelas': kelas})
        data_siswa = []
        if kelas_info and 'siswa' in kelas_info:
            for siswa in kelas_info['siswa']:
                data_siswa.append({
                    'id' : str(siswa['_id']),
                    'nisn': siswa['nisn'],
                    'nama': siswa['nama'],
                    'hadir': 0,
                    'izin': 0,
                    'sakit': 0,
                    'alpha': 0
                })

        kelas_data = {
            'id': str(ObjectId()),
            'nama_kelas': nama_kelas,
            'kelas': kelas,
            'jumlah_siswa': jumlah_siswa,
            'mata_pelajaran': mata_pelajaran,
            'timestamp': timestamp,
            'data_siswa': data_siswa
        }

        # Cek apakah ada pengguna dengan username yang sama di database
        existing_user = db.data_kelasUser.find_one({'username': username})

        # Jika pengguna tidak ada, buat entri baru dengan pengguna tersebut
        if not existing_user:
            db.data_kelasUser.insert_one({'username': username, 'kelas': [kelas_data]})
        else:
            # Jika pengguna sudah ada, tambahkan kelas baru ke daftar kelas mereka
            db.data_kelasUser.update_one(
                {'username': username},
                {'$push': {'kelas': kelas_data}}
            )

        return redirect(url_for('absensi'))

    return redirect(url_for('login'))

@app.route("/absensi3/<id>", methods=['GET'])
def absensi3(id):
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        payload = jwt.decode(
            token_receive, 
            SECRET_KEY, 
            algorithms=["HS256"]
        )
        user_info = db.users.find_one({"username": payload.get("username")})
        username = user_info['username']
        nama = session.get("nama")
        nip = session.get("nip")
        profile_picture = session.get("profile_picture")

        data_kelas = db.data_kelasUser.find_one({'kelas': {'$elemMatch': {'id': id}}})
        if data_kelas and 'kelas' in data_kelas:
            # Mencari data array kelas yang memiliki id yang dicari
            for kelas in data_kelas['kelas']:
                if kelas['id'] == id:
                    kelasUser = kelas

        return render_template("absensi3.html",nama=nama,nip=nip, profile_picture=profile_picture, username=username, kelasUser=kelasUser, id=id)
    except jwt.ExpiredSignatureError:
        msg = "Your login token has expired"
        return redirect(url_for("login", msg=msg))
    except jwt.exceptions.DecodeError:
        msg = "There was a problem logging you in"
        return redirect(url_for("login", msg=msg))
    

@app.route('/save_absensi', methods=['POST'])
def save_absensi():
    data = request.json
    idKelas = data['idKelas']
    absensiData = {
        'id' : str(ObjectId()),
        'tgl': data['tgl'],
        'uraian': data['uraian'],
        'jam': data['jam'],
        'keterlaksanaan': data['keterlaksanaan'],
        'dataSiswa': data['dataSiswa']
    }

    # Update data_kelasUser collection
    db.data_kelasUser.update_one(
        {'kelas.id': idKelas},
        {'$push': {'kelas.$.data_absensi': absensiData}}
    )

    # Update kehadiran siswa
    for siswa in data['dataSiswa']:
        kehadiran = siswa['kehadiran']
        nisn = siswa['nisn']
        update_field = 'kelas.$[outer].data_siswa.$[inner].' + kehadiran
        db.data_kelasUser.update_one(
            {'kelas.id': idKelas, 'kelas.data_siswa.nisn': nisn},
            {'$inc': {update_field: 1}},
            array_filters=[{'outer.id': idKelas}, {'inner.nisn': nisn}]
        )

    return jsonify({'status': 'success'})

@app.route('/edit_absensi/<idKelas>', methods=['GET'])
def edit_absensi_page(idKelas):
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        payload = jwt.decode(
            token_receive, 
            SECRET_KEY, 
            algorithms=["HS256"]
        )
        nama = session.get("nama")
        nip = session.get("nip")
        profile_picture = session.get("profile_picture")

        # Ambil data absensi berdasarkan idKelas 
        kelas_data = db.data_kelasUser.find_one({'kelas.id': idKelas})
        if not kelas_data:
            return "Data kelas tidak ditemukan", 404

        # Mengambil data absensi dari item pertama di dalam list kelas
        kelas_item = next((item for item in kelas_data['kelas'] if item['id'] == idKelas), None)
        if not kelas_item:
            return "Data absensi tidak ditemukan", 404

        absensi_data = kelas_item.get('data_absensi', [])

        return render_template('absensi4.html', absensi_data=absensi_data, kelas_data=kelas_item,nama=nama,nip=nip, profile_picture=profile_picture)

    except jwt.ExpiredSignatureError:
        msg = "Your login token has expired"
        return redirect(url_for("login", msg=msg))
    except jwt.exceptions.DecodeError:
        msg = "There was a problem logging you in"
        return redirect(url_for("login", msg=msg))


@app.route('/edit_absensi/<idKelas>', methods=['POST'])
def edit_absensi(idKelas):
    data = request.json
    absensi_id = data['absensi_id']
    tgl = data['tgl']
    uraian = data['uraian']
    jam = data['jam']
    keterlaksanaan = data['keterlaksanaan']
    dataSiswa = data['dataSiswa']

    # Ambil data absensi sebelumnya
    kelas_data = db.data_kelasUser.find_one({'kelas.id': idKelas, 'kelas.data_absensi.id': absensi_id}, {'kelas.$': 1})
    prev_absensi = None
    if kelas_data:
        for k in kelas_data['kelas']:
            for absensi in k['data_absensi']:
                if absensi['id'] == absensi_id:
                    prev_absensi = absensi
                    break
            if prev_absensi:
                break

    if not prev_absensi:
        return jsonify({'status': 'error', 'message': 'Absensi not found'}), 404

    # Update data_absensi
    db.data_kelasUser.update_one(
        {'kelas.id': idKelas, 'kelas.data_absensi.id': absensi_id},
        {'$set': {
            'kelas.$.data_absensi.$[absensi].tgl': tgl,
            'kelas.$.data_absensi.$[absensi].uraian': uraian,
            'kelas.$.data_absensi.$[absensi].jam': jam,
            'kelas.$.data_absensi.$[absensi].keterlaksanaan': keterlaksanaan,
            'kelas.$.data_absensi.$[absensi].dataSiswa': dataSiswa
        }},
        array_filters=[{'absensi.id': absensi_id}]
    )

    # Update kehadiran siswa hanya jika ada perubahan
    for siswa in dataSiswa:
        nisn = siswa['nisn']
        kehadiran = siswa['kehadiran']

        # Find previous kehadiran for this student
        prev_kehadiran = next((s['kehadiran'] for s in prev_absensi['dataSiswa'] if s['nisn'] == nisn), None)

        if prev_kehadiran and prev_kehadiran != kehadiran:
            # Decrement the previous kehadiran count
            decrement_field = 'kelas.$[outer].data_siswa.$[inner].' + prev_kehadiran
            db.data_kelasUser.update_one(
                {'kelas.id': idKelas},
                {'$inc': {decrement_field: -1}},
                array_filters=[{'outer.id': idKelas}, {'inner.nisn': nisn}]
            )

            # Increment the new kehadiran count
            increment_field = 'kelas.$[outer].data_siswa.$[inner].' + kehadiran
            db.data_kelasUser.update_one(
                {'kelas.id': idKelas},
                {'$inc': {increment_field: 1}},
                array_filters=[{'outer.id': idKelas}, {'inner.nisn': nisn}]
            )

    return jsonify({'status': 'success'})

@app.route('/hapus_absensi', methods=['POST'])
def hapus_absensi():
    id_kelas = request.form['id_kelas']
    id_absensi = request.form['id_absensi']

    # Ambil data absensi yang akan dihapus
    kelas_data = db.data_kelasUser.find_one(
        {'kelas.id': id_kelas, 'kelas.data_absensi.id': id_absensi},
        {'kelas.$': 1}
    )
    if not kelas_data:
        return jsonify({'status': 'error', 'message': 'Absensi not found'})
    # Temukan data absensi yang akan dihapus
    kelas_item = next((item for item in kelas_data['kelas'] if item['id'] == id_kelas), None)
    if not kelas_item:
        return jsonify({'status': 'error', 'message': 'Kelas not found'})
    absensi_item = next((item for item in kelas_item['data_absensi'] if item['id'] == id_absensi), None)
    if not absensi_item:
        return jsonify({'status': 'error', 'message': 'Absensi item not found'})
    # Update kehadiran siswa berdasarkan data absensi yang akan dihapus
    for siswa in absensi_item['dataSiswa']:
        nisn = siswa['nisn']
        kehadiran = siswa['kehadiran']
        decrement_field = 'kelas.$[outer].data_siswa.$[inner].' + kehadiran
        db.data_kelasUser.update_one(
            {'kelas.id': id_kelas},
            {'$inc': {decrement_field: -1}},
            array_filters=[{'outer.id': id_kelas}, {'inner.nisn': nisn}]
        )
    # Hapus data absensi
    result = db.data_kelasUser.update_one(
        {'kelas.id': id_kelas},
        {'$pull': {'kelas.$.data_absensi': {'id': id_absensi}}}
    )
    if result.modified_count > 0:
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': 'Absensi Tidak Bisa Dihapus'})

@app.route("/cetak_absen/<id>", methods=['GET'])
def cetak_absen(id):
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        payload = jwt.decode(
            token_receive, 
            SECRET_KEY, 
            algorithms=["HS256"]
        )
        # user_info = db.users.find_one({"username": payload.get("username")})
        # username = user_info['username']
        nama = session.get("nama")
        nip = session.get("nip")

        data_kelas = db.data_kelasUser.find_one({'kelas': {'$elemMatch': {'id': id}}})
        if data_kelas and 'kelas' in data_kelas:
            # Mencari data array kelas yang memiliki id yang dicari
            for kelas in data_kelas['kelas']:
                if kelas['id'] == id:
                    kelasUser = kelas
        return render_template("cetak_absensi.html",nama=nama,nip=nip, kelasUser=kelasUser,id=id)

    except jwt.ExpiredSignatureError:
        msg = "Your login token has expired"
        return redirect(url_for("login", msg=msg))
    except jwt.exceptions.DecodeError:
        msg = "There was a problem logging you in"
        return redirect(url_for("login", msg=msg))

@app.route("/pengaturan", methods=['GET'])
def pengaturan():
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        payload = jwt.decode(
            token_receive, 
            SECRET_KEY, 
            algorithms=["HS256"]
        )
        user_id = session.get("id")
        user_info = db.users.find_one({"_id": ObjectId(user_id)})

        if user_info:
            nama = user_info.get("nama")
            nip = user_info.get("nip")
            profile_picture = user_info.get("profile_picture")
            username = user_info.get("username")
            return render_template("pengaturan.html", nama=nama, nip=nip, profile_picture=profile_picture, username=username, id=user_id)
        else:
            msg = "User information not found"
            return redirect(url_for("login", msg=msg))
    except jwt.ExpiredSignatureError:
        msg = "Your login token has expired"
        return redirect(url_for("login", msg=msg))
    except jwt.exceptions.DecodeError:
        msg = "There was a problem logging you in"
        return redirect(url_for("login", msg=msg))

# Fungsi untuk memastikan direktori ada
def ensure_directory_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)    

# Fungsi untuk menghapus file
def delete_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)

@app.route('/upload_profile_picture', methods=['POST'])
def upload_profile_picture():
    if 'profile_picture' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file part in the request'}), 400

    file = request.files['profile_picture']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No selected file'}), 400

    if file:
        filename = secure_filename(file.filename)
        ensure_directory_exists(app.config['UPLOAD_FOLDER'])
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Simpan nama file lama
        user_id = request.form['user_id']
        user_info = db.users.find_one({'_id': ObjectId(user_id)})
        if user_info:
            old_profile_picture = user_info.get('profile_picture', None)

        # Update nama file di basis data
        db.users.update_one({'_id': ObjectId(user_id)}, {'$set': {'profile_picture': 'foto/'+filename}})

        # Hapus file lama jika ada
        if old_profile_picture:
            old_file_path = os.path.join(app.config['UPLOAD_FOLDER'], old_profile_picture.replace('foto/', ''))
            delete_file(old_file_path)

        return jsonify({'status': 'success', 'message': 'File uploaded, database updated, and old file deleted successfully'}), 200

    return jsonify({'status': 'error', 'message': 'Failed to upload file'}), 500

@app.route("/ubah_username_nip", methods=['POST'])
def update_username_nip():
    user_id = request.form['user_id']
    original_username = request.form['original_username']
    new_username = request.form['username']
    new_nip = request.form['nip']

    # Cek apakah username sudah ada, kecuali untuk data yang sedang diubah
    existing_user_by_username = db.users.find_one({'username': new_username, '_id': {'$ne': ObjectId(user_id)}})
    if existing_user_by_username:
        return jsonify({'status': 'error', 'message': 'Username sudah digunakan'}), 400

    # Cek apakah NIP sudah ada, kecuali untuk data yang sedang diubah
    existing_user_by_nip = db.users.find_one({'nip': new_nip, '_id': {'$ne': ObjectId(user_id)}})
    if existing_user_by_nip:
        return jsonify({'status': 'error', 'message': 'NIP sudah digunakan'}), 400

    # Lakukan pembaruan data pengguna
    try:
        # Update username dan NIP di koleksi users
        db.users.update_one({'_id': ObjectId(user_id)}, {'$set': {'username': new_username, 'nip': new_nip}})

        # Update username di koleksi data_kelasUser
        db.data_kelasUser.update_many({'username': original_username}, {'$set': {'username': new_username}})

        # Update username di koleksi matriks_pembelajaran
        db.matriks_pembelajaran.update_many({'username': original_username}, {'$set': {'username': new_username}})

        return jsonify({'status': 'success', 'message': 'Username dan NIP berhasil diperbarui'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# Rute untuk mengubah password
@app.route("/ubah_password", methods=['POST'])
def ubah_password():
    # Ambil data dari form
    user_id = request.form['id']
    old_password = request.form['old_password']
    new_password = request.form['new_password']
    konfirmasi_password = request.form['konfirmasi_password']
    
    # Validasi password baru dan konfirmasi password
    if new_password != konfirmasi_password:
        return jsonify({'status': 'error', 'message': 'Password baru dan konfirmasi password tidak cocok'})
    
    # Cari pengguna di database berdasarkan user_id
    user = db.users.find_one({'_id': ObjectId(user_id)})
    if not user:
        return jsonify({'status': 'error', 'message': 'Pengguna tidak ditemukan'})
    
    # Periksa apakah password lama sesuai
    if user['password'] != old_password:
        return jsonify({'status': 'error', 'message': 'Password lama salah'})

    # Perbarui password di database
    try:
        db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {'password': new_password}}
        )
        return jsonify({'status': 'success', 'message': 'Password berhasil diubah'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route("/pembelajaran", methods=['GET'])
def pembelajaran():
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        payload = jwt.decode(
            token_receive, 
            SECRET_KEY, 
            algorithms=["HS256"]
        )

        nama = session.get("nama")
        nip = session.get("nip")
        username = session.get("username")
        profile_picture = session.get("profile_picture")
        user = db.data_kelasUser.find_one({'username': username})
        pembelajaran = db.matriks_pembelajaran.find_one({'username': username})

        if pembelajaran:
            data_semesters = pembelajaran.get('data', [])

            # Ambil data nama dari setiap elemen data
            data_matriks = [data for data in data_semesters]

            return render_template("pembelajaran.html", data_matriks=data_matriks,nama=nama, nip=nip,profile_picture=profile_picture, user=user)
        else:
            return render_template("pembelajaran.html", data_matriks=[],nama=nama, nip=nip,profile_picture=profile_picture, user=user)
      
    except jwt.ExpiredSignatureError:
        msg = "Your login token has expired"
        return redirect(url_for("login", msg=msg))
    except jwt.exceptions.DecodeError:
        msg = "There was a problem logging you in"
        return redirect(url_for("login", msg=msg))
    
@app.route('/tambah_matriks', methods=['POST'])
def tambah_matriks():
    nama = request.form['nama']
    kelas_ids = request.form.getlist('kelas')
    username = session.get("username")

    rekap_absensi_list = []

    for kelas_id in kelas_ids:
        kelas = db.data_kelasUser.find_one(
            {'kelas.id': kelas_id},
            {'kelas.$': 1}
        )
        if kelas and 'kelas' in kelas:
            kelas_info = kelas['kelas'][0]

            for absensi in kelas_info.get('data_absensi', []):
                hadir = 0
                tidak_hadir = 0
                siswa_tidak_hadir = []

                for dataSiswa in absensi['dataSiswa']:
                    if dataSiswa['kehadiran'] == 'hadir':
                        hadir += 1
                    else:
                        tidak_hadir += 1
                        siswa_tidak_hadir.append(dataSiswa['nama'])

                data_rekap_absensi = {
                    'id': kelas_info['id'],
                    'nama_kelas': kelas_info['nama_kelas'],
                    'tanggal': absensi['tgl'],
                    'jam': absensi['jam'],
                    'kelas': kelas_info['kelas'],
                    'mata_pelajaran': kelas_info['mata_pelajaran'],
                    'uraian': absensi['uraian'],
                    'keterlaksanaan': absensi['keterlaksanaan'],
                    'kehadiran_siswa': {
                        'hadir': hadir,
                        'tidak_hadir': tidak_hadir,
                        'jumlah': hadir + tidak_hadir,
                        'siswa_tidak_hadir': siswa_tidak_hadir
                    }
                }

                rekap_absensi_list.append(data_rekap_absensi)

    # Mencari dokumen pengguna yang sesuai
    user_data = db.matriks_pembelajaran.find_one({'username': username})

    if user_data:
        # Jika dokumen pengguna ditemukan, tambahkan data baru ke array data
        db.matriks_pembelajaran.update_one(
            {'username': username},
            {'$push': {'data': {'id': str(ObjectId()), 'nama': nama, 'data_rekap': rekap_absensi_list}}}
        )
    else:
        # Jika dokumen pengguna tidak ditemukan, buat dokumen baru
        new_user_data = {
            'username': username,
            'data': [{'id': str(ObjectId()), 'nama': nama, 'data_rekap': rekap_absensi_list}]
        }
        db.matriks_pembelajaran.insert_one(new_user_data)

    return redirect(url_for('pembelajaran'))

@app.route("/pembelajaran2/<id>", methods=['GET'])
def pembelajaran2(id):
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        payload = jwt.decode(
            token_receive, 
            SECRET_KEY, 
            algorithms=["HS256"]
        )
        nip = session.get("nip")
        nama = session.get("nama")
        username = session.get("username")
        profile_picture = session.get("profile_picture")
        
        # Mengambil data matriks pembelajaran dari MongoDB berdasarkan ID
        pembelajaran = db.matriks_pembelajaran.find_one({
            'username': username,
            'data.id': id
        })
        if pembelajaran:
            data_semester = None
            for data in pembelajaran['data']:
                if data['id'] == id:
                    data_semester = data
                    break
            
            if data_semester:
                return render_template("pembelajaran2.html", 
                                       nip=nip, 
                                       profile_picture=profile_picture, 
                                       nama=nama,
                                       data_semester=data_semester)
            else:
                print(f'Data dengan id {id} tidak ditemukan.')
                return redirect(url_for('pembelajaran'))
        else:
            print('Data matriks pembelajaran tidak ditemukan.')
            return redirect(url_for('pembelajaran'))
      
    except jwt.ExpiredSignatureError:
        msg = "Your login token has expired"
        return redirect(url_for("login", msg=msg))
    except jwt.exceptions.DecodeError:
        msg = "There was a problem logging you in"
        return redirect(url_for("login", msg=msg))
    
@app.route('/hapusmatriks', methods=['POST'])
def hapusmatriks():
    id = request.form['id']
    username = session.get('username')

    # Konversi id ke ObjectId jika perlu
    id_to_delete = ObjectId(id)

    result = db.matriks_pembelajaran.update_one(
        {'username': username},
        {'$pull': {'data': {'id': id}}}
    )

    if result.modified_count > 0:
        return jsonify({'status': 'success', 'message': 'succsess'})
    else:
        return jsonify({'status': 'error', 'message': f'Data dengan id {id} tidak ditemukan atau tidak dihapus.'})

@app.route('/cetak/<id>', methods=['GET'])
def cetak(id):       
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        payload = jwt.decode(
            token_receive, 
            SECRET_KEY, 
            algorithms=["HS256"]
        )
        nip = session.get("nip")
        nama = session.get("nama")
        username = session.get("username")
        
        # Mengambil data matriks pembelajaran dari MongoDB berdasarkan ID
        pembelajaran = db.matriks_pembelajaran.find_one({
            'username': username,
            'data.id': id
        })
        if pembelajaran:
            data_semester = None
            for data in pembelajaran['data']:
                if data['id'] == id:
                    data_semester = data
                    break
            
            if data_semester:
                return render_template("print.html", 
                                       nama=nama,
                                       nip=nip, 
                                       username=username,
                                       data_semester=data_semester)
            else:
                print(f'Data dengan id {id} tidak ditemukan.')
                return redirect(url_for('pembelajaran'))
        else:
            print('Data matriks pembelajaran tidak ditemukan.')
            return redirect(url_for('pembelajaran'))
      
    except jwt.ExpiredSignatureError:
        msg = "Your login token has expired"
        return redirect(url_for("login", msg=msg))
    except jwt.exceptions.DecodeError:
        msg = "There was a problem logging you in"
        return redirect(url_for("login", msg=msg))


#FITUR ADMIN#
## 
## 
@app.route("/daftaruser", methods=['GET'])
def daftaruser():
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        payload = jwt.decode(
            token_receive, 
            SECRET_KEY, 
            algorithms=["HS256"]
        )

        users = list(db.users.find())
        
        return render_template("daftaruser.html",users=users)
    except jwt.ExpiredSignatureError:
        msg = "Your login token has expired"
        return redirect(url_for("login", msg=msg))
    except jwt.exceptions.DecodeError:
        msg = "There was a problem logging you in"
        return redirect(url_for("login", msg=msg))

@app.route("/tambah_user", methods=['POST'])
def tambah_user():
    nama = request.form['nama']
    nip = request.form['nip']
    username = request.form['username']
    password = request.form['password']
    role = 'guru'
    
    # Cek apakah username atau NIP sudah ada
    if db.users.find_one({'username': username}) or db.users.find_one({'nip': nip}):
        return jsonify({'status': 'error', 'message': 'Username atau NIP sudah ada'}), 400

    # Buat dokumen pengguna baru
    user_data = {
        'nama': nama,
        'nip': nip,
        'username': username,
        'password': password,
        'profile_picture': 'icon/Aktor.png',  
        'role': role
    }

    try:
        # Simpan ke MongoDB
        db.users.insert_one(user_data)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route("/update_user", methods=['POST'])
def update_user():
    user_id = request.form['id']
    nama = request.form['nama']
    nip = request.form['nip']
    username = request.form['username']
    password = request.form['password']

    db.users.update_one(
        {'_id': ObjectId(user_id)},
        {'$set': {
            'nama': nama,
            'nip': nip,
            'username': username,
            'password': password
        }}
    )
    return jsonify({'status': 'success'})


@app.route("/delete_user", methods=['POST'])
def delete_user():
    user_id = request.form['id']
    user_username = request.form['username']
    
    # Menghapus pengguna dari koleksi 'users'
    db.users.delete_one({'_id': ObjectId(user_id)})
    
    # Menghapus data dari koleksi 'data_kelasUser' berdasarkan 'username'
    db.data_kelasUser.delete_many({'username': user_username})
    
    # Menghapus data dari koleksi 'matriks_pembelajaran' berdasarkan 'username'
    db.matriks_pembelajaran.delete_many(
        {'username': user_username}
    )
    
    return jsonify({'status': 'success'})

@app.route('/tambah_kelas_admin', methods=['POST'])
def tambah_kelas_admin():
    namakelas = request.form['namakelas']
    print(namakelas)
    # Cek apakah nama kelas sudah ada
    if db.kelas.find_one({'nama_kelas': namakelas}):
        return jsonify({'status': 'error', 'message': 'Nama kelas sudah ada'})
    
    # Jika belum ada, tambahkan kelas baru ke database
    kelas = {
        'nama_kelas': namakelas,
        'siswa': []
    }
    db.kelas.insert_one(kelas)
    
    return jsonify({'status': 'success'})

@app.route("/daftarsiswa", methods=['GET'])
def daftarsiswa():
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        payload = jwt.decode(
            token_receive, 
            SECRET_KEY, 
            algorithms=["HS256"]
        )
        kelas_list = list(db.kelas.find())

        return render_template("daftarsiswa.html",kelas_list=kelas_list)
    except jwt.ExpiredSignatureError:
        msg = "Your login token has expired"
        return redirect(url_for("login", msg=msg))
    except jwt.exceptions.DecodeError:
        msg = "There was a problem logging you in"
        return redirect(url_for("login", msg=msg))
    
@app.route("/detailkelas/<id>", methods=['GET'])
def detailkelas(id):
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        payload = jwt.decode(
            token_receive, 
            SECRET_KEY, 
            algorithms=["HS256"]
        )
        # Cari kelas berdasarkan id
        kelas = db.kelas.find_one({"_id": ObjectId(id)})
        if not kelas:
            return redirect(url_for("daftarsiswa"))
        
        return render_template("detailkelas.html", kelas=kelas, id=id)
    except jwt.ExpiredSignatureError:
        msg = "Your login token has expired"
        return redirect(url_for("login", msg=msg))
    except jwt.exceptions.DecodeError:
        msg = "There was a problem logging you in"
        return redirect(url_for("login", msg=msg))

@app.route('/tambah_siswa_admin/<id>', methods=['POST'])
def tambah_siswa_admin(id):
    # Ambil data siswa dari request
    id_untuk_siswa = ObjectId()
    data_siswa = {
        '_id': id_untuk_siswa,  # Tambahkan ID unik untuk setiap siswa
        'nis': request.form['nis'],
        'nisn': request.form['nisn'],
        'nama': request.form['nama'],
        'jenis_kelamin': request.form['jk'],
    }

    # Cari kelas berdasarkan ID
    kelas = db.kelas.find_one({'_id': ObjectId(id)})
    if kelas:
        # Pengecekan apakah siswa dengan NIS atau NISN yang sama sudah ada
        if any(siswa['nis'] == data_siswa['nis'] for siswa in kelas['siswa']):
            return jsonify({'status': 'error', 'message': 'Siswa dengan NIS tersebut sudah ada dalam kelas'})

        if any(siswa['nisn'] == data_siswa['nisn'] for siswa in kelas['siswa']):
            return jsonify({'status': 'error', 'message': 'Siswa dengan NISN tersebut sudah ada dalam kelas'})

        # Tambahkan siswa ke dalam array siswa di kelas
        db.kelas.update_one(
            {'_id': kelas['_id']},
            {'$push': {'siswa': data_siswa}}
        )
        
        # Tambahkan atau perbarui siswa di koleksi data_kelasUser
        update_result = db.data_kelasUser.update_many(
            {'kelas.kelas': kelas['nama_kelas']},
            {
                '$push': {
                    'kelas.$[kelasElem].data_siswa': {
                        'id': str(id_untuk_siswa),
                        'nama': data_siswa['nama'],
                        'nisn': data_siswa['nisn'],
                        'hadir': 0,
                        'izin': 0,
                        'sakit': 0,
                        'alpha': 0
                    }
                },
                '$inc': {'kelas.$[kelasElem].jumlah_siswa': 1}
            },
            array_filters=[{'kelasElem.kelas': kelas['nama_kelas']}]
        )

        return jsonify({'status': 'success', 'message': 'Siswa berhasil ditambahkan ke dalam kelas'})
    else:
        return jsonify({'status': 'error', 'message': 'Kelas tidak ditemukan'})

@app.route('/hapus_kelas_admin', methods=['POST'])
def hapus_kelas_admin():
    try:
        id_kelas = ObjectId(request.form['id'])

        # Cari kelas berdasarkan ID
        kelas = db.kelas.find_one({'_id': id_kelas})

        if kelas:
            # Hapus kelas dari koleksi 'kelas'
            db.kelas.delete_one({'_id': id_kelas})
            
            # Di sini Anda bisa juga menghapus referensi kelas dari koleksi lain jika diperlukan

            return jsonify({'status': 'success', 'message': 'Kelas berhasil dihapus'})
        else:
            return jsonify({'status': 'error', 'message': 'Kelas tidak ditemukan'})

    except Exception as e:
        print(str(e))
        return jsonify({'status': 'error', 'message': 'Terjadi kesalahan saat menghapus kelas'})

@app.route('/edit_siswa_admin', methods=['POST'])
def edit_siswa_admin():
    try:
        id_siswa = request.form['id']
        nis = request.form['nis']
        nisn = request.form['nisn']
        nama = request.form['nama']
        jenis_kelamin = request.form['jk']

        # Update data siswa berdasarkan ID siswa
        result = db.kelas.update_one(
            {'siswa._id': ObjectId(id_siswa)},
            {'$set': {
                'siswa.$.nis': nis,
                'siswa.$.nisn': nisn,
                'siswa.$.nama': nama,
                'siswa.$.jenis_kelamin': jenis_kelamin
            }}
        )

        if result.matched_count > 0:
            # Update data_kelasUser juga
            update_kelasUser_result = db.data_kelasUser.update_many(
                {'kelas.data_siswa.id': id_siswa},
                {'$set': {
                    'kelas.$[kelasElem].data_siswa.$[siswaElem].nisn': nisn,
                    'kelas.$[kelasElem].data_siswa.$[siswaElem].nama': nama
                }},
                array_filters=[
                    {'kelasElem.data_siswa.id': id_siswa},
                    {'siswaElem.id': id_siswa}
                ]
            )

            return jsonify({'status': 'success', 'message': 'Siswa berhasil diubah'})
        else:
            return jsonify({'status': 'error', 'message': 'Siswa tidak ditemukan'})

    except Exception as e:
        print(str(e))
        return jsonify({'status': 'error', 'message': 'Terjadi kesalahan saat mengubah data siswa'})


@app.route('/hapus_siswa_admin', methods=['POST'])
def hapus_siswa_admin():
    try:
        id_siswa = ObjectId(request.form['id'])

        # Update data kelas, hapus siswa berdasarkan ID siswa
        result = db.kelas.update_one(
            {'siswa._id': id_siswa},
            {'$pull': {'siswa': {'_id': id_siswa}}}
        )

        if result.modified_count > 0:
            return jsonify({'status': 'success', 'message': 'Siswa berhasil dihapus'})
        else:
            return jsonify({'status': 'error', 'message': 'Siswa tidak ditemukan'})

    except Exception as e:
        print(str(e))
        return jsonify({'status': 'error', 'message': 'Terjadi kesalahan saat menghapus siswa'})

@app.route("/daftarmapel", methods=['GET'])
def daftarmapel():
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        payload = jwt.decode(
            token_receive, 
            SECRET_KEY, 
            algorithms=["HS256"]
        )
        matkul = list(db.mata_pelajaran.find())

        return render_template("daftarmapel.html",matkul=matkul)
    except jwt.ExpiredSignatureError:
        msg = "Your login token has expired"
        return redirect(url_for("login", msg=msg))
    except jwt.exceptions.DecodeError:
        msg = "There was a problem logging you in"
        return redirect(url_for("login", msg=msg))

@app.route('/tambah_matkul', methods=['POST'])
def tambah_matkul():
    nama = request.form.get('nama')
    
    if not nama:
        return jsonify({'status': 'fail', 'message': 'Nama mata pelajaran harus diisi!'})

    # Cek apakah nama mata pelajaran sudah ada di database
    existing_matkul = db.mata_pelajaran.find_one({'nama_pelajaran': nama})
    if existing_matkul:
        return jsonify({'status': 'fail', 'message': 'Nama mata pelajaran sudah ada!'})

    try:
        db.mata_pelajaran.insert_one({'nama_pelajaran': nama})
        return jsonify({'status': 'success', 'message': 'Mata pelajaran berhasil ditambahkan!'})
    except Exception as e:
        return jsonify({'status': 'fail', 'message': str(e)})

@app.route('/hapus_matkul', methods=['POST'])
def hapus_matkul():
    id = request.form.get('id')
    db.mata_pelajaran.delete_one({'_id': ObjectId(id)})
    return jsonify({'status': 'success', 'message': 'Mata pelajaran berhasil dihapus!'})

@app.route('/update_matkul', methods=['POST'])
def update_matkul():
    id = request.form.get('id')
    nama = request.form.get('nama')
    if db.mata_pelajaran.find_one({'nama_pelajaran': nama, '_id': {'$ne': ObjectId(id)}}):
        return jsonify({'status': 'fail', 'message': 'Nama mata pelajaran sudah ada!'})
    db.mata_pelajaran.update_one({'_id': ObjectId(id)}, {'$set': {'nama_pelajaran': nama}})
    return jsonify({'status': 'success', 'message': 'Mata pelajaran berhasil diperbarui!'})


if __name__ == "__main__":
    app.run("0.0.0.0", port=5000, debug=True)