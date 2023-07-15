## Authors:
##   João R. Campos <jrcampos@dei.uc.pt>
##
## FEAT:
##  Frederico Ferreira
##  Edsger W. Dijkstra
##  Carl Friedrich Gauss
##  Alan Turing
##  Ada Lovelace
##  Bill Gates
##  Steve Jobs
##  Sergey Brin
##  Jack Dorsey
##  Elon Musk
##  Jeff Bezos
##  HIDEO KOJIMA
##  e o Gui
##  aprentemente tinha me esqucido do goncalo com c de cedilha e g maiusculo

#* add more validations

import flask
import logging
import psycopg2
import datetime
import jwt
import os
from dotenv import load_dotenv
from functools import wraps
import random, string

app = flask.Flask(__name__)
print()
print(os.getenv('PASSWORD'))
def db_connection():
    db = psycopg2.connect(
        user=os.getenv('DB_USER'),
        password=os.getenv('PASSWORD'),
        host=os.getenv('IP'),
        port=os.getenv('PORT'),
        database=os.getenv('DATABASE')
    )

    return db


# decorator for verifying the JWT
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # jwt is passed in the request header
        if 'Authorization' in flask.request.headers:
            token = flask.request.headers['Authorization']
        # return 401 if token is not passed
        if not token:
            return flask.jsonify({'message' : 'Token is missing'}), 401
  
        try:
            # decoding the payload to fetch the stored details
            data = jwt.decode(token, key=os.getenv('SECRET_KEY'), algorithms=["HS256"])
        except:
            return flask.jsonify({
                'message' : 'Token is invalid !!'
            }), 401
        # returns the current logged in users context to the routes
        return  f(data['id'], data['role'], *args, **kwargs)
  
    return decorated

# REGISTER ENDPOINT
@app.route('/user/', methods=['POST'])
def add_user():
    logger.info('POST /user')
    payload = flask.request.get_json()
    role = 'COSTUMER'

    logger.debug(f'POST /user - payload: {payload}')

    if 'username' not in payload:
        response = {'status': 400, 'results': 'username is null'}
        return flask.jsonify(response), 400
    if 'password' not in payload:
        response = {'status': 400, 'results': 'password is null'}
        return flask.jsonify(response), 400 # TODO encrypt password
    if 'email' not in payload:
        response = {'status': 400, 'results': 'email is null'}
        return flask.jsonify(response), 400 # TODO add email validation
    if 'cc' not in payload:
        response = {'status': 400, 'results': 'cc is null'}
        return flask.jsonify(response), 400 # TODO add cc validation
    if 'name' not in payload:
        response = {'status': 400, 'results': 'name is null'}
        return flask.jsonify(response), 400
    if 'phone' not in payload:
        response = {'status': 400, 'results': 'phone is null'}
        return flask.jsonify(response), 400
    if 'address' not in payload:
        response = {'status': 400, 'results': 'address is null'}
        return flask.jsonify(response), 400
    if 'zip_code' not in payload:
        response = {'status': 400, 'results': 'zip_code is null'}
        return flask.jsonify(response), 400
    if 'city' not in payload:
        response = {'status': 400, 'results': 'city is null'}
        return flask.jsonify(response), 400
    if 'admin_id' in payload or 'artistic_name' in payload:
        role = 'ARTIST'
        if 'artistic_name' not in payload:
            response = {'status': 400, 'results': 'artistic_name is null'}
            return flask.jsonify(response), 400
        if 'publisher_id' not in payload:
            response = {'status': 400, 'results': 'publisher_id is null'}
            return flask.jsonify(response), 400
        if 'admin_id' not in payload:
            response = {'status': 400, 'results': 'admin_id is null'}
            return flask.jsonify(response), 400

    conn = db_connection()
    cur = conn.cursor()

    try:
        statement = 'INSERT INTO login (username, email, password, user_privilege) VALUES (%s, %s, %s, %s) RETURNING id'
        values = (payload['username'], payload['email'], payload['password'], role)
        cur.execute(statement, values)
        login_id = cur.fetchone()[0]

        statement = 'INSERT INTO person (cc, name, created_at, phone, address, zip_code, city, login_id) VALUES (%s, %s, NOW(), %s, %s, %s, %s, %s)'
        values = (payload['cc'], payload['name'], payload['phone'], payload['address'], payload['zip_code'], payload['city'], login_id)
        cur.execute(statement, values)
        if(role == 'ARTIST'):
            token = payload['admin_id']
            data = jwt.decode(token, key=os.getenv('SECRET_KEY'), algorithms=["HS256"])

            if(data['role'] != 'ADMIN'):
                response = flask.jsonify({'status': 401, 'results': 'invalid admin token'}), 401
                return response
            
            statement = 'INSERT INTO artist (artistic_name, administrator_id, publisher_id, login_id) VALUES (%s, %s, %s, %s)'
            values = (payload['artistic_name'], data['id'], payload['publisher_id'], login_id)
            cur.execute(statement, values)
        else:
            statement = 'INSERT INTO consumer (login_id, expire_date) VALUES (%s, NOW())'
            cur.execute(statement, [login_id, ])

        # commit the transaction
        conn.commit()
        response = flask.jsonify({'status': 200, 'results': f'{login_id}'}), 200

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'POST /user - error: {error}')
        response = flask.jsonify({'status': 500, 'errors': str(error)}), 500

        # an error occurred, rollback
        conn.rollback()

    finally:
        if conn is not None:
            conn.close()

    return response

