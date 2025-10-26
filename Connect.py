from flask import Flask, request, jsonify
from sqlalchemy import create_engine, text
import os, sys
from dotenv import load_dotenv 

# =====================================================
# 1️⃣ Cấu hình IBM DB2 driver cho Windows
# =====================================================
IBM_DB_DRIVER_PATH = os.environ.get(
    'IBM_DB_DRIVER_PATH', r"C:\Program Files\IBM\IBM DATA SERVER DRIVER\bin"
)
os.environ["IBM_DB_HOME"] = os.path.dirname(IBM_DB_DRIVER_PATH)
os.environ["PATH"] = IBM_DB_DRIVER_PATH + os.pathsep + os.environ.get("PATH", "")
if sys.version_info >= (3, 8):
    os.add_dll_directory(IBM_DB_DRIVER_PATH)

try:
    import ibm_db
    print("✅ ibm_db imported successfully")
except ImportError as e:
    print("❌ ImportError:", e)

# =====================================================
# 2️⃣ Cấu hình kết nối DB2 Cloud từ biến môi trường
# =====================================================
load_dotenv()  # Nếu bạn sử dụng python-dotenv để load biến môi trường từ .env file
dsn_hostname = os.environ.get('HOST_URL')
dsn_uid = os.environ.get('USERNAME')
dsn_pwd = os.environ.get('PASSWORD')
dsn_port = os.environ.get('PORT', '30875')
dsn_database = os.environ.get('DBNAME')

# Kiểm tra nếu biến môi trường chưa được set
if not all([dsn_hostname, dsn_uid, dsn_pwd, dsn_database]):
    raise EnvironmentError(
        "❌ Thiếu biến môi trường DB2. Vui lòng set: HOST_URL, USERNAME, PASSWORD, DBNAME"
    )

dsn = (
    f"ibm_db_sa://{dsn_uid}:{dsn_pwd}@"
    f"{dsn_hostname}:{dsn_port}/{dsn_database}?security=SSL"
)
engine = create_engine(dsn)
print("✅ DB2 Engine created successfully")

# =====================================================
# 3️⃣ Tạo Flask App
# =====================================================
app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({
        "message": "✅ Flask server đang chạy!",
        "routes": ["/query (POST)"]
    })

# =====================================================
# 4️⃣ Endpoint /query dành cho Watson Assistant
# =====================================================
@app.route('/query', methods=['POST'])
def query_db():
    user_data = request.get_json(silent=True)
    if not user_data or 'query_type' not in user_data or 'value' not in user_data:
        return jsonify({"error": "Thiếu JSON hoặc các trường 'query_type'/'value'"}), 400

    query_type = user_data['query_type'].strip().lower()
    value = user_data['value'].strip().lower()

    try:
        if query_type == "course":
            sql = text("SELECT * FROM CD106 WHERE LOWER(DESCRIPTION) LIKE :val FETCH FIRST 1 ROWS ONLY")
            with engine.connect() as conn:
                result = conn.execute(sql, {"val": f"%{value}%"}).fetchone()

            if not result:
                return jsonify({"Nothing_Found": f"Không tìm thấy '{value}' trong khóa học."})

            return jsonify({"COURSE": result.DESCRIPTION})

        else:
            return jsonify({"error": f"query_type '{query_type}' chưa được hỗ trợ"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =====================================================
# 5️⃣ Main
# =====================================================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
