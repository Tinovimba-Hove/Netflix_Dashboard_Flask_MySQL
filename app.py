from flask import Flask, render_template, request
import pymysql
import yaml
from pathlib import Path

app = Flask(__name__)

def get_db_connection():
    config = yaml.safe_load(Path("config.yml").read_text())
    return pymysql.connect(
        host=config['db']['host'],
        port=config['db']['port'],
        user=config['db']['user'],
        passwd=config['db']['passwd'],
        db=config['db']['db'],
        autocommit=True
    )
    
@app.route('/')  
def home():
    return render_template('dashboard.html')  

@app.route('/shows_by_country', methods=['GET', 'POST'])
def shows_by_country():
    countries = []  
    data = {
        'ratings': {'x': [], 'y': []},
        'types': {'x': [], 'y': []},
        'durations': {'x': [], 'y': []}
    }  

    conn = get_db_connection()
    cur = conn.cursor(pymysql.cursors.DictCursor)
    cur.execute('SELECT DISTINCT country FROM netflix_shows;')
    for row in cur:
        countries.append(row['country'])

    if request.method == 'POST':
        selected_country = request.form['country']
        
        # Query for ratings
        sql_ratings = '''
            SELECT rating, COUNT(*) as count 
            FROM netflix_shows 
            WHERE country = %s 
            GROUP BY rating;
        '''
        cur.execute(sql_ratings, (selected_country,))
        for row in cur:
            data['ratings']['x'].append(row['rating'])
            data['ratings']['y'].append(row['count'])
        
        # Query for types
        sql_types = '''
            SELECT type, COUNT(*) as count 
            FROM netflix_shows 
            WHERE country = %s 
            GROUP BY type;
        '''
        cur.execute(sql_types, (selected_country,))
        for row in cur:
            data['types']['x'].append(row['type'])
            data['types']['y'].append(row['count'])
        
        # Query for durations
        sql_durations = '''
            SELECT duration, COUNT(*) as count 
            FROM netflix_shows 
            WHERE country = %s 
            GROUP BY duration;
        '''
        cur.execute(sql_durations, (selected_country,))
        for row in cur:
            data['durations']['x'].append(row['duration'])
            data['durations']['y'].append(row['count'])
    
    return render_template('shows_by_country.html', data=data, countries=countries)

@app.route('/directors', methods=['GET', 'POST'])
def directors():
    results = []
    director_keyword = ""

    conn = get_db_connection()
    cur = conn.cursor(pymysql.cursors.DictCursor)

    if request.method == 'POST':
        director_keyword = request.form['director_keyword']

        sql = '''
            SELECT director, title 
            FROM netflix_shows 
            WHERE director LIKE %s;
        '''
        cur.execute(sql, ('%' + director_keyword + '%',))
        results = cur.fetchall()

    return render_template('directors.html', results=results, director_keyword=director_keyword)

@app.route('/shows_by_year', methods=['GET', 'POST'])
def shows_by_year():
    years = []  
    data = {'x': [], 'y': []}  

    conn = get_db_connection()
    cur = conn.cursor(pymysql.cursors.DictCursor)
    cur.execute('SELECT DISTINCT release_year FROM netflix_shows ORDER BY release_year;')
    for row in cur:
        years.append(row['release_year'])

    if request.method == 'POST':
        start_year = request.form['start_year']
        end_year = request.form['end_year']
        
        sql = '''
            SELECT release_year, COUNT(*) as count 
            FROM netflix_shows 
            WHERE release_year BETWEEN %s AND %s 
            GROUP BY release_year;
        '''
        cur.execute(sql, (start_year, end_year))
        
        for row in cur:
            data['x'].append(row['release_year'])
            data['y'].append(row['count'])
    
    return render_template('shows_by_year.html', data=data, years=years)

@app.route('/search_by_keyword', methods=['GET', 'POST'])
def search_by_keyword():
    data = []
    keyword = ""  

    if request.method == 'POST':
        keyword = request.form['keyword']
        conn = get_db_connection()
        cur = conn.cursor(pymysql.cursors.DictCursor)
        sql = 'SELECT title, description FROM netflix_shows WHERE description LIKE %s;'
        cur.execute(sql, ('%' + keyword + '%',))

        for row in cur:
            data.append(row)
    
    return render_template('search_by_keyword.html', data=data, keyword=keyword)

@app.route('/pie_by_list_year', methods=['GET', 'POST'])
def pie_by_country_year():
    data = []
    years = []
    listed_in = ""
    year_range = (None, None)

    conn = get_db_connection()
    cur = conn.cursor(pymysql.cursors.DictCursor)

    cur.execute('SELECT DISTINCT release_year FROM netflix_shows ORDER BY release_year;')
    years = [row['release_year'] for row in cur.fetchall()]

    if request.method == 'POST':
        listed_in = request.form['listed_in']
        year_range = (int(request.form['start_year']), int(request.form['end_year']))
        
        sql = '''
            SELECT rating, COUNT(*) as count 
            FROM netflix_shows 
            WHERE listed_in LIKE %s AND release_year BETWEEN %s AND %s 
            GROUP BY rating 
            ORDER BY count DESC;
        '''
        cur.execute(sql, (listed_in, year_range[0], year_range[1]))

        for row in cur:
            data.append({'rating': row['rating'], 'count': int(row['count'])})
    
    return render_template('pie_by_list_year.html', data=data, years=years, listed_in=listed_in, year_range=year_range)

@app.route('/genre_by_years', methods=['GET', 'POST'])
def genre_by_years():
    data = []
    years = []
    genre_keyword = ""

    conn = get_db_connection()
    cur = conn.cursor(pymysql.cursors.DictCursor)

    cur.execute('SELECT DISTINCT release_year FROM netflix_shows ORDER BY release_year;')
    years = [row['release_year'] for row in cur.fetchall()]

    if request.method == 'POST':
        genre_keyword = request.form['listed_in']
        start_year = int(request.form['start_year'])
        end_year = int(request.form['end_year'])

        sql = '''
            SELECT 
                listed_in AS genre, 
                release_year AS year, 
                COUNT(*) AS count 
            FROM 
                netflix_shows 
            WHERE 
                listed_in LIKE %s AND release_year BETWEEN %s AND %s
            GROUP BY 
                genre, year 
            ORDER BY 
                year, genre;
        '''
        cur.execute(sql, ('%' + genre_keyword + '%', start_year, end_year))
        data = cur.fetchall()

    return render_template('genre_by_years.html', data=data, genre_keyword=genre_keyword, years=years)

if __name__ == '__main__':
    app.run(debug=True)