# LOGIN ENDPOINT
@app.route('/user/', methods=['PUT'])
def login_user():
    logger.info('PUT /user')
    payload = flask.request.get_json()

    logger.debug(f'PUT /user - payload: {payload}')

    if 'username' not in payload:
        response = {'status': 400, 'results': 'username is null'}
        return flask.jsonify(response), 400
    if 'password' not in payload:
        response = {'status': 400, 'results': 'password is null'}
        return flask.jsonify(response), 400 # TODO encrypt password

    conn = db_connection()
    cur = conn.cursor()

    try:
        statement = 'SELECT id, username, password, user_privilege FROM login WHERE %s = username AND %s = password'
        values = (payload['username'], payload['password'])
        cur.execute(statement, values)
        user = cur.fetchall()
        
        if(len(user) == 0):
            return flask.jsonify({'status': 404, 'results': 'user not found'}), 404
        else:
            token = jwt.encode({'id': user[0][0], 'role': user[0][3], 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, key=os.getenv('SECRET_KEY'), algorithm="HS256")
            response = flask.jsonify({'status': 200, 'results': f'{token}'}), 200

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'PUT /user - error: {error}')
        response = flask.jsonify({'status': 500, 'errors': str(error)}), 500

    finally:
        if conn is not None:
            conn.close()

    return response


@app.route('/song/', methods=['POST'])
@token_required
def add_song(id, role):
    logger.info('POST /song')
    payload = flask.request.get_json()

    logger.debug(f'POST /song - payload: {payload}')

    conn = db_connection()
    cur = conn.cursor()

    if 'song_name' not in payload:
        response = {'status': 400, 'results': 'song_name is null'}
        return flask.jsonify(response), 400
    if 'publisher_id' not in payload:
        response = {'status': 400, 'results': 'publisher id is null'}
        return flask.jsonify(response), 400
    if 'release_date' not in payload:
        payload['release_date'] = datetime.datetime.now()
    if 'genre' not in payload:
        payload['genre'] = None
    if 'duration' not in payload:
        payload['duration'] = None
    if role != 'ARTIST':
        response = {'status': 400, 'results': 'you are not an artist'}
        return flask.jsonify(response), 400
    if 'other_artists' not in payload:
        payload['other_artists'] = []
    
    try:
        statement = 'INSERT INTO song (title, release_date, publisher_id, artist_id, genre, duration) VALUES (%s, %s, %s, %s, %s, %s) RETURNING ismn'
        values = (payload['song_name'], payload['release_date'], payload['publisher_id'], id, payload['genre'], payload['duration'])
        cur.execute(statement, values)
        song_ismn = cur.fetchone()[0]
        statement = 'INSERT INTO song_feat (artist_id, song_ismn) VALUES' + (' (%s, %s), '*len(payload['other_artists'])) + ' (%s, %s)'
        values = [id, song_ismn]
        for artist in payload['other_artists']:
            values.append(artist)
            values.append(song_ismn)
        cur.execute(statement, values)


        conn.commit()
        response = flask.jsonify({'status': 200, 'results': f'{song_ismn}'}), 200

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'PUT /user - error: {error}')
        response = flask.jsonify({'status': 500, 'errors': str(error)}), 500

        # an error occurred, rollback
        conn.rollback()

    finally:
        if conn is not None:
            conn.close()

    return response


