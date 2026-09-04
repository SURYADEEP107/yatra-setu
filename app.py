from flask import Flask, render_template, request, jsonify, session
import sqlite3
import os

app = Flask(__name__)
# REQUIRED: Flask needs a secret key to manage user login sessions safely
app.secret_key = 'sih_yatra_setu_secret_key_2024'
DB_FILE = 'yatrasetu_vikshit.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 1. Main Places Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS places (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            landscape TEXT,
            state TEXT,
            name TEXT,
            budget INTEGER,
            duration TEXT,
            description TEXT
        )
    ''')
    
    # 2. REQUIRED: Saved Trips Table (was missing)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS saved_trips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            destination_id INTEGER,
            FOREIGN KEY(destination_id) REFERENCES places(id)
        )
    ''')
    
    cursor.execute('SELECT COUNT(*) FROM places')
    if cursor.fetchone()[0] == 0:
        # Heavily expanded dataset
        sample_data = [
            # Mountains
            ('Mountains', 'Himachal Pradesh', 'Spiti Valley', 15000, '5 Days', 'A remote, high-altitude cold desert mountain valley.'),
            ('Mountains', 'West Bengal', 'Darjeeling', 12000, '3 Days', 'Famous for its tea gardens and views of Kangchenjunga.'),
            ('Mountains', 'Uttarakhand', 'Auli', 14000, '4 Days', 'A premier Himalayan ski resort and hill station.'),
            ('Mountains', 'Arunachal Pradesh', 'Tawang', 16000, '4 Days', 'Known for its beautiful monasteries and high altitude passes.'),
            # Waterfalls
            ('Waterfalls', 'Karnataka', 'Jog Falls', 8000, '2 Days', 'One of the highest plunge waterfalls in India.'),
            ('Waterfalls', 'Meghalaya', 'Nohkalikai Falls', 10000, '3 Days', 'The tallest plunge waterfall in India with a deep green pool.'),
            ('Waterfalls', 'Kerala', 'Athirappilly Falls', 9000, '2 Days', 'The largest waterfall in Kerala, often called the Niagara of India.'),
            # Forests & National Parks
            ('Forests', 'West Bengal', 'Sundarbans Forest', 9000, '2 Days', 'World\'s largest mangrove forest, home to the Royal Bengal Tiger.'),
            ('National parks', 'Uttarakhand', 'Jim Corbett National Park', 12000, '3 Days', 'The oldest national park in India, rich in flora and fauna.'),
            ('National parks', 'Assam', 'Kaziranga National Park', 14000, '3 Days', 'Hosts two-thirds of the world\'s Great One-horned Rhinoceroses.'),
            ('National parks', 'Madhya Pradesh', 'Kanha National Park', 13000, '3 Days', 'A vast expanse of grassland and forest, the inspiration for The Jungle Book.'),
            # Trekking Routes
            ('Trekking Routes', 'West Bengal', 'Sandakphu Trek', 8500, '5 Days', 'Trek to the highest peak in West Bengal offering views of Everest.'),
            ('Trekking Routes', 'Ladakh', 'Chadar Trek', 25000, '8 Days', 'A thrilling winter trek over the frozen Zanskar River.'),
            ('Trekking Routes', 'Uttarakhand', 'Valley of Flowers Trek', 11000, '4 Days', 'Trek through a UNESCO site filled with vibrant alpine flowers.'),
            # Plateaus
            ('Plateaus', 'Meghalaya', 'Shillong Plateau', 10000, '3 Days', 'A beautiful rolling plateau known as the Scotland of the East.'),
            ('Plateaus', 'Madhya Pradesh', 'Malwa Plateau', 8000, '2 Days', 'Rich volcanic soil region with deep historical significance.'),
            # Religious Places
            ('Religious places', 'Uttar Pradesh', 'Kashi Vishwanath Temple', 6000, '2 Days', 'One of the most famous Hindu temples dedicated to Lord Shiva in Varanasi.'),
            ('Religious places', 'Odisha', 'Jagannath Temple', 7000, '2 Days', 'An important Hindu temple dedicated to Jagannath in Puri.'),
            ('Religious places', 'Punjab', 'Golden Temple', 8000, '2 Days', 'The holiest Gurdwara of Sikhism, located in Amritsar.'),
            # Historical Monuments & Museums
            ('Historical monuments', 'Delhi', 'Red Fort', 5000, '1 Day', 'A historic fort that served as the main residence of the Mughal Emperors.'),
            ('Historical monuments', 'Rajasthan', 'Amer Fort', 9000, '2 Days', 'A massive fort in Jaipur known for its artistic Hindu style elements.'),
            ('Museums', 'West Bengal', 'Victoria Memorial Hall Museum', 3000, '1 Day', 'A vast museum housing British colonial and Indian historical artifacts.'),
            ('Museums', 'Telangana', 'Salar Jung Museum', 4000, '1 Day', 'One of the three National Museums of India, located in Hyderabad.'),
            # UNESCO Sites
            ('UNESCO Sites', 'Uttar Pradesh', 'Taj Mahal', 15000, '2 Days', 'The iconic ivory-white marble mausoleum on the Yamuna river.'),
            ('UNESCO Sites', 'Karnataka', 'Group of Monuments at Hampi', 9000, '3 Days', 'The ruins of the magnificent ancient Vijayanagara Empire.'),
            ('UNESCO Sites', 'Maharashtra', 'Ellora Caves', 8000, '2 Days', 'One of the largest rock-cut monastery-temple cave complexes in the world.'),
            # Desert
            ('Desert', 'Rajasthan', 'Thar Desert', 16000, '4 Days', 'The Great Indian Desert with vast sand dunes and camel safaris.'),
            ('Desert', 'Gujarat', 'Great Rann of Kutch', 12000, '3 Days', 'A massive area of salt marshes that span the border.')
        ]
        cursor.executemany('INSERT INTO places (landscape, state, name, budget, duration, description) VALUES (?, ?, ?, ?, ?, ?)', sample_data)
        
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/options')
def get_options():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('SELECT DISTINCT landscape FROM places ORDER BY landscape')
    landscapes = [row[0] for row in cursor.fetchall()]
    
    cursor.execute('SELECT DISTINCT state FROM places ORDER BY state')
    states = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    return jsonify({'landscapes': landscapes, 'states': states})

