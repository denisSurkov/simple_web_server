from sanic import Sanic
from sanic.response import json
from pymongo import MongoClient

from bson.objectid import ObjectId
from bson.errors import InvalidId

app = Sanic(name="simple-web-server")
mongo_client = MongoClient(host='localhost', port=27017)
users_db = mongo_client['users']


def _check_field_in_request(request, *fields):
    json_ = request.json
    return all(map(lambda f: f in json_, fields))


def _error_msg(msg, status_code=400):
    return json({'error': msg}, status=status_code)


@app.route('/user', methods=("POST", ))
async def create_new_user(request):
    json_ = request.json

    if 'name' not in json_:
        return _error_msg("missing name parameter")

    answer = users_db.users.insert_one(json_).inserted_id
    return json({'name': json_["name"], 'id': str(answer)})


@app.route('/users/<user_id>', methods=('GET', ))
async def get_user_by_id(request, user_id: str):
    answer = users_db.users.find_one({"_id": ObjectId(user_id)})

    if not answer:
        return _error_msg("no such user with id %s" % user_id)

    return json({'id': str(answer['_id']), 'name': answer['name']})


@app.route('/users/<user_id>', methods=('PUT', ))
async def update_user_by_id(request, user_id: str):
    json_ = request.json

    if not _check_field_in_request(request, 'name'):
        return _error_msg("missing name parameter")

    try:
        ob_id_user_id = ObjectId(str(user_id))
    except InvalidId:
        return json({"error": "invalid user_id"}, status=400)

    answer = users_db.users.update_one({"_id": ob_id_user_id}, {"$set": {"name": json_['name']}})

    if answer.matched_count == 0:
        return json({"error": "no such user to update with id %s" % user_id})

    return json({"id": user_id, "name": json_["name"]}, 200)


@app.route('/users', methods=('GET', ))
async def get_all_users(request):
    result = users_db.users.find({})

    total_json = [{id: str(user['_id']), 'name': user['name']} for user in result]
    return json(total_json)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