@app.route('/album/', methods=['POST'])
@token_required
def add_album(id, role):
    logger.info('POST /album')
    payload = flask.request.get_json()

    logger.debug(f'POST /album - payload: {payload}')

    conn = db_connection()
    cur = conn.cursor()

    if 'album_name' not in payload:
        response = {'status': 400, 'results': 'album_name is null'}
        return flask.jsonify(response), 400
    if 'publisher_id' not in payload:
        response = {'status': 400, 'results': 'publisher id is null'}
        return flask.jsonify(response), 400
    if 'release_date' not in payload:
        payload['release_date'] = datetime.datetime.now()
    if 'songs' not in payload:
        response = {'status': 400, 'results': 'songs are null'}
        return flask.jsonify(response), 400
    if role != 'ARTIST':
        response = {'status': 400, 'results': 'you are not an artist'}
        return flask.jsonify(response), 400
    
    try:
        statement = 'INSERT INTO album (name, releasedate, publisher_id) VALUES (%s, %s, %s) RETURNING id'
        values = (payload['album_name'], payload['release_date'], payload['publisher_id'])
        cur.execute(statement, values)
        album_id = cur.fetchone()[0]
        song_ismns = []
        for i in range(len(payload['songs'])):
            if('song_name' in payload['songs'][i]):
                if 'other_artists' not in payload['songs'][i]:
                    payload['songs'][i]['other_artists'] = []
                if'release_date' not in payload['songs'][i]:
                    payload['songs'][i]['release_date'] = datetime.datetime.now()
                statement = 'INSERT INTO song (title, release_date, publisher_id, artist_id, genre, duration) VALUES (%s, %s, %s, %s, %s, %s) RETURNING ismn'
                values = (payload['songs'][i]['song_name'], payload['songs'][i]['release_date'], payload['publisher_id'], id, payload['songs'][i]['genre'], payload['songs'][i]['duration'])
                cur.execute(statement, values)
                song_ismn = cur.fetchone()[0]
                values = [id, song_ismn]
                statement = 'INSERT INTO song_feat (artist_id, song_ismn) VALUES' + (' (%s, %s), '*len(payload['songs'][i]['other_artists'])) + ' (%s, %s)'
                for artist in payload['songs'][i]['other_artists']:
                    values.append(artist)
                    values.append(song_ismn)
                cur.execute(statement, values)
                song_ismns.append(song_ismn)
            else:
                song_ismns.append(payload['songs'][i])
        if len(song_ismns) > 0:
            values = []
            statement = 'INSERT INTO album_song_order (album_id, song_ismn, song_order) VALUES' + (' (%s, %s, %s), '*(len(song_ismns)-1)) + ' (%s, %s, %s)'
            for i in range(len(song_ismns)):
                values.append(album_id)
                values.append(str(song_ismns[i]))
                values.append(i)
            cur.execute(statement, values)

        conn.commit()
        response = flask.jsonify({'status': 200, 'results': f'{album_id}'}), 200

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'PUT /user - error: {error}')
        response = flask.jsonify({'status': 500, 'errors': str(error)}), 500

        # an error occurred, rollback
        conn.rollback()

    finally:
        if conn is not None:
            conn.close()

    return response