@app.route('/api/search')
def search():
    landscape = request.args.get('landscape')
    state = request.args.get('state')
    budget = request.args.get('budget', type=int)
    
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = "SELECT * FROM places WHERE 1=1"
    params = []
    
    if landscape and landscape != 'All':
        query += " AND landscape = ?"
        params.append(landscape)
    if state and state != 'All':
        query += " AND state = ?"
        params.append(state)
    if budget:
        query += " AND budget <= ?"
        params.append(budget)
        
    cursor.execute(query, params)
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(results)

# --- USER SESSION & TRIPS ROUTES ---

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json or {}
    username = data.get('username')
    if username:
        session['username'] = username.strip()
        return jsonify({'message': 'Logged in successfully', 'username': session['username']})
    return jsonify({'error': 'Username required'}), 400

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    return jsonify({'message': 'Logged out successfully'})

@app.route('/api/user_status')
def user_status():
    if 'username' in session:
        return jsonify({'logged_in': True, 'username': session['username']})
    return jsonify({'logged_in': False})

@app.route('/api/save_trip', methods=['POST'])
def save_trip():
    if 'username' not in session:
        return jsonify({'error': 'Please login first'}), 401
        
    data = request.json or {}
    destination_id = data.get('destination_id')
    username = session['username']
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('SELECT id FROM saved_trips WHERE username = ? AND destination_id = ?', (username, destination_id))
    if cursor.fetchone():
        conn.close()
        return jsonify({'message': 'This destination is already in your saved trips!'})
        
    cursor.execute('INSERT INTO saved_trips (username, destination_id) VALUES (?, ?)', (username, destination_id))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Destination saved to My Trips!'})

@app.route('/api/my_trips')
def my_trips():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
        
    username = session['username']
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # REQUIRED FIX: Changed 'destinations d' to 'places p' to match your schema
    cursor.execute('''
        SELECT p.* FROM places p
        JOIN saved_trips s ON p.id = s.destination_id
        WHERE s.username = ?
        ORDER BY p.budget ASC
    ''', (username,))
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(results)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)