@app.route('/song/<keyword>', methods=['GET'])
@token_required
def find_song(id, role, keyword):
    logger.info('GET /song')
    keyword = keyword.upper()
    logger.debug(f'get /song - param: {keyword}')

    conn = db_connection()
    cur = conn.cursor()

    
    try:
        statement = f'''SELECT song.title, song.genre, song.duration ,song.publisher_id, 
                            array_agg(distinct artist.artistic_name) FILTER (WHERE song_feat.artist_id IS NOT NULL) as artists , 
                            array_agg(distinct album_song_order.album_id) FILTER (WHERE album_song_order.album_id IS NOT NULL) as albums
                        FROM song
                        LEFT JOIN album_song_order ON (song.ismn = album_song_order.song_ismn)
                        LEFT JOIN song_feat ON (song.ismn = song_feat.song_ismn)
                        INNER JOIN artist ON (artist.login_id = song_feat.artist_id)
                        WHERE UPPER(title) LIKE '%{keyword}%'
                        GROUP BY song.ismn'''
        cur.execute(statement)
        rows = cur.fetchall()

        response = []
        for row in rows:
            response.append({"title": row[0], "genre":row[1], "duration":row[2], "publisher_id": row[3], "artists": row[4], "albums": row[5]})

        response = flask.jsonify({'status': 200, 'results': f'{response}'}), 200

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'PUT /user - error: {error}')
        response = flask.jsonify({'status': 500, 'errors': str(error)}), 500

        # an error occurred, rollback
        conn.rollback()

    finally:
        if conn is not None:
            conn.close()

    return response


@app.route('/artist_info/<artist_id>', methods=['GET'])
@token_required
def find_user(id, role, artist_id):
    logger.info('GET /artist_info')
    logger.debug(f'get /artist_info - param: {artist_id}')

    conn = db_connection()
    cur = conn.cursor()
    
    try: # TODO CHANGE TO ONLY PUBLIC PLAYLISTS
        statement = f'''SELECT artist.artistic_name, artist.publisher_id ,
                            array_agg(DISTINCT song_feat.song_ismn) FILTER (WHERE song_feat.song_ismn IS NOT NULL) as songs,
                            array_agg(DISTINCT album_song_order.album_id) FILTER (WHERE album_song_order.album_id IS NOT NULL) as albums,
                            array_agg(DISTINCT playlist_songs.playlist_id) FILTER (WHERE playlist_songs.playlist_id IS NOT NULL) as playlists
                        FROM artist
                        LEFT JOIN song_feat ON song_feat.artist_id = artist.login_id
                        LEFT JOIN album_song_order ON album_song_order.song_ismn = song_feat.song_ismn
                        LEFT JOIN playlist_songs ON playlist_songs.song_ismn = song_feat.song_ismn
                        INNER JOIN playlist ON playlist.id = playlist_songs.playlist_id WHERE playlist.private = FALSE
                        GROUP BY artist.login_id
                        HAVING artist.login_id = {artist_id}
                        '''
        cur.execute(statement)
        response = cur.fetchall()
        print(response)
        if (len(response) >= 1):
            response = {"artistic_name": response[0][0], "publisher_id": response[0][1], "songs": response[0][2], "albums": response[0][3], "playlists": response[0][4]}
            response = flask.jsonify({'status': 200, 'results': f'{response}'}), 200
        else:
            response = ""
            response = flask.jsonify({'status': 200}), 200
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'PUT /user - error: {error}')
        response = flask.jsonify({'status': 500, 'errors': str(error)}), 500

        # an error occurred, rollback
        conn.rollback()

    finally:
        if conn is not None:
            conn.close()

    return response

@app.route('/card/', methods=['POST'])
@token_required
def add_card(id, role):
    logger.info('POST /card')
    payload = flask.request.get_json()
    logger.debug(f'get /card - param: {payload}')

    conn = db_connection()
    cur = conn.cursor()
    limit_date = datetime.date.today() + datetime.timedelta(days=365)
    if 'number_cards' not in payload and payload['number_cards'] < 1:
        return flask.jsonify({'status': 400, 'errors': 'Missing number_cards'}), 400
    if 'card_price' not in payload:
        return flask.jsonify({'status': 400, 'errors': 'Missing card_price'}), 400
    if 'limit_date' in payload:
        limit_date = payload['limit_date']
    if role != 'ADMIN':
        return flask.jsonify({'status': 403, 'errors': 'Forbidden'}), 403
    
    try:
        statement = 'INSERT INTO pay_card (id, limit_date, price, ammount_left, admin_id) VALUES' + ' (%s, %s, %s, %s, %s),'*(int(payload['number_cards'])-1) + ' (%s, %s, %s, %s, %s)' 

        values = []
        ids = []
        for i in range(int(payload['number_cards'])):
            ids.append(''.join(random.choices(string.ascii_letters + string.digits, k=16)))
            values += [ids[i], limit_date, payload['card_price'], payload['card_price'], id]
        print(values)
        cur.execute(statement, values)
        conn.commit()
        
        response = flask.jsonify({'status': 200, 'results': f'{ids}'}), 200

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'PUT /user - error: {error}')
        response = flask.jsonify({'status': 500, 'errors': str(error)}), 500

        # an error occurred, rollback
        conn.rollback()

    finally:
        if conn is not None:
            conn.close()

    return response

@app.route('/comments/<song_id>',defaults={'parent_comment_id': None}, methods=['POST'])
@app.route('/comments/<song_id>/<parent_comment_id>', methods=['POST'])
@token_required
def add_comment(id, role, song_id, parent_comment_id):

    logger.info('POST /comments')
    payload = flask.request.get_json()
    logger.debug(f'POST /comments - param: {payload}')

    conn = db_connection()
    cur = conn.cursor()

    if 'comment' not in payload:
        return flask.jsonify({'status': 400, 'errors': 'Missing comment'}), 400
    
    try:
        statement = 'INSERT INTO comment (comment, song_ismn, consumer_id, comment_id) VALUES (%s, %s, %s, %s) RETURNING id'
        values = [payload['comment'], song_id, id, parent_comment_id]
        cur.execute(statement, values)
        conn.commit()
        response = cur.fetchone()[0]
        
        response = flask.jsonify({'status': 200, 'results': f'{response}'}), 200

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'PUT /user - error: {error}')
        response = flask.jsonify({'status': 500, 'errors': str(error)}), 500

        # an error occurred, rollback
        conn.rollback()

    finally:
        if conn is not None:
            conn.close()

    return response


    logger.info('POST /subscription')
    payload = flask.request.get_json()
    logger.debug(f'POST /subscription - param: {payload}')

    conn = db_connection()
    cur = conn.cursor()

    if 'period' not in payload or payload['period'].upper() not in ['MONTH', 'QUARTER', 'SEMESTER']:
        return flask.jsonify({'status': 400, 'errors': 'Missing period'}), 400
    if 'cards' not in payload or len(payload['cards']) < 1:
        return flask.jsonify({'status': 400, 'errors': 'Missing cards'}), 400
    if 'COSTUMER' != role:
        return flask.jsonify({'status': 403, 'errors': 'Forbidden'}), 403

    try:
        interval = 0
        if(payload['period'].upper() == 'MONTH'):
            interval = '1 month'
        elif(payload['period'].upper() == 'QUARTER'):
            interval = '3 month'
        elif(payload['period'].upper() == 'SEMESTER'):
            interval = '6 month'

        #! change to procedure
        statement = f"SELECT id, price FROM plan WHERE duration = '{payload['period'].upper()}' AND active = TRUE"
        values = [payload['period'].upper()]
        cur.execute(statement, values)
        response = cur.fetchall()
        print(response)

        if len(response) != 1:
            return flask.jsonify({'status': 400, 'errors': 'No plan found'}), 400
        plan_id = response[0][0]
        price = response[0][1]  
        cards_ids = str(payload['cards']).replace('[', '(').replace(']', ')')

        statement = f'UPDATE pay_card SET customer_id = %s WHERE customer_id IS NULL AND id IN {cards_ids}'
        values = [id]
        cur.execute(statement, values)

        statement = f'SELECT id, ammount_left FROM pay_card WHERE customer_id IS NOT NULL AND customer_id = {id} AND ammount_left > 0 AND limit_date > NOW() AND id IN {cards_ids}'
        cur.execute(statement)
        cards = cur.fetchall()

        if len(cards) != len(payload['cards']):
            return flask.jsonify({'status': 400, 'errors': 'Invalid cards inserted'}), 400

        sum = 0
        for card in cards:
            sum += card[1]
        print(sum, price, "HERE")
        if sum < price:
            return flask.jsonify({'status': 400, 'errors': 'Insufficient balance in the cards'}), 400
        
        statement = f'SELECT id, ammount_left FROM pay_card WHERE customer_id IS NOT NULL AND customer_id = {id} AND ammount_left > 0 AND limit_date > NOW() AND id IN {cards_ids}'
        cur.execute(statement)
        cards = cur.fetchall()

        statement = 'INSERT INTO subscription (movement_date, plan_id, consumer_id) VALUES (NOW(), %s, %s) RETURNING id'
        values = [plan_id, id]
        cur.execute(statement, values)
        sub_id = cur.fetchone()[0]

        statement = f'''
                    DO $$
                    DECLARE 
                        left_pay INT := {price};
                        spent INT := 0;
                        c1 cursor FOR 
                        SELECT id, ammount_left 
                        FROM pay_card 
                        WHERE customer_id IS NOT NULL AND customer_id = {id} 
                        AND ammount_left > 0 
                        AND limit_date > NOW() 
                        AND id IN {cards_ids};
                    BEGIN
                    FOR card IN c1
                        LOOP
                            IF card.ammount_left >= left_pay THEN
                                spent := left_pay;
                                UPDATE pay_card SET ammount_left = card.ammount_left-left_pay WHERE id = card.id;
                                left_pay := 0;
                                INSERT INTO subscription_ACTIVITY (subscription_id, pay_card_id, ammount) 
                                VALUES ({sub_id}, card.id, spent);
                                EXIT;
                            ELSE
                                spent := card.ammount_left;
                                left_pay := left_pay - card.ammount_left;
                                UPDATE pay_card SET ammount_left = 0 WHERE id = card.id;
                                INSERT INTO subscription_ACTIVITY (subscription_id, pay_card_id, ammount) 
                                VALUES ({sub_id}, card.id, spent);
                            END IF;
                        END LOOP;
                    END $$;'''
        cur.execute(statement)

        statement = '''
                    UPDATE consumer 
                    SET expire_date =
                        CASE WHEN expire_date < NOW() THEN NOW() +  INTERVAL %s ELSE expire_date +  INTERVAL %s END
                        WHERE login_id = %s
                    '''
        values = [interval, interval, id]
        cur.execute(statement, values)        

        conn.commit()
        
        response = flask.jsonify({'status': 200, 'results': f'{sub_id}'}), 200

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'PUT /user - error: {error}')
        response = flask.jsonify({'status': 500, 'errors': str(error)}), 500

        # an error occurred, rollback
        conn.rollback()

    finally:
        if conn is not None:
            conn.close()

    return response

@app.route('/subscription/', methods=['POST'])
@token_required
def add_subscription(id, role):

    logger.info('POST /subscription')
    payload = flask.request.get_json()
    logger.debug(f'POST /subscription - param: {payload}')

    conn = db_connection()
    cur = conn.cursor()

    if 'period' not in payload or payload['period'].upper() not in ['MONTH', 'QUARTER', 'SEMESTER']:
        return flask.jsonify({'status': 400, 'errors': 'Missing period'}), 400
    if 'cards' not in payload or len(payload['cards']) < 1:
        return flask.jsonify({'status': 400, 'errors': 'Missing cards'}), 400
    if 'COSTUMER' != role:
        return flask.jsonify({'status': 403, 'errors': 'Forbidden'}), 403

    try:
        interval = 0
        if(payload['period'].upper() == 'MONTH'):
            interval = '1 month'
        elif(payload['period'].upper() == 'QUARTER'):
            interval = '3 month'
        elif(payload['period'].upper() == 'SEMESTER'):
            interval = '6 month'

        statement = f"SELECT id, price FROM plan WHERE duration = '{payload['period'].upper()}' AND active = TRUE"
        values = [payload['period'].upper()]
        cur.execute(statement, values)
        response = cur.fetchall()
        print(response)

        if len(response) != 1:
            return flask.jsonify({'status': 400, 'errors': 'No plan found'}), 400
        plan_id = response[0][0]
        price = response[0][1]  
        cards_ids = str(payload['cards']).replace('[', '(').replace(']', ')')

        statement = f'UPDATE pay_card SET customer_id = %s WHERE customer_id IS NULL AND id IN {cards_ids}'
        values = [id]
        cur.execute(statement, values)

        statement = f'SELECT id, ammount_left FROM pay_card WHERE customer_id IS NOT NULL AND customer_id = {id} AND ammount_left > 0 AND limit_date > NOW() AND id IN {cards_ids}'
        cur.execute(statement)
        cards = cur.fetchall()

        if len(cards) != len(payload['cards']):
            return flask.jsonify({'status': 400, 'errors': 'Invalid cards inserted'}), 400

        sum = 0
        for card in cards:
            sum += card[1]
        print(sum, price, "HERE")
        if sum < price:
            return flask.jsonify({'status': 400, 'errors': 'Insufficient balance in the cards'}), 400

        statement = 'INSERT INTO subscription (movement_date, plan_id, consumer_id) VALUES (NOW(), %s, %s) RETURNING id'
        values = [plan_id, id]
        cur.execute(statement, values)
        sub_id = cur.fetchone()[0]

        statement = f'''
                    DO $$
                    DECLARE 
                        left_pay INT := {price};
                        spent INT := 0;
                        c1 cursor FOR 
                        SELECT id, ammount_left 
                        FROM pay_card 
                        WHERE customer_id IS NOT NULL AND customer_id = {id} 
                        AND ammount_left > 0 
                        AND limit_date > NOW() 
                        AND id IN {cards_ids};
                    BEGIN
                    FOR card IN c1
                        LOOP
                            IF card.ammount_left >= left_pay THEN
                                spent := left_pay;
                                UPDATE pay_card SET ammount_left = card.ammount_left-left_pay WHERE id = card.id;
                                left_pay := 0;
                                INSERT INTO subscription_ACTIVITY (subscription_id, pay_card_id, ammount) 
                                VALUES ({sub_id}, card.id, spent);
                                EXIT;
                            ELSE
                                spent := card.ammount_left;
                                left_pay := left_pay - card.ammount_left;
                                UPDATE pay_card SET ammount_left = 0 WHERE id = card.id;
                                INSERT INTO subscription_ACTIVITY (subscription_id, pay_card_id, ammount) 
                                VALUES ({sub_id}, card.id, spent);
                            END IF;
                        END LOOP;
                    END $$;'''
        cur.execute(statement)

        statement = '''
                    UPDATE consumer 
                    SET expire_date =
                        CASE WHEN expire_date < NOW() THEN NOW() +  INTERVAL %s ELSE expire_date +  INTERVAL %s END
                        WHERE login_id = %s
                    '''
        values = [interval, interval, id]
        cur.execute(statement, values)        

        conn.commit()
        
        response = flask.jsonify({'status': 200, 'results': f'{sub_id}'}), 200

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'PUT /user - error: {error}')
        response = flask.jsonify({'status': 500, 'errors': str(error)}), 500

        # an error occurred, rollback
        conn.rollback()

    finally:
        if conn is not None:
            conn.close()

    return response

@app.route('/playlist/', methods=['POST'])
@token_required
def add_playlist(id, role):
    logger.info('POST /playlist')
    payload = flask.request.get_json()
    logger.debug(f'POST /playlist - param: {payload}')

    conn = db_connection()
    cur = conn.cursor()

    if 'playlist_name' not in payload:
        return flask.jsonify({'status': 400, 'errors': 'Missing playlist_name'}), 400
    if 'songs' not in payload or len(payload['songs']) < 1:
        return flask.jsonify({'status': 400, 'errors': 'Missing songs'}), 400
    if 'visibility' not in payload or payload['visibility'].upper() not in ['PUBLIC', 'PRIVATE']:
        return flask.jsonify({'status': 400, 'errors': 'Missing visibility'}), 400
    if 'COSTUMER' != role:
        return flask.jsonify({'status': 403, 'errors': 'Forbidden'}), 403

    try:
        statement = "SELECT * FROM consumer WHERE login_id = %s AND expire_date > NOW()"
        values = [id]
        cur.execute(statement, values)
        response = cur.fetchall()
        
        if len(response) != 1:
            return flask.jsonify({'status': 400, 'errors': 'User does not have premium'}), 400
        
        visibility = 'FALSE'
        if payload['visibility'].upper() == 'PRIVATE':
            visibility = 'TRUE'
        statement = "INSERT INTO playlist (name, private, creator_id, created_at) VALUES (%s, %s, %s, NOW()) RETURNING id"
        values = [payload['playlist_name'], visibility, id]
        cur.execute(statement, values)
        playlist_id = cur.fetchone()[0]

        statement = "INSERT INTO playlist_songs (playlist_id, song_ismn) VALUES" + " (%s, %s),"*(len(payload['songs'])-1) + " (%s, %s)"
        values = []
        for song in payload['songs']:
            values += [playlist_id, song]
        cur.execute(statement, values)

        response = flask.jsonify({'status': 200, 'results': f'{playlist_id}'}), 200
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'PUT /user - error: {error}')
        response = flask.jsonify({'status': 500, 'errors': str(error)}), 500

        # an error occurred, rollback
        conn.rollback()

    finally:
        if conn is not None:
            conn.close()

    return response

@app.route('/<song_id>', methods=['PUT'])
@token_required
def play_song(id, role, song_id):
    logger.info('PUT /playlist')

    conn = db_connection()
    cur = conn.cursor()

    if 'COSTUMER' != role:
        return flask.jsonify({'status': 403, 'errors': 'Forbidden'}), 403

    try:
        statement = "INSERT INTO activity(listen_date, consumer_id, song_ismn) VALUES (NOW(), %s, %s)"
        values = [id, song_id]
        cur.execute(statement, values)

        response = flask.jsonify({'status': 200}), 200
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'PUT /user - error: {error}')
        response = flask.jsonify({'status': 500, 'errors': str(error)}), 500

        # an error occurred, rollback
        conn.rollback()

    finally:
        if conn is not None:
            conn.close()

    return response

@app.route('/report/<year_month>', methods=['GET'])
@token_required
def report(id, role, year_month):
    logger.info('GET /report')
    year_month = year_month
    conn = db_connection()
    cur = conn.cursor()

    try:
        statement = f'''SELECT EXTRACT(MONTH FROM activity.listen_date) as month,  song.genre as genre, COUNT(*) as playbacks
                        FROM activity
                        LEFT JOIN song ON song.ismn = activity.song_ismn
                        WHERE activity.listen_date BETWEEN TO_DATE('{year_month}','YYYY-MM') - (INTERVAL '1 year') AND TO_DATE('{year_month}','YYYY-MM')
                        GROUP BY month, genre
                        ORDER BY month, genre
                        '''
        cur.execute(statement)
        rows = cur.fetchall()
        response = []
        for i in rows:
            response.append({'month': i[0], 'genre': i[1], 'playbacks': i[2]})
        response = flask.jsonify({'status': 200, 'results': response}), 200
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'PUT /user - error: {error}')
        response = flask.jsonify({'status': 500, 'errors': str(error)}), 500
    finally:
        if conn is not None:
            conn.close()

    return response


if __name__ == '__main__':

    # # set up logging
    logger = logging.getLogger('logger')
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # # create formatter
    formatter = logging.Formatter('%(asctime)s [%(levelname)s]:  %(message)s', '%H:%M:%S')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    host = '127.0.0.1'
    port = 8080
    app.run(host=host, debug=True, threaded=True, port=port)
    logger.info(f'API v1.0 online: http://{host}:{port}/dbproj')


